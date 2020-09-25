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

proto_library(
    name = "result_proto",
    srcs = ["result.proto"],
)

py_proto_library(
    name = "page_view_sequence_py_proto",
    srcs = ["page_view_sequence.proto"],
    visibility = [
        "//tools:__pkg__",
    ],
)

py_proto_library(
    name = "result_py_proto",
    srcs = ["result.proto"],
    visibility = [
        "//tools:__pkg__",
    ],
)

py_binary(
    name = "analyzer",
    srcs = [
        "analyzer.py",
    ],
    srcs_version = "PY3",
    deps = [
        ":common",
        ":fake_pfe",
        ":page_view_sequence_py_proto",
        ":result_py_proto",
        ":simulation",
        "//analysis/pfe_methods",
        "//patch_subset/py",
        "@io_abseil_py//absl:app",
        "@io_abseil_py//absl/flags",
    ],
)

py_binary(
    name = "analyzer_codepoint_prediction",
    srcs = [
        "analyzer.py",
        "analyzer_codepoint_prediction.py",
    ],
    main = "analyzer_codepoint_prediction.py",
    srcs_version = "PY3",
    deps = [
        ":common",
        ":fake_pfe",
        ":page_view_sequence_py_proto",
        ":result_py_proto",
        ":simulation",
        "//analysis/pfe_methods",
        "//patch_subset/py",
        "@io_abseil_py//absl:app",
        "@io_abseil_py//absl/flags",
    ],
)

py_library(
    name = "simulation",
    srcs = [
        "network_models.py",
        "simulation.py",
    ],
    srcs_version = "PY3",
    visibility = [
        "//analysis/pfe_methods:__pkg__",
        "//patch_subset/py:__pkg__",
    ],
    deps = [
        ":common",
        ":page_view_sequence_py_proto",
    ],
)

py_library(
    name = "common",
    srcs = [
        "cost.py",
        "distribution.py",
        "font_loader.py",
        "languages.py",
        "request_graph.py",
    ],
    srcs_version = "PY3",
    visibility = [
        "//analysis/pfe_methods:__pkg__",
        "//patch_subset/py:__pkg__",
        "//tools:__pkg__",
    ],
    deps = [
        ":result_py_proto",
    ],
)

py_test(
    name = "distribution_test",
    srcs = [
        "distribution_test.py",
    ],
    deps = [
        ":common",
    ],
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
    name = "languages_test",
    srcs = [
        "languages_test.py",
    ],
    deps = [
        ":common",
        "@io_abseil_py//absl/testing:absltest",
        "@io_abseil_py//absl/testing:flagsaver",
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
    name = "cost_test",
    srcs = [
        "cost_test.py",
    ],
    deps = [
        ":common",
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
        ":result_py_proto",
    ],
)

py_test(
    name = "analyzer_integration_test",
    srcs = [
        "analyzer_integration_test.py",
    ],
    data = [
        "sample/english_sequence.result.textproto",
        "sample/english_sequence.textproto",
        "sample/range_request.english_sequence.result.textproto",
        ":analyzer",
        "//patch_subset:testdata",
    ],
    deps = [
    ],
)

py_test(
    name = "font_loader_test",
    srcs = [
        "font_loader_test.py",
    ],
    deps = [
        ":common",
    ],
)

py_library(
    name = "fake_pfe",
    srcs = [
        "fake_pfe_method.py",
    ],
    srcs_version = "PY3",
)
