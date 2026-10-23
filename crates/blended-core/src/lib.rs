// SPDX-License-Identifier: GPL-3.0-or-later
pub mod math;
pub mod compat_cases;
pub mod cycles_math;
pub mod browser_geometry;
pub mod scalar_math;
pub mod additional_cases;
pub mod data_structures;
pub mod structure_cases;
pub mod collections;
pub mod collection_cases;

#[unsafe(no_mangle)]
pub extern "C" fn blended_abi_version() -> u32 { 1 }
#[unsafe(no_mangle)]
pub extern "C" fn blended_case_count() -> u32 { compat_cases::CASES.len() as u32 }
#[unsafe(no_mangle)]
pub extern "C" fn blended_run_case(index: u32) -> i32 {
    compat_cases::CASES.get(index as usize).map(|(_,run)| i32::from(run())).unwrap_or(-1)
}
#[unsafe(no_mangle)]
pub extern "C" fn blended_case_assertion_count(index:u32) -> u32 {
    compat_cases::REPORTS.get(index as usize).map(|run|run().assertions).unwrap_or(0)
}
#[unsafe(no_mangle)]
pub extern "C" fn blended_scalar_square(x: f32) -> f32 { math::square3([x,0.0,0.0])[0] }
#[unsafe(no_mangle)]
pub extern "C" fn blended_additional_case_count() -> u32 { additional_cases::CASES.len() as u32 }
#[unsafe(no_mangle)]
pub extern "C" fn blended_additional_run_case(index:u32) -> i32 {
    additional_cases::CASES.get(index as usize).map(|(_,run)|i32::from(run().passed())).unwrap_or(-1)
}
#[unsafe(no_mangle)]
pub extern "C" fn blended_additional_assertion_count(index:u32) -> u32 {
    additional_cases::CASES.get(index as usize).map(|(_,run)|run().assertions).unwrap_or(0)
}
#[unsafe(no_mangle)]
pub extern "C" fn blended_structures_case_count() -> u32 { structure_cases::CASES.len() as u32 }
#[unsafe(no_mangle)]
pub extern "C" fn blended_structures_run_case(index:u32) -> i32 {
    structure_cases::CASES.get(index as usize).map(|(_,run,expected)| {
        let report=run();i32::from(report.passed() && report.assertions==*expected)
    }).unwrap_or(-1)
}
#[unsafe(no_mangle)]
pub extern "C" fn blended_structures_assertion_count(index:u32) -> u32 {
    structure_cases::CASES.get(index as usize).map(|(_,run,_)|run().assertions).unwrap_or(0)
}
#[unsafe(no_mangle)]
pub extern "C" fn blended_collections_case_count()->u32 {collection_cases::CASES.len() as u32}
#[unsafe(no_mangle)]
pub extern "C" fn blended_collections_run_case(index:u32)->i32 {
    collection_cases::CASES.get(index as usize).map(|(_,run,count)|{
        let r=run();i32::from(r.passed() && r.assertions==*count)
    }).unwrap_or(-1)
}
#[unsafe(no_mangle)]
pub extern "C" fn blended_collections_assertion_count(index:u32)->u32 {
    collection_cases::CASES.get(index as usize).map(|(_,run,_)|run().assertions).unwrap_or(0)
}

pub mod hashing;
pub mod compile_time_cases;

pub mod numerics_text_cases;

pub mod numeric_vectors;
pub mod string_views;
pub mod color_types;

#[unsafe(no_mangle)]
pub extern "C" fn blended_numerics_text_case_count()->u32 {numerics_text_cases::CASES.len() as u32}
#[unsafe(no_mangle)]
pub extern "C" fn blended_numerics_text_run_case(index:u32)->i32 {
    numerics_text_cases::CASES.get(index as usize).map(|(_,run,count)|{
        let r=run();i32::from(r.passed() && r.assertions==*count)
    }).unwrap_or(-1)
}
#[unsafe(no_mangle)]
pub extern "C" fn blended_numerics_text_assertion_count(index:u32)->u32 {
    numerics_text_cases::CASES.get(index as usize).map(|(_,run,_)|run().assertions).unwrap_or(0)
}

pub mod matrix_type_cases;

pub mod matrix_types;
#[unsafe(no_mangle)]
pub extern "C" fn blended_matrix_types_case_count()->u32 {matrix_type_cases::CASES.len() as u32}
#[unsafe(no_mangle)]
pub extern "C" fn blended_matrix_types_run_case(index:u32)->i32 {
 matrix_type_cases::CASES.get(index as usize).map(|(_,run,count)|{let r=run();i32::from(r.passed()&&r.assertions==*count)}).unwrap_or(-1)
}
#[unsafe(no_mangle)]
pub extern "C" fn blended_matrix_types_assertion_count(index:u32)->u32 {
 matrix_type_cases::CASES.get(index as usize).map(|(_,run,_)|run().assertions).unwrap_or(0)
}
