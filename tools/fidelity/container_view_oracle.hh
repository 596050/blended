// SPDX-License-Identifier: Apache-2.0
// Supplemental observer. No upstream test bodies or assertion expectations change.
#pragma once
#include "BLI_multi_value_map.hh"
#include "BLI_generic_span.hh"
#include <algorithm>
#include <array>
#include <bit>
#include <cstdint>
#include <fstream>
#include <memory>
#include <vector>
namespace blended_container_oracle {
inline void emit(std::vector<uint32_t>&out,int64_t v){out.push_back(uint32_t(v));}
inline void bucket(std::vector<uint32_t>&out,blender::Span<int> values){emit(out,values.size());for(int v:values)emit(out,v);}
inline void snapshot(std::vector<uint32_t>&out,const blender::MultiValueMap<int,int>&map){
 emit(out,map.size());emit(out,map.is_empty());std::vector<int> keys;for(int key:map.keys())keys.push_back(key);std::sort(keys.begin(),keys.end());
 emit(out,keys.size());for(int key:keys){emit(out,key);bucket(out,map.lookup(key));}
 std::vector<std::vector<int>> vals;for(auto span:map.values())vals.emplace_back(span.begin(),span.end());std::sort(vals.begin(),vals.end());emit(out,vals.size());for(const auto&v:vals){emit(out,v.size());for(int n:v)emit(out,n);}
 std::vector<std::pair<int,std::vector<int>>> items;for(auto&&item:map.items())items.emplace_back(item.key,std::vector<int>(item.value.begin(),item.value.end()));std::sort(items.begin(),items.end());emit(out,items.size());for(auto&&item:items){emit(out,item.first);emit(out,item.second.size());for(int n:item.second)emit(out,n);}
}
inline std::vector<uint32_t> generate(){
 using namespace blender;register_cpp_types();std::vector<uint32_t> out;
 emit(out,0x43564f31);emit(out,16);emit(out,64);
 for(int seed=0;seed<16;++seed){MultiValueMap<int,int> map;
  for(int step=0;step<64;++step){int key=(step*7+seed*3)%11-5;int v=(step*13+seed*17)%53-26;
   switch(step%8){
    case 0:map.add(key,v);break;
    case 1:map.add_multiple(key,{v,v+1,v});break;
    case 2:map.add_multiple(key,{});break;
    case 3:map.add_non_duplicates(key,v);map.add_non_duplicates(key,v);break;
    case 4:{auto values=map.lookup(key);for(int i=0;i<values.size();++i)values[i]+=i+1;break;}
    case 5:for(auto&&item:map.items())for(int &x:item.value)x+=item.key;break;
    case 6:bucket(out,map.lookup(999));break;
    case 7:{auto copy=map;map.add(key,v);snapshot(out,copy);if(step==31)map.clear();if(step==63)map.clear_and_shrink();break;}
   }snapshot(out,map);
  }
 }
 for(int n=0;n<=64;++n){std::array<int,64> values;for(int i=0;i<64;++i)values[i]=i*13-n;
  GMutableSpan mutable_span(CPPType::get<int>(),values.data(),n);GSpan read=mutable_span;
  emit(out,read.size());emit(out,read.size_in_bytes());emit(out,read.is_empty());emit(out,read.type().is<int>());
  for(int i=0;i<n;++i){emit(out,static_cast<const char*>(read[i])-reinterpret_cast<const char*>(values.data()));emit(out,read.typed<int>()[i]);if(i%2)*static_cast<int*>(mutable_span[i])+=7;else mutable_span.typed<int>()[i]+=7;emit(out,values[i]);emit(out,read.typed<int>()[i]);}
  for(int i=0;i<n;++i){values[i]=-values[i];emit(out,read.typed<int>()[i]);}
 }
 constexpr uint32_t bits[]={0,0x80000000,0x3f800000,0xbf800000,0x7f800000,0xff800000,0x7f812345,0x7fc12345};
 for(int n=0;n<=16;++n){std::array<float,16> values;for(int i=0;i<16;++i)values[i]=std::bit_cast<float>(bits[i%8]);GMutableSpan m(CPPType::get<float>(),values.data(),n);GSpan s=m;
  emit(out,s.size());emit(out,s.size_in_bytes());emit(out,s.type().is<float>());
  for(int i=0;i<n;++i){emit(out,std::bit_cast<uint32_t>(s.typed<float>()[i]));m.typed<float>()[i]=std::bit_cast<float>(bits[(i+3)%8]);emit(out,std::bit_cast<uint32_t>(values[i]));emit(out,std::bit_cast<uint32_t>(s.typed<float>()[i]));}
 }
 MultiValueMap<std::unique_ptr<int>,std::unique_ptr<int>> owned;owned.add(std::make_unique<int>(4),std::make_unique<int>(6));owned.add(std::make_unique<int>(4),std::make_unique<int>(7));emit(out,owned.size());std::vector<int> observed;
 for(auto&&item:owned.items()){emit(out,*item.key);emit(out,owned.lookup(item.key).size());for(auto&v:item.value)observed.push_back(*v);}
 std::sort(observed.begin(),observed.end());for(int v:observed)emit(out,v);
 owned.add(std::unique_ptr<int>{},std::make_unique<int>(3));owned.add(std::unique_ptr<int>{},std::make_unique<int>(4));emit(out,owned.size());auto null_values=owned.lookup(std::unique_ptr<int>{});emit(out,null_values.size());for(auto&v:null_values)emit(out,*v);
 return out;
}
class Listener final:public ::testing::EmptyTestEventListener{
 void OnTestProgramEnd(const ::testing::UnitTest&tests) override{
  const char*trace=std::getenv("BLENDED_ASSERTION_TRACE");if(!trace||tests.failed_test_count())return;
  std::string path(trace);auto cut=path.find_last_of("/\\");std::string name=path.substr(cut==std::string::npos?0:cut+1);
  if(name!="reference.jsonl")return;path=path.substr(0,cut==std::string::npos?0:cut+1)+"container-reference.bin";
  std::ofstream file(path,std::ios::binary);for(uint32_t word:generate()){char b[4]={char(word),char(word>>8),char(word>>16),char(word>>24)};file.write(b,4);}file.flush();if(!file)std::abort();
 }
};
inline const bool registered=[](){::testing::UnitTest::GetInstance()->listeners().Append(new Listener());return true;}();
}
