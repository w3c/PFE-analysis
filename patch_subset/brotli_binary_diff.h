#ifndef PATCH_SUBSET_BROTLI_BINARY_DIFF_H_
#define PATCH_SUBSET_BROTLI_BINARY_DIFF_H_

#include "common/status.h"
#include "patch_subset/binary_diff.h"
#include "patch_subset/font_data.h"

namespace patch_subset {

// Computes a binary diff using brotli compression
// with a shared dictionary.
class BrotliBinaryDiff : public BinaryDiff {
 public:
  StatusCode Diff(const FontData& font_base, const FontData& font_derived,
                  FontData* patch /* OUT */) const override;
};

}  // namespace patch_subset

#endif  // PATCH_SUBSET_BROTLI_BINARY_DIFF_H_
