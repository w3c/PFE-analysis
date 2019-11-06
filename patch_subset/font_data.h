#ifndef PATCH_SUBSET_FONT_DATA_H_
#define PATCH_SUBSET_FONT_DATA_H_

#include <cstring>
#include <memory>

#include "absl/strings/string_view.h"
#include "hb.h"

namespace patch_subset {

// Holds the binary data for a font.
class FontData {
 public:
  FontData() : buffer_(hb_blob_get_empty()) {}

  explicit FontData(::absl::string_view data) : buffer_(hb_blob_get_empty()) {
    copy(data);
  }

  FontData(const FontData&) = delete;

  FontData(FontData&& other) : buffer_(nullptr) {
    buffer_ = other.buffer_;
    other.buffer_ = hb_blob_get_empty();
  }

  FontData& operator=(const FontData&) = delete;

  FontData& operator=(FontData&& other) {
    if (this == &other) {
      return *this;
    }
    reset();
    buffer_ = other.buffer_;
    other.buffer_ = hb_blob_get_empty();
    return *this;
  }

  ~FontData() { reset(); }

  bool operator==(const FontData& other) const { return str() == other.str(); }

  bool empty() const { return size() == 0; }

  ::absl::string_view str() const {
    return ::absl::string_view(data(), size());
  }

  ::absl::string_view str(unsigned int start) const {
    if (start >= size()) {
      return ::absl::string_view();
    }
    return ::absl::string_view(data() + start, size() - start);
  }

  void set(hb_blob_t* blob) {
    reset();
    buffer_ = hb_blob_reference(blob);
  }

  void copy(const char* data, unsigned int length) {
    reset();
    char* buffer = reinterpret_cast<char*>(malloc(length));
    memcpy(buffer, data, length);
    buffer_ =
        hb_blob_create(buffer, length, HB_MEMORY_MODE_READONLY, buffer, &free);
  }

  void copy(::absl::string_view data) { copy(data.data(), data.size()); }

  void reset() {
    if (buffer_ != hb_blob_get_empty()) {
      hb_blob_destroy(buffer_);
      buffer_ = hb_blob_get_empty();
    }
  }

  hb_blob_t* reference_blob() const { return hb_blob_reference(buffer_); }

  const char* data() const {
    unsigned int size;
    return hb_blob_get_data(buffer_, &size);
  }

  unsigned int size() const { return hb_blob_get_length(buffer_); }

 private:
  hb_blob_t* buffer_;
};

}  // namespace patch_subset

#endif  // PATCH_SUBSET_FONT_DATA_H_
