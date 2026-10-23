// SPDX-License-Identifier: Apache-2.0
// Diagnostic overlay: original test bodies are unchanged. Evaluate arguments once,
// record values, then invoke Blender's pinned GoogleTest assertion machinery.
#pragma once
#include "testing/testing.h"
#include "BLI_bounds.hh"
#include "BLI_index_range.hh"
#include "BLI_math_vector_types.hh"
#include "BLI_bit_ref.hh"
#include "BLI_span.hh"
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <optional>
#include <sstream>
#include <type_traits>
namespace blended_fidelity {
template<class T> struct Encoder {
 static void write(std::ostream &out, const T &v) {
  if constexpr (std::is_same_v<T,bool>) {out << "\"b:" << (v ? '1':'0') << "\"";}
  else if constexpr (std::is_integral_v<T>) {
   out << "\"i:";
   if constexpr(std::is_signed_v<T>) out << static_cast<long long>(v);
   else out << static_cast<unsigned long long>(v);
   out << "\"";
  } else if constexpr(std::is_floating_point_v<T>) {
   const double d=static_cast<double>(v); unsigned long long bits; static_assert(sizeof(bits)==sizeof(d));
   std::memcpy(&bits,&d,sizeof(d));
   std::ostringstream hex;hex << std::hex << std::setw(16) << std::setfill('0') << bits;
   out << "\"f:" << hex.str() << "\"";
  } else {static_assert(std::is_arithmetic_v<T>, "Unreviewed trace value type");}
 }
};
template<class T> void value(std::ostream &out,const T &v) {Encoder<T>::write(out,v);}
template<class T,int N> struct Encoder<blender::VecBase<T,N>> {
 static void write(std::ostream &out,const blender::VecBase<T,N> &v) {out << '[';for(int i=0;i<N;i++){if(i)out<<',';value(out,v[i]);}out<<']';}
};
template<class T> struct Encoder<blender::Bounds<T>> {
 static void write(std::ostream &out,const blender::Bounds<T> &v) {out<<"{\"min\":";value(out,v.min);out<<",\"max\":";value(out,v.max);out<<'}';}
};
template<class T> struct Encoder<std::optional<T>> {
 static void write(std::ostream &out,const std::optional<T> &v) {if(v)value(out,*v);else out<<"\"none\"";}
};
template<> struct Encoder<std::nullopt_t> {static void write(std::ostream &out,std::nullopt_t){out<<"\"none\"";}};
template<> struct Encoder<blender::IndexRange> {
 static void write(std::ostream &out,const blender::IndexRange &v) {
  // Upstream equality ignores the start of an empty range. Preserve that contract.
  out<<"{\"start\":";value(out,v.is_empty()?int64_t(0):v.start());out<<",\"size\":";value(out,v.size());out<<'}';
 }
};
// Address values are compared as word offsets within this pointer-only test.
inline void pointer_value(std::ostream &out,const uint64_t *v) {
 static const ::testing::TestInfo *last=nullptr;static std::uintptr_t base=0;
 const auto *test=::testing::UnitTest::GetInstance()->current_test_info();
 const auto address=reinterpret_cast<std::uintptr_t>(v);
 if(last!=test){last=test;base=address;}
 const auto difference=static_cast<int64_t>(address)-static_cast<int64_t>(base);
 if(difference%int64_t(sizeof(uint64_t)))std::abort();
 out<<"\"p64:"<<difference/int64_t(sizeof(uint64_t))<<"\"";
}
template<> struct Encoder<uint64_t*> {static void write(std::ostream &out,uint64_t *v){pointer_value(out,v);}};
template<> struct Encoder<const uint64_t*> {static void write(std::ostream &out,const uint64_t *v){pointer_value(out,v);}};
template<> struct Encoder<blender::bits::BitRef> {
 static void write(std::ostream &out,const blender::bits::BitRef &v){value(out,bool(v));}
};
template<class T> struct Encoder<blender::Span<T>> {
 static void write(std::ostream &out,const blender::Span<T> &v){out<<'[';for(int64_t i=0;i<v.size();++i){if(i)out<<',';value(out,v[i]);}out<<']';}
};
inline std::ofstream &stream() {
 static std::ofstream out([](){const char *p=std::getenv("BLENDED_ASSERTION_TRACE");if(!p)std::abort();return p;}());
 if(!out)std::abort();return out;
}
inline bool literal(const char *s) {
 bool digit=false;for(;*s;++s){if(*s>='0'&&*s<='9')digit=true;else if(!std::strchr(" +-eEfF.\t\n",*s))return false;}return digit;
}
template<class... T> void record(const char *kind,bool passed,const char *ea,const char *eb,const T &...args) {
 auto *test=::testing::UnitTest::GetInstance()->current_test_info();if(!test)std::abort();
 auto &out=stream();out<<"{\"case\":\""<<test->test_suite_name()<<'.'<<test->name()<<"\",\"kind\":\""<<kind<<"\",\"passed\":"<<(passed?"true":"false")<<",\"values\":[";
 int i=0;((out<<(i++?",":""),value(out,args)),...);out<<']';
 if(ea){out<<",\"fixed\":["<<(literal(ea)?"true":"false")<<','<<(literal(eb)?"true":"false");if constexpr(sizeof...(args)==3)out<<",true";out<<']';}
 out<<"}\n";out.flush();
}
template<class A,class B> void eq(const A &a,const B &b) {record("EQ",bool(::testing::internal::EqHelper::Compare("a","b",a,b)),nullptr,nullptr,a,b);EXPECT_EQ(a,b);}
template<class A,class B> void gt(const A &a,const B &b) {record("GT",a>b,nullptr,nullptr,a,b);EXPECT_GT(a,b);}
inline void feq(float a,float b,const char *ea,const char *eb) {record("FLOAT_EQ",bool(::testing::internal::CmpHelperFloatingPointEQ<float>("a","b",a,b)),ea,eb,a,b);EXPECT_FLOAT_EQ(a,b);}
inline void near(double a,double b,double e,const char *ea,const char *eb) {record("NEAR",bool(::testing::internal::DoubleNearPredFormat("a","b","e",a,b,e)),ea,eb,a,b,e);EXPECT_NEAR(a,b,e);}
inline void yes(bool v){record("TRUE",v,nullptr,nullptr,v);EXPECT_TRUE(v);}
inline void no(bool v){record("FALSE",!v,nullptr,nullptr,v);EXPECT_FALSE(v);}
}
#undef EXPECT_EQ
#undef EXPECT_GT
#undef EXPECT_FLOAT_EQ
#undef EXPECT_NEAR
#undef EXPECT_TRUE
#undef EXPECT_FALSE
#define EXPECT_EQ(a,b) ::blended_fidelity::eq((a),(b))
#define EXPECT_GT(a,b) ::blended_fidelity::gt((a),(b))
#define EXPECT_FLOAT_EQ(a,b) ::blended_fidelity::feq((a),(b),#a,#b)
#define EXPECT_NEAR(a,b,e) ::blended_fidelity::near((a),(b),(e),#a,#b)
#define EXPECT_TRUE(v) ::blended_fidelity::yes(bool(v))
#define EXPECT_FALSE(v) ::blended_fidelity::no(bool(v))
