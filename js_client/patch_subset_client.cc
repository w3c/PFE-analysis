#include <emscripten/bind.h>
#include <emscripten/val.h>
#include <stdio.h>

#include <string>
#include <vector>

#include "hb.h"
#include "js_client/remote_patch_subset_server.h"
#include "patch_subset/patch_subset.pb.h"
#include "patch_subset/patch_subset_client.h"
#include "patch_subset/brotli_binary_patch.h"
#include "patch_subset/farm_hasher.h"
#include "patch_subset/null_request_logger.h"

using namespace emscripten;

class State {
 public:
  State() :
      _state(),
      _server("https://fonts.gstatic.com/experimental/patch_subset/"),
      _logger(),
      _client(&_server,
              &_logger,
              std::unique_ptr<patch_subset::BinaryPatch>(new patch_subset::BrotliBinaryPatch()),
              std::unique_ptr<patch_subset::Hasher>(new patch_subset::FarmHasher()))

  {}

  void init_from(std::string buffer) { _state.ParseFromString(buffer); }

  val font_data() {
    return val(typed_memory_view(_state.font_data().length(),
                                 _state.font_data().data()));
  }

  bool extend(val codepoints_js) {
    std::vector<int> codepoints = convertJSArrayToNumberVector<int>(codepoints_js);
    hb_set_t* codepoints_set = hb_set_create();
    for (int cp : codepoints) {
      hb_set_add(codepoints_set, cp);
    }

    patch_subset::StatusCode code = _client.Extend(*codepoints_set, &_state);
    hb_set_destroy(codepoints_set);

    return code == patch_subset::StatusCode::kOk;
  }

 private:
  patch_subset::ClientState _state;
  patch_subset::RemotePatchSubsetServer _server;
  patch_subset::NullRequestLogger _logger;
  patch_subset::PatchSubsetClient _client;
};

EMSCRIPTEN_BINDINGS(patch_subset) {
  class_<State>("State")
          .constructor()
          .function("font_data", &State::font_data)
          .function("extend", &State::extend);
}
