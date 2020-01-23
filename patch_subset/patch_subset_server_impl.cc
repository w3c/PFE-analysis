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

// Helper object, which holds all of the relevant state for
// handling a single request.
struct RequestState {
  RequestState()
      : codepoints_have(make_hb_set()), codepoints_needed(make_hb_set()) {}

  bool IsPatch() const { return !hb_set_is_empty(codepoints_have.get()); }

  bool IsRebase() const { return !IsPatch(); }

  hb_set_unique_ptr codepoints_have;
  hb_set_unique_ptr codepoints_needed;
  FontData font_data;
  FontData client_subset;
  FontData client_target_subset;
  FontData patch;
};

StatusCode PatchSubsetServerImpl::Handle(const std::string& font_id,
                                         const PatchRequestProto& request,
                                         PatchResponseProto* response) {
  RequestState state;

  LoadInputCodepoints(request, &state);

  StatusCode result;
  if (!Check(result = font_provider_->GetFont(font_id, &state.font_data),
             "Failed to load font (font_id = " + font_id + ").")) {
    return result;
  }

  CheckOriginalFingerprint(request.original_font_fingerprint(), &state);

  if (!Check(result = ComputeSubsets(font_id, &state))) {
    return result;
  }

  ValidatePatchBase(request.base_fingerprint(), &state);

  if (!Check(result = binary_diff_->Diff(
                 state.client_subset, state.client_target_subset, &state.patch),
             "Diff computation failed (font_id = " + font_id + ").")) {
    return result;
  }

  // TODO(garretrieger): rename the proto package.
  // TODO(garretrieger): check which diffs the client supports.
  // TODO(garretrieger): handle exceptional cases (see design doc).

  ConstructResponse(state, response);

  return StatusCode::kOk;
}

void PatchSubsetServerImpl::LoadInputCodepoints(
    const PatchRequestProto& request, RequestState* state) const {
  CompressedSet::Decode(request.codepoints_have(),
                        state->codepoints_have.get());
  CompressedSet::Decode(request.codepoints_needed(),
                        state->codepoints_needed.get());
  hb_set_union(state->codepoints_needed.get(), state->codepoints_have.get());

  // TODO(garretrieger): add a function that adjusts the codepoint sets (if
  // codepoints_have is set
  //   and we have a remapper available).
  //   Should also check the fingerprint and return failure if it doesn't match.
  //   On a no match, terminate early and send a re-index response.
}

void PatchSubsetServerImpl::CheckOriginalFingerprint(
    uint64_t original_fingerprint, RequestState* state) const {
  if (state->IsPatch() &&
      !Check(ValidateFingerPrint(original_fingerprint, state->font_data),
             "Client's original fingerprint does not match. Switching to "
             "REBASE.")) {
    hb_set_clear(state->codepoints_have.get());
  }
}

void PatchSubsetServerImpl::AddCodepointRemapping(
    const FontData& font_data, CodepointRemappingProto* response) const {
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

StatusCode PatchSubsetServerImpl::ComputeSubsets(const std::string& font_id,
                                                 RequestState* state) const {
  StatusCode result = subsetter_->Subset(
      state->font_data, *state->codepoints_have, &state->client_subset);
  if (result != StatusCode::kOk) {
    LOG(WARNING) << "Subsetting for client_subset "
                 << "(font_id = " << font_id << ")"
                 << "failed.";
    return result;
  }

  result = subsetter_->Subset(state->font_data, *state->codepoints_needed,
                              &state->client_target_subset);
  if (result != StatusCode::kOk) {
    LOG(WARNING) << "Subsetting for client_target_subset "
                 << "(font_id = " << font_id << ")"
                 << "failed.";
    return result;
  }

  return result;
}

void PatchSubsetServerImpl::ValidatePatchBase(uint64_t base_fingerprint,
                                              RequestState* state) const {
  if (state->IsPatch() &&
      !Check(ValidateFingerPrint(base_fingerprint, state->client_subset),
             "Client's base does not match. Switching to REBASE.")) {
    // Clear the client_subset since it doesn't match. The diff will then diff
    // in rebase mode.
    state->client_subset.reset();
    hb_set_clear(state->codepoints_have.get());
  }
}

void PatchSubsetServerImpl::ConstructResponse(
    const RequestState& state, PatchResponseProto* response) const {
  if (state.IsRebase()) {
    response->set_type(ResponseType::REBASE);
    if (codepoint_mapper_) {
      AddCodepointRemapping(state.font_data,
                            response->mutable_codepoint_remapping());
    }
  } else {
    response->set_type(ResponseType::PATCH);
  }
  PatchProto* patch_proto = response->mutable_patch();
  patch_proto->set_format(PatchFormat::BROTLI_SHARED_DICT);
  patch_proto->set_patch(state.patch.data(), state.patch.size());

  AddFingerprints(state.font_data, state.client_target_subset, response);
}

StatusCode PatchSubsetServerImpl::ValidateFingerPrint(
    uint64_t fingerprint, const FontData& data) const {
  if (hasher_->Checksum(data.str()) != fingerprint) {
    return StatusCode::kInvalidArgument;
  }
  return StatusCode::kOk;
}

void PatchSubsetServerImpl::AddFingerprints(
    const FontData& font_data, const FontData& target_subset,
    PatchResponseProto* response) const {
  response->set_original_font_fingerprint(
      hasher_->Checksum(string_view(font_data.str())));
  response->mutable_patch()->set_patched_fingerprint(
      hasher_->Checksum(string_view(target_subset.str())));
}

bool PatchSubsetServerImpl::Check(StatusCode result) const {
  return result == StatusCode::kOk;
}

bool PatchSubsetServerImpl::Check(StatusCode result,
                                  const std::string& message) const {
  if (result == StatusCode::kOk) {
    return true;
  }
  LOG(WARNING) << message;
  return false;
}

}  // namespace patch_subset
