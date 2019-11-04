#!/bin/bash
#
# Use this script to automatically format the c++ files in
# this repository.

for f in common/*.h patch_subset/*.cc patch_subset/*.h; do
  clang-format -i --style=Google $f
done
