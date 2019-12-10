#include "patch_subset/brotli_request_logger.h"

#include "gtest/gtest.h"

namespace patch_subset {

class BrotliRequestLoggerTest : public ::testing::Test {
 protected:
  BrotliRequestLoggerTest()
      : memory_request_logger_(new MemoryRequestLogger()),
        request_logger_(new BrotliRequestLogger(memory_request_logger_.get())) {
  }

  ~BrotliRequestLoggerTest() override {}

  void SetUp() override {}

  std::unique_ptr<MemoryRequestLogger> memory_request_logger_;
  std::unique_ptr<BrotliRequestLogger> request_logger_;
};

TEST_F(BrotliRequestLoggerTest, Compresses) {
  std::string request_data =
      "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
      "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
      "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
  std::string response_data =
      "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
      "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
      "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";

  request_logger_->LogRequest(request_data, response_data);

  EXPECT_EQ(memory_request_logger_->Records().size(), 1);
  const MemoryRequestLogger::Record& record =
      memory_request_logger_->Records()[0];
  EXPECT_LT(record.request_size, request_data.size());
  EXPECT_LT(record.response_size, response_data.size());
}

TEST_F(BrotliRequestLoggerTest, DoesntCompress) {
  std::string request_data = "abcdefghijk";
  std::string response_data = "abcdefghijk";

  request_logger_->LogRequest(request_data, response_data);

  EXPECT_EQ(memory_request_logger_->Records().size(), 1);
  const MemoryRequestLogger::Record& record =
      memory_request_logger_->Records()[0];
  EXPECT_EQ(record.request_size, request_data.size());
  EXPECT_EQ(record.response_size, response_data.size());
}

}  // namespace patch_subset
