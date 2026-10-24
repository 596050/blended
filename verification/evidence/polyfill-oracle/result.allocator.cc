// Supplemental host-allocation bridge, not Blender guarded-allocation parity.
// Original ear clipping, beauty, heap and arena sources remain unedited.
#include "MEM_guardedalloc.h"
#include <cstdlib>
#include <cstring>
#include <limits>
#include <cstddef>
void *MEM_new_uninitialized(size_t n,const char*){void*p=std::malloc(n?n:1);if(!p)std::abort();return p;}
void *MEM_new_zeroed(size_t n,const char*){void*p=std::calloc(1,n?n:1);if(!p)std::abort();return p;}
static void *zero_aligned(size_t n,size_t s,size_t a,const char*){if(s&&n>std::numeric_limits<size_t>::max()/s)std::abort();if(a>alignof(std::max_align_t))std::abort();void*p=std::calloc(n?n:1,s?s:1);if(!p)std::abort();return p;}
static void *reallocate(void*p,size_t n,const char*){void*q=std::realloc(p,n?n:1);if(!q)std::abort();return q;}
static void release(void*p,mem_guarded::internal::DestructorType){std::free(p);}
void *(*MEM_new_array_zeroed_aligned)(size_t,size_t,size_t,const char*)=zero_aligned;
void *(*MEM_realloc_uninitialized_id)(void*,size_t,const char*)=reallocate;
void (*mem_guarded::internal::mem_freeN_ex)(void*,mem_guarded::internal::DestructorType)=release;
