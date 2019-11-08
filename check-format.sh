#!/bin/bash
#
# Use this script to automatically format the c++ files in
# this repository.

FIX=0
while test $# -gt 0; do
  case "$1" in
    --fix)
      shift
      FIX=1
      ;;
  esac
done

FAILED=0
FORMAT_MESSAGE="is formatted incorrectly. Use ./check-format.sh --fix to format all source files."

# C++ Formatting
for f in $(find ./ -name "*.cc") $(find ./ -name "*.h"); do
  clang-format --style=Google --output-replacements-xml $f | grep -q "<replacement "
  if [ $? -eq 0 ]; then
    if [ $FIX -eq 1 ]; then
      clang-format --style=Google -i $f
    else
      echo $f $FORMAT_MESSAGE
      FAILED=1
    fi
  fi
done

# Python Formatting
for f in $(find ./ -name "*.py"); do
  yapf --style="{based_on_style: google, indent_width: 2}" -d $f \    
  if [ $? -ne 0 ]; then
    if [ $FIX -eq 1 ]; then
      yapf --style="{based_on_style: google, indent_width: 2}" -i $f
    else
      echo $f $FORMAT_MESSAGE
      FAILED=1
    fi
  fi
  python3 -m pylint -s no \
    -d R0903,E0401,E0611,fixme \
    --no-docstring-rgx=".+Test|test_" \
    --indent-string="  " \
    $f
  if [ $? -ne 0 ]; then
    echo "pylint failed for $f"
    echo ""
    FAILED=1
  fi
done

if [ $FAILED -eq 1 ]; then
  exit -1
else
  echo "Formatting is correct :)"
fi
