#!/bin/bash
#
# Use this script to automatically format the c++ files in
# this repository.

FAILED=0
for f in common/*.h patch_subset/*.cc patch_subset/*.h; do
  clang-format --style=Google --output-replacements-xml $f | grep -q "<replacement "
  if [ $? -eq 0 ]; then
    echo "$f is formatted incorrectly. Use ./format.sh to format all source files."
    FAILED=1
  fi
done

if [ $FAILED -eq 1 ]; then
  exit -1
else
  echo "Formatting is correct :)"
fi
