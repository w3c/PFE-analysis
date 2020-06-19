#include "patch_subset/frequency_codepoint_predictor.h"

#include <google/protobuf/text_format.h>

#include <filesystem>
#include <fstream>
#include <iterator>
#include <vector>

#include "analysis/pfe_methods/unicode_range_data/slicing_strategy.pb.h"
#include "common/logging.h"
#include "common/status.h"

using analysis::pfe_methods::unicode_range_data::SlicingStrategy;
using google::protobuf::TextFormat;

namespace patch_subset {

static const char* kSlicingStrategyDataDirectory =
    "analysis/pfe_methods/unicode_range_data/";

StatusCode LoadStrategy(const std::string& path, SlicingStrategy* out) {
  std::ifstream input(path);
  std::string data;

  if (!input.is_open()) {
    LOG(WARNING) << "Could not open strategy file: " << path;
    return StatusCode::kNotFound;
  }

  input.seekg(0, std::ios::end);
  data.reserve(input.tellg());
  input.seekg(0, std::ios::beg);
  data.assign((std::istreambuf_iterator<char>(input)),
              std::istreambuf_iterator<char>());

  if (!TextFormat::ParseFromString(data, out)) {
    LOG(WARNING) << "Unable to parse strategy file: " << path;
    return StatusCode::kInternal;
  }

  return StatusCode::kOk;
}

StatusCode LoadAllStrategies(std::vector<SlicingStrategy>* strategies) {
  for (const auto& entry :
       std::filesystem::directory_iterator(kSlicingStrategyDataDirectory)) {
    if (entry.path().extension() != std::filesystem::path(".textproto")) {
      continue;
    }

    SlicingStrategy strategy;
    StatusCode result;
    if ((result = LoadStrategy(entry.path(), &strategy)) != StatusCode::kOk) {
      return result;
    }
    strategies->push_back(strategy);
  }

  return StatusCode::kOk;
}

FrequencyCodepointPredictor::FrequencyCodepointPredictor() {
  LoadAllStrategies(&strategies);
}

void FrequencyCodepointPredictor::Predict(
    const hb_set_t* font_codepoints, const hb_set_t* requested_codepoints,
    unsigned max, hb_set_t* predicted_codepoints /* OUT */) const {
  // 1. Pick a strategy
  // 2. Identify subsets that intersect codepoints.
  // 3. Select the highest use codepoints that are not already present.
  // TODO(garretrieger): Implement me!
}

}  // namespace patch_subset
