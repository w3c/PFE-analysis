#ifndef PATCH_SUBSET_FAKE_SUBSETTER_H_
#define PATCH_SUBSET_FAKE_SUBSETTER_H_

#include <algorithm>

#include "common/status.h"
#include "hb.h"
#include "patch_subset/font_data.h"
#include "patch_subset/subsetter.h"

namespace patch_subset {

// Fake implementation of Subsetter for use in testing.
class FakeSubsetter : public Subsetter {
 public:
  FakeSubsetter() {}

  StatusCode Subset(const FontData& font, const hb_set_t& codepoints,
                    FontData* subset /* OUT */) const override {
    if (font.empty()) {
      return StatusCode::kInternal;
    }

    if (!hb_set_get_population(&codepoints)) {
      subset->reset();
      return StatusCode::kOk;
    }

    std::string result(font.data(), font.size());
    result.push_back(':');
    for (hb_codepoint_t cp = HB_SET_VALUE_INVALID;
         hb_set_next(&codepoints, &cp);) {
      result.push_back(static_cast<char>(cp));
    }

    subset->copy(result.c_str(), result.size());
    return StatusCode::kOk;
  }

  void CodepointsInFont(const FontData& font,
                        hb_set_t* codepoints) const override {
    hb_set_add(codepoints, 1);
    hb_set_add(codepoints, 2);
    hb_set_add(codepoints, 3);
  }
};

}  // namespace patch_subset

#endif  // PATCH_SUBSET_FAKE_SUBSETTER_H_
