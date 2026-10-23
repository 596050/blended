// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: Apache-2.0
// Source-locked translations. See compatibility/heap-ports.json.
#![allow(non_snake_case,unused_mut,unused_parens)]
use crate::priority_heaps::{MinHeap,SimpleMinHeap,NodeId,InplacePriorityQueue,BlenderRng,array_randomize};
use core::cell::Cell;
const SIZE:i32=1024;
#[derive(Debug,Default)]pub struct Report{pub assertions:u32,pub failures:Vec<String>}
impl Report{
 pub fn check(&mut self,p:bool,expression:&str,line:u32){self.assertions+=1;if !p{self.failures.push(format!("line {line}: {expression}"));}}
 pub fn passed(&self)->bool{self.assertions>0&&self.failures.is_empty()}
}
macro_rules! eq {($r:expr,$a:expr,$b:expr)=>{{$r.check(($a)==($b),stringify!($a == $b),line!());}};}
macro_rules! le {($r:expr,$a:expr,$b:expr)=>{{$r.check(($a)<=($b),stringify!($a <= $b),line!());}};}
macro_rules! yes {($r:expr,$a:expr)=>{{$r.check($a,stringify!($a),line!());}};}
macro_rules! no {($r:expr,$a:expr)=>{{$r.check(!$a,stringify!(!$a),line!());}};}
// range_fl preserves the reverse write order of the original helper. The safe
// slice replaces a pointer that was decremented past the beginning after its last use.
fn range_fl(values:&mut [f32],size:i32){let mut i=size;while i>0{i-=1;values[i as usize]=i as f32;}}

// Original helper: source/blender/blenlib/tests/BLI_heap_test.cc:116
fn random_heap_helper(report:&mut Report,items_total:i32,random_seed:i32){

  let mut heap=MinHeap::<i32>::new();
  let mut values=vec![0.0_f32;items_total as usize];
  range_fl(&mut values, items_total);
  array_randomize(&mut values[..(items_total) as usize], (random_seed) as u32);
  for i in 0..items_total {
    heap.insert(values[(i) as usize], ((values[(i) as usize]) as i32) as i32);
  }
  for out_test in 0..items_total {
    eq!(report, out_test, heap.pop_min());
  }
  yes!(report, heap.is_empty());
  drop(heap);
  drop(values);

}

// Original helper: source/blender/blenlib/tests/BLI_heap_test.cc:167
fn random_heap_reinsert_helper(report:&mut Report,items_total:i32,random_seed:i32){

  let mut heap=MinHeap::<i32>::new();
  let mut nodes=vec![NodeId::INVALID;items_total as usize];
  for input in 0..items_total {
    nodes[(input) as usize] = heap.insert((input) as f32, (input) as i32);
  }
  array_randomize(&mut nodes[..(items_total) as usize], (random_seed) as u32);
  for i in 0..items_total {
    heap.update(nodes[(i) as usize], (i) as f32);
  }
  yes!(report, heap.is_valid());

  for out_test in 0..items_total {
    let node_top=heap.top();
    let mut out:f32=heap.node_value(node_top);
    eq!(report, out, heap.top_value());
    eq!(report, (out_test) as f32, out);
    heap.pop_min();
  }
  yes!(report, heap.is_empty());
  drop(heap);
  drop(nodes);

}

// source/blender/blenlib/tests/BLI_heap_test.cc:28
pub fn heap__Empty()->Report{let mut report=Report::default();

  

  let mut heap=MinHeap::<i32>::new();
  yes!(report, heap.is_empty());
  eq!(report, heap.len(), 0);
  drop(heap);

report
}

// source/blender/blenlib/tests/BLI_heap_test.cc:38
pub fn heap__One()->Report{let mut report=Report::default();

  
  let input = b"test\0".as_ptr();

  let mut heap=MinHeap::<*const u8>::new();

  heap.insert(0.0_f32, input);
  no!(report, heap.is_empty());
  eq!(report, heap.len(), 1);
  eq!(report, input, heap.pop_min());
  yes!(report, heap.is_empty());
  eq!(report, heap.len(), 0);
  drop(heap);

report
}

