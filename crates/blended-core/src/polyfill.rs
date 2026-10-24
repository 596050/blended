// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: GPL-2.0-or-later
// Adapted from pinned polyfill_2d.cc and polyfill_2d_beautify.cc, revision
// 94363991e7dcf39e2d70614aa002ab6f67764a5d. The original ear-clipping algorithm
// credits LIBGDX's Apache-2.0 implementation (2013-11-28).
// Safe indexed storage replaces circular pointers and arenas; no ABI/allocation
// or performance-parity claim. Finite single-boundary polygons only.
use crate::priority_heaps::{MinHeap,NodeId};
const NONE:usize=usize::MAX;
type Point=[f32;2];
fn cross(a:Point,b:Point,c:Point)->f32{(a[0]-b[0])*(b[1]-c[1])+(a[1]-b[1])*(c[0]-b[0])}
fn cross_polygon(points:&[Point])->f32{
    let mut previous=points[points.len()-1];let mut sum=0.0_f32;
    for &p in points{sum+=(previous[0]-p[0])*(p[1]+previous[1]);previous=p;}sum
}
fn sign(a:Point,b:Point,c:Point)->i8{
    let d2=[b[0]-c[0],b[1]-c[1]];let d3=[a[0]-c[0],a[1]-c[1]];
    let value=d2[0]*d3[1]-d3[0]*d2[1];
    if value>0.0{1}else if value==0.0{0}else{-1}
}
fn validate(points:&[Point]){
    assert!(points.len()>=3 && points.len()<=u32::MAX as usize,"Polygon length outside index range");
    assert!(points.iter().flatten().all(|x|x.is_finite()),"Non-finite coordinates are outside the compatibility contract");
}
#[derive(Clone,Copy)]struct Ring{next:usize,prev:usize,index:usize,sign:i8,dirty:bool,cached:usize}
#[derive(Clone,Copy)]struct KNode{neg:usize,pos:usize,index:usize,axis:usize,parent:usize,removed:bool}
struct KTree{nodes:Vec<KNode>,map:Vec<usize>,root:usize,live:usize}
struct TriangleQuery{indices:[usize;3],edges:[Point;3],constants:[f32;3],min:Point,max:Point,center:Point}
impl TriangleQuery{
    fn new(points:&[Point],indices:[usize;3])->Self{
        let vs=indices.map(|i|points[i]);
        let edges=core::array::from_fn(|i|[vs[(i+1)%3][0]-vs[i][0],vs[(i+1)%3][1]-vs[i][1]]);
        let constants=core::array::from_fn(|i|edges[i][0]*vs[i][1]-vs[i][0]*edges[i][1]);
        Self{indices,edges,constants,min:core::array::from_fn(|i|vs[0][i].min(vs[1][i]).min(vs[2][i])),max:core::array::from_fn(|i|vs[0][i].max(vs[1][i]).max(vs[2][i])),center:core::array::from_fn(|i|(vs[0][i]+vs[1][i]+vs[2][i])*(1.0_f32/3.0_f32))}
    }
    fn contains(&self,p:Point)->bool{
        [1,2,0].into_iter().all(|i|self.edges[i][1]*p[0]-self.edges[i][0]*p[1]+self.constants[i]>=0.0)
    }
}
impl KTree{
    fn new(points:&[Point],ring:&[Ring])->Self{
        let nodes=ring.iter().filter(|r|r.sign!=1).map(|r|KNode{neg:NONE,pos:NONE,index:r.index,axis:0,parent:NONE,removed:false}).collect::<Vec<_>>();
        let live=nodes.len();let mut result=Self{nodes,map:vec![NONE;points.len()],root:NONE,live};
        result.root=result.balance(points,0,live,0);
        for i in 0..live{let n=result.nodes[i];if n.neg!=NONE{result.nodes[n.neg].parent=i;}if n.pos!=NONE{result.nodes[n.pos].parent=i;}result.map[n.index]=i;}
        result
    }
    fn balance(&mut self,points:&[Point],offset:usize,len:usize,axis:usize)->usize{
        if len==0{return NONE;}if len==1{return offset;}
        let median=len/2;let mut neg=0_usize;let mut pos=len-1;
        while pos>neg{
            let coordinate=points[self.nodes[offset+pos].index][axis];
            let mut i=neg as isize-1;let mut j=pos;
            loop{
                loop{i+=1;if !(points[self.nodes[offset+i as usize].index][axis]<coordinate){break;}}
                loop{j-=1;if !(points[self.nodes[offset+j].index][axis]>coordinate && j>neg){break;}}
                if i as usize>=j{break;}
                // All metadata in this not-yet-balanced subrange is still initial.
                self.nodes.swap(offset+i as usize,offset+j);
            }
            let i=i as usize;self.nodes.swap(offset+i,offset+pos);
            if i>=median{pos=i-1;}if i<=median{neg=i+1;}
        }
        let center=offset+median;self.nodes[center].axis=axis;
        self.nodes[center].neg=self.balance(points,offset,median,1-axis);
        self.nodes[center].pos=self.balance(points,center+1,len-median-1,1-axis);center
    }
    fn remove(&mut self,index:usize){
        let mut i=self.map[index];if i==NONE{return;}self.map[index]=NONE;self.live-=1;self.nodes[i].removed=true;
        while self.nodes[i].parent!=NONE{
            let n=self.nodes[i];let child=if n.neg==NONE{n.pos}else if n.pos==NONE{n.neg}else{break};let parent=n.parent;
            if self.nodes[parent].neg==i{self.nodes[parent].neg=child;}else{assert_eq!(self.nodes[parent].pos,i);self.nodes[parent].pos=child;}
            if child!=NONE{self.nodes[child].parent=parent;}
            if !self.nodes[parent].removed{break;}i=parent;
        }
    }
    fn find(&self,points:&[Point],query:&TriangleQuery,i:usize)->usize{
        if i==NONE{return NONE;}let node=self.nodes[i];let co=points[node.index];
        if !node.removed && query.contains(co) && !query.indices.contains(&node.index){return node.index;}
        let neg=if node.neg!=NONE && co[node.axis]>=query.min[node.axis]{node.neg}else{NONE};
        let pos=if node.pos!=NONE && co[node.axis]<=query.max[node.axis]{node.pos}else{NONE};
        let order=if query.center[node.axis]>co[node.axis]{[pos,neg]}else{[neg,pos]};
        for child in order{let hit=self.find(points,query,child);if hit!=NONE{return hit;}}NONE
    }
    fn single(&self,points:&[Point],query:&TriangleQuery,index:usize)->bool{
        self.map[index]!=NONE && !query.indices.contains(&index) && query.contains(points[index])
    }
}

