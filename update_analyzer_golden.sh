#!/bin/bash
bazel run analysis:analyzer_integration_test -- \
  --update_golden=$(pwd)/analysis/sample/english_sequence.result.textproto

bazel run analysis:analyzer_integration_test -- \
  --update_golden=$(pwd)/analysis/sample/range_request.english_sequence.result.textproto \
  --simulate_range_request
