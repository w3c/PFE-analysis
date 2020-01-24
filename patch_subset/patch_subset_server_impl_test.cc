#include "patch_subset/patch_subset_server_impl.h"

#include <google/protobuf/util/message_differencer.h>

#include <algorithm>

#include "absl/strings/string_view.h"
#include "gmock/gmock.h"
#include "gtest/gtest.h"
#include "hb.h"
#include "patch_subset/codepoint_mapper.h"
#include "patch_subset/compressed_set.h"
#include "patch_subset/fake_subsetter.h"
#include "patch_subset/hb_set_unique_ptr.h"
#include "patch_subset/mock_binary_diff.h"
#include "patch_subset/mock_codepoint_mapping_checksum.h"
#include "patch_subset/mock_font_provider.h"
#include "patch_subset/mock_hasher.h"
#include "patch_subset/simple_codepoint_mapper.h"

using ::absl::string_view;
using ::google::protobuf::util::MessageDifferencer;

using ::testing::_;
using ::testing::Invoke;
using ::testing::Return;

namespace patch_subset {

MATCHER_P(EqualsProto, other, "") {
  return MessageDifferencer::Equals(arg, other);
}

StatusCode returnFontId(const std::string& id, FontData* out) {
  out->copy(id.c_str(), id.size());
  return StatusCode::kOk;
}

StatusCode diff(const FontData& font_base, const FontData& font_derived,
                FontData* out /* OUT */) {
  if (font_base.empty()) {
    out->copy(font_derived.data(), font_derived.size());
    return StatusCode::kOk;
  }

  std::string base(font_base.data(), font_base.size());
  std::string derived(font_derived.data(), font_derived.size());
  std::string patch(derived + " - " + base);
  out->copy(patch.c_str(), patch.size());
  return StatusCode::kOk;
}

class PatchSubsetServerImplTestBase : public ::testing::Test {
 protected:
  PatchSubsetServerImplTestBase()
      : font_provider_(new MockFontProvider()),
        binary_diff_(new MockBinaryDiff()),
        hasher_(new MockHasher()),
        set_abcd_(make_hb_set_from_ranges(1, 0x61, 0x64)),
        set_ab_(make_hb_set_from_ranges(1, 0x61, 0x62)) {}

  void ExpectDiff() {
    EXPECT_CALL(*binary_diff_, Diff(_, _, _))
        .Times(1)
        .WillRepeatedly(Invoke(diff));
  }

  void ExpectRoboto() {
    EXPECT_CALL(*font_provider_, GetFont("Roboto-Regular.ttf", _))
        .Times(1)
        .WillRepeatedly(Invoke(returnFontId));
  }

  void ExpectChecksum(string_view value, uint64_t checksum) {
    EXPECT_CALL(*hasher_, Checksum(value)).WillRepeatedly(Return(checksum));
  }

  MockFontProvider* font_provider_;
  MockBinaryDiff* binary_diff_;
  MockHasher* hasher_;
  hb_set_unique_ptr set_abcd_;
  hb_set_unique_ptr set_ab_;
};

class PatchSubsetServerImplTest : public PatchSubsetServerImplTestBase {
 protected:
  PatchSubsetServerImplTest()
      : server_(std::unique_ptr<FontProvider>(font_provider_),
                std::unique_ptr<Subsetter>(new FakeSubsetter()),
                std::unique_ptr<BinaryDiff>(binary_diff_),
                std::unique_ptr<Hasher>(hasher_),
                std::unique_ptr<CodepointMapper>(nullptr),
                std::unique_ptr<CodepointMappingChecksum>(nullptr)) {}

