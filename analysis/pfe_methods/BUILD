py_library(
    name = "pfe_methods",
    srcs = [
        "unicode_range_pfe_method.py",
        "whole_font_pfe_method.py",
    ],
    visibility = [
        "//analysis:__pkg__",
    ],
    deps = [
        "//analysis:common",
        "//analysis/pfe_methods/unicode_range_data:slicing_strategy_loader",
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

py_test(
    name = "unicode_range_pfe_method_test",
    srcs = [
        "unicode_range_pfe_method_test.py",
    ],
    data = [
        "//patch_subset:testdata",
    ],
    deps = [
        ":pfe_methods",
    ],
)
