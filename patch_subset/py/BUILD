cc_binary(
    name = "patch_subset_session.so",
    srcs = [
        "patch_subset_session.cc",
    ],
    linkshared = 1,
    linkstatic = 1,
    deps = [
        "//common",
        "//patch_subset:client",
        "//patch_subset:common",
        "//patch_subset:server",
    ],
)

py_library(
    name = "py",
    srcs = [
        "patch_subset_method.py",
    ],
    data = [
        ":patch_subset_session.so",
    ],
)

py_test(
    name = "patch_subset_method_test",
    srcs = [
        "patch_subset_method_test.py",
    ],
    data = [
        "//patch_subset:testdata",
    ],
    deps = [
        ":py",
    ],
)
