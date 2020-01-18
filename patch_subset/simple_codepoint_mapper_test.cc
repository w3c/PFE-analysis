#include "patch_subset/simple_codepoint_mapper.h"

#include "gtest/gtest.h"
#include "patch_subset/hb_set_unique_ptr.h"

namespace patch_subset {

class SimpleCodepointMapperTest : public ::testing::Test {
 protected:
  SimpleCodepointMapperTest() {}

  SimpleCodepointMapper codepoint_mapper_;
};

TEST_F(SimpleCodepointMapperTest, MapCodepoints) {
  hb_set_unique_ptr codepoints = make_hb_set(4, 1, 7, 8, 11);

  std::vector<hb_codepoint_t> mapping;
  codepoint_mapper_.ComputeMapping(*codepoints, &mapping);

  std::vector<hb_codepoint_t> expected = {1, 7, 8, 11};
  EXPECT_EQ(mapping, expected);
}

}  // namespace patch_subset
