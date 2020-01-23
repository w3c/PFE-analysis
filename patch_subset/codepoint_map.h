#ifndef PATCH_SUBSET_CODEPOINT_MAP_H_
#define PATCH_SUBSET_CODEPOINT_MAP_H_

#include <unordered_map>
#include <vector>

#include "common/status.h"
#include "hb.h"

namespace patch_subset {

class CodepointMap {
 public:
  void SetMapping(const std::vector<hb_codepoint_t> mapping);

  StatusCode Encode(hb_set_t* codepoints) const;

  StatusCode Decode(hb_set_t* codepoints) const;

 private:
  std::unordered_map<hb_codepoint_t, hb_codepoint_t> encode_map;
  std::unordered_map<hb_codepoint_t, hb_codepoint_t> decode_map;
};

}  // namespace patch_subset

#endif  // PATCH_SUBSET_CODEPOINT_MAP_H_
