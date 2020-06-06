#ifndef PATCH_SUBSET_PATCH_SUBSET_SERVER_IMPL_H_
#define PATCH_SUBSET_PATCH_SUBSET_SERVER_IMPL_H_

#include <string>

#include "common/status.h"
#include "hb.h"
#include "patch_subset/binary_diff.h"
#include "patch_subset/brotli_binary_diff.h"
#include "patch_subset/codepoint_mapper.h"
#include "patch_subset/codepoint_mapping_checksum.h"
#include "patch_subset/codepoint_mapping_checksum_impl.h"
#include "patch_subset/farm_hasher.h"
#include "patch_subset/file_font_provider.h"
#include "patch_subset/font_provider.h"
#include "patch_subset/harfbuzz_subsetter.h"
#include "patch_subset/hasher.h"
#include "patch_subset/patch_subset.pb.h"
#include "patch_subset/patch_subset_server.h"
#include "patch_subset/simple_codepoint_mapper.h"
#include "patch_subset/subsetter.h"

namespace patch_subset {

struct RequestState;

class PatchSubsetServerImpl : public PatchSubsetServer {
 public:
  static std::unique_ptr<PatchSubsetServer> CreateServer(
      const std::string& font_directory, const std::string& default_font_id, bool with_codepoint_remapping) {
    Hasher* hasher = new FarmHasher();
    CodepointMapper* codepoint_mapper =
        with_codepoint_remapping ? new SimpleCodepointMapper() : nullptr;
    CodepointMappingChecksum* mapping_checksum =
        with_codepoint_remapping ? new CodepointMappingChecksumImpl(hasher)
                                 : nullptr;
    return std::unique_ptr<PatchSubsetServer>(new PatchSubsetServerImpl(
        std::unique_ptr<FontProvider>(new FileFontProvider(font_directory, default_font_id)),
        std::unique_ptr<Subsetter>(new HarfbuzzSubsetter()),
        std::unique_ptr<BinaryDiff>(new BrotliBinaryDiff()),
        std::unique_ptr<Hasher>(hasher),
        std::unique_ptr<CodepointMapper>(codepoint_mapper),
        std::unique_ptr<CodepointMappingChecksum>(mapping_checksum)));
  }

  // Takes ownership of font_provider, subsetter, and binary_diff.
  PatchSubsetServerImpl(
      std::unique_ptr<FontProvider> font_provider,
      std::unique_ptr<Subsetter> subsetter,
      std::unique_ptr<BinaryDiff> binary_diff, std::unique_ptr<Hasher> hasher,
      std::unique_ptr<CodepointMapper> codepoint_mapper,
      std::unique_ptr<CodepointMappingChecksum> codepoint_mapping_checksum)
      : font_provider_(std::move(font_provider)),
        subsetter_(std::move(subsetter)),
        binary_diff_(std::move(binary_diff)),
        hasher_(std::move(hasher)),
        codepoint_mapper_(std::move(codepoint_mapper)),
        codepoint_mapping_checksum_(std::move(codepoint_mapping_checksum)) {}

  // Handle a patch request from a client. Writes the resulting response
  // into response.
  StatusCode Handle(const std::string& font_id,
                    const PatchRequestProto& request,
                    PatchResponseProto* response /* OUT */) override;

 private:
  void LoadInputCodepoints(const PatchRequestProto& request,
                           RequestState* state) const;

  void CheckOriginalFingerprint(uint64_t original_fingerprint,
                                RequestState* state) const;

  StatusCode ComputeCodepointRemapping(RequestState* state) const;

  void AddCodepointRemapping(const RequestState& state,
                             CodepointRemappingProto* response) const;

  StatusCode ComputeSubsets(const std::string& font_id,
                            RequestState* state) const;

  void ValidatePatchBase(uint64_t base_fingerprint, RequestState* state) const;

  void ConstructResponse(const RequestState& state,
                         PatchResponseProto* response) const;

  StatusCode ValidateFingerPrint(uint64_t fingerprint,
                                 const FontData& data) const;

  void AddFingerprints(const FontData& font_data, const FontData& target_subset,
                       PatchResponseProto* response) const;

  void AddFingerprints(const FontData& font_data,
                       PatchResponseProto* response) const;

  bool Check(StatusCode result) const;
  bool Check(StatusCode result, const std::string& message) const;

  std::unique_ptr<FontProvider> font_provider_;
  std::unique_ptr<Subsetter> subsetter_;
  std::unique_ptr<BinaryDiff> binary_diff_;
  std::unique_ptr<Hasher> hasher_;
  std::unique_ptr<CodepointMapper> codepoint_mapper_;
  std::unique_ptr<CodepointMappingChecksum> codepoint_mapping_checksum_;
};

}  // namespace patch_subset

#endif  // PATCH_SUBSET_PATCH_SUBSET_SERVER_IMPL_H_
