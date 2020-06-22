#ifndef PATCH_SUBSET_FREQUENCY_CODEPOINT_PREDICTOR_H_
#define PATCH_SUBSET_FREQUENCY_CODEPOINT_PREDICTOR_H_

#include <vector>

#include "analysis/pfe_methods/unicode_range_data/slicing_strategy.pb.h"
#include "codepoint_predictor.h"
#include "hb.h"

namespace patch_subset {

/*
 * Provides predictions on what additional codepoints a client might
 * need based on the codepoints requested and the set of codepoints
 * in the font being augmented.
 */
class FrequencyCodepointPredictor : public CodepointPredictor {
 public:
  static FrequencyCodepointPredictor* Create();

  void Predict(const hb_set_t* font_codepoints,
               const hb_set_t* requested_codepoints, unsigned max,
               hb_set_t* predicted_codepoints /* OUT */) const;

 private:
  FrequencyCodepointPredictor(
      std::vector<analysis::pfe_methods::unicode_range_data::SlicingStrategy>
          strategies);

  bool Intersects(
      const analysis::pfe_methods::unicode_range_data::Subset& subset,
      const hb_set_t* requested_codepoints) const;

  const analysis::pfe_methods::unicode_range_data::SlicingStrategy&
  BestStrategyFor(const hb_set_t* codepoints) const;

  std::vector<analysis::pfe_methods::unicode_range_data::SlicingStrategy>
      strategies_;
};

}  // namespace patch_subset

#endif  // PATCH_SUBSET_FREQUENCY_CODEPOINT_PREDICTOR_H_
