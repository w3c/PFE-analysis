py_binary(
    name = "create_data_set",
    srcs = [
        "create_data_set.py",
    ],
    deps = [
        "//analysis:page_view_sequence_py_proto",
        "@io_abseil_py//absl:app",
    ],
)

py_binary(
    name = "summarize_results",
    srcs = [
        "summarize_results.py",
    ],
    deps = [
        "//analysis:result_py_proto",
        "@io_abseil_py//absl:app",
        "@io_abseil_py//absl/flags",
    ],
)

py_binary(
    name = "filter_data_set",
    srcs = [
        "filter_data_set.py",
    ],
    deps = [
        "//analysis:common",
        "//analysis:page_view_sequence_py_proto",
        "@io_abseil_py//absl:app",
        "@io_abseil_py//absl/flags",
    ],
)

py_binary(
    name = "merge_frequencies",
    srcs = [
        "merge_frequencies.py",
    ],
    deps = [
        "//analysis/pfe_methods/unicode_range_data:slicing_strategy_py_proto",
        "@io_abseil_py//absl:app",
        "@io_abseil_py//absl/flags",
    ],
)

py_binary(
    name = "merge_results",
    srcs = [
        "merge_results.py",
    ],
    deps = [
        "//analysis:result_py_proto",
        "@io_abseil_py//absl:app",
    ],
)

py_test(
    name = "merge_results_test",
    srcs = [
        "merge_results_test.py",
    ],
    data = glob(["testdata/**"]),
    deps = [
        ":merge_results",
        "@io_abseil_py//absl/testing:absltest",
        "@io_abseil_py//absl/testing:flagsaver",
    ],
)
