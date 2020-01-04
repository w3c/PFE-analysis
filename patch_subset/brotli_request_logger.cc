#include "patch_subset/brotli_request_logger.h"

#include <string>
#include <vector>

#include "patch_subset/brotli_binary_diff.h"
#include "patch_subset/font_data.h"

namespace patch_subset {

void BrotliRequestLogger::LogRequest(const std::string& request_data,
                                     const std::string& response_data) {
  std::string compressed_request_data;
  CompressIfSmaller(request_data, &compressed_request_data);
  std::string compressed_response_data;
  CompressIfSmaller(response_data, &compressed_response_data);

  memory_request_logger_->LogRequest(compressed_request_data,
                                     compressed_response_data);
}

void BrotliRequestLogger::CompressIfSmaller(const std::string& data,
                                            std::string* output_data) {
  FontData empty;
  FontData compressed;
  FontData font_data(data);

  StatusCode result = brotli_diff_->Diff(empty, font_data, &compressed);
  if (result == StatusCode::kOk && compressed.size() < data.size()) {
    output_data->assign(compressed.data(), compressed.size());
  } else {
    *output_data = data;
  }
}

}  // namespace patch_subset
