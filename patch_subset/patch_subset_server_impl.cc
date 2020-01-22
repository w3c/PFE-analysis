#include "patch_subset/patch_subset_server_impl.h"

#include <stdio.h>

#include "absl/strings/string_view.h"
#include "common/logging.h"
#include "hb-subset.h"
#include "hb.h"
#include "patch_subset/compressed_set.h"
#include "patch_subset/hb_set_unique_ptr.h"
#include "patch_subset/patch_subset.pb.h"

using ::absl::string_view;

namespace patch_subset {

StatusCode PatchSubsetServerImpl::Handle(const std::string& font_id,
                                         const PatchRequestProto& request,
                                         PatchResponseProto* response) {
  // TODO(garretrieger): check fingerprint on codepoint remapping
  //                     (if this is a patch request).
  // TODO(garretrieger): apply codepoint remapping when decoding code point
  // sets.
  //                     (if this is a patch request).

  hb_set_unique_ptr codepoints_have = make_hb_set();
  CompressedSet::Decode(request.codepoints_have(), codepoints_have.get());

  hb_set_unique_ptr codepoints_needed = make_hb_set();
  CompressedSet::Decode(request.codepoints_needed(), codepoints_needed.get());
  hb_set_union(codepoints_needed.get(), codepoints_have.get());

  FontData font_data;
  StatusCode result;
  if (!Check(result = font_provider_->GetFont(font_id, &font_data),
             "Failed to load font (font_id = " + font_id + ").")) {
    return result;
  }

  if (!hb_set_is_empty(codepoints_have.get()) &&
      !Check(result = ValidateFingerPrint(request.original_font_fingerprint(),
                                          font_data),
             "Client's original fingerprint does not match. Switching to "
             "REBASE.")) {
    hb_set_clear(codepoints_have.get());
  }

  FontData client_subset;
  FontData client_target_subset;
  result =
      ComputeSubsets(font_id, font_data, *codepoints_have, *codepoints_needed,
                     &client_subset, &client_target_subset);
  if (!Check(result)) {
    return result;
  }

  if (!hb_set_is_empty(codepoints_have.get()) &&
      !Check(result =
                 ValidateFingerPrint(request.base_fingerprint(), client_subset),
             "Client's base does not match. Switching to REBASE.")) {
    // Clear the client_subset since it doesn't match. The diff will then diff
    // in rebase mode.
    client_subset.reset();
    hb_set_clear(codepoints_have.get());
  }

  FontData patch;
  if (!Check(result = binary_diff_->Diff(client_subset, client_target_subset,
                                         &patch),
             "Diff computation failed (font_id = " + font_id + ").")) {
    return result;
  }
  // TODO(garretrieger): rename the proto package.
  // TODO(garretrieger): check which diffs the client supports.
  // TODO(garretrieger): handle exceptional cases (see design doc).

  if (hb_set_get_population(codepoints_have.get()) == 0) {
    response->set_type(ResponseType::REBASE);
    if (codepoint_mapper_) {
      AddCodepointRemapping(font_data, response->mutable_codepoint_remapping());
    }
  } else {
    response->set_type(ResponseType::PATCH);
  }
  PatchProto* patch_proto = response->mutable_patch();
  patch_proto->set_format(PatchFormat::BROTLI_SHARED_DICT);
  patch_proto->set_patch(patch.data(), patch.size());

  AddFingerprints(font_data, client_target_subset, response);

  return StatusCode::kOk;
}

void PatchSubsetServerImpl::AddCodepointRemapping(
    const FontData& font_data, CodepointRemappingProto* response) {
  hb_set_t* codepoints = hb_set_create();
  subsetter_->CodepointsInFont(font_data, codepoints);

  std::vector<hb_codepoint_t> mapping;
  codepoint_mapper_->ComputeMapping(*codepoints, &mapping);

  int previous_cp = 0;
  for (hb_codepoint_t cp : mapping) {
    response->mutable_codepoint_ordering()->add_deltas(cp - previous_cp);
    previous_cp = cp;
  }

  // TODO(garretrieger): add a grouping strategy if it's needed.

  response->set_fingerprint(codepoint_mapping_checksum_->Checksum(*response));
}

StatusCode PatchSubsetServerImpl::ComputeSubsets(
    const std::string& font_id, const FontData& font_data,
    const hb_set_t& codepoints_have, const hb_set_t& codepoints_needed,
    FontData* client_subset, FontData* client_target_subset) {
  StatusCode result =
      subsetter_->Subset(font_data, codepoints_have, client_subset);
  if (result != StatusCode::kOk) {
    LOG(WARNING) << "Subsetting for client_subset "
                 << "(font_id = " << font_id << ")"
                 << "failed.";
    return result;
  }

  result =
      subsetter_->Subset(font_data, codepoints_needed, client_target_subset);
  if (result != StatusCode::kOk) {
    LOG(WARNING) << "Subsetting for client_target_subset "
                 << "(font_id = " << font_id << ")"
                 << "failed.";
    return result;
  }

  return result;
}

StatusCode PatchSubsetServerImpl::ValidateFingerPrint(uint64_t fingerprint,
                                                      const FontData& data) {
  if (hasher_->Checksum(data.str()) != fingerprint) {
    return StatusCode::kInvalidArgument;
  }
  return StatusCode::kOk;
}

void PatchSubsetServerImpl::AddFingerprints(const FontData& font_data,
                                            const FontData& target_subset,
                                            PatchResponseProto* response) {
  response->set_original_font_fingerprint(
      hasher_->Checksum(string_view(font_data.str())));
  response->mutable_patch()->set_patched_fingerprint(
      hasher_->Checksum(string_view(target_subset.str())));
}

bool PatchSubsetServerImpl::Check(StatusCode result) {
  return result == StatusCode::kOk;
}

bool PatchSubsetServerImpl::Check(StatusCode result,
                                  const std::string& message) {
  if (result == StatusCode::kOk) {
    return true;
  }
  LOG(WARNING) << message;
  return false;
}

}  // namespace patch_subset
