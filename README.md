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

## Code Style
The code follows the [Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html). Formatting is enforced by an automated check for new commits to this repo. You can auto-correct formatting for all files using the format.sh script.
