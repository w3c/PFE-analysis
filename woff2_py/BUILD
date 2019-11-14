cc_binary(
    name = "woff2_py.so",
    srcs = [
        "woff2_py.cc",
    ],
    linkshared = 1,
    linkstatic = 1,
    deps = [
        "@woff2",
    ],
)

py_library(
    name = "woff2_py",
    srcs = [
        "woff2.py",
    ],
    data = [
        ":woff2_py.so",
    ],
    visibility = [
        "//analysis/pfe_methods:__pkg__",
    ],
)

py_test(
    name = "woff2_py_test",
    srcs = [
        "woff2_test.py",
    ],
    data = [
        "//patch_subset:testdata",
    ],
    main = "woff2_test.py",
    deps = [
        ":woff2_py",
    ],
)
