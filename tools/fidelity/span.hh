// SPDX-License-Identifier: Apache-2.0
#pragma once
#include "trace.hh"
namespace blended_fidelity {
template<class A,class B> void span_values_equal(const A &a,const B &b) {
  if constexpr(std::is_pointer_v<A> && std::is_pointer_v<B>) {
    const bool passed=bool(::testing::internal::EqHelper::Compare("a","b",a,b));
    const void *aa=static_cast<const void*>(a),*bb=static_cast<const void*>(b);
    const void *origin=aa?aa:bb;
    record("EQ",passed,nullptr,nullptr,PointerAlias{aa,origin},PointerAlias{bb,origin});
    // Same pinned nonfatal GoogleTest equality, not text-value equality.
    EXPECT_PRED_FORMAT2(::testing::internal::EqHelper::Compare,a,b);
  } else {
    ::blended_fidelity::eq(a,b);
  }
}
}
#undef EXPECT_EQ
#define EXPECT_EQ(a,b) ::blended_fidelity::span_values_equal((a),(b))
