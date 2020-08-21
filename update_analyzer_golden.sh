#!/bin/bash
bazel run analysis:analyzer_integration_test -- --update_golden=$(pwd)/analysis/sample/english_sequence.result.textproto
