workspace(name = "PFE_analysis")
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

# Google Test
http_archive(
    name = "gtest",
    url = "https://github.com/google/googletest/archive/master.zip",
    strip_prefix = "googletest-master",
)

# Brotli Encoder/Decoder
http_archive(
    name = "brotli",
    url = "https://github.com/google/brotli/archive/shared-brotli.zip",
    strip_prefix = "brotli-shared-brotli",
)

# harfbuzz
http_archive(
    name = "harfbuzz",
    build_file = "//third_party:harfbuzz.BUILD",
    strip_prefix = "harfbuzz-master",
    urls = ["https://github.com/harfbuzz/harfbuzz/archive/master.zip"],
    sha256 = "3d620080d8e897f8b89c691cb01d14313f2d048640c296df3d6a061a1068e54c"
)

# farmhash
http_archive(
    name = "farmhash",
    build_file = "//third_party:farmhash.BUILD",
    strip_prefix = "farmhash-master",
    urls = ["https://github.com/google/farmhash/archive/master.zip"],
    sha256 = "d27a245e59f5e10fba10b88cb72c5f0e03d3f2936abbaf0cb78eeec686523ec1",
)

# abseil-cpp
http_archive(
     name = "com_google_absl",
     urls = ["https://github.com/abseil/abseil-cpp/archive/master.zip"],
     strip_prefix = "abseil-cpp-master",
)

# rules_cc defines rules for generating C++ code from Protocol Buffers.
http_archive(
    name = "rules_cc",
    strip_prefix = "rules_cc-master",
    urls = ["https://github.com/bazelbuild/rules_cc/archive/master.zip"],
    sha256 = "6ad4a8bb96bf92ad1165568f16e0164662f20e0c672cebba9a8de386493e8c36",
)

# rules_proto defines abstract rules for building Protocol Buffers.
http_archive(
    name = "rules_proto",
    strip_prefix = "rules_proto-master",
    urls = [
        "https://github.com/bazelbuild/rules_proto/archive/master.zip",
    ],
    sha256 = "6ae258a3974c768390b5569d4a52a940cae063405c2282ef11a9ed13e7049b41",
)

load("@rules_cc//cc:repositories.bzl", "rules_cc_dependencies")
rules_cc_dependencies()

load("@rules_proto//proto:repositories.bzl", "rules_proto_dependencies", "rules_proto_toolchains")
rules_proto_dependencies()
rules_proto_toolchains()
