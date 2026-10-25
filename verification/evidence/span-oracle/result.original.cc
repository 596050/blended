
#include "BLI_span.hh"
#include <array>
#include <vector>
#include <iostream>
#include <cstring>
#include <cstdint>
using namespace blender;
std::vector<uint32_t> output;
void emit(int64_t x){output.push_back(uint32_t(x));}
void view(Span<int> s){emit(s.size());for(int x:s)emit(x);}
void mutable_view(MutableSpan<int> s){view(s);}
int main(){
 for(int n=0;n<=32;++n){
  std::array<int,96> storage;for(int i=0;i<96;++i)storage[i]=(i*17+n*3)%101-50;
  Span<int> s(storage.data(),n);MutableSpan<int> m(storage.data(),n);
  emit(s.size_in_bytes());emit(s.is_empty());view(s);
  for(int k=0;k<=n+6;++k){view(s.drop_front(k));view(s.drop_back(k));view(s.take_front(k));view(s.take_back(k));mutable_view(m.drop_front(k));mutable_view(m.drop_back(k));mutable_view(m.take_front(k));mutable_view(m.take_back(k));}
  for(int start=0;start<=n;++start){
   for(int len=0;len<=n-start;++len){auto a=s.slice(start,len);auto b=m.slice(start,len);view(a);mutable_view(b);emit(a.data()-storage.data());emit(b.data()-storage.data());}
   for(int len=0;len<=n+3;++len){view(s.slice_safe(start,len));mutable_view(m.slice_safe(start,len));}
  }
  for(int value=-55;value<=55;++value){emit(s.contains(value));emit(s.count(value));}
  emit(s.has_duplicates__linear_search());
  for(int i=0;i<n;++i){emit(s.first_index(s[i]));emit(s.last(i));emit(s.contains_ptr(storage.data()+i));}
  emit(s.contains_ptr(storage.data()+n));
  for(auto it=s.rbegin();it!=s.rend();++it)emit(*it);
  m.fill(7);view(s);m.reverse();view(s);
  for(int i=0;i<n;++i)storage[i]=i*5-17;
  view(s);m.reverse();view(s);
  std::vector<int> selected;for(int i=0;i<n;i+=3)selected.push_back(i);
  m.fill_indices(Span<int>(selected),-11);view(s);
  for(auto it=m.rbegin();it!=m.rend();++it)*it+=13;
  view(s);std::array<int,96> copy;for(int i=0;i<96;++i)copy[i]=90-i;
  m.copy_from(Span<int>(copy.data(),n));view(s);
 }
 for(int length=0;length<=8;++length){
  alignas(8) std::array<uint32_t,8> raw={0x01234567,0x89abcdef,0x00000000,0xffffffff,0x80000000,0x7fc12345,0x3f800000,0xdeadbeef};
  Span<uint32_t> words(raw.data(),length);auto bytes=words.cast<uint8_t>();auto shorts=words.cast<uint16_t>();
  emit(bytes.size());for(int64_t i=0;i<bytes.size();++i){uint8_t value;std::memcpy(&value,bytes.data()+i,1);emit(value);}
  emit(shorts.size());for(int64_t i=0;i<shorts.size();++i){uint16_t value;std::memcpy(&value,shorts.data()+i,2);emit(value);}
  auto roundtrip=shorts.cast<uint32_t>();emit(roundtrip.size());for(int64_t i=0;i<roundtrip.size();++i){uint32_t value;std::memcpy(&value,roundtrip.data()+i,4);emit(value);}
 }
 int a=2,b=5,c=8;std::array<int*,3> pointers={&a,&b,nullptr};
 MutableSpan<int*> mut(pointers);Span<const int*> read=mut;
 emit(read[0]==&a);pointers[0]=&c;emit(read[0]==&c);mut[1]=&a;emit(pointers[1]==&a);
 Span<int*> original=mut;auto floats=original.cast<float*>();emit(floats[0]==reinterpret_cast<float*>(&c));emit(floats[1]==reinterpret_cast<float*>(&a));emit(floats[2]==nullptr);
 for(uint32_t w:output){char b[4]={char(w),char(w>>8),char(w>>16),char(w>>24)};std::cout.write(b,4);}
 return std::cout?0:2;
}
