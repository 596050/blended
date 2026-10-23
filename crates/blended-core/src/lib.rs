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

pub mod string_ref_cases;

pub mod string_refs;

pub mod bit_span_cases;

pub mod bit_spans;

// Additional runtime groups retain the legacy application ABI unchanged.
macro_rules! exported_cases {
    ($count:ident,$run:ident,$assertions:ident,$module:ident)=>{
        #[unsafe(no_mangle)] pub extern "C" fn $count()->u32{$module::CASES.len() as u32}
        #[unsafe(no_mangle)] pub extern "C" fn $run(index:u32)->i32{
            $module::CASES.get(index as usize).map(|(_,run,expected)|{let r=run();i32::from(r.passed()&&r.assertions==*expected)}).unwrap_or(-1)
        }
        #[unsafe(no_mangle)] pub extern "C" fn $assertions(index:u32)->u32{
            $module::CASES.get(index as usize).map(|(_,run,_)|run().assertions).unwrap_or(0)
        }
    };
}
exported_cases!(blended_strings_case_count,blended_strings_run_case,blended_strings_assertion_count,string_ref_cases);
exported_cases!(blended_bit_spans_case_count,blended_bit_spans_run_case,blended_bit_spans_assertion_count,bit_span_cases);

pub mod numeric_vectors;

pub mod color_types;

pub mod matrix_types;

pub mod numeric_type_cases;

pub mod matrix_type_cases;

#[unsafe(no_mangle)]
pub extern "C" fn blended_numeric_types_case_count()->u32 {numeric_type_cases::CASES.len() as u32}
#[unsafe(no_mangle)]
pub extern "C" fn blended_numeric_types_run_case(index:u32)->i32 {
    numeric_type_cases::CASES.get(index as usize).map(|(_,run,count)|{
        let r=run();i32::from(r.passed() && r.assertions==*count)
    }).unwrap_or(-1)
}
#[unsafe(no_mangle)]
pub extern "C" fn blended_numeric_types_assertion_count(index:u32)->u32 {
    numeric_type_cases::CASES.get(index as usize).map(|(_,run,_)|run().assertions).unwrap_or(0)
}

#[unsafe(no_mangle)]
pub extern "C" fn blended_matrix_types_case_count()->u32 {matrix_type_cases::CASES.len() as u32}
#[unsafe(no_mangle)]
pub extern "C" fn blended_matrix_types_run_case(index:u32)->i32 {
    matrix_type_cases::CASES.get(index as usize).map(|(_,run,count)|{
        let r=run();i32::from(r.passed() && r.assertions==*count)
    }).unwrap_or(-1)
}
#[unsafe(no_mangle)]
pub extern "C" fn blended_matrix_types_assertion_count(index:u32)->u32 {
    matrix_type_cases::CASES.get(index as usize).map(|(_,run,_)|run().assertions).unwrap_or(0)
}

pub mod geometry_math;
pub mod geometry_math_cases;
#[unsafe(no_mangle)]
pub extern "C" fn blended_geometry_math_case_count()->u32 {geometry_math_cases::CASES.len() as u32}
#[unsafe(no_mangle)]
pub extern "C" fn blended_geometry_math_run_case(index:u32)->i32 {
    geometry_math_cases::CASES.get(index as usize).map(|(_,run,count)|{
        let r=run();i32::from(r.passed() && r.assertions==*count)
    }).unwrap_or(-1)
}
#[unsafe(no_mangle)]
pub extern "C" fn blended_geometry_math_assertion_count(index:u32)->u32 {
    geometry_math_cases::CASES.get(index as usize).map(|(_,run,_)|run().assertions).unwrap_or(0)
}
