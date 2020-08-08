py_binary(
    name = "create_data_set",
    srcs = [
        "create_data_set.py",
    ],
    deps = [
        "//analysis:page_view_sequence_proto_py",
        "@io_abseil_py//absl:app",
    ],
)

py_binary(
    name = "summarize_results",
    srcs = [
        "summarize_results.py",
    ],
    deps = [
        "//analysis:result_proto_py",
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
        "//analysis:page_view_sequence_proto_py",
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
        "//analysis/pfe_methods/unicode_range_data:slicing_strategy_proto_py",
        "@io_abseil_py//absl:app",
        "@io_abseil_py//absl/flags",
    ],
)