// source/blender/blenlib/tests/BLI_heap_test.cc:54
pub fn heap__Range()->Report{let mut report=Report::default();

  let mut items_total:i32=SIZE;
  let mut heap=MinHeap::<i32>::new();
  for input in 0..items_total {
    heap.insert((input) as f32, (input) as i32);
  }
  for out_test in 0..items_total {
    eq!(report, out_test, heap.pop_min());
  }
  yes!(report, heap.is_empty());
  drop(heap);

report
}

// source/blender/blenlib/tests/BLI_heap_test.cc:68
pub fn heap__RangeReverse()->Report{let mut report=Report::default();

  let mut items_total:i32=SIZE;
  let mut heap=MinHeap::<i32>::new();
  for input in 0..items_total {
    heap.insert((-input) as f32, (-input) as i32);
  }
  for out_test in (0..items_total).rev() {
    eq!(report, -out_test, heap.pop_min());
  }
  yes!(report, heap.is_empty());
  drop(heap);

report
}

// source/blender/blenlib/tests/BLI_heap_test.cc:82
pub fn heap__RangeRemove()->Report{let mut report=Report::default();

  let mut items_total:i32=SIZE;
  let mut heap=MinHeap::<i32>::new();
  let mut nodes=vec![NodeId::INVALID;items_total as usize];
  for input in 0..items_total {
    nodes[(input) as usize] = heap.insert((input) as f32, (input) as i32);
  }
  for i in (0..items_total).step_by(2) {
    heap.remove(nodes[(i) as usize]);
    nodes[(i) as usize] = NodeId::INVALID;
  }
  for out_test in (1..items_total).step_by(2) {
    eq!(report, out_test, heap.pop_min());
  }
  yes!(report, heap.is_empty());
  drop(heap);
  drop(nodes);

report
}

// source/blender/blenlib/tests/BLI_heap_test.cc:102
pub fn heap__Duplicates()->Report{let mut report=Report::default();

  let mut items_total:i32=SIZE;
  let mut heap=MinHeap::<i32>::new();
  for input in 0..items_total {
    heap.insert(1.0_f32, 0_i32);
  }
  for out_test in 0..items_total {
    eq!(report, 0, heap.pop_min());
  }
  yes!(report, heap.is_empty());
  drop(heap);

report
}

// source/blender/blenlib/tests/BLI_heap_test.cc:133
pub fn heap__Rand1()->Report{let mut report=Report::default();

  random_heap_helper(&mut report, 1, 1234);

report
}

// source/blender/blenlib/tests/BLI_heap_test.cc:137
pub fn heap__Rand2()->Report{let mut report=Report::default();

  random_heap_helper(&mut report, 2, 1234);

report
}

// source/blender/blenlib/tests/BLI_heap_test.cc:141
pub fn heap__Rand100()->Report{let mut report=Report::default();

  random_heap_helper(&mut report, 100, 4321);

report
}

// source/blender/blenlib/tests/BLI_heap_test.cc:146
pub fn heap__ReInsertSimple()->Report{let mut report=Report::default();

  let mut items_total:i32=SIZE;
  let mut heap=MinHeap::<i32>::new();
  let mut nodes=vec![NodeId::INVALID;items_total as usize];
  for input in 0..items_total {
    nodes[(input) as usize] = heap.insert((input) as f32, (input) as i32);
  }
  for i in 0..items_total {
    heap.update(nodes[(i) as usize], (items_total + i) as f32);
  }

  for out_test in 0..items_total {
    eq!(report, out_test, heap.pop_min());
  }

  yes!(report, heap.is_empty());
  drop(heap);
  drop(nodes);

report
}

// source/blender/blenlib/tests/BLI_heap_test.cc:192
pub fn heap__ReInsertRandom1()->Report{let mut report=Report::default();

  random_heap_reinsert_helper(&mut report, 1, 1234);

report
}

