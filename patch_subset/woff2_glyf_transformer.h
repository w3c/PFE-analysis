#ifndef PATCH_SUBSET_WOFF2_GLYF_TRANSFORMER_H_
#define PATCH_SUBSET_WOFF2_GLYF_TRANSFORMER_H_

#include "common/status.h"
#include "patch_subset/font_data.h"
#include "patch_subset/glyf_transformer.h"

namespace patch_subset {

// Applies the woff2 glyf and loca transformations to a font.
class Woff2GlyfTransformer : public GlyfTransformer {
 public:
  StatusCode Encode(FontData* font /* IN/OUT */) const override;
};

}  // namespace patch_subset

#endif  // PATCH_SUBSET_WOFF2_GLYF_TRANSFORMER_H_
