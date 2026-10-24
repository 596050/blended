// Supplemental driver. Original math_half.cc and normalised header are unedited.
#include "BLI_math_half.hh"
#include "BLI_normalized_int_types.hh"
#include "BLI_simd.hh"
#include <bit>
#include <fstream>
#include <iostream>
#include <vector>
#include <cstdint>
#include <cstdlib>
#include <immintrin.h>
using namespace blender;
std::vector<uint32_t> words;
void emit(uint32_t v){words.push_back(v);}
uint32_t read32(std::istream &s){unsigned char b[4];s.read((char*)b,4);if(!s)std::abort();return uint32_t(b[0])|(uint32_t(b[1])<<8)|(uint32_t(b[2])<<16)|(uint32_t(b[3])<<24);}
std::vector<float> read_vector(std::istream &s){auto n=read32(s);std::vector<float> v(n);for(auto &f:v)f=std::bit_cast<float>(read32(s));return v;}
template<class T,int N> void normalised(const std::vector<float>&input,int width,bool is_signed,uint32_t raw_count){
 using V=typename T::VecT;using I=typename T::IntVecT;
 for(size_t k=0;k<input.size();++k){V f;for(int j=0;j<N;++j)f[j]=input[(k+size_t(j)*17)%input.size()];T packed(f);I iv(packed);V decoded(packed);uint64_t storage=0;int shift=0;
 for(int j=0;j<N;++j){int w=(width==10&&j==3)?2:width;storage|=(uint64_t(uint32_t(iv[j]))&((uint64_t(1)<<w)-1))<<shift;shift+=w;emit(uint32_t(iv[j]));}
 for(int j=0;j<N;++j)emit(std::bit_cast<uint32_t>(decoded[j]));emit(uint32_t(storage));emit(uint32_t(storage>>32));}
 for(uint32_t raw=0;raw<raw_count;++raw){I fields;for(int j=0;j<N;++j){int w=(width==10&&j==3)?2:width;uint32_t v=(raw+uint32_t(j)*53)&((1u<<w)-1);int32_t signed_value=(is_signed&&(v&(1u<<(w-1))))?int32_t(v)-int32_t(1u<<w):int32_t(v);fields[j]=signed_value;}T packed(fields);I back(packed);V decoded(packed);for(int j=0;j<N;++j)emit(uint32_t(back[j]));for(int j=0;j<N;++j)emit(std::bit_cast<uint32_t>(decoded[j]));}
}
int main(int argc,char**argv){
 if(argc!=3)return 2;std::ifstream input(argv[1],std::ios::binary);auto floats=read_vector(input);auto norm=read_vector(input);if(input.peek()!=EOF)return 3;
 // Explicit baseline profile: nearest-even, gradual input denormals, exceptions masked.
 uint32_t saved=_mm_getcsr();_mm_setcsr(0x1f80);std::vector<uint16_t> halves(65536);for(uint32_t i=0;i<65536;++i){halves[i]=uint16_t(i);emit(std::bit_cast<uint32_t>(math::half_to_float(uint16_t(i))));}
 std::vector<float> decoded(65536);math::half_to_float_array(halves.data(),decoded.data(),halves.size());for(float v:decoded)emit(std::bit_cast<uint32_t>(v));
 uint32_t before=_mm_getcsr(),during=0,after=0;
 {ScopedFlushToZero guard;during=_mm_getcsr();if((during&0x8040)!=0x8040)return 4;math::half_to_float_array(halves.data(),decoded.data(),halves.size());for(float v:decoded)emit(std::bit_cast<uint32_t>(v));}
 after=_mm_getcsr();if(after!=before)return 5;
 for(float v:floats){emit(math::float_to_half(v));emit(math::float_to_half_make_finite(v));}
 std::vector<uint16_t> output(floats.size());math::float_to_half_array(floats.data(),output.data(),output.size());for(auto v:output)emit(v);
 math::float_to_half_make_finite_array(floats.data(),output.data(),output.size());for(auto v:output)emit(v);
math::float_to_half_clamp_array(floats.data(),output.data(),output.size(),-10.0f,1000.0f);for(auto v:output)emit(v);
math::float_to_half_clamp_array(floats.data(),output.data(),output.size(),1.0f,2.0f);for(auto v:output)emit(v);
math::float_to_half_clamp_array(floats.data(),output.data(),output.size(),-2.0f,-1.0f);for(auto v:output)emit(v);
const uint32_t tail_bits[]={0x7f800001u,0xffc12345u,0x0u,0x80000000u,0x33800000u,0xb3800000u,0x387fc000u,0x38800000u,0x477fe000u,0xc77fe000u,0x7f800000u,0xff800000u,0x3f801000u,0x3f803000u,0x3f800000u,0xbf800000u,0x800000u,0x1u,0x7fffffffu};
const uint16_t tail_half[]={0x7c01,0xfe23,0x0,0x8000,0x1,0x8001,0x3ff,0x400,0x7bff,0xfbff,0x7c00,0xfc00,0x3c01,0x3c02,0x3c00,0xbc00,0x2,0x3,0x7fff};

 for(size_t rotation=0;rotation<4;++rotation){float src[20];uint16_t hsrc[20];for(size_t i=0;i<20;++i){src[i]=std::bit_cast<float>(tail_bits[(i+rotation)%19]);hsrc[i]=tail_half[(i+rotation)%19];}
 for(size_t n=0;n<18;++n){std::vector<float> f(20,std::bit_cast<float>(0x41234567u));math::half_to_float_array(hsrc,f.data(),n);for(float v:f)emit(std::bit_cast<uint32_t>(v));
 std::vector<uint16_t> h(20,0xa55a);math::float_to_half_array(src,h.data(),n);for(auto v:h)emit(v);
 std::fill(h.begin(),h.end(),0xa55a);math::float_to_half_make_finite_array(src,h.data(),n);for(auto v:h)emit(v);
std::fill(h.begin(),h.end(),0xa55a);math::float_to_half_clamp_array(src,h.data(),n,-10.0f,1000.0f);for(auto v:h)emit(v);
std::fill(h.begin(),h.end(),0xa55a);math::float_to_half_clamp_array(src,h.data(),n,1.0f,2.0f);for(auto v:h)emit(v);
std::fill(h.begin(),h.end(),0xa55a);math::float_to_half_clamp_array(src,h.data(),n,-2.0f,-1.0f);for(auto v:h)emit(v);
}}
normalised<char4_norm,4>(norm,8,true,256);
normalised<uchar4_norm,4>(norm,8,false,256);
normalised<short2_norm,2>(norm,16,true,65536);
normalised<ushort2_norm,2>(norm,16,false,65536);
normalised<short4_norm,4>(norm,16,true,0);
normalised<ushort4_norm,4>(norm,16,false,0);
normalised<int1010102_norm,4>(norm,10,true,1024);
normalised<uint1010102_norm,4>(norm,10,false,1024);

 _mm_setcsr(saved);std::ofstream result(argv[2],std::ios::binary);for(auto w:words){const char b[4]={char(w),char(w>>8),char(w>>16),char(w>>24)};result.write(b,4);}if(!result)return 6;
 std::cerr<<"{\"hardware_fp_control\":true,\"before\":"<<before<<",\"during\":"<<during<<",\"after\":"<<after<<",\"restored\":true,\"output_words\":"<<words.size()<<"}\n";
}
