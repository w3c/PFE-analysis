workspace(name = "PFE_analysis")

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

# Google Test
http_archive(
    name = "gtest",
    sha256 = "94c634d499558a76fa649edb13721dce6e98fb1e7018dfaeba3cd7a083945e91",
    strip_prefix = "googletest-release-1.10.0",
    url = "https://github.com/google/googletest/archive/release-1.10.0.zip",
)

# FontTools
http_archive(
    name = "fonttools",
    build_file = "//third_party:fonttools.BUILD",
    sha256 = "9d02d0d4408c0b547360d69a41dd3887e52968f0b9cf654c3b26a2d33c80f319",
    strip_prefix = "fonttools-4.2.0",
    url = "https://github.com/fonttools/fonttools/archive/4.2.0.zip",
)

# Brotli Encoder/Decoder
http_archive(
    name = "brotli",
    sha256 = "7a0424ed544806a63bb78698f7dbfd44c7f47d2cca41638e53cd208a7d9247a9",
    strip_prefix = "brotli-shared-brotli",
    url = "https://github.com/google/brotli/archive/shared-brotli.zip",
)

# WOFF2 Encoder/Decoder
http_archive(
    name = "woff2",
    build_file = "//third_party:woff2.BUILD",
    sha256 = "db9ebe2aff6520e22ad9491863fc9e851b71fedbabefbb32508935d0f5cecf91",
    strip_prefix = "woff2-a0d0ed7da27b708c0a4e96ad7a998bddc933c06e",
    url = "https://github.com/google/woff2/archive/a0d0ed7da27b708c0a4e96ad7a998bddc933c06e.zip",
)

# harfbuzz
http_archive(
    name = "harfbuzz",
    build_file = "//third_party:harfbuzz.BUILD",
    sha256 = "c7d1d52d530b967a0cef8b7bb157474821c2e1ab609672fa255cced12e90c869",
    strip_prefix = "harfbuzz-2.6.7",
    urls = ["https://github.com/harfbuzz/harfbuzz/archive/2.6.7.zip"],
)

# farmhash
http_archive(
    name = "farmhash",
    build_file = "//third_party:farmhash.BUILD",
    sha256 = "470e87745d1393cc2793f49e9bfbd2c2cf282feeeb0c367f697996fa7e664fc5",
    strip_prefix = "farmhash-0d859a811870d10f53a594927d0d0b97573ad06d",
    urls = ["https://github.com/google/farmhash/archive/0d859a811870d10f53a594927d0d0b97573ad06d.zip"],
)

# abseil-cpp
http_archive(
    name = "com_google_absl",
    sha256 = "aa6386de0481bd4a096c25a0dc7ae50c2b57a064abd39f961fb3ce68eda933f8",
    strip_prefix = "abseil-cpp-20200225",
    urls = ["https://github.com/abseil/abseil-cpp/archive/20200225.zip"],
)

# abseil-py
http_archive(
    name = "io_abseil_py",
    sha256 = "e7f5624c861c51901d9d40ebb09490cf728e3bd6133c9ce26059cdc548fc201e",
    strip_prefix = "abseil-py-pypi-v0.9.0",
    urls = ["https://github.com/abseil/abseil-py/archive/pypi-v0.9.0.zip"],
)

# six archive - needed by abseil-py
http_archive(
    name = "six_archive",
    build_file = "@//third_party:six.BUILD",
    sha256 = "105f8d68616f8248e24bf0e9372ef04d3cc10104f1980f54d57b2ce73a5ad56a",
    strip_prefix = "six-1.10.0",
    urls = [
        "http://mirror.bazel.build/pypi.python.org/packages/source/s/six/six-1.10.0.tar.gz",
        "https://pypi.python.org/packages/source/s/six/six-1.10.0.tar.gz",
    ],
)

# Proto buf generating rules
http_archive(
    name = "rules_proto",
    sha256 = "4d421d51f9ecfe9bf96ab23b55c6f2b809cbaf0eea24952683e397decfbd0dd0",
    strip_prefix = "rules_proto-f6b8d89b90a7956f6782a4a3609b2f0eee3ce965",
    urls = [
        "https://mirror.bazel.build/github.com/bazelbuild/rules_proto/archive/f6b8d89b90a7956f6782a4a3609b2f0eee3ce965.tar.gz",
        "https://github.com/bazelbuild/rules_proto/archive/f6b8d89b90a7956f6782a4a3609b2f0eee3ce965.tar.gz",
    ],
)
load("@rules_proto//proto:repositories.bzl", "rules_proto_dependencies", "rules_proto_toolchains")
rules_proto_dependencies()
rules_proto_toolchains()

### Emscripten ###

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

http_archive(
    name = "build_bazel_rules_nodejs",
    sha256 = "0f2de53628e848c1691e5729b515022f5a77369c76a09fbe55611e12731c90e3",
    urls = ["https://github.com/bazelbuild/rules_nodejs/releases/download/2.0.1/rules_nodejs-2.0.1.tar.gz"],
)

load("@build_bazel_rules_nodejs//:index.bzl", "npm_install")

# emscripten 2.0.9
http_archive(
    name = "emscripten",
    sha256 = "42e06a5ad4b369fcb435db097edb8c4fb824b3125a3b8996aca6f10bc79d9dca",
    strip_prefix = "install",
    url = "https://storage.googleapis.com/webassembly/emscripten-releases-builds/linux/d8e430f9a9b6e87502f826c39e7684852f59624f/wasm-binaries.tbz2",
    build_file = "//emscripten_toolchain:emscripten.BUILD",
    type = "tar.bz2",
)

npm_install(
    name = "npm",
    package_json = "@emscripten//:emscripten/package.json",
    package_lock_json = "@emscripten//:emscripten/package-lock.json",
)