  PatchSubsetServerImpl server_;
};

class PatchSubsetServerImplWithCodepointRemappingTest
    : public PatchSubsetServerImplTestBase {
 protected:
  PatchSubsetServerImplWithCodepointRemappingTest()
      : codepoint_mapping_checksum_(new MockCodepointMappingChecksum()),
        server_(std::unique_ptr<FontProvider>(font_provider_),
                std::unique_ptr<Subsetter>(new FakeSubsetter()),
                std::unique_ptr<BinaryDiff>(binary_diff_),
                std::unique_ptr<Hasher>(hasher_),
                std::unique_ptr<CodepointMapper>(new SimpleCodepointMapper()),
                std::unique_ptr<CodepointMappingChecksum>(
                    codepoint_mapping_checksum_)) {}

  void ExpectCodepointMappingChecksum(std::vector<int> mapping_deltas,
                                      uint64_t checksum) {
    CodepointRemappingProto proto;
    CompressedListProto* compressed_list = proto.mutable_codepoint_ordering();
    for (int delta : mapping_deltas) {
      compressed_list->add_deltas(delta);
    }

    EXPECT_CALL(*codepoint_mapping_checksum_, Checksum(EqualsProto(proto)))
        .WillRepeatedly(Return(checksum));
  }

  MockCodepointMappingChecksum* codepoint_mapping_checksum_;
  PatchSubsetServerImpl server_;
};

// TODO(garretrieger): subsetter failure test.
// TODO(garretrieger):
//  - REINDEX response
//  - PATCH response, with client using codepoint mapping.

TEST_F(PatchSubsetServerImplTest, NewRequest) {
  ExpectRoboto();
  ExpectDiff();

  ExpectChecksum("Roboto-Regular.ttf", 42);
  ExpectChecksum("Roboto-Regular.ttf:abcd", 43);

  PatchRequestProto request;
  PatchResponseProto response;
  CompressedSet::Encode(*set_abcd_, request.mutable_codepoints_needed());

  EXPECT_EQ(server_.Handle("Roboto-Regular.ttf", request, &response),
            StatusCode::kOk);
  EXPECT_EQ(response.original_font_fingerprint(), 42);
  EXPECT_EQ(response.type(), ResponseType::REBASE);
  EXPECT_EQ(response.patch().patch(), "Roboto-Regular.ttf:abcd");
  EXPECT_EQ(response.patch().patched_fingerprint(), 43);
  EXPECT_EQ(response.patch().format(), PatchFormat::BROTLI_SHARED_DICT);

  EXPECT_FALSE(response.has_codepoint_remapping());
}

TEST_F(PatchSubsetServerImplWithCodepointRemappingTest,
       NewRequestWithCodepointRemapping) {
  ExpectRoboto();
  ExpectDiff();

  ExpectChecksum("Roboto-Regular.ttf", 42);
  ExpectChecksum("Roboto-Regular.ttf:abcd", 43);

  ExpectCodepointMappingChecksum({1, 1, 1}, 44);

  PatchRequestProto request;
  PatchResponseProto response;
  CompressedSet::Encode(*set_abcd_, request.mutable_codepoints_needed());

  EXPECT_EQ(server_.Handle("Roboto-Regular.ttf", request, &response),
            StatusCode::kOk);

  // Check that a codepoint mapping response has been included.
  EXPECT_EQ(response.codepoint_remapping().fingerprint(), 44);
  EXPECT_EQ(response.codepoint_remapping().codepoint_ordering().deltas_size(),
            3);
  for (int i = 0; i < 3; i++) {
    EXPECT_EQ(response.codepoint_remapping().codepoint_ordering().deltas(i), 1);
  }
}

TEST_F(PatchSubsetServerImplTest, PatchRequest) {
  ExpectRoboto();
  ExpectDiff();
  ExpectChecksum("Roboto-Regular.ttf", 42);
  ExpectChecksum("Roboto-Regular.ttf:ab", 43);
  ExpectChecksum("Roboto-Regular.ttf:abcd", 44);

  PatchRequestProto request;
  PatchResponseProto response;
  CompressedSet::Encode(*set_ab_, request.mutable_codepoints_have());
  CompressedSet::Encode(*set_abcd_, request.mutable_codepoints_needed());
  request.set_original_font_fingerprint(42);
  request.set_base_fingerprint(43);

  EXPECT_EQ(server_.Handle("Roboto-Regular.ttf", request, &response),
            StatusCode::kOk);
  EXPECT_EQ(response.original_font_fingerprint(), 42);
  EXPECT_EQ(response.type(), ResponseType::PATCH);
  EXPECT_EQ(response.patch().patch(),
            "Roboto-Regular.ttf:abcd - Roboto-Regular.ttf:ab");
  EXPECT_EQ(response.patch().patched_fingerprint(), 44);
  EXPECT_EQ(response.patch().format(), PatchFormat::BROTLI_SHARED_DICT);

  EXPECT_FALSE(response.has_codepoint_remapping());
}

TEST_F(PatchSubsetServerImplWithCodepointRemappingTest, PatchRequest) {
  ExpectRoboto();
  ExpectDiff();
  ExpectChecksum("Roboto-Regular.ttf", 42);
  ExpectChecksum("Roboto-Regular.ttf:ab", 43);
  ExpectChecksum("Roboto-Regular.ttf:abcd", 44);

  PatchRequestProto request;
  PatchResponseProto response;
  CompressedSet::Encode(*set_ab_, request.mutable_codepoints_have());
  CompressedSet::Encode(*set_abcd_, request.mutable_codepoints_needed());
  request.set_original_font_fingerprint(42);
  request.set_base_fingerprint(43);

  EXPECT_EQ(server_.Handle("Roboto-Regular.ttf", request, &response),
            StatusCode::kOk);

  // Patch request should not send back a codepoint remapping.
  EXPECT_FALSE(response.has_codepoint_remapping());
}

// TODO(garretrieger): test for bad codepoint remapping checksum (on patch
// request).

TEST_F(PatchSubsetServerImplTest, BadOriginalFontChecksum) {
  ExpectRoboto();
  ExpectDiff();
  ExpectChecksum("Roboto-Regular.ttf", 42);
  ExpectChecksum("Roboto-Regular.ttf:abcd", 44);

  PatchRequestProto request;
  PatchResponseProto response;
  CompressedSet::Encode(*set_ab_, request.mutable_codepoints_have());
  CompressedSet::Encode(*set_abcd_, request.mutable_codepoints_needed());
  request.set_original_font_fingerprint(100);
  request.set_base_fingerprint(43);

  EXPECT_EQ(server_.Handle("Roboto-Regular.ttf", request, &response),
            StatusCode::kOk);
  EXPECT_EQ(response.original_font_fingerprint(), 42);
  EXPECT_EQ(response.type(), ResponseType::REBASE);
  EXPECT_EQ(response.patch().patch(), "Roboto-Regular.ttf:abcd");
  EXPECT_EQ(response.patch().patched_fingerprint(), 44);
  EXPECT_EQ(response.patch().format(), PatchFormat::BROTLI_SHARED_DICT);
}

TEST_F(PatchSubsetServerImplTest, BadBaseChecksum) {
  ExpectRoboto();
  ExpectDiff();
  ExpectChecksum("Roboto-Regular.ttf", 42);
  ExpectChecksum("Roboto-Regular.ttf:ab", 43);
  ExpectChecksum("Roboto-Regular.ttf:abcd", 44);

  PatchRequestProto request;
  PatchResponseProto response;
  CompressedSet::Encode(*set_ab_, request.mutable_codepoints_have());
  CompressedSet::Encode(*set_abcd_, request.mutable_codepoints_needed());
  request.set_original_font_fingerprint(42);
  request.set_base_fingerprint(100);

  EXPECT_EQ(server_.Handle("Roboto-Regular.ttf", request, &response),
            StatusCode::kOk);
  EXPECT_EQ(response.original_font_fingerprint(), 42);
  EXPECT_EQ(response.type(), ResponseType::REBASE);
  EXPECT_EQ(response.patch().patch(), "Roboto-Regular.ttf:abcd");
  EXPECT_EQ(response.patch().patched_fingerprint(), 44);
  EXPECT_EQ(response.patch().format(), PatchFormat::BROTLI_SHARED_DICT);
}

TEST_F(PatchSubsetServerImplTest, NotFound) {
  EXPECT_CALL(*font_provider_, GetFont("Roboto-Regular.ttf", _))
      .Times(1)
      .WillRepeatedly(Return(StatusCode::kNotFound));

  PatchRequestProto request;
  PatchResponseProto response;
  CompressedSet::Encode(*set_abcd_, request.mutable_codepoints_needed());

  EXPECT_EQ(server_.Handle("Roboto-Regular.ttf", request, &response),
            StatusCode::kNotFound);
}

}  // namespace patch_subset
