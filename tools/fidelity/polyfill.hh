// SPDX-License-Identifier: Apache-2.0
// Include-only polygon instrumentation; original test bodies are unchanged.
#pragma once
#include "trace.hh"
namespace blended_fidelity {
template<class A,class B> void ne(const A &a,const B &b) {
  record("NE",a!=b,nullptr,nullptr,a,b);
  EXPECT_NE(a,b);
}
}
#undef EXPECT_NE
#define EXPECT_NE(a,b) ::blended_fidelity::ne((a),(b))
