#ifndef PATCH_SUBSET_MOCK_GLYF_TRANSFORMER_H_
#define PATCH_SUBSET_MOCK_GLYF_TRANSFORMER_H_

#include "common/status.h"
#include "gmock/gmock.h"
#include "gtest/gtest.h"
#include "patch_subset/font_data.h"
#include "patch_subset/glyf_transformer.h"

namespace patch_subset {

// Interface to an object which can apply transformations to the glyf
// and loca table. For example the WOFF2 glyf and loca transformation.
class MockGlyfTransformer : public GlyfTransformer {
 public:

  MOCK_METHOD(StatusCode,
              Encode,
              (FontData* font /* IN/OUT */),
              (const override));
};

}  // namespace patch_subset

#endif  // PATCH_SUBSET_MOCK_GLYF_TRANSFORMER_H_
