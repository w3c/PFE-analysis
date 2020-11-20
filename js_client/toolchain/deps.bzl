load("//js_client/toolchain:cc_toolchain_config.bzl", "emsdk_configure")

def js_client_deps():
    # Make emdsk available as external/emsdk/emsdk/*
    emsdk_configure(name = "emsdk")
