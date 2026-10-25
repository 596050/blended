// SPDX-License-Identifier: Apache-2.0
#pragma once
#include "trace.hh"
namespace blended_fidelity {
template<class A,class B> void generic_span_equal(const A &a,const B &b){
 if constexpr(std::is_pointer_v<A> && std::is_pointer_v<B>){
  const bool passed=bool(::testing::internal::EqHelper::Compare("a","b",a,b));
  // All pointer pairs in this original fixture address one backing array.
  // Preserve relative offsets, not pointed-to values or a Boolean-only stand-in.
  record("EQ",passed,nullptr,nullptr,reinterpret_cast<const char*>(a),reinterpret_cast<const char*>(b));
  EXPECT_PRED_FORMAT2(::testing::internal::EqHelper::Compare,a,b);
 }else{::blended_fidelity::eq(a,b);}
}
}
#undef EXPECT_EQ
#define EXPECT_EQ(a,b) ::blended_fidelity::generic_span_equal((a),(b))
