#include "patch_subset/patch_subset_client.h"

#include <google/protobuf/util/message_differencer.h>

#include "common/status.h"
#include "gmock/gmock.h"
#include "gtest/gtest.h"
#include "patch_subset/compressed_set.h"
#include "patch_subset/file_font_provider.h"
#include "patch_subset/hb_set_unique_ptr.h"
#include "patch_subset/mock_binary_patch.h"
#include "patch_subset/mock_hasher.h"
#include "patch_subset/mock_patch_subset_server.h"
#include "patch_subset/null_request_logger.h"
#include "patch_subset/patch_subset.pb.h"

using ::absl::string_view;
using ::google::protobuf::util::MessageDifferencer;

using ::testing::_;
using ::testing::ByRef;
using ::testing::Eq;
using ::testing::Invoke;
using ::testing::Return;

namespace patch_subset {

static uint64_t kOriginalFingerprint = 1;
static uint64_t kBaseFingerprint = 2;
static uint64_t kPatchedFingerprint = 3;

MATCHER_P(EqualsProto, other, "") {
  return MessageDifferencer::Equals(arg, other);
}

class PatchSubsetClientTest : public ::testing::Test {
 protected:
  PatchSubsetClientTest()
      : binary_patch_(new MockBinaryPatch()),
        hasher_(new MockHasher()),
        client_(
            new PatchSubsetClient(&server_, &request_logger_,
                                  std::unique_ptr<BinaryPatch>(binary_patch_),
                                  std::unique_ptr<Hasher>(hasher_))),
        font_provider_(new FileFontProvider("patch_subset/testdata/")) {
    font_provider_->GetFont("Roboto-Regular.ab.ttf", &roboto_ab_);
  }

  PatchRequestProto CreateRequest(const hb_set_t& codepoints) {
    PatchRequestProto request;
    request.mutable_codepoints_have();
    CompressedSet::Encode(codepoints, request.mutable_codepoints_needed());
    request.add_accept_format(PatchFormat::BROTLI_SHARED_DICT);
    return request;
  }

  PatchRequestProto CreateRequest(const hb_set_t& codepoints_have,
                                  const hb_set_t& codepoints_needed) {
    PatchRequestProto request;
    CompressedSet::Encode(codepoints_have, request.mutable_codepoints_have());
    CompressedSet::Encode(codepoints_needed,
                          request.mutable_codepoints_needed());
    request.add_accept_format(PatchFormat::BROTLI_SHARED_DICT);
    request.set_original_font_fingerprint(kOriginalFingerprint);
    request.set_base_fingerprint(kBaseFingerprint);
    return request;
  }

  PatchResponseProto CreateResponse(ResponseType type) {
    PatchResponseProto response;
    response.set_type(type);
    response.set_original_font_fingerprint(kOriginalFingerprint);
    response.mutable_patch()->set_format(PatchFormat::BROTLI_SHARED_DICT);
    response.mutable_patch()->set_patch("roboto.patch.ttf");
    response.mutable_patch()->set_patched_fingerprint(kPatchedFingerprint);
    return response;
  }

  void ExpectRequest(const PatchRequestProto& expected_request) {
    EXPECT_CALL(server_, Handle("roboto", EqualsProto(expected_request), _))
        .Times(1)
        // Short circuit the response handling code.
        .WillOnce(Return(StatusCode::kInternal));
  }

  void ExpectChecksum(string_view data, uint64_t checksum) {
    EXPECT_CALL(*hasher_, Checksum(data)).WillRepeatedly(Return(checksum));
  }

  void SendResponse(const PatchResponseProto& response) {
    EXPECT_CALL(server_, Handle(_, _, _))
        .Times(1)
        .WillOnce(Invoke(ReturnResponse(response)));
  }

  void ExpectPatch(const FontData& base, const FontData& patch,
                   string_view patched) {
    EXPECT_CALL(*binary_patch_, Patch(Eq(ByRef(base)), Eq(ByRef(patch)), _))
        .Times(1)
        .WillOnce(Invoke(ApplyPatch(patched)));
  }

  MockPatchSubsetServer server_;
  NullRequestLogger request_logger_;
  MockBinaryPatch* binary_patch_;
  MockHasher* hasher_;

  std::unique_ptr<PatchSubsetClient> client_;