/// Triangulate a single polygon. `coords_sign` is -1/0/1 with zero auto-detecting
/// winding, matching the pinned API. Degenerate/self-crossing inputs get a filled
/// index triangulation but cannot be promised a non-overlapping geometric fill.
pub fn triangulate_into(points:&[Point],mut coords_sign:i32,output:&mut [[u32;3]]){
    validate(points);let n=points.len();assert_eq!(output.len(),n-2);assert!((-1..=1).contains(&coords_sign));
    if coords_sign==0{coords_sign=if cross_polygon(points)<=0.0{1}else{-1};}
    let mut ring=(0..n).map(|i|Ring{next:(i+1)%n,prev:(i+n-1)%n,index:if coords_sign==1{i}else{n-1-i},sign:0,dirty:false,cached:NONE}).collect::<Vec<_>>();
    for i in 0..n{ring[i].sign=sign(points[ring[ring[i].prev].index],points[ring[i].index],points[ring[ring[i].next].index]);}
    let mut tree=KTree::new(points,&ring);let mut concave=tree.live;let mut remaining=n;let mut head=0;let mut initial=0;let mut reverse=false;let mut written=0;
    while remaining>3{
        let mut found=NONE;
        'passes:for accept in [1_i8,0_i8]{
            let mut candidate=initial;
            for _ in 0..remaining{
                let r=ring[candidate];
                let valid=if concave==0{true}else if r.sign!=accept{false}else{
                    let q=TriangleQuery::new(points,[r.index,ring[r.next].index,ring[r.prev].index]);
                    let cached_blocks=r.cached!=NONE && if !r.dirty{tree.map[r.cached]!=NONE}else{tree.single(points,&q,r.cached)};
                    if cached_blocks{if r.dirty{ring[candidate].dirty=false;}false}else{
                        let hit=tree.find(points,&q,tree.root);
                        if hit!=NONE{ring[candidate].cached=hit;ring[candidate].dirty=false;false}else{true}
                    }
                };
                if valid{found=candidate;break 'passes;}
                candidate=if reverse{r.prev}else{r.next};
            }
        }
        if found==NONE{
            let mut candidate=initial;
            for _ in 0..remaining{if ring[candidate].sign!=-1{break;}candidate=ring[candidate].next;}
            found=candidate;
        }
        let ear=ring[found];let previous=ear.prev;let next=ear.next;
        if ear.sign!=1{concave-=1;}
        output[written]=[ring[previous].index as u32,ear.index as u32,ring[next].index as u32];written+=1;
        if tree.live>0{tree.remove(ear.index);}
        ring[next].prev=previous;ring[previous].next=next;if head==found{head=next;}remaining-=1;
        ring[previous].dirty=true;ring[next].dirty=true;
        for neighbor in [previous,next]{
            if ring[neighbor].sign!=1{
                let r=ring[neighbor];ring[neighbor].sign=sign(points[ring[r.prev].index],points[r.index],points[ring[r.next].index]);
                if ring[neighbor].sign==1{concave-=1;tree.remove(r.index);}
            }
        }
        initial=if reverse{ring[previous].prev}else{ring[next].next};
        if ring[initial].sign!=1{initial=if reverse{ring[initial].prev}else{ring[initial].next};reverse=!reverse;}
    }
    output[written]=[ring[head].index as u32,ring[ring[head].next].index as u32,ring[ring[ring[head].next].next].index as u32];
}
pub fn triangulate(points:&[Point])->Vec<[u32;3]>{validate(points);let mut tris=vec![[u32::MAX;3];points.len()-2];triangulate_into(points,0,&mut tris);tris}

