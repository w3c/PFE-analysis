# PFE-analysis
Code repository for tools for the the testing and analysis of potential Progressive Font Enrichment ([PFE](https://github.com/w3c/PFE)) solutions.

## Build
This repository uses the bazel build system. You can build everything:

```sh
bazel build ...
```

and run all of the tests:
```sh
bazel test ...
```

## Example of Running the Analysis

```sh
# Run the analysis
SCDontUseServer=1 OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES bazel run analysis:analyzer -- --input_data=$(pwd)/analysis/sample/english_sequence.textproto --input_form=text --font_directory=$(pwd)/patch_subset/testdata/ --default_font_id=Roboto-Regular.ttf > /tmp/pfe-analysis-results.textproto

# Inspect the results
bazel run tools:summarize_results -- --input_file=/tmp/pfe-analysis-results.textproto cost_summary
```

## Code Style
The code follows the [Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html). Formatting is enforced by an automated check for new commits to this repo. You can auto-correct formatting for all files using the format.sh script.