// source/blender/blenlib/tests/BLI_heap_test.cc:196
pub fn heap__ReInsertRandom2()->Report{let mut report=Report::default();

  random_heap_reinsert_helper(&mut report, 2, 1234);

report
}

// source/blender/blenlib/tests/BLI_heap_test.cc:200
pub fn heap__ReInsertRandom100()->Report{let mut report=Report::default();

  random_heap_reinsert_helper(&mut report, 100, 4321);

report
}

// source/blender/blenlib/tests/BLI_heap_test.cc:204
pub fn heap__ReInsertRandom1024()->Report{let mut report=Report::default();

  random_heap_reinsert_helper(&mut report, 1024, 9876);

report
}

// source/blender/blenlib/tests/BLI_heap_test.cc:208
pub fn heap__ReInsertRandom2048()->Report{let mut report=Report::default();

  random_heap_reinsert_helper(&mut report, 2048, 5321);

report
}

// Original helper: source/blender/blenlib/tests/BLI_heap_simple_test.cc:97
fn random_heapsimple_helper(report:&mut Report,items_total:i32,random_seed:i32){

  let mut heap=SimpleMinHeap::<i32>::new();
  let mut values=vec![0.0_f32;items_total as usize];
  range_fl(&mut values, items_total);
  array_randomize(&mut values[..(items_total) as usize], (random_seed) as u32);
  for i in 0..items_total {
    heap.insert(values[(i) as usize], ((values[(i) as usize]) as i32) as i32);
  }
  for out_test in 0..items_total {
    eq!(report, out_test, heap.pop_min());
  }
  yes!(report, heap.is_empty());
  drop(heap);
  drop(values);

}

// source/blender/blenlib/tests/BLI_heap_simple_test.cc:29
pub fn heap__SimpleEmpty()->Report{let mut report=Report::default();

  

  let mut heap=SimpleMinHeap::<i32>::new();
  yes!(report, heap.is_empty());
  eq!(report, heap.len(), 0);
  drop(heap);

report
}

// source/blender/blenlib/tests/BLI_heap_simple_test.cc:39
pub fn heap__SimpleOne()->Report{let mut report=Report::default();

  
  let input = b"test\0".as_ptr();

  let mut heap=SimpleMinHeap::<*const u8>::new();

  heap.insert(0.0_f32, input);
  no!(report, heap.is_empty());
  eq!(report, heap.len(), 1);
  eq!(report, input, heap.pop_min());
  yes!(report, heap.is_empty());
  eq!(report, heap.len(), 0);
  drop(heap);

report
}

// source/blender/blenlib/tests/BLI_heap_simple_test.cc:55
pub fn heap__SimpleRange()->Report{let mut report=Report::default();

  let mut items_total:i32=SIZE;
  let mut heap=SimpleMinHeap::<i32>::new();
  for input in 0..items_total {
    heap.insert((input) as f32, (input) as i32);
  }
  for out_test in 0..items_total {
    eq!(report, out_test, heap.pop_min());
  }
  yes!(report, heap.is_empty());
  drop(heap);

report
}

// source/blender/blenlib/tests/BLI_heap_simple_test.cc:69
pub fn heap__SimpleRangeReverse()->Report{let mut report=Report::default();

  let mut items_total:i32=SIZE;
  let mut heap=SimpleMinHeap::<i32>::new();
  for input in 0..items_total {
    heap.insert((-input) as f32, (-input) as i32);
  }
  for out_test in (0..items_total).rev() {
    eq!(report, -out_test, heap.pop_min());
  }
  yes!(report, heap.is_empty());
  drop(heap);

report
}

// source/blender/blenlib/tests/BLI_heap_simple_test.cc:83
pub fn heap__SimpleDuplicates()->Report{let mut report=Report::default();

  let mut items_total:i32=SIZE;
  let mut heap=SimpleMinHeap::<i32>::new();
  for input in 0..items_total {
    heap.insert(1.0_f32, 0_i32);
  }
  for out_test in 0..items_total {
    eq!(report, 0, heap.pop_min());
  }
  yes!(report, heap.is_empty());
  drop(heap);

report
}

