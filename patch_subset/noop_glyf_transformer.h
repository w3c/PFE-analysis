#ifndef PATCH_SUBSET_NOOP_GLYF_TRANSFORMER_H_
#define PATCH_SUBSET_NOOP_GLYF_TRANSFORMER_H_

#include "common/status.h"
#include "patch_subset/font_data.h"
#include "patch_subset/glyf_transformer.h"

namespace patch_subset {

// Applies no glyf transformation.
class NoopGlyfTransformer : public GlyfTransformer {
 public:
  StatusCode Encode(FontData* font /* IN/OUT */) const override {
    return StatusCode::kOk;
  }
};

}  // namespace patch_subset

#endif  // PATCH_SUBSET_NOOP_GLYF_TRANSFORMER_H_
