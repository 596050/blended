#include "BLI_span.hh"
#include <type_traits>
using namespace blender;
static_assert(std::is_convertible_v<MutableSpan<int*>,MutableSpan<const int*>>);
void instantiate(MutableSpan<int*> input){MutableSpan<const int*> output=input;(void)output;}
