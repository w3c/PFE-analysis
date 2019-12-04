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
