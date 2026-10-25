"""Explicit implemented runtime groups, separate from the full upstream universe.

Removing a group cannot silently reduce the accepted subset: reviewed runtime
contract identities must form an exact bijection with these registered cases.
"""
from dataclasses import dataclass
from pathlib import Path
import hashlib,json

@dataclass(frozen=True)
class Group:
    name:str
    manifest:str
    module:str
    native_suite:str
    generator:str
    total_key:str
    abi:tuple[str,str,str]

GROUPS=(
    Group('additional','additional-ports.json','additional_cases','upstream_additional','port_scalar_tests.py','additional_assertions',('blended_additional_case_count','blended_additional_run_case','blended_additional_assertion_count')),
    Group('structures','structure-ports.json','structure_cases','upstream_structures','port_structure_tests.py','structure_assertions',('blended_structures_case_count','blended_structures_run_case','blended_structures_assertion_count')),
    Group('collections','collection-ports.json','collection_cases','upstream_collections','port_collection_tests.py','collection_assertions',('blended_collections_case_count','blended_collections_run_case','blended_collections_assertion_count')),
    Group('strings','string-ref-ports.json','string_ref_cases','upstream_string_refs','port_string_ref_tests.py','string_assertions',('blended_strings_case_count','blended_strings_run_case','blended_strings_assertion_count')),
    Group('bit_spans','bit-span-ports.json','bit_span_cases','upstream_bit_spans','port_bit_span_tests.py','bit_span_assertions',('blended_bit_spans_case_count','blended_bit_spans_run_case','blended_bit_spans_assertion_count')),
    Group('numeric_types','numeric-type-ports.json','numeric_type_cases','upstream_numeric_types','port_numeric_type_tests.py','numeric_type_assertions',('blended_numeric_types_case_count','blended_numeric_types_run_case','blended_numeric_types_assertion_count')),
    Group('matrix_types','matrix-type-ports.json','matrix_type_cases','upstream_matrix_types','port_matrix_type_tests.py','matrix_type_assertions',('blended_matrix_types_case_count','blended_matrix_types_run_case','blended_matrix_types_assertion_count')),
    Group('geometry_math','geometry-math-ports.json','geometry_math_cases','upstream_geometry_math','port_geometry_math_tests.py','geometry_math_assertions',('blended_geometry_math_case_count','blended_geometry_math_run_case','blended_geometry_math_assertion_count')),
    Group('sampling','sampling-ports.json','sampling_cases','upstream_sampling','port_sampling_tests.py','sampling_assertions',('blended_sampling_case_count','blended_sampling_run_case','blended_sampling_assertion_count')),
    Group('curves','curve-ports.json','curve_cases','upstream_curves','port_sampling_tests.py','curve_assertions',('blended_curves_case_count','blended_curves_run_case','blended_curves_assertion_count')),
    Group('heaps','heap-ports.json','heap_cases','upstream_heaps','port_heap_tests.py','heap_assertions',('blended_heaps_case_count','blended_heaps_run_case','blended_heaps_assertion_count')),
    Group('data','data-ports.json','data_cases','upstream_data','port_data_tests.py','data_assertions',('blended_data_case_count','blended_data_run_case','blended_data_assertion_count')),
    Group('string_ops','string-ops-ports.json','string_ops_cases','upstream_string_ops','port_string_ops_tests.py','string_ops_assertions',('blended_string_ops_case_count','blended_string_ops_run_case','blended_string_ops_assertion_count')),
    Group('utf8','utf8-ports.json','utf8_cases','upstream_utf8','port_utf8_tests.py','utf8_assertions',('blended_utf8_case_count','blended_utf8_run_case','blended_utf8_assertion_count')),
    Group('pixel_formats','pixel-format-ports.json','pixel_format_cases','upstream_pixel_formats','port_pixel_format_tests.py','pixel_format_assertions',('blended_pixel_formats_case_count','blended_pixel_formats_run_case','blended_pixel_formats_assertion_count')),
    Group('polyfill','polyfill-ports.json','polyfill_cases','upstream_polyfill','port_polyfill_compact.py','polyfill_assertions',('blended_polyfill_case_count','blended_polyfill_run_case','blended_polyfill_assertion_count')),
    Group('spans','span-ports.json','span_cases','upstream_spans','port_span_tests.py','span_assertions',('blended_spans_case_count','blended_spans_run_case','blended_spans_assertion_count')),
    Group('mask_expressions','mask-expression-ports.json','mask_expression_cases','upstream_mask_expressions','port_mask_expression_tests.py','mask_expression_assertions',('blended_mask_expressions_case_count','blended_mask_expressions_run_case','blended_mask_expressions_assertion_count')),
    Group('container_views','container-view-ports.json','container_view_cases','upstream_container_views','port_container_view_tests.py','container_view_assertions',('blended_container_views_case_count','blended_container_views_run_case','blended_container_views_assertion_count')),
)
TOTAL_KEYS={'legacy':'vector_assertions',**{g.name:g.total_key for g in GROUPS}}
ABI={'legacy':('blended_case_count','blended_run_case','blended_case_assertion_count'),**{g.name:g.abi for g in GROUPS}}

def verify_runtime_contract_bijection(root:Path,cases:list):
    from contract_registry import load_contracts
    contracts=load_contracts(root)
    registered={c['id'] for c in cases};reviewed=[]
    for c in contracts['contracts']:
        if c['target_path'].endswith('/compile_time_cases.rs'):continue
        if hashlib.sha256((root/c['target_path']).read_bytes()).hexdigest()!=c['target_sha256']:
            raise ValueError('Reviewed test source has changed: '+c['target_path'])
        reviewed.extend(identity for identity in c['case_ids'] if not identity.startswith('static_assert@'))
    if len(reviewed)!=len(set(reviewed)) or set(reviewed)!=registered or len(cases)!=len(registered):
        raise ValueError('Reviewed runtime contracts and executable registries do not match exactly')
