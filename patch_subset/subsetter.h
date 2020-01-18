#ifndef PATCH_SUBSET_SUBSETTER_H_
#define PATCH_SUBSET_SUBSETTER_H_

#include "common/status.h"
#include "hb.h"
#include "patch_subset/font_data.h"

namespace patch_subset {

// Interface to a font subsetter.
class Subsetter {
 public:
  virtual ~Subsetter() = default;

  // Subset 'font' such that it only contains the data necessary to
  // render any combination of 'codepoints'. Result is wrtitten to
  // 'subset'.
  virtual StatusCode Subset(const FontData& font, const hb_set_t& codepoints,
                            FontData* subset /* OUT */) const = 0;

  // Writes the set of all unicode codepoints that are in font to
  // the codepoints set.
  virtual void CodepointsInFont(const FontData& font,
                                hb_set_t* codepoints) const = 0;
};

}  // namespace patch_subset

#endif  // PATCH_SUBSET_SUBSETTER_H_
