load("@rules_proto//proto:defs.bzl", "proto_library")
load("@com_google_protobuf//:protobuf.bzl", "py_proto_library")

filegroup(
    name = "sample",
    srcs = glob(["sample/*.textproto"]),
)

proto_library(
    name = "page_view_sequence_proto",
    srcs = ["page_view_sequence.proto"],
)

py_proto_library(
    name = "page_view_sequence_proto_py",
    srcs = ["page_view_sequence.proto"],
)

py_binary(
    name = "analyzer",
    srcs = [
        "analyzer.py",
    ],
    srcs_version = "PY3",
    deps = [
        ":page_view_sequence_proto_py",
        "@io_abseil_py//absl:app",
        "@io_abseil_py//absl/flags",
    ],
)
