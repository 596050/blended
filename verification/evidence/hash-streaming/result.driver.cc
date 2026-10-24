// SPDX-License-Identifier: GPL-2.0-or-later
// Driver only. The complete original hash_mm2a.cc is compiled unedited.
#include "BLI_hash_mm2a.hh"
#include <cstdint>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include <stdexcept>
int main(int argc,char**argv){
 if(argc!=2)return 2;std::ifstream file(argv[1]);if(!file)return 3;
 std::string line;std::cout<<'[';bool first=true;
 while(std::getline(file,line)){
  std::istringstream in(line);uint32_t seed;std::string hex;size_t chunks;
  if(!(in>>seed>>hex>>chunks))throw std::runtime_error("Malformed input");
  std::vector<unsigned char> bytes;
  if(hex!="-")for(size_t i=0;i<hex.size();i+=2)bytes.push_back(std::stoul(hex.substr(i,2),nullptr,16));
  // Non-null backing storage for empty adds; its contents are never read then.
  const size_t size=bytes.size();bytes.push_back(0);
  blender::BLI_HashMurmur2A h;blender::BLI_hash_mm2a_init(&h,seed);size_t offset=0;
  for(size_t i=0;i<chunks;++i){size_t count;if(!(in>>count)||count>size-offset)throw std::runtime_error("Invalid chunk");blender::BLI_hash_mm2a_add(&h,bytes.data()+offset,count);offset+=count;}
  if(offset!=size)throw std::runtime_error("Missing bytes");
  const uint32_t a=blender::BLI_hash_mm2a_end(&h),b=blender::BLI_hash_mm2a_end(&h);
  blender::BLI_hash_mm2a_init(&h,seed);blender::BLI_hash_mm2a_add(&h,bytes.data(),size);
  const uint32_t c=blender::BLI_hash_mm2a_end(&h);
  if(!first)std::cout<<',';first=false;std::cout<<'['<<a<<','<<b<<','<<c<<']';
 }
 std::cout<<"]\n";
}
