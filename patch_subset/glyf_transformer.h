#ifndef PATCH_SUBSET_GLYF_TRANSFORMER_H_
#define PATCH_SUBSET_GLYF_TRANSFORMER_H_

#include "common/status.h"
#include "patch_subset/font_data.h"

namespace patch_subset {

// Interface to an object which can apply transformations to the glyf
// and loca table. For example the WOFF2 glyf and loca transformation.
class GlyfTransformer {
 public:
  virtual ~GlyfTransformer() = default;

  virtual StatusCode Encode(FontData* font /* IN/OUT */) const = 0;
};

}  // namespace patch_subset

#endif  // PATCH_SUBSET_GLYF_TRANSFORMER_H_
