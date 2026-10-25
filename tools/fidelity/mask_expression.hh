// SPDX-License-Identifier: Apache-2.0
// Include-only diagnostic overlay. Original test and helper bodies are unchanged.
#pragma once
#include "trace.hh"
#include "BLI_index_mask.hh"
#include "BLI_index_mask_expression.hh"
#include "BLI_array.hh"
#include "BLI_rand.hh"
#include <vector>
namespace blended_fidelity {
// Canonical maximal runs, then unsigned LEB128(gap,length), as exact hex bytes.
// This is a reversible value encoding, not a hash, sample or cardinality check.
inline void mask_varint(std::vector<uint8_t>&out,uint64_t v){do{uint8_t b=v&127;v>>=7;out.push_back(b|(v?128:0));}while(v);}
template<> struct Encoder<blender::IndexMask>{
 static void write(std::ostream&out,const blender::IndexMask&mask){
  std::vector<uint8_t> bytes;int64_t previous_end=0,start=-1,end=-1;
  auto emit=[&](){if(start>=0){mask_varint(bytes,uint64_t(start-previous_end));mask_varint(bytes,uint64_t(end-start));previous_end=end;}};
  mask.foreach_range([&](blender::IndexRange run){
   if(start>=0 && run.start()==end){end=run.one_after_last();return;}
   emit();start=run.start();end=run.one_after_last();
  });emit();
  out<<"{\"mask_runs\":\"s:";constexpr char hex[]="0123456789abcdef";for(uint8_t b:bytes){out<<hex[b>>4]<<hex[b&15];}out<<"\"}";
 }
};
}
// Forward declaration of the unedited original helper defined after this include.
namespace blender::index_mask::tests {static Array<bool> random_bools(RandomNumberGenerator&,int64_t);}
namespace blended_fidelity {
class MaskOracleListener final:public ::testing::EmptyTestEventListener {
 public:
 void OnTestProgramEnd(const ::testing::UnitTest&)override{
  const char*path=std::getenv("BLENDED_MASK_ORACLE");if(!path)return;
  std::ofstream out(path,std::ios::binary);if(!out)std::abort();out.write("MASKORC1",8);
  auto u64=[&](uint64_t v){for(int j=0;j<8;j++)out.put(char(v>>(8*j)));};
  blender::RandomNumberGenerator rng(0);
  // Exact original helper and all 50 iterations; raw booleans, not trace codec.
  u64(50);
  for(int iteration=0;iteration<50;iteration++){
   const int64_t size=rng.get_int32(200000)+1;u64(size);
   for(int term=0;term<3;term++){
    auto values=blender::index_mask::tests::random_bools(rng,size);
    for(bool v:values)out.put(v?1:0);
   }
  }
  using namespace blender;using namespace blender::index_mask;
  u64(3*2*64*64);
  for(int64_t origin:{int64_t(0),int64_t(16380),(int64_t(1)<<31)-128}){
   for(int64_t stride:{int64_t(1),int64_t(17)}){
    for(int abits=0;abits<64;abits++)for(int bbits=0;bbits<64;bbits++){
     const int cbits=((abits*17)^(bbits*31))&63;IndexMaskMemory memory;
     auto build=[&](int bits){Vector<int64_t>indices;for(int i=0;i<6;i++)if(bits&(1<<i))indices.append(origin+i*stride);return IndexMask::from_indices<int64_t>(indices,memory);};
     const IndexMask a=build(abits),b=build(bbits),c=build(cbits),universe=build(63);ExprBuilder builder;
     auto emit=[&](const IndexMask&m){uint64_t bits=0;for(int i=0;i<6;i++)if(m.contains(origin+i*stride))bits|=uint64_t(1)<<i;u64(m.size());u64(bits);};
     emit(evaluate_expression(builder.merge({&a,&b,&c}),memory));
     emit(evaluate_expression(builder.intersect({&a,&b}),memory));
     emit(evaluate_expression(builder.subtract(&a,{&b,&c}),memory));
     emit(a.complement(universe,memory));
     emit(a.complement(b,memory));
     emit(evaluate_expression(builder.subtract(&builder.merge({&a,&b}),{&builder.intersect({&b,&c})}),memory));
    }
   }
  }
  out.flush();if(!out)std::abort();
 }
};
inline const bool mask_oracle_registered=[](){::testing::UnitTest::GetInstance()->listeners().Append(new MaskOracleListener);return true;}();
}
