#ifndef PATCH_SUBSET_HARFBUZZ_SUBSETTER_H_
#define PATCH_SUBSET_HARFBUZZ_SUBSETTER_H_

#include "common/status.h"
#include "hb.h"
#include "patch_subset/font_data.h"
#include "patch_subset/subsetter.h"

namespace patch_subset {

// Computes a subset using harfbuzz hb-subset library.
class HarfbuzzSubsetter : public Subsetter {
 public:
  HarfbuzzSubsetter() {}

  StatusCode Subset(const FontData& font, const hb_set_t& codepoints,
                    FontData* subset /* OUT */) const override;

  void CodepointsInFont(const FontData& font,
                        hb_set_t* codepoints) const override;

 private:
};

}  // namespace patch_subset

#endif  // PATCH_SUBSET_HARFBUZZ_SUBSETTER_H_
