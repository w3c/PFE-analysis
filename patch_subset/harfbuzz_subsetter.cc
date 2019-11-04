#include "patch_subset/harfbuzz_subsetter.h"

#include "common/logging.h"
#include "common/status.h"
#include "hb-subset.h"
#include "patch_subset/font_data.h"

namespace patch_subset {

StatusCode HarfbuzzSubsetter::Subset(const FontData& font,
                                     const hb_set_t& codepoints,
                                     FontData* subset /* OUT */) const {
  if (!hb_set_get_population(&codepoints)) {
    subset->reset();
    return StatusCode::kOk;
  }

  hb_blob_t* blob = font.reference_blob();
  hb_face_t* face = hb_face_create(blob, 0);
  hb_blob_destroy(blob);

  hb_subset_input_t* input = hb_subset_input_create_or_fail();
  hb_set_t* input_codepoints = hb_subset_input_unicode_set(input);
  hb_set_union(input_codepoints, &codepoints);

  // For subsetting we want to retain glyph ids, this helps reduce
  // patch size by keeping the ids consistent between patches.
  hb_subset_input_set_retain_gids(input, true);
  // hb-subset by default drops layout tables, keep them.
  hb_set_del(hb_subset_input_drop_tables_set(input),
             HB_TAG('G', 'S', 'U', 'B'));
  hb_set_del(hb_subset_input_drop_tables_set(input),
             HB_TAG('G', 'P', 'O', 'S'));
  hb_set_del(hb_subset_input_drop_tables_set(input),
             HB_TAG('G', 'D', 'E', 'F'));

  hb_face_t* subset_face = hb_subset(face, input);
  hb_subset_input_destroy(input);
  hb_face_destroy(face);

  bool result = (subset_face != hb_face_get_empty());
  if (!result) {
    hb_face_destroy(subset_face);
    LOG(WARNING) << "Internal subsetting failure.";
    return StatusCode::kInternal;
  }

  hb_blob_t* subset_blob = hb_face_reference_blob(subset_face);
  hb_face_destroy(subset_face);

  subset->set(subset_blob);

  hb_blob_destroy(subset_blob);

  return StatusCode::kOk;
}

}  // namespace patch_subset
