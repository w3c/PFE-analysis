/*
 * Implements a C API interface into a patch subset client.
 * Needed in order to have python create and interact with
 * patch subset clients.
 */
#include <string>

#include "hb.h"
#include "patch_subset/brotli_binary_diff.h"
#include "patch_subset/brotli_binary_patch.h"
#include "patch_subset/farm_hasher.h"
#include "patch_subset/file_font_provider.h"
#include "patch_subset/font_provider.h"
#include "patch_subset/harfbuzz_subsetter.h"
#include "patch_subset/null_request_logger.h"
#include "patch_subset/patch_subset.pb.h"
#include "patch_subset/patch_subset_client.h"
#include "patch_subset/patch_subset_server_impl.h"
#include "common/status.h"

using ::patch_subset::BinaryDiff;
using ::patch_subset::BinaryPatch;
using ::patch_subset::BrotliBinaryDiff;
using ::patch_subset::BrotliBinaryPatch;
using ::patch_subset::ClientState;
using ::patch_subset::FarmHasher;
using ::patch_subset::FileFontProvider;
using ::patch_subset::FontProvider;
using ::patch_subset::HarfbuzzSubsetter;
using ::patch_subset::Hasher;
using ::patch_subset::NullRequestLogger;
using ::patch_subset::PatchSubsetClient;
using ::patch_subset::PatchSubsetServerImpl;
using ::patch_subset::StatusCode;
using ::patch_subset::Subsetter;

class PatchSubsetSession {
 public:
  PatchSubsetSession(const std::string& font_directory,
                     const std::string& font_id)
      : font_provider_(new FileFontProvider(font_directory)),
        binary_diff_(new BrotliBinaryDiff()),
        binary_patch_(new BrotliBinaryPatch()),
        server_(std::unique_ptr<FontProvider>(font_provider_),
                std::unique_ptr<Subsetter>(new HarfbuzzSubsetter()),
                std::unique_ptr<BinaryDiff>(binary_diff_),
                std::unique_ptr<Hasher>(new FarmHasher())),
        client_(&server_, &request_logger_,
                std::unique_ptr<BinaryPatch>(binary_patch_),
                std::unique_ptr<Hasher>(new FarmHasher())) {
    client_state_.set_font_id(font_id);
  }

  StatusCode Extend(const hb_set_t& codepoints) {
    return client_.Extend(codepoints, &client_state_);
  }

  const std::string& client_font_data() {
    return client_state_.font_data();
  }

  FontProvider* font_provider_;
  BinaryDiff* binary_diff_;
  BinaryPatch* binary_patch_;
  NullRequestLogger request_logger_;
  PatchSubsetServerImpl server_;
  PatchSubsetClient client_;
  ClientState client_state_;
};

extern "C" {

PatchSubsetSession* PatchSubsetSession_new(const char* font_directory,
                                           const char* font_id) {
  std::string font_directory_string(font_directory);
  std::string font_id_string(font_id);
  return new PatchSubsetSession(font_directory_string, font_id);
}

bool PatchSubsetSession_extend(PatchSubsetSession* session,
                               int* codepoints,
                               int codepoints_count) {
  hb_set_t* codepoints_set = hb_set_create();
  for (int i = 0; i < codepoints_count; i++) {
    hb_set_add(codepoints_set, codepoints[i]);
  }
  StatusCode result = session->Extend(*codepoints_set);
  hb_set_destroy(codepoints_set);
  return result == StatusCode::kOk;
}

const char* PatchSubsetSession_get_font(PatchSubsetSession* session,
                                        int* size) {
  *size = session->client_font_data().size();
  return session->client_font_data().c_str();
}

}
