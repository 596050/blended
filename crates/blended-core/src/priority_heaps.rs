// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: GPL-2.0-or-later
// Rust adaptation of pinned BLI_heap.cc, BLI_heap_simple.cc,
// BLI_inplace_priority_queue.hh, BLI_rand.hh and rand.cc.
// Reference: 94363991e7dcf39e2d70614aa002ab6f67764a5d.
// Stable checked indices replace node addresses; shared Cells preserve borrowed
// externally mutable priorities. No allocator-layout or performance parity claim.
use core::cell::Cell;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct NodeId(usize);
impl NodeId { pub const INVALID: Self = Self(usize::MAX); }

#[derive(Clone, Copy)]
struct Node<T: Copy> { priority: f32, payload: T, index: usize, alive: bool }

/// Min-heap with checked stable handles. Removed handles are never reused.
/// Methods that require a non-empty heap or live handle assert that precondition.
pub struct MinHeap<T: Copy> { nodes: Vec<Node<T>>, tree: Vec<usize> }
impl<T: Copy> Default for MinHeap<T> { fn default()->Self { Self::new() } }
impl<T: Copy> MinHeap<T> {
    pub fn new()->Self { Self {nodes:Vec::new(),tree:Vec::new()} }
    pub fn len(&self)->usize { self.tree.len() }
    pub fn is_empty(&self)->bool { self.tree.is_empty() }
    fn node(&self,id:NodeId)->&Node<T> {
        let node=self.nodes.get(id.0).expect("Heap handle out of bounds");
        assert!(node.alive,"Removed heap handle"); node
    }
    fn swap(&mut self,a:usize,b:usize) {
        self.tree.swap(a,b);
        self.nodes[self.tree[a]].index=a;
        self.nodes[self.tree[b]].index=b;
    }
    fn up(&mut self,mut i:usize) {
        while i>0 {
            let p=(i-1)/2;
            // The original handle-based heap swaps equal-priority ancestors.
            if self.nodes[self.tree[p]].priority < self.nodes[self.tree[i]].priority {break;}
            self.swap(p,i); i=p;
        }
    }
    fn down(&mut self,mut i:usize) {
        loop {
            let l=i*2+1; let r=l+1; let mut smallest=i;
            if l<self.len() && self.nodes[self.tree[l]].priority<self.nodes[self.tree[smallest]].priority {smallest=l;}
            if r<self.len() && self.nodes[self.tree[r]].priority<self.nodes[self.tree[smallest]].priority {smallest=r;}
            if smallest==i {break;}
            self.swap(i,smallest); i=smallest;
        }
    }
    pub fn insert(&mut self,priority:f32,payload:T)->NodeId {
        let id=NodeId(self.nodes.len()); let index=self.len();
        self.nodes.push(Node{priority,payload,index,alive:true});
        self.tree.push(id.0); self.up(index); id
    }
    pub fn top(&self)->NodeId { NodeId(*self.tree.first().expect("Empty heap")) }
    pub fn top_value(&self)->f32 { self.node_value(self.top()) }
    pub fn node_value(&self,id:NodeId)->f32 { self.node(id).priority }
    pub fn pop_min(&mut self)->T {
        let id=self.top(); let payload=self.node(id).payload; let last=self.len()-1;
        if last>0 {self.swap(0,last);}
        self.tree.pop(); self.nodes[id.0].alive=false;
        if !self.is_empty() {self.down(0);}
        payload
    }
    pub fn remove(&mut self,id:NodeId) {
        let mut i=self.node(id).index;
        while i>0 {let p=(i-1)/2;self.swap(p,i);i=p;}
        self.pop_min();
    }
    pub fn update(&mut self,id:NodeId,priority:f32) {
        let old=self.node(id).priority; let index=self.node(id).index;
        // Equal values, including +/-0, and NaN follow the pinned comparison
        // branches. Do not replace with total_cmp or a different tie policy.
        if priority<old {self.nodes[id.0].priority=priority;self.up(index);}
        else if priority>old {self.nodes[id.0].priority=priority;self.down(index);}
    }
    pub fn is_valid(&self)->bool {
        self.tree.iter().enumerate().all(|(i,&id)| {
            let node=&self.nodes[id];
            node.alive && node.index==i && [i*2+1,i*2+2].into_iter().all(|j|
                j>=self.len() || !(self.nodes[self.tree[j]].priority<node.priority))
        })
    }
}

