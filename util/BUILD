load("@rules_cc//cc:defs.bzl", "cc_binary")

cc_binary(
    name = "fingerprint",
    srcs = [
        "fingerprint.cc",
    ],
    copts = [
        "-std=c++17",
    ],
    deps = [
        "//patch_subset:common",
    ],
)
