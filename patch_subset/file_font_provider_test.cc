#include "patch_subset/file_font_provider.h"

#include <string>

#include "gtest/gtest.h"
#include "patch_subset/font_provider.h"

namespace patch_subset {

class FileFontProviderTest : public ::testing::Test {
 protected:
  FileFontProviderTest()
      : font_provider_(new FileFontProvider("patch_subset/testdata/")) {}

  ~FileFontProviderTest() override {}

  std::unique_ptr<FileFontProvider> font_provider_;
};

TEST_F(FileFontProviderTest, LoadFont) {
  FontData font_data;
  EXPECT_EQ(font_provider_.get()->GetFont("font.txt", &font_data),
            StatusCode::kOk);

  std::string data(font_data.data(), font_data.size());
  EXPECT_EQ(data, "a font\n");
}

TEST_F(FileFontProviderTest, FontNotFound) {
  FontData font_data;
  EXPECT_EQ(font_provider_.get()->GetFont("nothere.txt", &font_data),
            StatusCode::kNotFound);
}

}  // namespace patch_subset
