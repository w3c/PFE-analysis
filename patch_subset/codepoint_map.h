#ifndef PATCH_SUBSET_CODEPOINT_MAP_H_
#define PATCH_SUBSET_CODEPOINT_MAP_H_

#include <unordered_map>
#include <vector>

#include "common/status.h"
#include "hb.h"
#include "patch_subset/patch_subset.pb.h"

namespace patch_subset {

class CodepointMap {
 public:
  void Clear();

  void AddMapping(hb_codepoint_t from, hb_codepoint_t to);

  StatusCode FromProto(const CodepointRemappingProto& proto) const;
  StatusCode ToProto(CodepointRemappingProto* proto) const;

  StatusCode Encode(hb_set_t* codepoints) const;
  StatusCode Encode(hb_codepoint_t* cp /* IN/OUT */) const;

  StatusCode Decode(hb_set_t* codepoints) const;
  StatusCode Decode(hb_codepoint_t* cp /* IN/OUT */) const;

 private:
  std::unordered_map<hb_codepoint_t, hb_codepoint_t> encode_map;
  std::unordered_map<hb_codepoint_t, hb_codepoint_t> decode_map;
};

}  // namespace patch_subset

#endif  // PATCH_SUBSET_CODEPOINT_MAP_H_
