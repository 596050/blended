// SPDX-FileCopyrightText: 2001-2002 NaN Holding BV. All rights reserved.
// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-FileCopyrightText: 2026 Blended contributors
// Diagnostic adaptation of Blender pinned bmo_dupe.cc/bmo_utils.cc/math_matrix_c.cc.
// SPDX-License-Identifier: GPL-2.0-or-later
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
extern "C" bool inverse_sse(const float *,float *);
extern "C" bool inverse_scalar(const float *,float *);
using Matrix = float[4][4];
static uint32_t bits(float f) { uint32_t b; memcpy(&b,&f,4); return b; }
static float frombits(uint32_t b) { float f; memcpy(&f,&b,4); return f; }
static void identity(Matrix &m) { for(int i=0;i<4;i++) for(int j=0;j<4;j++) m[i][j]=i==j ? 1.0f : 0.0f; }
static void multiply(Matrix &r,const Matrix &a,const Matrix &b,bool paired) {
 for(int j=0;j<4;j++) for(int k=0;k<4;k++) {
  float p0=b[j][0]*a[0][k],p1=b[j][1]*a[1][k],p2=b[j][2]*a[2][k],p3=b[j][3]*a[3][k];
  r[j][k]=paired ? (p0+p1)+(p2+p3) : ((p0+p1)+p2)+p3;
 }
}
static void conjugate(Matrix &out,const Matrix &inverse,const Matrix &op,const Matrix &space,bool paired) {
 Matrix tmp; multiply(tmp,inverse,op,paired); multiply(out,tmp,space,paired);
}
static void apply(const Matrix &m,float r[3]) {
 const float x=r[0],y=r[1];
 r[0]=x*m[0][0]+y*m[1][0]+m[2][0]*r[2]+m[3][0];
 r[1]=x*m[0][1]+y*m[1][1]+m[2][1]*r[2]+m[3][1];
 r[2]=x*m[0][2]+y*m[1][2]+m[2][2]*r[2]+m[3][2];
}
static void axis_z_rotation(Matrix &m,float angle) {
 identity(m); float s=sinf(angle),c=cosf(angle),ico=1.0f-c;
 float axis[3]={0,0,1},nsi[3]={axis[0]*s,axis[1]*s,axis[2]*s};
 float n00=(axis[0]*axis[0])*ico,n01=(axis[0]*axis[1])*ico,n11=(axis[1]*axis[1])*ico;
 float n02=(axis[0]*axis[2])*ico,n12=(axis[1]*axis[2])*ico,n22=(axis[2]*axis[2])*ico;
 m[0][0]=n00+c;m[0][1]=n01+nsi[2];m[0][2]=n02-nsi[1];
 m[1][0]=n01-nsi[2];m[1][1]=n11+c;m[1][2]=n12+nsi[0];
 m[2][0]=n02+nsi[1];m[2][1]=n12-nsi[0];m[2][2]=n22+c;
}
int main() {
 Matrix space; for(int row=0;row<4;row++) for(int col=0;col<4;col++) {uint32_t b; if(scanf("%x",&b)!=1)return 1;space[col][row]=frombits(b);}
 const float seeds[7][3]={{11,0,0},{11,0,1},{11,0,2},{11,0,3},{12,0,3},{12,0,4},{11,0,4}};
 const float angle_total=(float)6.283185307179586;
 for(int scalar_inverse=0;scalar_inverse<2;scalar_inverse++) for(int paired=0;paired<2;paired++) {
  Matrix inv; (scalar_inverse ? inverse_scalar : inverse_sse)(&space[0][0],&inv[0][0]);
  for(int row=0;row<4;row++) for(int col=0;col<4;col++) printf("inverse %d %d %d %d %08x\n",scalar_inverse,paired,row,col,bits(inv[col][row]));
  for(int step=0;step<=6;step++) {
   Matrix rotated,translated,rot,translation;
   if(step) {
    const float angle=angle_total*((float)step/6.0f); axis_z_rotation(rot,angle);
    conjugate(rotated,inv,rot,space,paired);
    identity(translation);
    for(int d=0;d<3;d++) translation[3][d]=((0.0f*rot[0][d]+0.0f*rot[1][d])+0.5f*rot[2][d])*(float)step;
    conjugate(translated,inv,translation,space,paired);
   }
   for(int seed=0;seed<7;seed++) {
    float co[3];memcpy(co,seeds[seed],sizeof(co));if(step) {apply(rotated,co);apply(translated,co);}
    printf("vertex %d %d %d %d %08x %08x %08x\n",scalar_inverse,paired,step,seed,bits(co[0]),bits(co[1]),bits(co[2]));
   }
  }
 }
}
