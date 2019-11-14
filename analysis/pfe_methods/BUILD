py_library(
    name = "pfe_methods",
    srcs = [
        "whole_font_pfe_method.py",
    ],
    visibility = [
        "//analysis:__pkg__",
    ],
    deps = [
        "//analysis:common",
        "//woff2_py",
    ],
)

py_test(
    name = "whole_font_pfe_method_test",
    srcs = [
        "whole_font_pfe_method_test.py",
    ],
    data = [
        "//patch_subset:testdata",
    ],
    deps = [
        ":pfe_methods",
    ],
)