// source/blender/blenlib/tests/BLI_heap_simple_test.cc:114
pub fn heap__SimpleRand1()->Report{let mut report=Report::default();

  random_heapsimple_helper(&mut report, 1, 1234);

report
}

// source/blender/blenlib/tests/BLI_heap_simple_test.cc:118
pub fn heap__SimpleRand2()->Report{let mut report=Report::default();

  random_heapsimple_helper(&mut report, 2, 1234);

report
}

// source/blender/blenlib/tests/BLI_heap_simple_test.cc:122
pub fn heap__SimpleRand100()->Report{let mut report=Report::default();

  random_heapsimple_helper(&mut report, 100, 4321);

report
}

// source/blender/blenlib/tests/BLI_inplace_priority_queue_test.cc:12
pub fn inplace_priority_queue__BuildSmall()->Report{let mut report=Report::default();

  let values:Vec<Cell<i32>>=vec![1, 5, 2, 8, 5, 6, 5, 4, 3, 6, 7, 3].into_iter().map(Cell::new).collect();
  let mut priority_queue=InplacePriorityQueue::new(&values);

  eq!(report, priority_queue.peek(), 8);
  eq!(report, priority_queue.pop(), 8);
  eq!(report, priority_queue.peek(), 7);
  eq!(report, priority_queue.pop(), 7);
  eq!(report, priority_queue.pop(), 6);
  eq!(report, priority_queue.pop(), 6);
  eq!(report, priority_queue.pop(), 5);

report
}

// source/blender/blenlib/tests/BLI_inplace_priority_queue_test.cc:26
pub fn inplace_priority_queue__DecreasePriority()->Report{let mut report=Report::default();

  let values:Vec<Cell<i32>>=vec![5, 2, 7, 4].into_iter().map(Cell::new).collect();
  let mut priority_queue=InplacePriorityQueue::new(&values);

  eq!(report, priority_queue.peek(), 7);
  values[(2) as usize].set(0);
  eq!(report, priority_queue.peek(), 0);
  priority_queue.priority_decreased((2) as usize);
  eq!(report, priority_queue.peek(), 5);

report
}

// source/blender/blenlib/tests/BLI_inplace_priority_queue_test.cc:38
pub fn inplace_priority_queue__IncreasePriority()->Report{let mut report=Report::default();

  let values:Vec<Cell<i32>>=vec![5, 2, 7, 4].into_iter().map(Cell::new).collect();
  let mut priority_queue=InplacePriorityQueue::new(&values);

  eq!(report, priority_queue.peek(), 7);
  values[(1) as usize].set(10);
  eq!(report, priority_queue.peek(), 7);
  priority_queue.priority_increased((1) as usize);
  eq!(report, priority_queue.peek(), 10);

report
}

// source/blender/blenlib/tests/BLI_inplace_priority_queue_test.cc:50
pub fn inplace_priority_queue__PopAll()->Report{let mut report=Report::default();

  let mut rng=BlenderRng::new(0);
  let mut values:Vec<Cell<i32>>=Vec::new();
  let mut amount:i32=1000;
  for i in 0..amount {
    values.push(Cell::new(rng.get_int32() % amount));
  }

  let mut priority_queue=InplacePriorityQueue::new(&values);

  let mut last_value:i32=amount;
  while !priority_queue.is_empty() {
    let mut value:i32=priority_queue.pop();
    le!(report, value, last_value);
    last_value = value;
  }

report
}

