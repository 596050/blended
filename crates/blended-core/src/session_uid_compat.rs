// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: GPL-2.0-or-later
// Session-scoped monotonically increasing UID adapted from pinned session_uid.cc.
#[derive(Clone,Copy,Debug,PartialEq,Eq,PartialOrd,Ord,Hash)]
pub struct SessionUID(u64);
impl SessionUID{pub const fn is_generated(self)->bool{self.0!=0}pub const fn value(self)->u64{self.0}}
#[cfg(target_has_atomic="64")]
static COUNTER:core::sync::atomic::AtomicU64=core::sync::atomic::AtomicU64::new(0);
#[cfg(target_has_atomic="64")]
pub fn generate_session_uid()->SessionUID{
 use core::sync::atomic::Ordering;
 let mut value=COUNTER.fetch_add(1,Ordering::SeqCst).wrapping_add(1);
 if value==0{value=COUNTER.fetch_add(1,Ordering::SeqCst).wrapping_add(1);}
 SessionUID(value)
}
#[cfg(not(target_has_atomic="64"))]
static mut COUNTER_FALLBACK:u64=0;
#[cfg(not(target_has_atomic="64"))]
pub fn generate_session_uid()->SessionUID{
 unsafe{
  COUNTER_FALLBACK=COUNTER_FALLBACK.wrapping_add(1);
  if COUNTER_FALLBACK==0{COUNTER_FALLBACK=COUNTER_FALLBACK.wrapping_add(1);}
  SessionUID(COUNTER_FALLBACK)
 }
}
