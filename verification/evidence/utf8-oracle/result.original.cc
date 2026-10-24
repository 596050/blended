#include "BLI_rand.hh"
#include "BLI_string_utf8.hh"
#include "BLI_utildefines.hh"
#include <fstream>
#include <iostream>
#include <vector>
namespace blender {
BLI_INLINE int utf8_char_compute_skip(const char c)
{
  if (c >= 192) [[unlikely]] {
    if ((c & 0xe0) == 0xc0) {
      return 2;
    }
    if ((c & 0xf0) == 0xe0) {
      return 3;
    }
    if ((c & 0xf8) == 0xf0) {
      return 4;
    }
    if ((c & 0xfc) == 0xf8) {
      return 5;
    }
    if ((c & 0xfe) == 0xfc) {
      return 6;
    }
  }
  return 1;
}
BLI_INLINE int utf8_char_compute_skip_or_error_with_mask(const char c, char *r_mask)
{
  /* Originally from GLIB `UTF8_COMPUTE` macro. */
  if (c < 128) {
    *r_mask = 0x7f;
    return 1;
  }
  if ((c & 0xe0) == 0xc0) {
    *r_mask = 0x1f;
    return 2;
  }
  if ((c & 0xf0) == 0xe0) {
    *r_mask = 0x0f;
    return 3;
  }
  if ((c & 0xf8) == 0xf0) {
    *r_mask = 0x07;
    return 4;
  }
  if ((c & 0xfc) == 0xf8) {
    *r_mask = 0x03;
    return 5;
  }
  if ((c & 0xfe) == 0xfc) {
    *r_mask = 0x01;
    return 6;
  }
  return -1;
}
BLI_INLINE uint utf8_char_decode(const char *p, const char mask, const int len, const uint err)
{
  /* Originally from GLIB `UTF8_GET` macro, added an 'err' argument. */
  uint result = p[0] & mask;
  for (int count = 1; count < len; count++) {
    if ((p[count] & 0xc0) != 0x80) {
      return err;
    }
    result <<= 6;
    result |= p[count] & 0x3f;
  }
  return result;
}
ptrdiff_t BLI_str_utf8_invalid_byte(const char *str, size_t str_len)
{
  /* NOTE(@ideasman42): from libswish3, originally called `u8_isvalid()`,
   * modified to return the index of the bad character (byte index not UTF).
   * http://svn.swish-e.org/libswish3/trunk/src/libswish3/utf8.c r3044.
   *
   * Comment from code in: `libswish3`.
   * Based on the `valid_utf8` routine from the PCRE library by Philip Hazel
   *
   * length is in bytes, since without knowing whether the string is valid
   * it's hard to know how many characters there are! */

  const uchar *p, *perr, *pend = reinterpret_cast<const uchar *>(str) + str_len;
  uchar c;
  int ab;

  for (p = reinterpret_cast<const uchar *>(str); p < pend; p++, str_len--) {
    c = *p;
    perr = p; /* Erroneous char is always the first of an invalid UTF8 sequence... */
    if (ELEM(c, 0xfe, 0xff, 0x00)) {
      /* Those three values are not allowed in UTF8 string. */
      goto utf8_error;
    }
    if (c < 128) {
      continue;
    }
    if ((c & 0xc0) != 0xc0) {
      goto utf8_error;
    }

    /* Note that since we always increase p (and decrease length) by one byte in main loop,
     * we only add/subtract extra UTF8 bytes in code below
     * (ab number, aka number of bytes remaining in the UTF8 sequence after the initial one). */
    ab = utf8_char_compute_skip(c) - 1;
    if (str_len <= size_t(ab)) {
      goto utf8_error;
    }

    /* Check top bits in the second byte */
    p++;
    str_len--;
    if ((*p & 0xc0) != 0x80) {
      goto utf8_error;
    }

    /* Check for overlong sequences for each different length */
    switch (ab) {
      case 1:
        /* Check for: `XX00 000X`. */
        if ((c & 0x3e) == 0) {
          goto utf8_error;
        }
        continue; /* We know there aren't any more bytes to check */

      case 2:
        /* Check for: `1110 0000, XX0X XXXX`. */
        if (c == 0xe0 && (*p & 0x20) == 0) {
          goto utf8_error;
        }
        /* Some special cases, see section 5 of UTF8 decoder stress-test by Markus Kuhn
         * (https://www.cl.cam.ac.uk/~mgk25/ucs/examples/UTF-8-test.txt). */
        /* From section 5.1 (and 5.2) */
        if (c == 0xed) {
          if (*p == 0xa0 && *(p + 1) == 0x80) {
            goto utf8_error;
          }
          if (*p == 0xad && *(p + 1) == 0xbf) {
            goto utf8_error;
          }
          if (*p == 0xae && *(p + 1) == 0x80) {
            goto utf8_error;
          }
          if (*p == 0xaf && *(p + 1) == 0xbf) {
            goto utf8_error;
          }
          if (*p == 0xb0 && *(p + 1) == 0x80) {
            goto utf8_error;
          }
          if (*p == 0xbe && *(p + 1) == 0x80) {
            goto utf8_error;
          }
          if (*p == 0xbf && *(p + 1) == 0xbf) {
            goto utf8_error;
          }
        }
        /* From section 5.3 */
        if (c == 0xef) {
          if (*p == 0xbf && *(p + 1) == 0xbe) {
            goto utf8_error;
          }
          if (*p == 0xbf && *(p + 1) == 0xbf) {
            goto utf8_error;
          }
        }
        break;

      case 3:
        /* Check for: `1111 0000, XX00 XXXX`. */
        if (c == 0xf0 && (*p & 0x30) == 0) {
          goto utf8_error;
        }
        break;

      case 4:
        /* Check for `1111 1000, XX00 0XXX`. */
        if (c == 0xf8 && (*p & 0x38) == 0) {
          goto utf8_error;
        }
        break;

      case 5:
        /* Check for: `1111 1100, XX00 00XX`. */
        if (c == 0xfc && (*p & 0x3c) == 0) {
          goto utf8_error;
        }
        break;
    }

    /* Check for valid bytes after the 2nd, if any; all must start 10. */
    while (--ab > 0) {
      p++;
      str_len--;
      if ((*p & 0xc0) != 0x80) {
        goto utf8_error;
      }
    }
  }

  return -1;

utf8_error:

  return (reinterpret_cast<const char *>(perr) - static_cast<const char *>(str));
}
uint BLI_str_utf8_as_unicode_step_or_error(const char *__restrict p,
                                           const size_t p_len,
                                           size_t *__restrict index)
{
  const uchar c = uchar(*(p += *index));

  BLI_assert(*index < p_len);
  BLI_assert(c != '\0');

  char mask = 0;
  const int len = utf8_char_compute_skip_or_error_with_mask(c, &mask);
  if (UNLIKELY(len == -1) || (*index + size_t(len) > p_len)) {
    return BLI_UTF8_ERR;
  }

  const uint result = utf8_char_decode(p, mask, len, BLI_UTF8_ERR);
  if (result == BLI_UTF8_ERR) [[unlikely]] {
    return BLI_UTF8_ERR;
  }
  *index += size_t(len);
  BLI_assert(*index <= p_len);
  return result;
}
uint BLI_str_utf8_as_unicode_step_safe(const char *__restrict p,
                                       const size_t p_len,
                                       size_t *__restrict index)
{
  uint result = BLI_str_utf8_as_unicode_step_or_error(p, p_len, index);
  if (result == BLI_UTF8_ERR) [[unlikely]] {
    result = uint(p[*index]);
    *index += 1;
  }
  BLI_assert(*index <= p_len);
  return result;
}
void RandomNumberGenerator::get_bytes(MutableSpan<char> r_bytes)
{
  constexpr int64_t mask_bytes = 2;
  constexpr int64_t rand_stride = int64_t(sizeof(x_)) - mask_bytes;

  int64_t last_len = 0;
  int64_t trim_len = r_bytes.size();

  if (trim_len > rand_stride) {
    last_len = trim_len % rand_stride;
    trim_len = trim_len - last_len;
  }
  else {
    trim_len = 0;
    last_len = r_bytes.size();
  }

  const char *data_src = reinterpret_cast<const char *>(&x_);
  int64_t i = 0;
  while (i != trim_len) {
    BLI_assert(i < trim_len);
    /* NOTE: this is endianness-sensitive.
     * Big Endian needs to iterate in reverse, with a `mask_bytes - 1` offset. */
    for (int64_t j = 0; j != rand_stride; j++) {
      r_bytes[i++] = data_src[j];
    }
    this->step();
  }
  if (last_len) {
    for (int64_t j = 0; j != last_len; j++) {
      r_bytes[i++] = data_src[j];
    }
  }
}
}

