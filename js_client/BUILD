package(default_visibility = ["//visibility:public"])

DEFAULT_EMSCRIPTEN_LINKOPTS = [
    "-flto",  # Specify lto (has to be set on for compiler as well)
    "--bind",  # Compiles the source code using the Embind bindings to connect C/C++ and JavaScript
    "--closure 1",  # Run the closure compiler
    "-s MALLOC=emmalloc",  # Switch to using the much smaller implementation
    "-s ALLOW_MEMORY_GROWTH=0",  # Our example doesn't need memory growth
    "-s USE_PTHREADS=0",  # Disable pthreads
    "-s ASSERTIONS=0",  # Turn off assertions
    "-s MODULARIZE=1",  # Allows us to manually invoke the initialization of wasm
    "-s EXPORT_NAME=createModule",  # Not used, but good to specify
    "-s SINGLE_FILE=1",  # Pack all webassembly into base64
    "-s FETCH=1",  # Enable fetch API
]

ASMJS_LINKOPTS = [
    "-s WASM=0",  # Specify asm.js output
]

WASM_LINKOPTS = [
    "-s WASM=1",  # Specify wasm output
]

cc_binary(
    name = "patch_subset_wasm.js",
    srcs = [
        "patch_subset_client.cc",
        "remote_patch_subset_server.cc",
        "remote_patch_subset_server.h",
    ],
    linkopts = DEFAULT_EMSCRIPTEN_LINKOPTS + WASM_LINKOPTS,
    deps = [
        "//common",
        "//patch_subset:client",
        "//patch_subset:common",
        "//patch_subset:patch_subset_cc_proto",
        "@com_google_absl//absl/strings",
        "@harfbuzz",
    ],
)