#[derive(Clone,Copy)]struct HalfEdge{v:usize,next:usize,radial:usize,base:usize}
fn length(a:Point,b:Point)->f32{let x=a[0]-b[0];let y=a[1]-b[1];(x*x+y*y).sqrt()}
/// Original area/perimeter rotation cost. Returns maximum finite float when the
/// proposed replacement is inadmissible, negative maximum for forced repair.
pub fn rotation_cost(v1:Point,v2:Point,v3:Point,v4:Point,lock_degenerate:bool)->(f32,f32){
    let a234=cross(v2,v3,v4);let a241=cross(v2,v4,v1);let a123=cross(v1,v2,v3);let a134=cross(v1,v3,v4);
    let area=(a234.abs()+a241.abs()+a123.abs()+a134.abs())/8.0_f32;
    if (a123>=0.0)!=(a134>=0.0) || a123.abs()<=1e-12_f32 || a134.abs()<=1e-12_f32{return(f32::MAX,area);}
    if (a234>=0.0)!=(a241>=0.0){return(if lock_degenerate{f32::MAX}else{-f32::MAX},area);}
    if a234.abs()<=1e-12_f32 || a241.abs()<=1e-12_f32{return(-f32::MAX,area);}
    let l12=length(v1,v2);let l23=length(v2,v3);let l34=length(v3,v4);let l41=length(v4,v1);let l13=length(v1,v3);let l24=length(v2,v4);
    let old=a234.abs()/(l23+l34+l24)+a241.abs()/(l41+l12+l24);
    let new=a123.abs()/(l12+l23+l13)+a134.abs()/(l34+l41+l13);
    (old-new,area)
}
fn edge_cost(points:&[Point],edges:&[HalfEdge],a:usize)->(f32,f32){
    let b=edges[a].radial;let oa=edges[edges[a].next].next;let ob=edges[edges[b].next].next;
    rotation_cost(points[edges[oa].v],points[edges[a].v],points[edges[ob].v],points[edges[b].v],false)
}
fn rotate(edges:&mut[HalfEdge],a:usize){
    let b=edges[a].radial;let a1=edges[a].next;let a2=edges[a1].next;let b1=edges[b].next;let b2=edges[b1].next;
    edges[a].next=a2;edges[a1].next=b;edges[a2].next=b1;edges[b].next=b2;edges[b1].next=a;edges[b2].next=a1;
    edges[a].v=edges[b2].v;edges[b].v=edges[a2].v;
}

