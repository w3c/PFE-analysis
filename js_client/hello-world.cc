#include <stdio.h>
#include <emscripten/bind.h>

using namespace emscripten;

float add(float a, float b) {
  printf("adding %f and %f\n", a, b);
  return a + b;
}

EMSCRIPTEN_BINDINGS(my_module) {
    function("add", &add);
}
