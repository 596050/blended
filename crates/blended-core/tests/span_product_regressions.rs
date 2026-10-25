// SPDX-License-Identifier: GPL-3.0-or-later
// Supplemental product regressions, not translated Blender cases.
use blended_core::spans::{Span,MutableSpan};
use core::cell::Cell;
#[test]
fn readonly_and_mutable_views_observe_the_same_storage(){
    let data=[1,2,3,4].map(Cell::new);let mutable=MutableSpan::from_cells(&data);
    let read:Span<'_,i32>=mutable.into();mutable.set(1,20);assert_eq!(read.at(1),20);
    data[2].set(30);assert_eq!(mutable.at(2),30);assert_eq!(read.at(2),30);
    mutable.slice(1,2).fill(9);assert_eq!(read.to_vec(),vec![1,9,9,4]);
}
#[test]
fn interleaved_double_ended_iteration_never_duplicates_elements(){
    let data=[1,2,3,4,5];let mut iter=Span::from_slice(&data).iter();
    assert_eq!(iter.len(),5);assert_eq!(iter.next_back(),Some(5));assert_eq!(iter.next(),Some(1));
    assert_eq!(iter.next_back(),Some(4));assert_eq!(iter.next(),Some(2));assert_eq!(iter.len(),1);
    assert_eq!(iter.next_back(),Some(3));assert_eq!(iter.next(),None);assert_eq!(iter.next_back(),None);
}
#[test]
fn casts_keep_actual_bytes_and_support_unaligned_reads(){
    let bytes=[0_u8,0x12,0x34,0x56,0x78];let words=Span::from_slice(&bytes[1..]).cast::<u32>();
    assert_eq!(words.at(0),u32::from_ne_bytes([0x12,0x34,0x56,0x78]));
    assert_eq!(words.cast::<u8>().to_vec(),bytes[1..]);
}
#[test]
fn safe_oversize_views_do_not_form_out_of_allocation_pointers(){
    let a=[1,2,3];let span=Span::from_slice(&a);let empty=span.drop_front(usize::MAX);
    assert!(empty.is_empty());assert_eq!(empty.data(),a.as_ptr().wrapping_add(a.len()));
    assert!(span.slice_safe(usize::MAX,usize::MAX).is_empty());assert_eq!(span.take_back(usize::MAX).to_vec(),a);
}
#[test]
fn immutable_pointer_views_keep_slots_live_without_granting_pointee_mutation(){
    let mut a=1;let mut b=2;let ap=&mut a as *mut i32;let bp=&mut b as *mut i32;
    let slots=[Cell::new(ap)];let original=MutableSpan::from_cells(&slots);
    let read:Span<'_,*const i32>=original.into();let const_slots:MutableSpan<'_,*const i32>=original.into();
    original.set(0,bp);assert_eq!(read.at(0),bp);const_slots.set(0,ap);assert_eq!(slots[0].get(),ap);
    // This operational capability is a Rust extension to the original declared
    // trait, whose pinned C++ constructor fails when instantiated. The oracle
    // documents that discrepancy rather than calling it executable parity.
}
#[test]
fn borrowing_mutable_slice_writes_back_after_view_scope(){
    let mut data=[1,2,3,4];{
        let view=MutableSpan::from_mut(&mut data);view.reverse();view.slice(1,2).fill(-1);
    }
    assert_eq!(data,[4,-1,-1,1]);
}
#[test]
fn copying_subviews_leaves_other_storage_untouched(){
    let destination=[10,20,30,40,50].map(Cell::new);
    MutableSpan::from_cells(&destination).slice(1,3).copy_from(Span::from_slice(&[7,8,9]));
    assert_eq!(destination.map(|v|v.get()),[10,7,8,9,50]);
}