uint32_t read32(std::istream &s){unsigned char b[4];s.read(reinterpret_cast<char*>(b),4);if(!s)std::abort();return uint32_t(b[0])|(uint32_t(b[1])<<8)|(uint32_t(b[2])<<16)|(uint32_t(b[3])<<24);}
int main(int argc,char **argv){if(argc!=2)return 2;std::ifstream input(argv[1],std::ios::binary);const auto count=read32(input);std::cout<<"[\n";
for(uint32_t n=0;n<count;++n){auto len=read32(input);std::vector<char> data(len+1,0);input.read(data.data(),len);if(!input) return 3;if(n)std::cout<<",\n";std::cout<<"["<<blender::BLI_str_utf8_invalid_byte(data.data(),len);size_t index=0;while(index<len&&data[index]!=0){auto value=blender::BLI_str_utf8_as_unicode_step_safe(data.data(),len,&index);std::cout<<","<<value<<","<<index;}std::cout<<"]";}
std::cout<<",[";bool first=true;
{blender::RandomNumberGenerator rng(1);std::vector<char> data(1);for(int i=0;i<256;++i){rng.get_bytes(blender::MutableSpan<char>(data.data(),data.size()));for(unsigned char b:data){if(!first)std::cout<<",";first=false;std::cout<<unsigned(b);}}}
{blender::RandomNumberGenerator rng(1);std::vector<char> data(2);for(int i=0;i<256;++i){rng.get_bytes(blender::MutableSpan<char>(data.data(),data.size()));for(unsigned char b:data){if(!first)std::cout<<",";first=false;std::cout<<unsigned(b);}}}
{blender::RandomNumberGenerator rng(1);std::vector<char> data(3);for(int i=0;i<256;++i){rng.get_bytes(blender::MutableSpan<char>(data.data(),data.size()));for(unsigned char b:data){if(!first)std::cout<<",";first=false;std::cout<<unsigned(b);}}}
{blender::RandomNumberGenerator rng(1);std::vector<char> data(4);for(int i=0;i<256;++i){rng.get_bytes(blender::MutableSpan<char>(data.data(),data.size()));for(unsigned char b:data){if(!first)std::cout<<",";first=false;std::cout<<unsigned(b);}}}
{blender::RandomNumberGenerator rng(1);std::vector<char> data(5);for(int i=0;i<256;++i){rng.get_bytes(blender::MutableSpan<char>(data.data(),data.size()));for(unsigned char b:data){if(!first)std::cout<<",";first=false;std::cout<<unsigned(b);}}}
{blender::RandomNumberGenerator rng(1);std::vector<char> data(6);for(int i=0;i<256;++i){rng.get_bytes(blender::MutableSpan<char>(data.data(),data.size()));for(unsigned char b:data){if(!first)std::cout<<",";first=false;std::cout<<unsigned(b);}}}
{blender::RandomNumberGenerator rng(1);std::vector<char> data(7);for(int i=0;i<256;++i){rng.get_bytes(blender::MutableSpan<char>(data.data(),data.size()));for(unsigned char b:data){if(!first)std::cout<<",";first=false;std::cout<<unsigned(b);}}}
{blender::RandomNumberGenerator rng(1);std::vector<char> data(8);for(int i=0;i<256;++i){rng.get_bytes(blender::MutableSpan<char>(data.data(),data.size()));for(unsigned char b:data){if(!first)std::cout<<",";first=false;std::cout<<unsigned(b);}}}
{blender::RandomNumberGenerator rng(1);std::vector<char> data(9);for(int i=0;i<256;++i){rng.get_bytes(blender::MutableSpan<char>(data.data(),data.size()));for(unsigned char b:data){if(!first)std::cout<<",";first=false;std::cout<<unsigned(b);}}}
{blender::RandomNumberGenerator rng(1);std::vector<char> data(10);for(int i=0;i<256;++i){rng.get_bytes(blender::MutableSpan<char>(data.data(),data.size()));for(unsigned char b:data){if(!first)std::cout<<",";first=false;std::cout<<unsigned(b);}}}
{blender::RandomNumberGenerator rng(1);std::vector<char> data(11);for(int i=0;i<256;++i){rng.get_bytes(blender::MutableSpan<char>(data.data(),data.size()));for(unsigned char b:data){if(!first)std::cout<<",";first=false;std::cout<<unsigned(b);}}}
{blender::RandomNumberGenerator rng(1);std::vector<char> data(12);for(int i=0;i<256;++i){rng.get_bytes(blender::MutableSpan<char>(data.data(),data.size()));for(unsigned char b:data){if(!first)std::cout<<",";first=false;std::cout<<unsigned(b);}}}
{blender::RandomNumberGenerator rng(1);std::vector<char> data(16);for(int i=0;i<256;++i){rng.get_bytes(blender::MutableSpan<char>(data.data(),data.size()));for(unsigned char b:data){if(!first)std::cout<<",";first=false;std::cout<<unsigned(b);}}}
{blender::RandomNumberGenerator rng(1);std::vector<char> data(31);for(int i=0;i<256;++i){rng.get_bytes(blender::MutableSpan<char>(data.data(),data.size()));for(unsigned char b:data){if(!first)std::cout<<",";first=false;std::cout<<unsigned(b);}}}
{blender::RandomNumberGenerator rng(1);std::vector<char> data(32);for(int i=0;i<256;++i){rng.get_bytes(blender::MutableSpan<char>(data.data(),data.size()));for(unsigned char b:data){if(!first)std::cout<<",";first=false;std::cout<<unsigned(b);}}}
{blender::RandomNumberGenerator rng(1);std::vector<char> data(33);for(int i=0;i<256;++i){rng.get_bytes(blender::MutableSpan<char>(data.data(),data.size()));for(unsigned char b:data){if(!first)std::cout<<",";first=false;std::cout<<unsigned(b);}}}
std::cout<<"]]\n";}
