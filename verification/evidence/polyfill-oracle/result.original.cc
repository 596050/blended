// GPL-3.0-or-later supplemental driver; original implementations linked unchanged.
#include "BLI_polyfill_2d.hh"
#include "BLI_polyfill_2d_beautify.hh"
#include "BLI_heap.hh"
#include "BLI_memarena.hh"
#include <array>
#include <vector>
#include <fstream>
#include <bit>
#include <cstdlib>
uint32_t read(std::istream&s){unsigned char b[4];s.read((char*)b,4);if(!s)std::abort();return uint32_t(b[0])|uint32_t(b[1])<<8|uint32_t(b[2])<<16|uint32_t(b[3])<<24;}
void write(std::ostream&s,uint32_t v){char b[4]={char(v),char(v>>8),char(v>>16),char(v>>24)};s.write(b,4);}
int main(int argc,char**argv){if(argc!=3)return 2;std::ifstream input(argv[1],std::ios::binary);std::ofstream out(argv[2],std::ios::binary);uint32_t total=read(input);
for(uint32_t k=0;k<total;++k){uint32_t n=read(input);std::vector<std::array<uint32_t,2>> base(n);for(auto&v:base){v[0]=read(input);v[1]=read(input);}
 for(uint32_t rev=0;rev<2;++rev)for(uint32_t cycle=0;cycle<n;++cycle)for(uint32_t fx=0;fx<2;++fx)for(uint32_t fy=0;fy<2;++fy){
  for(uint32_t v:{k,rev,cycle,fx,fy,n})write(out,v);
  std::vector<std::array<float,2>> points(n);for(uint32_t i=0;i<n;++i){uint32_t j=(i+cycle)%n;if(rev)j=n-1-j;auto a=base[j][0]^(fx<<31),b=base[j][1]^(fy<<31);points[i]={std::bit_cast<float>(a),std::bit_cast<float>(b)};write(out,a);write(out,b);}
  std::vector<std::array<uint32_t,3>> triangles(n-2);auto*p=reinterpret_cast<const float(*)[2]>(points.data());auto*t=reinterpret_cast<unsigned(*)[3]>(triangles.data());
  blender::BLI_polyfill_calc(p,n,0,t);for(auto&tri:triangles)for(auto v:tri)write(out,v);
  auto*a=blender::BLI_memarena_new(16384,"polygon oracle");auto*h=blender::BLI_heap_new();blender::BLI_polyfill_beautify(p,n,t,a,h);for(auto&tri:triangles)for(auto v:tri)write(out,v);blender::BLI_heap_free(h,nullptr);blender::BLI_memarena_free(a);
 }
}if(input.peek()!=EOF||!out)return 3;}