/// Improve the provided index triangulation through the pinned half-edge
/// rotations and heap tie policy. Requires n-2 triangles and exactly paired
/// internal edges, as the original caller contract does.
pub fn beautify(points:&[Point],tris:&mut [[u32;3]]){
    validate(points);let n=points.len();assert_eq!(tris.len(),n-2);
    let mut edges=vec![HalfEdge{v:NONE,next:NONE,radial:NONE,base:NONE};tris.len()*3];let mut ordered=Vec::new();
    for (i,tri) in tris.iter().enumerate(){
        for current in 0..3{
            let previous=(current+2)%3;let index=i*3+previous;let a=tri[previous] as usize;let b=tri[current] as usize;
            assert!(a<n&&b<n&&a!=b,"Invalid triangulation edge");
            edges[index].v=a;edges[index].next=i*3+current;
            let (lo,hi)=if a<b{(a,b)}else{(b,a)};
            if !(lo+1==hi || (lo==0&&hi==n-1)){ordered.push((lo,hi,index));}
        }
    }
    assert_eq!(ordered.len(),2*(n-3),"Internal edge count differs from the original precondition");ordered.sort_unstable();
    for (base,pair) in ordered.chunks_exact(2).enumerate(){
        assert_eq!((pair[0].0,pair[0].1),(pair[1].0,pair[1].1),"Unpaired internal edge");let a=pair[0].2;let b=pair[1].2;
        edges[a].radial=b;edges[b].radial=a;edges[a].base=base;edges[b].base=base;
    }
    let mut heap=MinHeap::<usize>::new();let mut handles:Vec<Option<NodeId>>=vec![None;n-3];let mut payload=vec![NONE;n-3];
    // Base indices are stable heap payloads; a side table retains the most recent
    // half-edge address, including updates from the opposite radial side.
    for i in 0..edges.len(){if edges[i].radial<i{let base=edges[i].base;let cost=edge_cost(points,&edges,i).0;if cost<0.0{handles[base]=Some(heap.insert(cost,base));payload[base]=i;}}}
    while !heap.is_empty(){
        let base=heap.pop_min();handles[base]=None;let a=payload[base];rotate(&mut edges,a);
        let a1=edges[a].next;let a2=edges[a1].next;let b=edges[a].radial;let b1=edges[b].next;let b2=edges[b1].next;
        for e in [a1,a2,b1,b2]{
            let base=edges[e].base;if base==NONE{continue;}let(cost,area)=edge_cost(points,&edges,e);
            if cost < -1e-6_f32*area.max(1.0){
                if let Some(handle)=handles[base]{heap.update(handle,cost);}else{handles[base]=Some(heap.insert(cost,base));}
                payload[base]=e;
            }else if let Some(handle)=handles[base].take(){heap.remove(handle);}
        }
    }
    let mut count=0;
    for i in 0..edges.len(){if edges[i].v!=NONE{let mut e=i;let mut tri=[0;3];for value in &mut tri{*value=edges[e].v as u32;edges[e].v=NONE;e=edges[e].next;}tris[count]=tri;count+=1;}}
    assert_eq!(count,tris.len());
}
