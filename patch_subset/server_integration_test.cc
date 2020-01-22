#include "gtest/gtest.h"
#include "patch_subset/brotli_binary_diff.h"
#include "patch_subset/brotli_binary_patch.h"
#include "patch_subset/codepoint_mapper.h"
#include "patch_subset/codepoint_mapping_checksum.h"
#include "patch_subset/compressed_set.h"
#include "patch_subset/farm_hasher.h"
#include "patch_subset/file_font_provider.h"
#include "patch_subset/harfbuzz_subsetter.h"
#include "patch_subset/hb_set_unique_ptr.h"
#include "patch_subset/patch_subset_server_impl.h"

using ::absl::string_view;

namespace patch_subset {

static const uint64_t kOriginalFontFingerprint = 0xA55ED7AAAA5AABB1;
static const uint64_t kSubsetAbFingerprint = 0x736883EEAB917A2B;
static const uint64_t kSubsetAbcdFingerprint = 0x6CB91B25FC508BDB;

class PatchSubsetServerIntegrationTest : public ::testing::Test {
 protected:
  PatchSubsetServerIntegrationTest()
      : font_provider_(new FileFontProvider("patch_subset/testdata/")),
        binary_diff_(new BrotliBinaryDiff()),
        server_(std::unique_ptr<FontProvider>(font_provider_),
                std::unique_ptr<Subsetter>(new HarfbuzzSubsetter()),
                std::unique_ptr<BinaryDiff>(binary_diff_),
                std::unique_ptr<Hasher>(new FarmHasher()),
                std::unique_ptr<CodepointMapper>(nullptr),
                std::unique_ptr<CodepointMappingChecksum>(nullptr)) {
    font_provider_->GetFont("Roboto-Regular.abcd.ttf", &roboto_abcd_);
    font_provider_->GetFont("Roboto-Regular.ab.ttf", &roboto_ab_);
  }

  void CheckPatch(const FontData& base, const FontData& target,
                  string_view patch_string) {
    // Check that diff base and target produces patch,
    // and that applying patch to base produces target.
    BrotliBinaryDiff binary_diff;
    FontData expected_patch;
    EXPECT_EQ(binary_diff.Diff(base, target, &expected_patch), StatusCode::kOk);
    EXPECT_EQ(patch_string, expected_patch.str());

    FontData actual_target;
    FontData patch;
    BrotliBinaryPatch binary_patch;
    patch.copy(patch_string.data(), patch_string.size());
    EXPECT_EQ(binary_patch.Patch(base, patch, &actual_target), StatusCode::kOk);
    EXPECT_EQ(actual_target.str(), target.str());
  }

  FontProvider* font_provider_;
  BinaryDiff* binary_diff_;
  PatchSubsetServerImpl server_;

  FontData empty_;
  FontData roboto_abcd_;
  FontData roboto_ab_;
};

TEST_F(PatchSubsetServerIntegrationTest, NewRequest) {
  hb_set_unique_ptr set_abcd = make_hb_set_from_ranges(1, 0x61, 0x64);

  PatchRequestProto request;
  CompressedSet::Encode(*set_abcd, request.mutable_codepoints_needed());

  PatchResponseProto response;
  EXPECT_EQ(server_.Handle("Roboto-Regular.ttf", request, &response),
            StatusCode::kOk);

  EXPECT_EQ(response.original_font_fingerprint(), kOriginalFontFingerprint);
  EXPECT_EQ(response.type(), ResponseType::REBASE);
  EXPECT_EQ(response.patch().patched_fingerprint(), kSubsetAbcdFingerprint);
  EXPECT_EQ(response.patch().format(), PatchFormat::BROTLI_SHARED_DICT);

  CheckPatch(empty_, roboto_abcd_, response.patch().patch());
}

TEST_F(PatchSubsetServerIntegrationTest, PatchRequest) {
  hb_set_unique_ptr set_ab = make_hb_set_from_ranges(1, 0x61, 0x62);
  hb_set_unique_ptr set_abcd = make_hb_set_from_ranges(1, 0x61, 0x64);

  PatchRequestProto request;
  CompressedSet::Encode(*set_ab, request.mutable_codepoints_have());
  CompressedSet::Encode(*set_abcd, request.mutable_codepoints_needed());
  request.set_original_font_fingerprint(kOriginalFontFingerprint);
  request.set_base_fingerprint(kSubsetAbFingerprint);

  PatchResponseProto response;
  EXPECT_EQ(server_.Handle("Roboto-Regular.ttf", request, &response),
            StatusCode::kOk);

  EXPECT_EQ(response.original_font_fingerprint(), kOriginalFontFingerprint);
  EXPECT_EQ(response.type(), ResponseType::PATCH);
  EXPECT_EQ(response.patch().patched_fingerprint(), kSubsetAbcdFingerprint);
  EXPECT_EQ(response.patch().format(), PatchFormat::BROTLI_SHARED_DICT);

  CheckPatch(roboto_ab_, roboto_abcd_, response.patch().patch());
}

TEST_F(PatchSubsetServerIntegrationTest, BadOriginalFingerprint) {
  hb_set_unique_ptr set_ab = make_hb_set_from_ranges(1, 0x61, 0x62);
  hb_set_unique_ptr set_abcd = make_hb_set_from_ranges(1, 0x61, 0x64);

  PatchRequestProto request;
  CompressedSet::Encode(*set_ab, request.mutable_codepoints_have());
  CompressedSet::Encode(*set_abcd, request.mutable_codepoints_needed());
  request.set_original_font_fingerprint(0);
  request.set_base_fingerprint(kSubsetAbFingerprint);

  PatchResponseProto response;
  EXPECT_EQ(server_.Handle("Roboto-Regular.ttf", request, &response),
            StatusCode::kOk);

  EXPECT_EQ(response.original_font_fingerprint(), kOriginalFontFingerprint);
  EXPECT_EQ(response.type(), ResponseType::REBASE);
  EXPECT_EQ(response.patch().patched_fingerprint(), kSubsetAbcdFingerprint);
  EXPECT_EQ(response.patch().format(), PatchFormat::BROTLI_SHARED_DICT);

  CheckPatch(empty_, roboto_abcd_, response.patch().patch());
}

TEST_F(PatchSubsetServerIntegrationTest, BadBaseFingerprint) {
  hb_set_unique_ptr set_ab = make_hb_set_from_ranges(1, 0x61, 0x62);
  hb_set_unique_ptr set_abcd = make_hb_set_from_ranges(1, 0x61, 0x64);

  PatchRequestProto request;
  CompressedSet::Encode(*set_ab, request.mutable_codepoints_have());
  CompressedSet::Encode(*set_abcd, request.mutable_codepoints_needed());
  request.set_original_font_fingerprint(kOriginalFontFingerprint);
  request.set_base_fingerprint(0);

  PatchResponseProto response;
  EXPECT_EQ(server_.Handle("Roboto-Regular.ttf", request, &response),
            StatusCode::kOk);

  EXPECT_EQ(response.original_font_fingerprint(), kOriginalFontFingerprint);
  EXPECT_EQ(response.type(), ResponseType::REBASE);
  EXPECT_EQ(response.patch().patched_fingerprint(), kSubsetAbcdFingerprint);
  EXPECT_EQ(response.patch().format(), PatchFormat::BROTLI_SHARED_DICT);

  CheckPatch(empty_, roboto_abcd_, response.patch().patch());
}

}  // namespace patch_subset
