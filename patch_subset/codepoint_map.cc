#include "patch_subset/codepoint_map.h"

#include "common/logging.h"
#include "hb.h"
#include "patch_subset/hb_set_unique_ptr.h"

namespace patch_subset {

void CodepointMap::Clear() {
  encode_map.clear();
  decode_map.clear();
}

void CodepointMap::AddMapping(hb_codepoint_t from, hb_codepoint_t to) {
  encode_map[from] = to;
  decode_map[to] = from;
}

StatusCode CodepointMap::FromProto(const CodepointRemappingProto& proto) const {
  // TODO(garretrieger): implement me!
  LOG(WARNING) << "Not implemeneted yet.";
  return StatusCode::kUnimplemented;
}

StatusCode CodepointMap::ToProto(CodepointRemappingProto* proto) const {
  CompressedListProto* codepoint_ordering = proto->mutable_codepoint_ordering();

  int last_cp = 0;
  for (unsigned int i = 0; i < encode_map.size(); i++) {
    hb_codepoint_t cp_for_index = i;
    StatusCode result = Decode(&cp_for_index);
    if (result != StatusCode::kOk) {
      return result;
    }

    int delta = cp_for_index - last_cp;
    last_cp = cp_for_index;

    codepoint_ordering->add_deltas(delta);
  }

  return StatusCode::kOk;
}

StatusCode Remap(
    const std::unordered_map<hb_codepoint_t, hb_codepoint_t>& mapping,
    hb_codepoint_t* cp) {
  auto new_cp = mapping.find(*cp);
  if (new_cp == mapping.end()) {
    LOG(WARNING)
        << "Encountered codepoint that is unspecified in the remapping: " << cp;
    return StatusCode::kInvalidArgument;
  }

  *cp = new_cp->second;
  return StatusCode::kOk;
}

StatusCode Remap(
    const std::unordered_map<hb_codepoint_t, hb_codepoint_t>& mapping,
    hb_set_t* codepoints) {
  hb_set_unique_ptr new_codepoints = make_hb_set();

  for (hb_codepoint_t cp = HB_SET_VALUE_INVALID;
       hb_set_next(codepoints, &cp);) {
    hb_codepoint_t new_cp = cp;
    StatusCode result = Remap(mapping, &new_cp);
    if (result != StatusCode::kOk) {
      return result;
    }
    hb_set_add(new_codepoints.get(), new_cp);
  }

  hb_set_clear(codepoints);
  hb_set_union(codepoints, new_codepoints.get());

  return StatusCode::kOk;
}

StatusCode CodepointMap::Encode(hb_set_t* codepoints) const {
  return Remap(encode_map, codepoints);
}

StatusCode CodepointMap::Encode(hb_codepoint_t* cp) const {
  return Remap(encode_map, cp);
}

StatusCode CodepointMap::Decode(hb_set_t* codepoints) const {
  return Remap(decode_map, codepoints);
}

StatusCode CodepointMap::Decode(hb_codepoint_t* cp) const {
  return Remap(decode_map, cp);
}

}  // namespace patch_subset
