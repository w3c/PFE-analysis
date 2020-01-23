#include "patch_subset/codepoint_map.h"

#include "common/logging.h"
#include "hb.h"
#include "patch_subset/hb_set_unique_ptr.h"

namespace patch_subset {

void CodepointMap::SetMapping(const std::vector<hb_codepoint_t> mapping) {
  encode_map.clear();
  decode_map.clear();
  for (size_t new_cp = 0; new_cp < mapping.size(); new_cp++) {
    encode_map[mapping[new_cp]] = new_cp;
    decode_map[new_cp] = mapping[new_cp];
  }
}

StatusCode Remap(
    const std::unordered_map<hb_codepoint_t, hb_codepoint_t>& mapping,
    hb_set_t* codepoints) {
  hb_set_unique_ptr new_codepoints = make_hb_set();

  for (hb_codepoint_t cp = HB_SET_VALUE_INVALID;
       hb_set_next(codepoints, &cp);) {
    auto new_cp = mapping.find(cp);
    if (new_cp == mapping.end()) {
      LOG(WARNING)
          << "Encountered codepoint that is unspecified in the remapping: "
          << cp;
      return StatusCode::kInvalidArgument;
    }

    hb_set_add(new_codepoints.get(), new_cp->second);
  }

  hb_set_clear(codepoints);
  hb_set_union(codepoints, new_codepoints.get());

  return StatusCode::kOk;
}

StatusCode CodepointMap::Encode(hb_set_t* codepoints) const {
  return Remap(encode_map, codepoints);
}

StatusCode CodepointMap::Decode(hb_set_t* codepoints) const {
  return Remap(decode_map, codepoints);
}

}  // namespace patch_subset
