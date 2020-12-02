#include <emscripten/bind.h>
#include <emscripten/val.h>
#include <stdio.h>

#include <string>

#include "patch_subset/patch_subset.pb.h"

using namespace emscripten;

class State {
 public:
  State() : state() {}

  void init_from(std::string buffer) { state.ParseFromString(buffer); }

  val font_data() {
    return val(typed_memory_view(state.font_data().length(),
                                 state.font_data().data()));
  }

 private:
  patch_subset::ClientState state;
};

EMSCRIPTEN_BINDINGS(patch_subset) {
  class_<State>("State").constructor().function("font_data", &State::font_data);
}
