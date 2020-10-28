#include "patch_subset/woff2_glyf_transformer.h"

#include "common/status.h"
#include "font.h"
#include "gtest/gtest.h"
#include "patch_subset/file_font_provider.h"
#include "patch_subset/font_provider.h"

namespace patch_subset {

static const uint32_t kGlyfTableTag = 0x676c7966;
static const uint32_t kLocaTableTag = 0x6c6f6361;

class Woff2GlyfTransformerTest : public ::testing::Test {
 protected:
  Woff2GlyfTransformerTest()
      : font_provider_(new FileFontProvider("patch_subset/testdata/")) {}

  ~Woff2GlyfTransformerTest() override {}

  void SetUp() override {
    ASSERT_EQ(font_provider_->GetFont("Roboto-Regular.Awesome.ttf", &a_font_),
              StatusCode::kOk);
    ASSERT_GT(a_font_.size(), 0);
  }

  std::unique_ptr<FontProvider> font_provider_;
  Woff2GlyfTransformer transformer_;
  FontData a_font_;
};

TEST_F(Woff2GlyfTransformerTest, TransformModifiesGlyf) {
  ::woff2::Font orig_font;
  ASSERT_TRUE(woff2::ReadFont(reinterpret_cast<const uint8_t*>(a_font_.data()),
                              a_font_.size(), &orig_font));

  ASSERT_EQ(transformer_.Encode(&a_font_), StatusCode::kOk);

  ::woff2::Font transformed_font;
  ASSERT_TRUE(woff2::ReadFont(reinterpret_cast<const uint8_t*>(a_font_.data()),
                              a_font_.size(), &transformed_font));

  // Some basic sanity checks on the transformation:
  EXPECT_EQ(orig_font.tables.size(), transformed_font.tables.size());
  EXPECT_TRUE(orig_font.FindTable(kGlyfTableTag));
  EXPECT_TRUE(orig_font.FindTable(kLocaTableTag));
  EXPECT_TRUE(transformed_font.FindTable(kGlyfTableTag));
  EXPECT_TRUE(transformed_font.FindTable(kLocaTableTag));

  EXPECT_GT(orig_font.FindTable(kLocaTableTag)->length, 0);
  EXPECT_EQ(transformed_font.FindTable(kLocaTableTag)->length, 0);

  EXPECT_GT(orig_font.FindTable(kGlyfTableTag)->length, 0);
  EXPECT_GT(transformed_font.FindTable(kGlyfTableTag)->length, 0);
  EXPECT_NE(orig_font.FindTable(kGlyfTableTag)->length,
            transformed_font.FindTable(kGlyfTableTag)->length);
}

TEST_F(Woff2GlyfTransformerTest, TransformEmptyFont) {
  FontData empty_font;
  ASSERT_EQ(transformer_.Encode(&empty_font), StatusCode::kOk);
  EXPECT_EQ(empty_font.size(), 0);
}

}  // namespace patch_subset
