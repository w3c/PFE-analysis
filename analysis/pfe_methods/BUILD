py_library(
    name = "pfe_methods",
    srcs = [
        "combined_patch_subset_method.py",
        "logged_pfe_method.py",
        "optimal_one_font_method.py",
        "optimal_pfe_method.py",
        "range_request_pfe_method.py",
        "subset_sizer.py",
        "unicode_range_pfe_method.py",
        "whole_font_pfe_method.py",
    ],
    visibility = [
        "//analysis:__pkg__",
    ],
    deps = [
        "//analysis:common",
        "//analysis:simulation",
        "//analysis/pfe_methods/unicode_range_data:slicing_strategy_loader",
        "//patch_subset/py",
        "//woff2_py",
    ],
)

py_test(
    name = "combined_patch_subset_method_test",
    srcs = [
        "combined_patch_subset_method_test.py",
    ],
    data = [
        "@patch_subset//patch_subset:testdata",
    ],
    deps = [
        ":pfe_methods",
        "//analysis:common",
        "@io_abseil_py//absl/testing:flagsaver",
    ],
)

py_test(
    name = "whole_font_pfe_method_test",
    srcs = [
        "whole_font_pfe_method_test.py",
    ],
    data = [
        "@patch_subset//patch_subset:testdata",
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
        "@patch_subset//patch_subset:testdata",
    ],
    deps = [
        ":pfe_methods",
    ],
)

py_test(
    name = "range_request_pfe_method_test",
    srcs = [
        "range_request_pfe_method_test.py",
    ],
    data = [
        "@patch_subset//patch_subset:testdata",
    ],
    deps = [
        ":pfe_methods",
    ],
)

py_test(
    name = "optimal_pfe_method_test",
    srcs = [
        "optimal_pfe_method_test.py",
    ],
    data = [
        "@patch_subset//patch_subset:testdata",
    ],
    deps = [
        ":pfe_methods",
    ],
)

py_test(
    name = "optimal_one_font_method_test",
    srcs = [
        "optimal_one_font_method_test.py",
    ],
    data = [
        "@patch_subset//patch_subset:testdata",
    ],
    deps = [
        ":pfe_methods",
    ],
)

py_test(
    name = "logged_pfe_method_test",
    srcs = [
        "logged_pfe_method_test.py",
    ],
    deps = [
        ":pfe_methods",
    ],
)

py_test(
    name = "subset_sizer_test",
    srcs = [
        "subset_sizer_test.py",
    ],
    data = [
        "@patch_subset//patch_subset:testdata",
    ],
    deps = [
        ":pfe_methods",
    ],
)
