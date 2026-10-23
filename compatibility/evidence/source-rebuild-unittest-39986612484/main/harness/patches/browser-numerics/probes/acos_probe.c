/* SPDX-FileCopyrightText: 2023 Blender Authors
 * SPDX-FileCopyrightText: 2026 Blended contributors
 * SPDX-License-Identifier: GPL-2.0-or-later */
/* Diagnostic-only native C harness. Does not modify Blender or its tests. */
#include <float.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
float em_acosf(float);
float em_acosf_candidate(float);
static float frombits(uint32_t b) { float x; memcpy(&x, &b, sizeof(x)); return x; }
static uint32_t bits(float x) { uint32_t b; memcpy(&b, &x, sizeof(b)); return b; }
int main(void) {
  unsigned index; uint32_t b[6];
  fprintf(stderr,"FLT_EVAL_METHOD=%d sizeof_float=%zu sizeof_double=%zu\n",FLT_EVAL_METHOD,sizeof(float),sizeof(double));
  while (scanf("%u %x %x %x %x %x %x",&index,&b[0],&b[1],&b[2],&b[3],&b[4],&b[5])==7) {
    float v[3],o[3]; double dot=0, dv=0, do_=0;
    for (int i=0;i<3;i++) { v[i]=frombits(b[i]); o[i]=frombits(b[i+3]); }
    for (int i=0;i<3;i++) { dot+=(double)v[i]*(double)o[i]; dv+=(double)v[i]*(double)v[i]; do_+=(double)o[i]*(double)o[i]; }
    double c64=dot/(sqrt(dv)*sqrt(do_)); float c=(float)c64;
    float native=acosf(c),em=em_acosf(c),candidate=em_acosf_candidate(c),double_cast=(float)acos(c);
    printf("%u %.17g %08x %08x %08x %08x %08x\n",index,c64,bits(c),bits(native),bits(em),bits(candidate),bits(double_cast));
  }
  return 0;
}
