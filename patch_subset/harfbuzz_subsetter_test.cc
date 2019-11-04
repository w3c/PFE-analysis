#include "patch_subset/harfbuzz_subsetter.h"

#include <memory>

#include "gtest/gtest.h"
#include "hb.h"
#include "patch_subset/file_font_provider.h"
#include "patch_subset/hb_set_unique_ptr.h"

namespace patch_subset {

class HarfbuzzSubsetterTest : public ::testing::Test {
 protected:
  HarfbuzzSubsetterTest()
      : font_provider_(new FileFontProvider("patch_subset/testdata/")),
        subsetter_(std::make_unique<HarfbuzzSubsetter>()) {}

  std::unique_ptr<FontProvider> font_provider_;
  std::unique_ptr<Subsetter> subsetter_;
};

TEST_F(HarfbuzzSubsetterTest, Subset) {
  FontData font_data;
  EXPECT_EQ(font_provider_->GetFont("Roboto-Regular.ttf", &font_data),
            StatusCode::kOk);

  hb_set_unique_ptr codepoints = make_hb_set_from_ranges(1, 0x61, 0x64);

  FontData subset_data;
  EXPECT_EQ(subsetter_->Subset(font_data, *codepoints, &subset_data),
            StatusCode::kOk);

  hb_blob_t* subset_blob =
      hb_blob_create(subset_data.data(), subset_data.size(),
                     HB_MEMORY_MODE_READONLY, nullptr, nullptr);
  hb_face_t* subset_face = hb_face_create(subset_blob, 0);
  hb_blob_destroy(subset_blob);

  hb_set_unique_ptr subset_codepoints = make_hb_set();
  hb_face_collect_unicodes(subset_face, subset_codepoints.get());
  hb_face_destroy(subset_face);

  EXPECT_TRUE(hb_set_is_equal(codepoints.get(), subset_codepoints.get()));
}

TEST_F(HarfbuzzSubsetterTest, SubsetEmpty) {
  FontData font_data;
  EXPECT_EQ(font_provider_->GetFont("Roboto-Regular.ttf", &font_data),
            StatusCode::kOk);

  hb_set_unique_ptr codepoints = make_hb_set(0);

  FontData subset_data;
  EXPECT_EQ(subsetter_->Subset(font_data, *codepoints, &subset_data),
            StatusCode::kOk);

  hb_blob_t* subset_blob =
      hb_blob_create(subset_data.data(), subset_data.size(),
                     HB_MEMORY_MODE_READONLY, nullptr, nullptr);
  EXPECT_EQ(hb_blob_get_length(subset_blob), 0);
  hb_blob_destroy(subset_blob);
}

}  // namespace patch_subset
