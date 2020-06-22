#include "patch_subset/frequency_codepoint_predictor.h"

#include <google/protobuf/text_format.h>

#include <filesystem>
#include <fstream>
#include <iterator>
#include <vector>

#include "absl/container/btree_set.h"
#include "analysis/pfe_methods/unicode_range_data/slicing_strategy.pb.h"
#include "common/logging.h"
#include "common/status.h"

using absl::btree_set;
using analysis::pfe_methods::unicode_range_data::Codepoint;
using analysis::pfe_methods::unicode_range_data::SlicingStrategy;
using analysis::pfe_methods::unicode_range_data::Subset;
using google::protobuf::TextFormat;

namespace patch_subset {

static const char* kSlicingStrategyDataDirectory =
    "analysis/pfe_methods/unicode_range_data/";

struct CodepointFreqCompare {
  bool operator()(const Codepoint& lhs, const Codepoint& rhs) const {
    return lhs.count() > rhs.count();
  }
};

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

FrequencyCodepointPredictor* FrequencyCodepointPredictor::Create() {
  std::vector<SlicingStrategy> strategies;
  StatusCode result = LoadAllStrategies(&strategies);
  if (result != StatusCode::kOk) {
    return nullptr;
  }

  return new FrequencyCodepointPredictor(std::move(strategies));
}

FrequencyCodepointPredictor::FrequencyCodepointPredictor(
    std::vector<SlicingStrategy> strategies)
    : strategies_(std::move(strategies)) {}

void FrequencyCodepointPredictor::Predict(
    const hb_set_t* font_codepoints, const hb_set_t* requested_codepoints,
    unsigned max, hb_set_t* predicted_codepoints /* OUT */) const {
  const SlicingStrategy& best_strategy = BestStrategyFor(font_codepoints);

  btree_set<Codepoint, CodepointFreqCompare> additional_codepoints;
  for (auto subset : best_strategy.subsets()) {
    if (!Intersects(subset, requested_codepoints)) {
      continue;
    }

    for (auto codepoint : subset.codepoint_frequencies()) {
      additional_codepoints.insert(codepoint);

      if (additional_codepoints.size() > max) {
        // We only keep at most 'max' codepoints so remove the lowest frequency
        // one.
        additional_codepoints.erase(additional_codepoints.end());
      }
    }
  }

  for (auto codepoint : additional_codepoints) {
    hb_set_add(predicted_codepoints, codepoint.codepoint());
  }
}

bool FrequencyCodepointPredictor::Intersects(
    const Subset& subset, const hb_set_t* requested_codepoints) const {
  // TODO(garretrieger): Implement me!
  return true;
}

const SlicingStrategy& FrequencyCodepointPredictor::BestStrategyFor(
    const hb_set_t* codepoints) const {
  // TODO(garretrieger): Implement me!
}

}  // namespace patch_subset