/// Contiguous min-heap without handles. The original simple heap's equal-key
/// insertion policy differs from MinHeap, so this is not an alias to that type.
pub struct SimpleMinHeap<T:Copy> { tree:Vec<(f32,T)> }
impl<T:Copy> Default for SimpleMinHeap<T> {fn default()->Self{Self::new()}}
impl<T:Copy> SimpleMinHeap<T> {
    pub fn new()->Self {Self{tree:Vec::new()}}
    pub fn len(&self)->usize{self.tree.len()}
    pub fn is_empty(&self)->bool{self.tree.is_empty()}
    pub fn insert(&mut self,priority:f32,payload:T) {
        let mut i=self.len(); self.tree.push((priority,payload));
        while i>0 {
            let p=(i-1)/2;
            if priority>=self.tree[p].0 {break;}
            self.tree[i]=self.tree[p];i=p;
        }
        self.tree[i]=(priority,payload);
    }
    pub fn pop_min(&mut self)->T {
        let payload=self.tree.first().expect("Empty simple heap").1;
        let active=self.tree.pop().unwrap();
        if !self.is_empty() {
            let mut i=0;self.tree[0]=active;
            loop {
                let l=i*2+1;let r=l+1;let mut smallest=i;
                if l<self.len() && self.tree[l].0<active.0 {smallest=l;}
                if r<self.len() && self.tree[r].0<self.tree[smallest].0 {smallest=r;}
                if smallest==i {break;}
                self.tree[i]=self.tree[smallest]; i=smallest;self.tree[i]=active;
            }
            self.tree[i]=active;
        }
        payload
    }
}

/// Compatibility implementation of the pinned queue, not a snapshot of values.
/// Cells permit external edits without an unsafe shared mutable reference.
pub struct InplacePriorityQueue<'a> {
    data:&'a [Cell<i32>], heap_to_orig:Vec<usize>, orig_to_heap:Vec<usize>, heap_size:usize,
}
impl<'a> InplacePriorityQueue<'a> {
    pub fn new(data:&'a [Cell<i32>])->Self {
        let n=data.len();
        let mut q=Self{data,heap_to_orig:(0..n).collect(),orig_to_heap:(0..n).collect(),heap_size:0};
        q.rebuild();q
    }
    fn higher(&self,a:usize,b:usize)->bool {
        self.data[self.heap_to_orig[a]].get()>self.data[self.heap_to_orig[b]].get()
    }
    fn swap(&mut self,a:usize,b:usize) {
        self.heap_to_orig.swap(a,b);
        self.orig_to_heap[self.heap_to_orig[a]]=a;self.orig_to_heap[self.heap_to_orig[b]]=b;
    }
    fn heapify(&mut self,mut parent:usize,size:usize) {
        loop {
            let left=parent*2+1;let right=left+1;let mut max=parent;
            if left<size && self.higher(left,max) {max=left;}
            if right<size && self.higher(right,max) {max=right;}
            if max==parent {break;}
            self.swap(parent,max); parent=max;
        }
    }
    pub fn rebuild(&mut self) {
        let size=self.data.len();
        if size>1 {for i in (0..=(size-2)/2).rev(){self.heapify(i,size);}}
        self.heap_size=size;
    }
    pub fn is_empty(&self)->bool{self.heap_size==0}
    pub fn len(&self)->usize{self.heap_size}
    pub fn peek_index(&self)->usize{assert!(!self.is_empty(),"Empty priority queue");self.heap_to_orig[0]}
    pub fn peek(&self)->i32{self.data[self.peek_index()].get()}
    pub fn pop_index(&mut self)->usize {
        let top=self.peek_index();self.heap_size-=1;
        // Exact pinned behaviour: no swap when the new size is one. This can
        // repeat the penultimate index at the final pop. Keep visible rather
        // than silently fixing the reference semantics during a test port.
        if self.heap_size>1 {self.swap(0,self.heap_size);self.heapify(0,self.heap_size);}
        top
    }
    pub fn pop(&mut self)->i32{let index=self.pop_index();self.data[index].get()}
    pub fn priority_decreased(&mut self,index:usize) {
        let heap_index=self.orig_to_heap[index];
        if heap_index<self.heap_size {self.heapify(heap_index,self.heap_size);}
    }
    pub fn priority_increased(&mut self,index:usize) {
        let mut current=self.orig_to_heap[index];if current>=self.heap_size{return;}
        while current>0 {
            let parent=(current-1)/2;
            if self.higher(parent,current){break;}
            self.swap(current,parent);current=parent;
        }
    }
    pub fn priority_changed(&mut self,index:usize){self.priority_increased(index);self.priority_decreased(index);}
    pub fn active_indices(&self)->&[usize]{&self.heap_to_orig[..self.heap_size]}
    pub fn inactive_indices(&self)->&[usize]{&self.heap_to_orig[self.heap_size..]}
    pub fn all_indices(&self)->&[usize]{&self.heap_to_orig}
}

/// Exact 48-bit integer generator used by the pinned BLI test fixtures.
pub struct BlenderRng { state:u64 }
impl BlenderRng {
    pub fn new(seed:u32)->Self{Self{state:((seed as u64)<<16)|0x330e}}
    pub fn get_int32(&mut self)->i32 {
        self.state=self.state.wrapping_mul(0x5deece66d).wrapping_add(0xb)&0x0000ffffffffffff;
        (self.state>>17) as i32
    }
}
/// Preserve BLI_array_randomize's actual shuffle, not a substituted standard
/// distribution: descending positions, a fixed full-array modulus on every draw.
pub fn array_randomize<T>(values:&mut [T],seed:u32) {
    let n=values.len();if n<=1{return;}
    assert!(n<=u32::MAX as usize,"Original shuffle size is uint32");
    let mut rng=BlenderRng::new(seed);
    for i in (0..n).rev(){let j=rng.get_int32() as usize%n;if i!=j{values.swap(i,j);}}
}
