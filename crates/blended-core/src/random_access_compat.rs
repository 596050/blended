// SPDX-FileCopyrightText: 2024 Blender Authors
// SPDX-License-Identifier: GPL-2.0-or-later
// Narrow compatibility implementation for the random-access iterator behavior
// exercised by BLI_random_access_iterator_mixin_test.cc.
#[derive(Clone,Copy)]
pub struct DoublingIterator<'a>{slice:&'a [i32],index:isize}
impl<'a> DoublingIterator<'a>{
 pub fn new(slice:&'a [i32])->Self{Self{slice,index:0}}
 pub fn offset(self,delta:isize)->Self{Self{slice:self.slice,index:self.index+delta}}
 pub fn value(self)->i32{assert!(self.index>=0&&(self.index as usize)<self.slice.len());self.slice[self.index as usize]*2}
 pub fn distance_to(self,other:Self)->isize{assert!(core::ptr::eq(self.slice.as_ptr(),other.slice.as_ptr()));other.index-self.index}
}
impl PartialEq for DoublingIterator<'_>{fn eq(&self,other:&Self)->bool{core::ptr::eq(self.slice.as_ptr(),other.slice.as_ptr())&&self.index==other.index}}
impl Eq for DoublingIterator<'_>{}
