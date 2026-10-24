// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: GPL-2.0-or-later
// Behavioural Rust adaptation of pinned BLI_span.hh (94363991...).
// Views borrow storage. Values are copied on access; no shared reference to
// Cell-backed elements escapes, so simultaneous readonly/mutable views remain
// sound. Raw-pointer fields keep these views !Send/!Sync. Native ABI and undefined
// out-of-allocation pointer arithmetic are not compatibility promises.
use core::{cell::Cell, marker::PhantomData, mem::size_of};

#[derive(Clone, Copy)]
pub struct Span<'a, T: Copy> {
    ptr: *const T,
    len: usize,
    _borrow: PhantomData<&'a Cell<T>>,
}
impl<'a, T: Copy> Span<'a, T> {
    pub const fn from_slice(values: &'a [T]) -> Self {
        Self { ptr: values.as_ptr(), len: values.len(), _borrow: PhantomData }
    }
    pub fn from_cells(values: &'a [Cell<T>]) -> Self {
        // Cell<T> has T's layout. We copy values without making a reference to T.
        Self { ptr: values.as_ptr().cast::<T>(), len: values.len(), _borrow: PhantomData }
    }
    pub const fn len(self) -> usize { self.len }
    pub const fn is_empty(self) -> bool { self.len == 0 }
    pub const fn data(self) -> *const T { self.ptr }
    pub const fn size_in_bytes(self) -> usize {
        match self.len.checked_mul(size_of::<T>()) {
            Some(n) => n,
            None => panic!("Span byte length overflow"),
        }
    }
    pub const fn at(self, index: usize) -> T {
        assert!(index < self.len, "Span index out of bounds");
        // SAFETY: constructors and slicing preserve a live borrowed allocation
        // with len initialized Copy elements. PlainBits casting permits unaligned
        // byte views; read_unaligned avoids constructing a misaligned reference.
        unsafe { self.ptr.add(index).read_unaligned() }
    }
    pub const fn slice(self, start: usize, len: usize) -> Self {
        assert!(start <= self.len && len <= self.len - start, "Span slice out of bounds");
        // SAFETY: start lies inside or exactly one past the borrowed allocation.
        Self { ptr: unsafe { self.ptr.add(start) }, len, _borrow: PhantomData }
    }
    pub fn slice_range(self, range: crate::data_structures::IndexRange) -> Self {
        assert!(range.start() >= 0 && range.size() >= 0);
        self.slice(range.start() as usize, range.size() as usize)
    }
    pub const fn slice_safe(self, start: usize, len: usize) -> Self {
        let start = if start < self.len { start } else { self.len };
        let remaining = self.len - start;
        self.slice(start, if len < remaining { len } else { remaining })
    }
    pub const fn drop_front(self, n: usize) -> Self {
        let start = if n < self.len { n } else { self.len };
        self.slice(start, self.len - start)
    }
    pub const fn drop_back(self, n: usize) -> Self {
        let removed = if n < self.len { n } else { self.len };
        self.slice(0, self.len - removed)
    }
    pub const fn take_front(self, n: usize) -> Self {
        self.slice(0, if n < self.len { n } else { self.len })
    }
    pub const fn take_back(self, n: usize) -> Self {
        let len = if n < self.len { n } else { self.len };
        self.slice(self.len - len, len)
    }
    pub const fn first(self) -> T { self.at(0) }
    pub const fn last(self, n: usize) -> T {
        assert!(n < self.len, "Empty or too-short span");
        self.at(self.len - n - 1)
    }
    pub fn contains_ptr(self, candidate: *const T) -> bool {
        let first = self.ptr as usize;
        let address = candidate as usize;
        let bytes = self.size_in_bytes();
        address >= first && address - first < bytes
    }
    pub fn iter(self) -> SpanIter<'a, T> { SpanIter { span: self, front: 0, back: self.len } }
    pub fn to_vec(self) -> Vec<T> { self.iter().collect() }
}
impl<'a, T: Copy + PartialEq> Span<'a, T> {
    pub fn contains(self, value: T) -> bool { self.iter().any(|v| v == value) }
    pub fn count(self, value: T) -> usize { self.iter().filter(|&v| v == value).count() }
}
impl Span<'_, i32> {
    // Specialised const comparisons avoid falsely claiming generic const-trait
    // support. The original constant-evaluation cases use precisely i32 values.
    pub const fn has_duplicates_linear(self) -> bool {
        let mut i = 0;
        while i < self.len {
            let mut j = i + 1;
            while j < self.len {
                if self.at(i) == self.at(j) { return true; }
                j += 1;
            }
            i += 1;
        }
        false
    }
    pub const fn first_index(self, value: i32) -> usize {
        let mut i = 0;
        while i < self.len {
            if self.at(i) == value { return i; }
            i += 1;
        }
        panic!("Value not present in span")
    }
}
impl<T: Copy + PartialEq> PartialEq for Span<'_, T> {
    fn eq(&self, other: &Self) -> bool {
        self.len == other.len && self.iter().zip(other.iter()).all(|(a, b)| a == b)
    }
}
impl<T: Copy + Eq> Eq for Span<'_, T> {}

