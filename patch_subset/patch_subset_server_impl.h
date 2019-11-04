#ifndef PATCH_SUBSET_PATCH_SUBSET_SERVER_IMPL_H_
#define PATCH_SUBSET_PATCH_SUBSET_SERVER_IMPL_H_

#include <string>

#include "common/status.h"
#include "hb.h"
#include "patch_subset/binary_diff.h"
#include "patch_subset/font_provider.h"
#include "patch_subset/hasher.h"
#include "patch_subset/patch_subset.pb.h"
#include "patch_subset/patch_subset_server.h"
#include "patch_subset/subsetter.h"

namespace patch_subset {

class PatchSubsetServerImpl : public PatchSubsetServer {
 public:
  // Takes ownership of font_provider, subsetter, and binary_diff.
  PatchSubsetServerImpl(std::unique_ptr<FontProvider> font_provider,
                        std::unique_ptr<Subsetter> subsetter,
                        std::unique_ptr<BinaryDiff> binary_diff,
                        std::unique_ptr<Hasher> hasher)
      : font_provider_(std::move(font_provider)),
        subsetter_(std::move(subsetter)),
        binary_diff_(std::move(binary_diff)),
        hasher_(std::move(hasher)) {}

  // Handle a patch request from a client. Writes the resulting response
  // into response.
  StatusCode Handle(const std::string& font_id,
                    const PatchRequestProto& request,
                    PatchResponseProto* response /* OUT */) override;

 private:
  StatusCode ComputeSubsets(const std::string& font_id,
                            const FontData& font_data,
                            const hb_set_t& codepoints_have,
                            const hb_set_t& codepoints_needed,
                            FontData* client_subset,
                            FontData* client_target_subset);

  StatusCode ValidateFingerPrint(uint64_t fingerprint, const FontData& data);

  void AddFingerprints(const FontData& font_data, const FontData& target_subset,
                       PatchResponseProto* response);

  bool Check(StatusCode result);
  bool Check(StatusCode result, const std::string& message);

  std::unique_ptr<FontProvider> font_provider_;
  std::unique_ptr<Subsetter> subsetter_;
  std::unique_ptr<BinaryDiff> binary_diff_;
  std::unique_ptr<Hasher> hasher_;
};

}  // namespace patch_subset

#endif  // PATCH_SUBSET_PATCH_SUBSET_SERVER_IMPL_H_
