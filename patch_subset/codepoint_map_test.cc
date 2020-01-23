#include "patch_subset/codepoint_map.h"

#include "common/status.h"
#include "gtest/gtest.h"
#include "patch_subset/hb_set_unique_ptr.h"

namespace patch_subset {

class CodepointMapTest : public ::testing::Test {
 protected:
  CodepointMapTest() {
    // Map
    // 7 -> 0
    // 3 -> 1
    // 4 -> 2
    codepoint_map_.SetMapping({7, 3, 4});
  }

  CodepointMap codepoint_map_;
};

TEST_F(CodepointMapTest, EncodeEmpty) {
  hb_set_unique_ptr codepoints = make_hb_set();
  EXPECT_EQ(StatusCode::kOk, codepoint_map_.Encode(codepoints.get()));
  EXPECT_TRUE(hb_set_is_empty(codepoints.get()));
}

TEST_F(CodepointMapTest, Encode) {
  hb_set_unique_ptr codepoints = make_hb_set(2, 4, 7);
  EXPECT_EQ(StatusCode::kOk, codepoint_map_.Encode(codepoints.get()));

  hb_set_unique_ptr expected = make_hb_set(2, 0, 2);
  EXPECT_TRUE(hb_set_is_equal(codepoints.get(), expected.get()));
}

TEST_F(CodepointMapTest, EncodeMissing) {
  hb_set_unique_ptr codepoints = make_hb_set(3, 2, 4, 7);
  EXPECT_EQ(StatusCode::kInvalidArgument,
            codepoint_map_.Encode(codepoints.get()));
}

TEST_F(CodepointMapTest, Decode) {
  hb_set_unique_ptr codepoints = make_hb_set();
  EXPECT_EQ(StatusCode::kOk, codepoint_map_.Decode(codepoints.get()));
  EXPECT_TRUE(hb_set_is_empty(codepoints.get()));
}

TEST_F(CodepointMapTest, DecodeEmpty) {
  hb_set_unique_ptr codepoints = make_hb_set(2, 0, 2);
  EXPECT_EQ(StatusCode::kOk, codepoint_map_.Decode(codepoints.get()));

  hb_set_unique_ptr expected = make_hb_set(2, 4, 7);
  EXPECT_TRUE(hb_set_is_equal(codepoints.get(), expected.get()));
}

TEST_F(CodepointMapTest, DecodeMissing) {
  hb_set_unique_ptr codepoints = make_hb_set(3, 0, 2, 3);
  EXPECT_EQ(StatusCode::kInvalidArgument,
            codepoint_map_.Decode(codepoints.get()));
}

}  // namespace patch_subset
