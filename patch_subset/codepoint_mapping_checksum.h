#ifndef PATCH_SUBSET_CODEPOINT_MAPPING_CHECKSUM_H_
#define PATCH_SUBSET_CODEPOINT_MAPPING_CHECKSUM_H_

#include "patch_subset/hasher.h"
#include "patch_subset/patch_subset.pb.h"

namespace patch_subset {

// Interface to a codepoint mapper.
class CodepointMappingChecksum {
 public:
  // Does not take ownership of hasher. hasher must live longer than this
  // object.
  CodepointMappingChecksum(Hasher* hasher) : hasher_(hasher) {}

  // Compute a checksum for the provided CodepointRemappingProto. This
  // checksum function must be stable. It should always return the same
  // value for the same input proto.
  uint64_t Checksum(const CodepointRemappingProto& response);

 private:
  const Hasher* hasher_;
};

}  // namespace patch_subset

#endif  // PATCH_SUBSET_CODEPOINT_MAPPING_CHECKSUM_H_
