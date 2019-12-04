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
    visibility = [
        "//analysis/pfe_methods:__pkg__",
    ],
)