pub struct SpanIter<'a, T: Copy> { span: Span<'a, T>, front: usize, back: usize }
impl<T: Copy> Iterator for SpanIter<'_, T> {
    type Item = T;
    fn next(&mut self) -> Option<T> {
        if self.front == self.back { return None; }
        let value = self.span.at(self.front);
        self.front += 1;
        Some(value)
    }
    fn size_hint(&self) -> (usize, Option<usize>) {
        let remaining = self.back - self.front;
        (remaining, Some(remaining))
    }
}
impl<T: Copy> DoubleEndedIterator for SpanIter<'_, T> {
    fn next_back(&mut self) -> Option<T> {
        if self.front == self.back { return None; }
        self.back -= 1;
        Some(self.span.at(self.back))
    }
}
impl<T: Copy> ExactSizeIterator for SpanIter<'_, T> {}
impl<T: Copy> core::iter::FusedIterator for SpanIter<'_, T> {}

#[derive(Clone, Copy)]
pub struct MutableSpan<'a, T: Copy> { cells: &'a [Cell<T>] }
impl<'a, T: Copy> MutableSpan<'a, T> {
    pub fn from_cells(cells: &'a [Cell<T>]) -> Self { Self { cells } }
    pub fn from_mut(values: &'a mut [T]) -> Self {
        Self { cells: Cell::from_mut(values).as_slice_of_cells() }
    }
    pub fn len(self) -> usize { self.cells.len() }
    pub fn is_empty(self) -> bool { self.cells.is_empty() }
    pub fn at(self, index: usize) -> T { self.cells[index].get() }
    pub fn set(self, index: usize, value: T) { self.cells[index].set(value); }
    pub fn as_span(self) -> Span<'a, T> { Span::from_cells(self.cells) }
    pub fn to_vec(self) -> Vec<T> { self.as_span().to_vec() }
    pub fn slice(self, start: usize, len: usize) -> Self {
        assert!(start <= self.len() && len <= self.len() - start, "Mutable span slice out of bounds");
        Self { cells: &self.cells[start..start + len] }
    }
    pub fn slice_safe(self, start: usize, len: usize) -> Self {
        let start = start.min(self.len());
        self.slice(start, len.min(self.len() - start))
    }
    pub fn drop_front(self, n: usize) -> Self {
        let start = n.min(self.len());
        self.slice(start, self.len() - start)
    }
    pub fn drop_back(self, n: usize) -> Self { self.slice(0, self.len().saturating_sub(n)) }
    pub fn take_front(self, n: usize) -> Self { self.slice(0, n.min(self.len())) }
    pub fn take_back(self, n: usize) -> Self {
        let len = n.min(self.len());
        self.slice(self.len() - len, len)
    }
    pub fn fill(self, value: T) { for cell in self.cells { cell.set(value); } }
    pub fn fill_indices(self, indices: &[usize], value: T) {
        for &index in indices { self.set(index, value); }
    }
    pub fn copy_from(self, other: Span<'_, T>) {
        assert_eq!(self.len(), other.len(), "Copy spans must have equal sizes");
        for i in 0..self.len() { self.set(i, other.at(i)); }
    }
    pub fn reverse(self) {
        for i in 0..self.len() / 2 {
            let j = self.len() - 1 - i;
            let a = self.at(i);
            self.set(i, self.at(j));
            self.set(j, a);
        }
    }
    pub fn iter(self) -> core::slice::Iter<'a, Cell<T>> { self.cells.iter() }
}
impl<T: Copy + PartialEq> MutableSpan<'_, T> {
    pub fn contains(self, value: T) -> bool { self.as_span().contains(value) }
}
impl<'a, T: Copy> From<MutableSpan<'a, T>> for Span<'a, T> {
    fn from(value: MutableSpan<'a, T>) -> Self { value.as_span() }
}
impl<'a, T> From<Span<'a, *mut T>> for Span<'a, *const T> {
    fn from(value: Span<'a, *mut T>) -> Self {
        Self { ptr: value.ptr.cast(), len: value.len, _borrow: PhantomData }
    }
}
impl<'a, T> From<MutableSpan<'a, *mut T>> for Span<'a, *const T> {
    fn from(value: MutableSpan<'a, *mut T>) -> Self { value.as_span().into() }
}
impl<'a, T> From<MutableSpan<'a, *mut T>> for MutableSpan<'a, *const T> {
    fn from(value: MutableSpan<'a, *mut T>) -> Self {
        // SAFETY: raw const/mut pointers have identical layout and validity. Cell
        // permits shared mutation of the slots. No pointee is dereferenced and
        // this grants no write access to any immutable pointee.
        let cells = unsafe {
            core::slice::from_raw_parts(value.cells.as_ptr().cast::<Cell<*const T>>(), value.len())
        };
        Self { cells }
    }
}

// Restrict safe byte casts to sealed, padding-free types with every bit pattern
// valid. References, bools, enums, structs with padding and zero-sized types are
// deliberately excluded. Unaligned reads are supported without creating &U.
mod sealed {
    pub trait Bits: Copy {}
    macro_rules! primitive {($($t:ty),*)=>{$(impl Bits for $t {})*};}
    primitive!(i8,u8,i16,u16,i32,u32,i64,u64,isize,usize,f32,f64);
    impl<T> Bits for *const T {}
    impl<T> Bits for *mut T {}
}
#[allow(private_bounds)]
impl<'a, T: sealed::Bits> Span<'a, T> {
    pub fn cast<U: sealed::Bits>(self) -> Span<'a, U> {
        let bytes = self.size_in_bytes();
        assert_eq!(bytes % size_of::<U>(), 0, "Span cast length is not a whole number of destination elements");
        Span { ptr: self.ptr.cast(), len: bytes / size_of::<U>(), _borrow: PhantomData }
    }
}