  std::unique_ptr<FontProvider> font_provider_;
  FontData roboto_ab_;
};

TEST_F(PatchSubsetClientTest, SendsNewRequest) {
  hb_set_unique_ptr codepoints = make_hb_set_from_ranges(1, 0x61, 0x64);
  PatchRequestProto expected_request = CreateRequest(*codepoints);
  ExpectRequest(expected_request);

  ClientState state;
  state.set_font_id("roboto");
  client_->Extend(*codepoints, &state);
}

TEST_F(PatchSubsetClientTest, SendPatchRequest) {
  hb_set_unique_ptr codepoints_have = make_hb_set_from_ranges(1, 0x61, 0x62);
  hb_set_unique_ptr codepoints_needed = make_hb_set_from_ranges(1, 0x63, 0x64);
  PatchRequestProto expected_request =
      CreateRequest(*codepoints_have, *codepoints_needed);
  ExpectRequest(expected_request);
  ExpectChecksum(roboto_ab_.str(), kBaseFingerprint);

  ClientState state;
  state.set_font_id("roboto");
  state.set_font_data(roboto_ab_.data(), roboto_ab_.size());
  state.set_original_font_fingerprint(kOriginalFingerprint);
  client_->Extend(*codepoints_needed, &state);
}

TEST_F(PatchSubsetClientTest, SendPatchRequest_RemovesExistingCodepoints) {
  hb_set_unique_ptr codepoints_have = make_hb_set_from_ranges(1, 0x61, 0x62);
  hb_set_unique_ptr codepoints_needed = make_hb_set_from_ranges(1, 0x63, 0x64);
  PatchRequestProto expected_request =
      CreateRequest(*codepoints_have, *codepoints_needed);
  ExpectRequest(expected_request);
  ExpectChecksum(roboto_ab_.str(), kBaseFingerprint);

  hb_set_union(codepoints_needed.get(), codepoints_have.get());
  ClientState state;
  state.set_font_id("roboto");
  state.set_font_data(roboto_ab_.data(), roboto_ab_.size());
  state.set_original_font_fingerprint(kOriginalFingerprint);
  client_->Extend(*codepoints_needed, &state);
}

TEST_F(PatchSubsetClientTest, DoesntSendPatchRequest_NoNewCodepoints) {
  hb_set_unique_ptr codepoints_needed = make_hb_set_from_ranges(1, 0x61, 0x62);

  EXPECT_CALL(server_, Handle(_, _, _)).Times(0);

  ClientState state;
  state.set_font_id("roboto");
  state.set_font_data(roboto_ab_.data(), roboto_ab_.size());
  state.set_original_font_fingerprint(kOriginalFingerprint);
  EXPECT_EQ(client_->Extend(*codepoints_needed, &state), StatusCode::kOk);
}

TEST_F(PatchSubsetClientTest, HandlesRebaseResponse) {
  hb_set_unique_ptr codepoints = make_hb_set(1, 0x61);

  PatchResponseProto response = CreateResponse(ResponseType::REBASE);
  SendResponse(response);
  ExpectChecksum("roboto.patched.ttf", kPatchedFingerprint);

  FontData base("");
  FontData patch("roboto.patch.ttf");
  ExpectPatch(base, patch, "roboto.patched.ttf");

  ClientState state;
  state.set_font_data("roboto.base.ttf");
  EXPECT_EQ(client_->Extend(*codepoints, &state), StatusCode::kOk);

  EXPECT_EQ(state.font_data(), "roboto.patched.ttf");
  EXPECT_EQ(state.original_font_fingerprint(), kOriginalFingerprint);
}

TEST_F(PatchSubsetClientTest, HandlesPatchResponse) {
  hb_set_unique_ptr codepoints = make_hb_set(1, 0x61);

  PatchResponseProto response = CreateResponse(ResponseType::PATCH);

  SendResponse(response);
  ExpectChecksum("roboto.patched.ttf", kPatchedFingerprint);

  FontData base("roboto.base.ttf");
  FontData patch("roboto.patch.ttf");
  ExpectPatch(base, patch, "roboto.patched.ttf");

  ClientState state;
  state.set_font_data("roboto.base.ttf");
  EXPECT_EQ(client_->Extend(*codepoints, &state), StatusCode::kOk);

  EXPECT_EQ(state.font_data(), "roboto.patched.ttf");
  EXPECT_EQ(state.original_font_fingerprint(), kOriginalFingerprint);
}

// TODO(garretrieger): add more response handling tests:
//   - checksum mismatch.
//   - bad patch format.

}  // namespace patch_subset
