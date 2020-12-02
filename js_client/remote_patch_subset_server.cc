#include "js_client/remote_patch_subset_server.h"

#include <string>

#include <emscripten/fetch.h>
#include <google/protobuf/io/zero_copy_stream_impl_lite.h>

using google::protobuf::io::ArrayInputStream;

namespace patch_subset {

StatusCode RemotePatchSubsetServer::Handle(const std::string& font_id,
                                           const PatchRequestProto& request,
                                           PatchResponseProto* response) {
  std::string payload;
  if (!request.SerializeToString(&payload)) {
    LOG(WARNING) << "Failed to serialize request.";
    return StatusCode::kInternal;
  }

  emscripten_fetch_attr_t attr;
  emscripten_fetch_attr_init(&attr);
  strcpy(attr.requestMethod, "POST");
  attr.attributes = EMSCRIPTEN_FETCH_LOAD_TO_MEMORY | EMSCRIPTEN_FETCH_SYNCHRONOUS;

  attr.requestData = payload.data();
  attr.requestDataSize = payload.size();

  std::string url = _remote_address + font_id;
  emscripten_fetch_t *fetch = emscripten_fetch(&attr, url.c_str());

  if (fetch->status != 200) {
    LOG(WARNING) << "Extend http request failed with code " << fetch->status;
    if (fetch->status >= 400 && fetch->status < 500) {
      emscripten_fetch_close(fetch);
      return StatusCode::kNotFound;
    }
    emscripten_fetch_close(fetch);
    return StatusCode::kInternal;
  }

  ArrayInputStream response_data(fetch->data, fetch->numBytes);
  if (!response->ParseFromZeroCopyStream(&response_data)) {
    LOG(WARNING) << "Failed to decode server response.";
    emscripten_fetch_close(fetch);
    return StatusCode::kInternal;
  }

  emscripten_fetch_close(fetch);
  return StatusCode::kOk;
}

}  // namespace patch_subset
