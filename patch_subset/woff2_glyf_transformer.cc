#include "patch_subset/woff2_glyf_transformer.h"

#include "common/logging.h"
#include "common/status.h"
#include "font.h"
#include "hb.h"
#include "transform.h"

using ::woff2::Font;

namespace patch_subset {

static const uint32_t kGlyfTableTag = 0x676c7966;
static const uint32_t kLocaTableTag = 0x6c6f6361;
static const uint32_t kTransformed = 0x80808080;

void SerializeFont(const Font& font, FontData* font_data /* OUT */) {
  hb_face_t* out = hb_face_builder_create();

  for (const auto tag : font.OutputOrderedTags()) {
    if (tag & kTransformed) {
      continue;
    }
    const Font::Table* original = font.FindTable(tag);
    const Font::Table* table_to_store = font.FindTable(tag ^ kTransformed);
    if (table_to_store == nullptr) {
      table_to_store = original;
    }

    hb_blob_t* table_blob = hb_blob_create(
        reinterpret_cast<const char*>(table_to_store->data),
        table_to_store->length, HB_MEMORY_MODE_READONLY, nullptr, nullptr);
    hb_face_builder_add_table(out, tag, table_blob);
    hb_blob_destroy(table_blob);
  }

  hb_blob_t* result = hb_face_reference_blob(out);
  hb_face_destroy(out);

  font_data->set(result);
  hb_blob_destroy(result);
}

StatusCode Woff2GlyfTransformer::Encode(
    FontData* font_data /* IN/OUT */) const {
  Font font;
  if (!woff2::ReadFont(reinterpret_cast<const uint8_t*>(font_data->data()),
                       font_data->size(), &font)) {
    LOG(WARNING) << "Failed to parse font for glyf and loca transform.";
    return StatusCode::kInternal;
  }

  if (!woff2::TransformGlyfAndLocaTables(&font)) {
    LOG(WARNING) << "Glyf and loca transformation failed.";
    return StatusCode::kInternal;
  }

  if (!font.FindTable(kGlyfTableTag ^ kTransformed) ||
      !font.FindTable(kLocaTableTag ^ kTransformed)) {
    // No transformation was created (typically that means this is
    // a CFF font). So no further work to do.
    return StatusCode::kOk;
  }

  SerializeFont(font, font_data);
  return StatusCode::kOk;
}

}  // namespace patch_subset
