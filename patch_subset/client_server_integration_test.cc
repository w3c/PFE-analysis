#include "gtest/gtest.h"
#include "patch_subset/brotli_binary_diff.h"
#include "patch_subset/brotli_binary_patch.h"
#include "patch_subset/codepoint_mapper.h"
#include "patch_subset/codepoint_mapping_checksum.h"
#include "patch_subset/codepoint_mapping_checksum_impl.h"
#include "patch_subset/compressed_set.h"
#include "patch_subset/farm_hasher.h"
#include "patch_subset/file_font_provider.h"
#include "patch_subset/harfbuzz_subsetter.h"
#include "patch_subset/hb_set_unique_ptr.h"
#include "patch_subset/noop_codepoint_predictor.h"
#include "patch_subset/noop_glyf_transformer.h"
#include "patch_subset/null_request_logger.h"
#include "patch_subset/patch_subset.pb.h"
#include "patch_subset/patch_subset_client.h"
#include "patch_subset/patch_subset_server_impl.h"
#include "patch_subset/simple_codepoint_mapper.h"

using ::absl::string_view;

namespace patch_subset {

class PatchSubsetClientServerIntegrationTest : public ::testing::Test {
 protected:
  const std::string kTestDataDir = "patch_subset/testdata/";

  PatchSubsetClientServerIntegrationTest()
      : hasher_(new FarmHasher()),

        server_(
            0,
            std::unique_ptr<FontProvider>(new FileFontProvider(kTestDataDir)),
            std::unique_ptr<Subsetter>(new HarfbuzzSubsetter()),
            std::unique_ptr<BinaryDiff>(new BrotliBinaryDiff()),
            std::unique_ptr<Hasher>(new FarmHasher()),
            std::unique_ptr<CodepointMapper>(nullptr),
            std::unique_ptr<CodepointMappingChecksum>(nullptr),
            std::unique_ptr<CodepointPredictor>(new NoopCodepointPredictor()),
            std::unique_ptr<GlyfTransformer>(new NoopGlyfTransformer())),
        client_(&server_, &request_logger_,
                std::unique_ptr<BinaryPatch>(new BrotliBinaryPatch()),
                std::unique_ptr<Hasher>(new FarmHasher())),

        server_with_mapping_(
            0,
            std::unique_ptr<FontProvider>(new FileFontProvider(kTestDataDir)),
            std::unique_ptr<Subsetter>(new HarfbuzzSubsetter()),
            std::unique_ptr<BinaryDiff>(new BrotliBinaryDiff()),
            std::unique_ptr<Hasher>(new FarmHasher()),
            std::unique_ptr<CodepointMapper>(new SimpleCodepointMapper()),
            std::unique_ptr<CodepointMappingChecksum>(
                new CodepointMappingChecksumImpl(hasher_.get())),
            std::unique_ptr<CodepointPredictor>(new NoopCodepointPredictor()),
            std::unique_ptr<GlyfTransformer>(new NoopGlyfTransformer())),
        client_with_mapping_(
            &server_with_mapping_, &request_logger_,
            std::unique_ptr<BinaryPatch>(new BrotliBinaryPatch()),
            std::unique_ptr<Hasher>(new FarmHasher())) {
    FileFontProvider font_provider(kTestDataDir);
    font_provider.GetFont("Roboto-Regular.abcd.ttf", &roboto_abcd_);
    font_provider.GetFont("Roboto-Regular.ab.ttf", &roboto_ab_);
  }

  std::unique_ptr<Hasher> hasher_;
  NullRequestLogger request_logger_;

  PatchSubsetServerImpl server_;
  PatchSubsetClient client_;

  PatchSubsetServerImpl server_with_mapping_;
  PatchSubsetClient client_with_mapping_;

  FontData roboto_abcd_;
  FontData roboto_ab_;
};

TEST_F(PatchSubsetClientServerIntegrationTest, Session) {
  hb_set_unique_ptr set_ab = make_hb_set_from_ranges(1, 0x61, 0x62);
  ClientState state;
  state.set_font_id("Roboto-Regular.ttf");
  EXPECT_EQ(client_.Extend(*set_ab, &state), StatusCode::kOk);

  EXPECT_EQ(state.font_id(), "Roboto-Regular.ttf");
  EXPECT_EQ(state.original_font_fingerprint(), 0xA55ED7AAAA5AABB1);
  EXPECT_EQ(state.font_data(), roboto_ab_.str());

  hb_set_unique_ptr set_abcd = make_hb_set_from_ranges(1, 0x61, 0x64);
  EXPECT_EQ(client_.Extend(*set_abcd, &state), StatusCode::kOk);

  EXPECT_EQ(state.font_id(), "Roboto-Regular.ttf");
  EXPECT_EQ(state.original_font_fingerprint(), 0xA55ED7AAAA5AABB1);
  EXPECT_EQ(state.font_data(), roboto_abcd_.str());
  EXPECT_FALSE(state.has_codepoint_remapping());
}

TEST_F(PatchSubsetClientServerIntegrationTest, SessionWithCodepointRemapping) {
  hb_set_unique_ptr set_ab = make_hb_set_from_ranges(1, 0x61, 0x62);
  ClientState state;
  state.set_font_id("Roboto-Regular.ttf");
  EXPECT_EQ(client_with_mapping_.Extend(*set_ab, &state), StatusCode::kOk);

  EXPECT_EQ(state.font_id(), "Roboto-Regular.ttf");
  EXPECT_EQ(state.original_font_fingerprint(), 0xA55ED7AAAA5AABB1);
  EXPECT_EQ(state.font_data(), roboto_ab_.str());
  EXPECT_TRUE(state.has_codepoint_remapping());
  EXPECT_EQ(state.codepoint_remapping().fingerprint(), 0xBFA518E3A093ACEF);

  hb_set_unique_ptr set_abcd = make_hb_set_from_ranges(1, 0x61, 0x64);
  EXPECT_EQ(client_with_mapping_.Extend(*set_abcd, &state), StatusCode::kOk);

  EXPECT_EQ(state.font_id(), "Roboto-Regular.ttf");
  EXPECT_EQ(state.original_font_fingerprint(), 0xA55ED7AAAA5AABB1);
  EXPECT_EQ(state.font_data(), roboto_abcd_.str());
  EXPECT_TRUE(state.has_codepoint_remapping());
  EXPECT_EQ(state.codepoint_remapping().fingerprint(), 0xBFA518E3A093ACEF);
}

}  // namespace patch_subset
