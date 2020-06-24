#include "patch_subset/frequency_codepoint_predictor.h"

#include <google/protobuf/text_format.h>

#include <filesystem>
#include <fstream>
#include <iterator>
#include <vector>

#include "absl/container/btree_map.h"
#include "absl/container/btree_set.h"
#include "analysis/pfe_methods/unicode_range_data/slicing_strategy.pb.h"
#include "common/logging.h"
#include "common/status.h"
#include "patch_subset/hb_set_unique_ptr.h"

using absl::btree_map;
using absl::btree_set;
using analysis::pfe_methods::unicode_range_data::Codepoint;
using analysis::pfe_methods::unicode_range_data::SlicingStrategy;
using analysis::pfe_methods::unicode_range_data::Subset;
using google::protobuf::TextFormat;

namespace patch_subset {

static const char* kSlicingStrategyDataDirectory =
    "analysis/pfe_methods/unicode_range_data/";

struct CodepointFreqCompare {
  bool operator()(const Codepoint* lhs, const Codepoint* rhs) const {
    if (lhs->count() == rhs->count()) {
      return lhs->codepoint() < rhs->codepoint();
    }
    return lhs->count() > rhs->count();
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

StatusCode LoadAllStrategies(const std::string& directory,
                             std::vector<SlicingStrategy>* strategies) {
  for (const auto& entry : std::filesystem::directory_iterator(directory)) {
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
  return Create(kSlicingStrategyDataDirectory);
}

FrequencyCodepointPredictor* FrequencyCodepointPredictor::Create(
    const std::string& directory) {
  std::vector<SlicingStrategy> strategies;
  StatusCode result = LoadAllStrategies(directory, &strategies);
  if (result != StatusCode::kOk) {
    return nullptr;
  }

  return new FrequencyCodepointPredictor(std::move(strategies));
}

FrequencyCodepointPredictor::FrequencyCodepointPredictor(
    std::vector<SlicingStrategy> strategies)
    : strategies_(std::move(strategies)) {}

void FrequencyCodepointPredictor::Predict(
    const hb_set_t* font_codepoints,
    const hb_set_t* have_codepoints,
    const hb_set_t* requested_codepoints,
    unsigned max, hb_set_t* predicted_codepoints /* OUT */) const {
  const SlicingStrategy* best_strategy = BestStrategyFor(font_codepoints);
  if (!best_strategy) {
    LOG(WARNING) << "No strategies are available for prediction.";
    return;
  }

  btree_set<const Codepoint*, CodepointFreqCompare> additional_codepoints;
  for (const auto& subset : best_strategy->subsets()) {
    if (!Intersects(subset, requested_codepoints)) {
      continue;
    }

    for (const auto& codepoint : subset.codepoint_frequencies()) {
      if (hb_set_has(requested_codepoints, codepoint.codepoint())) {
        continue;
      }
      if (hb_set_has(have_codepoints, codepoint.codepoint())) {
        continue;
      }

      additional_codepoints.insert(&codepoint);

      if (additional_codepoints.size() > max) {
        // We only keep at most 'max' codepoints so remove the lowest frequency
        // one.
        additional_codepoints.erase(--additional_codepoints.end());
      }
    }
  }

  for (auto codepoint : additional_codepoints) {
    hb_set_add(predicted_codepoints, codepoint->codepoint());
  }
}

bool FrequencyCodepointPredictor::Intersects(
    const Subset& subset, const hb_set_t* requested_codepoints) const {
  for (auto cp : subset.codepoint_frequencies()) {
    if (hb_set_has(requested_codepoints, cp.codepoint())) {
      return true;
    }
  }
  return false;
}

int FrequencyCodepointPredictor::IntersectionSize(
    const SlicingStrategy& strategy, const hb_set_t* codepoints) const {
  hb_set_unique_ptr unique_codepoints = make_hb_set();
  for (auto subset : strategy.subsets()) {
    for (auto cp : subset.codepoint_frequencies()) {
      hb_set_add(unique_codepoints.get(), cp.codepoint());
    }
  }

  hb_set_intersect(unique_codepoints.get(), codepoints);
  return hb_set_get_population(unique_codepoints.get());
}

const SlicingStrategy* FrequencyCodepointPredictor::BestStrategyFor(
    const hb_set_t* codepoints) const {
  btree_map<int, const SlicingStrategy*> strategies;
  for (const auto& strategy : strategies_) {
    // TODO(garretrieger): should factor in the frequencies of codepoints in the
    //   intersection. For example the various CJK strategies share many of the
    //   same codepoints so we may mismatch the strategy using intersection
    //   count alone.
    strategies[IntersectionSize(strategy, codepoints)] = &strategy;
  }

  if (strategies.empty()) {
    return nullptr;
  }
  return (--strategies.end())->second;
}

}  // namespace patch_subset
