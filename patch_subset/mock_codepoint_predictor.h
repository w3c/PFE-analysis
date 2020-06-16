#ifndef PATCH_SUBSET_MOCK_CODEPOINT_PREDICTOR_H_
#define PATCH_SUBSET_MOCK_CODEPOINT_PREDICTOR_H_

#include <string>

#include "gmock/gmock.h"
#include "gtest/gtest.h"
#include "patch_subset/codepoint_predictor.h"

namespace patch_subset {

class MockCodepointPredictor : public CodepointPredictor {
 public:
  MOCK_METHOD(void, Predict,
              (const hb_set_t* font_codepoints,
               const hb_set_t* requested_codepoints, unsigned count,
               hb_set_t* predicted_codepoints /* OUT */),
              (const override));
};

}  // namespace patch_subset

#endif  // PATCH_SUBSET_MOCK_CODEPOINT_PREDICTOR_H_
