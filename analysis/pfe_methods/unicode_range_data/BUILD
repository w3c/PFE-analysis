load("@com_google_protobuf//:protobuf.bzl", "py_proto_library")

filegroup(
    name = "slicing_strategies",
    srcs = glob(["*.textproto"]),
)

proto_library(
    name = "slicing_strategy_proto",
    srcs = ["slicing_strategy.proto"],
)

py_proto_library(
    name = "slicing_strategy_proto_py",
    srcs = ["slicing_strategy.proto"],
)

py_library(
    name = "slicing_strategy_loader",
    srcs = [
        "slicing_strategy_loader.py",
    ],
    data = [
        ":slicing_strategies",
    ],
    visibility = [
        "//analysis/pfe_methods:__pkg__",
    ],
    deps = [
        ":slicing_strategy_proto_py",
        "@fonttools",
    ],
)

py_test(
    name = "slicing_strategy_loader_test",
    srcs = [
        "slicing_strategy_loader_test.py",
    ],
    deps = [
        ":slicing_strategy_loader",
    ],
)
