#include "gtest/gtest.h"
#include "patch_subset/brotli_binary_diff.h"
#include "patch_subset/brotli_binary_patch.h"
#include "patch_subset/compressed_set.h"
#include "patch_subset/farm_hasher.h"
#include "patch_subset/file_font_provider.h"
#include "patch_subset/harfbuzz_subsetter.h"
#include "patch_subset/hb_set_unique_ptr.h"
#include "patch_subset/null_request_logger.h"
#include "patch_subset/patch_subset.pb.h"
#include "patch_subset/patch_subset_client.h"
#include "patch_subset/patch_subset_server_impl.h"

using ::absl::string_view;

namespace patch_subset {

class PatchSubsetClientServerIntegrationTest : public ::testing::Test {
 protected:
  PatchSubsetClientServerIntegrationTest()
      : font_provider_(new FileFontProvider("patch_subset/testdata/")),
        binary_diff_(new BrotliBinaryDiff()),
        binary_patch_(new BrotliBinaryPatch()),
        server_(std::unique_ptr<FontProvider>(font_provider_),
                std::unique_ptr<Subsetter>(new HarfbuzzSubsetter()),
                std::unique_ptr<BinaryDiff>(binary_diff_),
                std::unique_ptr<Hasher>(new FarmHasher())),
        client_(&server_, &request_logger_,
                std::unique_ptr<BinaryPatch>(binary_patch_),
                std::unique_ptr<Hasher>(new FarmHasher())) {
    font_provider_->GetFont("Roboto-Regular.abcd.ttf", &roboto_abcd_);
    font_provider_->GetFont("Roboto-Regular.ab.ttf", &roboto_ab_);
  }

  FontProvider* font_provider_;
  BinaryDiff* binary_diff_;
  BinaryPatch* binary_patch_;
  NullRequestLogger request_logger_;
  PatchSubsetServerImpl server_;
  PatchSubsetClient client_;

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
}

}  // namespace patch_subset
