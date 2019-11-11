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
        "simulation.py",
    ],
    srcs_version = "PY3",
    deps = [
        ":common",
        ":fake_pfe",
        ":page_view_sequence_proto_py",
        "@io_abseil_py//absl:app",
        "@io_abseil_py//absl/flags",
    ],
)

py_library(
    name = "common",
    srcs = [
        "request_graph.py",
    ],
    srcs_version = "PY3",
)

py_test(
    name = "request_graph_test",
    srcs = [
        "request_graph_test.py",
    ],
    deps = [
        ":common",
    ],
)

py_test(
    name = "simulation_test",
    srcs = [
        "simulation_test.py",
    ],
    deps = [
        ":analyzer",
        ":common",
        ":fake_pfe",
    ],
)

py_test(
    name = "analyzer_test",
    srcs = [
        "analyzer_test.py",
    ],
    data = [
        ":sample",
    ],
    deps = [
        ":analyzer",
        ":common",
        ":fake_pfe",
    ],
)

py_library(
    name = "fake_pfe",
    srcs = [
        "fake_pfe_method.py",
    ],
    srcs_version = "PY3",
)
