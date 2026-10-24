// SPDX-License-Identifier: GPL-2.0-or-later
#include <cctype>
#include <clocale>
#include <cstring>
#include <string>
#include <vector>
#include <fstream>
#include <iostream>
#include <stdexcept>
#define ELEM(a,b,c) (((a)==(b))||((a)==(c)))
namespace blender {
int BLI_strncasecmp(const char *s1, const char *s2, size_t len)
{
  size_t i;
  char c1, c2;

  for (i = 0; i < len; i++) {
    c1 = char(tolower(s1[i]));
    c2 = char(tolower(s2[i]));

    if (c1 < c2) {
      return -1;
    }
    if (c1 > c2) {
      return 1;
    }
    if (c1 == 0) {
      break;
    }
  }

  return 0;
}

char *BLI_strncasestr(const char *s, const char *find, size_t len)
{
  char c, sc;

  if ((c = *find++) != 0) {
    c = char(tolower(c));
    if (len > 1) {
      do {
        do {
          if ((sc = *s++) == 0) {
            return nullptr;
          }
          sc = char(tolower(sc));
        } while (sc != c);
      } while (BLI_strncasecmp(s, find, len - 1) != 0);
    }
    else {
      {
        do {
          if ((sc = *s++) == 0) {
            return nullptr;
          }
          sc = char(tolower(sc));
        } while (sc != c);
      }
    }
    s--;
  }
  return (const_cast<char *>(s));
}

static int left_number_strcmp(const char *s1, const char *s2, int *tiebreaker)
{
  const char *p1 = s1, *p2 = s2;
  int numdigit, numzero1, numzero2;

  /* count and skip leading zeros */
  for (numzero1 = 0; *p1 == '0'; numzero1++) {
    p1++;
  }
  for (numzero2 = 0; *p2 == '0'; numzero2++) {
    p2++;
  }

  /* find number of consecutive digits */
  for (numdigit = 0;; numdigit++) {
    if (isdigit(*(p1 + numdigit)) && isdigit(*(p2 + numdigit))) {
      continue;
    }
    if (isdigit(*(p1 + numdigit))) {
      return 1; /* s2 is bigger */
    }
    if (isdigit(*(p2 + numdigit))) {
      return -1; /* s1 is bigger */
    }
    break;
  }

  /* same number of digits, compare size of number */
  if (numdigit > 0) {
    int compare = strncmp(p1, p2, size_t(numdigit));

    if (compare != 0) {
      return compare;
    }
  }

  /* use number of leading zeros as tie breaker if still equal */
  if (*tiebreaker == 0) {
    if (numzero1 > numzero2) {
      *tiebreaker = 1;
    }
    else if (numzero1 < numzero2) {
      *tiebreaker = -1;
    }
  }

  return 0;
}

int BLI_strcasecmp_natural(const char *s1, const char *s2)
{
  int d1 = 0, d2 = 0;
  char c1, c2;
  int tiebreaker = 0;

  /* if both chars are numeric, to a left_number_strcmp().
   * then increase string deltas as long they are
   * numeric, else do a tolower and char compare */

  while (true) {
    if (isdigit(s1[d1]) && isdigit(s2[d2])) {
      int numcompare = left_number_strcmp(s1 + d1, s2 + d2, &tiebreaker);

      if (numcompare != 0) {
        return numcompare;
      }

      /* Some wasted work here, left_number_strcmp already consumes at least some digits. */
      d1++;
      while (isdigit(s1[d1])) {
        d1++;
      }
      d2++;
      while (isdigit(s2[d2])) {
        d2++;
      }
    }

    /* Test for end of strings first so that shorter strings are ordered in front. */
    if (ELEM(0, s1[d1], s2[d2])) {
      break;
    }

    c1 = char(tolower(s1[d1]));
    c2 = char(tolower(s2[d2]));

    if (c1 == c2) {
      /* Continue iteration */
    }
    /* Check for '.' so "foo.bar" comes before "foo 1.bar". */
    else if (c1 == '.') {
      return -1;
    }
    else if (c2 == '.') {
      return 1;
    }
    else if (c1 < c2) {
      return -1;
    }
    else if (c1 > c2) {
      return 1;
    }

    d1++;
    d2++;
  }

  if (tiebreaker) {
    return tiebreaker;
  }

  /* we might still have a different string because of lower/upper case, in
   * that case fall back to regular string comparison */
  return strcmp(s1, s2);
}
}
int main(int argc,char**argv){
 if(argc!=2)return 2;std::setlocale(LC_ALL,"C");std::ifstream file(argv[1]);if(!file)return 3;
 std::vector<std::string> words;std::string line;
 while(std::getline(file,line)){std::string word;if(line!="-"){if(line.size()%2)throw std::runtime_error("Bad fixture");for(size_t i=0;i<line.size();i+=2)word.push_back(char(std::stoul(line.substr(i,2),nullptr,16)));}words.push_back(word);}
 bool first=true;std::cout<<'[';
 for(const auto&a:words)for(const auto&b:words){
  if(!first)std::cout<<',';first=false;std::cout<<'['<<blender::BLI_strcasecmp_natural(a.c_str(),b.c_str());
  for(size_t n: {0,1,2,3,4,8,32}){const char*p=blender::BLI_strncasestr(a.c_str(),b.c_str(),n);std::cout<<','<<(p?p-a.c_str():-1);}
  std::cout<<']';
 }
 std::cout<<"]\n";
}
