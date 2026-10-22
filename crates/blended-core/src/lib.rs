// SPDX-License-Identifier: GPL-3.0-or-later
pub mod math;
pub mod compat_cases;
pub mod cycles_math;
pub mod browser_geometry;

#[unsafe(no_mangle)]
pub extern "C" fn blended_abi_version() -> u32 { 1 }
#[unsafe(no_mangle)]
pub extern "C" fn blended_case_count() -> u32 { compat_cases::CASES.len() as u32 }
#[unsafe(no_mangle)]
pub extern "C" fn blended_run_case(index: u32) -> i32 {
    compat_cases::CASES.get(index as usize).map(|(_,run)| i32::from(run())).unwrap_or(-1)
}
#[unsafe(no_mangle)]
pub extern "C" fn blended_scalar_square(x: f32) -> f32 { math::square3([x,0.0,0.0])[0] }