// source/blender/blenlib/tests/BLI_inplace_priority_queue_test.cc:69
pub fn inplace_priority_queue__ManyPriorityChanges()->Report{let mut report=Report::default();

  let mut rng=BlenderRng::new(0);
  let mut values:Vec<Cell<i32>>=Vec::new();
  let mut amount:i32=1000;
  for i in 0..amount {
    values.push(Cell::new(rng.get_int32() % amount));
  }

  let mut priority_queue=InplacePriorityQueue::new(&values);

  for i in 0..amount {
    let mut index:i32=rng.get_int32() % amount;
    let mut new_priority:i32=rng.get_int32() % amount;
    values[(index) as usize].set(new_priority);
    priority_queue.priority_changed((index) as usize);
  }

  let mut last_value:i32=amount;
  while !priority_queue.is_empty() {
    let mut value:i32=priority_queue.pop();
    le!(report, value, last_value);
    last_value = value;
  }

report
}

// source/blender/blenlib/tests/BLI_inplace_priority_queue_test.cc:95
pub fn inplace_priority_queue__IndicesAccess()->Report{let mut report=Report::default();

  let values:Vec<Cell<i32>>=vec![4, 6, 2, 4, 8, 1, 10, 2, 5].into_iter().map(Cell::new).collect();
  let mut priority_queue=InplacePriorityQueue::new(&values);

  eq!(report, priority_queue.active_indices().len(), 9);
  eq!(report, priority_queue.inactive_indices().len(), 0);
  eq!(report, priority_queue.all_indices().len(), 9);
  eq!(report, priority_queue.pop(), 10);
  eq!(report, priority_queue.active_indices().len(), 8);
  eq!(report, priority_queue.inactive_indices().len(), 1);
  eq!(report, values[priority_queue.inactive_indices()[0]].get(), 10);
  eq!(report, priority_queue.all_indices().len(), 9);
  eq!(report, priority_queue.pop(), 8);
  eq!(report, priority_queue.inactive_indices().len(), 2);
  eq!(report, values[priority_queue.inactive_indices()[0]].get(), 8);
  eq!(report, values[priority_queue.inactive_indices()[1]].get(), 10);
  eq!(report, priority_queue.all_indices().len(), 9);

report
}

pub const CASES:&[(&str,fn()->Report,u32)]=&[
("heap.Empty",heap__Empty,2),
("heap.One",heap__One,5),
("heap.Range",heap__Range,1025),
("heap.RangeReverse",heap__RangeReverse,1025),
("heap.RangeRemove",heap__RangeRemove,513),
("heap.Duplicates",heap__Duplicates,1025),
("heap.Rand1",heap__Rand1,2),
("heap.Rand2",heap__Rand2,3),
("heap.Rand100",heap__Rand100,101),
("heap.ReInsertSimple",heap__ReInsertSimple,1025),
("heap.ReInsertRandom1",heap__ReInsertRandom1,4),
("heap.ReInsertRandom2",heap__ReInsertRandom2,6),
("heap.ReInsertRandom100",heap__ReInsertRandom100,202),
("heap.ReInsertRandom1024",heap__ReInsertRandom1024,2050),
("heap.ReInsertRandom2048",heap__ReInsertRandom2048,4098),
("heap.SimpleEmpty",heap__SimpleEmpty,2),
("heap.SimpleOne",heap__SimpleOne,5),
("heap.SimpleRange",heap__SimpleRange,1025),
("heap.SimpleRangeReverse",heap__SimpleRangeReverse,1025),
("heap.SimpleDuplicates",heap__SimpleDuplicates,1025),
("heap.SimpleRand1",heap__SimpleRand1,2),
("heap.SimpleRand2",heap__SimpleRand2,3),
("heap.SimpleRand100",heap__SimpleRand100,101),
("inplace_priority_queue.BuildSmall",inplace_priority_queue__BuildSmall,7),
("inplace_priority_queue.DecreasePriority",inplace_priority_queue__DecreasePriority,3),
("inplace_priority_queue.IncreasePriority",inplace_priority_queue__IncreasePriority,3),
("inplace_priority_queue.PopAll",inplace_priority_queue__PopAll,1000),
("inplace_priority_queue.ManyPriorityChanges",inplace_priority_queue__ManyPriorityChanges,1000),
("inplace_priority_queue.IndicesAccess",inplace_priority_queue__IndicesAccess,13),
];
