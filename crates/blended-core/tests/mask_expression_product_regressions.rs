// SPDX-License-Identifier: GPL-3.0-or-later
// Supplemental product tests, not translated upstream Blender cases.
use blended_core::data_structures::IndexRange;
use blended_core::mask_expressions::{ExprBuilder,IndexMask};
fn selected(bits:u32)->IndexMask{IndexMask::from_indices((0..6).filter(|i|bits&(1<<i)!=0).map(i64::from))}
#[test]
fn canonical_intervals_merge_duplicates_overlap_and_adjacency(){
 let mask=IndexMask::from_ranges([IndexRange::new(7,3),IndexRange::new(2,2),IndexRange::new(3,5),IndexRange::new(99,0)]);
 assert_eq!(mask.canonical_ranges(),&[[2,10]]);assert_eq!(mask.len(),8);
 assert_eq!(mask,IndexMask::from_indices([2,3,3,4,5,6,7,8,9]));
 assert_eq!(mask.iter().collect::<Vec<_>>(),(2..10).collect::<Vec<_>>());
}
#[test]
fn large_ranges_remain_compact_without_losing_64_bit_indices(){
 let first=1_i64<<40;let length=1_i64<<35;
 let mask=IndexMask::from_range(IndexRange::new(first,length));
 let cut=IndexMask::from_range(IndexRange::new(first+5,length-10));
 let result=mask.difference(&cut);
 assert_eq!(result.canonical_ranges(),&[[first,first+5],[first+length-5,first+length]]);
 assert_eq!(result.len(),10);assert!(!result.contains(first-1));assert!(!result.contains(first+length));
 assert!(result.contains(first+length-1));assert!(!result.contains(i64::MAX));
}
#[test]
fn complement_respects_sparse_universe_and_operand_direction(){
 let a=IndexMask::from_indices([3,8,9,40]);let universe=IndexMask::from_indices([1,3,4,8,20]);
 assert_eq!(a.complement(&universe).iter().collect::<Vec<_>>(),vec![1,4,20]);
 assert_eq!(universe.complement(&a).iter().collect::<Vec<_>>(),vec![9,40]);
 assert_eq!(a.complement_range(IndexRange::new(7,4)).iter().collect::<Vec<_>>(),vec![7,10]);
}
#[test]
fn predicate_visits_original_indices_and_stride_counts_selected_items(){
 let mut visited=Vec::new();let mask=IndexMask::from_predicate(IndexRange::new(40,7),|i|{visited.push(i);i%2==0});
 assert_eq!(visited,vec![40,41,42,43,44,45,46]);assert_eq!(mask.iter().collect::<Vec<_>>(),vec![40,42,44,46]);
 assert_eq!(IndexMask::from_every_nth(3,4,40).iter().collect::<Vec<_>>(),vec![40,43,46,49]);
 assert_eq!(IndexMask::from_bools(&[false,true,true,false,true]).iter().collect::<Vec<_>>(),vec![1,2,4]);
}
#[test]
fn all_six_bit_subsets_agree_with_independent_boolean_algebra(){
 let builder=ExprBuilder::new();
 for abits in 0_u32..64{for bbits in 0_u32..64{
  let a=selected(abits);let b=selected(bbits);let c=selected((abits*17)^(bbits*31));
  assert_eq!(a.union(&b),selected(abits|bbits));assert_eq!(a.intersection(&b),selected(abits&bbits));
  assert_eq!(a.difference(&b),selected(abits&!bbits));
  let result=builder.subtract(builder.merge([(&a).into(),(&b).into()]),[builder.intersect([(&b).into(),(&c).into()])]).evaluate();
  assert_eq!(result,selected((abits|bbits)&!(bbits&((abits*17)^(bbits*31)))));
 }}
}
#[test]
fn nested_range_terms_leave_borrowed_sources_unchanged(){
 let source=IndexMask::from_indices([4,7,8,20]);let saved=source.clone();let builder=ExprBuilder::new();
 let expression=builder.subtract(builder.merge([(&source).into(),IndexRange::new(5,5).into()]),[IndexRange::new(7,2).into()]);
 assert_eq!(expression.evaluate().iter().collect::<Vec<_>>(),vec![4,5,6,9,20]);
 assert_eq!(source,saved);assert_eq!(expression.evaluate(),expression.evaluate());
}
#[test]
fn empty_sets_and_subtraction_across_several_runs_keep_boundaries(){
 let empty=IndexMask::default();let source=IndexMask::from_ranges([IndexRange::new(2,3),IndexRange::new(8,4),IndexRange::new(20,5)]);
 assert_eq!(source.union(&empty),source);assert!(source.intersection(&empty).is_empty());assert_eq!(source.difference(&empty),source);
 let cut=IndexMask::from_ranges([IndexRange::new(4,18),IndexRange::new(23,1)]);
 assert_eq!(source.difference(&cut).canonical_ranges(),&[[2,4],[22,23],[24,25]]);
 assert_eq!(empty.to_range(),Some(IndexRange::empty()));assert_eq!(empty.segments_num(),0);
 assert_eq!(IndexMask::from_indices([3,5,6]).segments_num(),1);
 assert!(ExprBuilder::new().merge([]).evaluate().is_empty());
}
