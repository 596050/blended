#include "BLI_rand.hh"
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <vector>
namespace blender { struct RNG { RandomNumberGenerator rng; };
void BLI_rng_seed(RNG *rng, uint seed)
{
  rng->rng.seed(seed);
}
uint BLI_rng_get_uint(RNG *rng)
{
  return rng->rng.get_uint32();
}
void BLI_rng_shuffle_array(RNG *rng, void *data, uint elem_size_i, uint elem_num)
{
  if (elem_num <= 1) {
    return;
  }

  const uint elem_size = elem_size_i;
  uint i = elem_num;
  void *temp = malloc(elem_size);

  while (i--) {
    const uint j = BLI_rng_get_uint(rng) % elem_num;
    if (i != j) {
      void *iElem = static_cast<uchar *>(data) + i * elem_size_i;
      void *jElem = static_cast<uchar *>(data) + j * elem_size_i;
      memcpy(temp, iElem, elem_size);
      memcpy(iElem, jElem, elem_size);
      memcpy(jElem, temp, elem_size);
    }
  }

  free(temp);
}
void BLI_array_randomize(void *data, uint elem_size, uint elem_num, uint seed)
{
  RNG rng;

  BLI_rng_seed(&rng, seed);
  BLI_rng_shuffle_array(&rng, data, elem_size, elem_num);
}
}
void print(const std::vector<int>&v){std::cout<<"[";for(size_t i=0;i<v.size();++i){if(i)std::cout<<",";std::cout<<v[i];}std::cout<<"]";}
int main(){std::cout<<"[";std::cout<<"[";bool first=true;
{if(!first)std::cout<<",";first=false;blender::RandomNumberGenerator rng(0u);std::vector<int> v;for(int i=0;i<3000;++i)v.push_back(rng.get_int32());print(v);}
{if(!first)std::cout<<",";first=false;blender::RandomNumberGenerator rng(1234u);std::vector<int> v;for(int i=0;i<3000;++i)v.push_back(rng.get_int32());print(v);}
{if(!first)std::cout<<",";first=false;blender::RandomNumberGenerator rng(4321u);std::vector<int> v;for(int i=0;i<3000;++i)v.push_back(rng.get_int32());print(v);}
{if(!first)std::cout<<",";first=false;blender::RandomNumberGenerator rng(9876u);std::vector<int> v;for(int i=0;i<3000;++i)v.push_back(rng.get_int32());print(v);}
{if(!first)std::cout<<",";first=false;blender::RandomNumberGenerator rng(5321u);std::vector<int> v;for(int i=0;i<3000;++i)v.push_back(rng.get_int32());print(v);}
std::cout<<"],[";first=true;
{if(!first)std::cout<<",";first=false;std::vector<int> v(1);for(int i=0;i<1;++i)v[i]=i;blender::BLI_array_randomize(v.data(),sizeof(int),1,1234u);print(v);}
{if(!first)std::cout<<",";first=false;std::vector<int> v(2);for(int i=0;i<2;++i)v[i]=i;blender::BLI_array_randomize(v.data(),sizeof(int),2,1234u);print(v);}
{if(!first)std::cout<<",";first=false;std::vector<int> v(100);for(int i=0;i<100;++i)v[i]=i;blender::BLI_array_randomize(v.data(),sizeof(int),100,4321u);print(v);}
{if(!first)std::cout<<",";first=false;std::vector<int> v(1024);for(int i=0;i<1024;++i)v[i]=i;blender::BLI_array_randomize(v.data(),sizeof(int),1024,9876u);print(v);}
{if(!first)std::cout<<",";first=false;std::vector<int> v(2048);for(int i=0;i<2048;++i)v[i]=i;blender::BLI_array_randomize(v.data(),sizeof(int),2048,5321u);print(v);}
std::cout<<"]]\n";}
