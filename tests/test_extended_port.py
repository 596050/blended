"""Source fidelity and audit failure-detection tests, not Blender feature counts."""
import copy,hashlib,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from assertion_fidelity import compare,contracts
from port_string_ref_tests import extract,split_args,strip_comments,rewrite_calls,generate as strings_generate
from port_bit_span_tests import generate as bits_generate
from port_workbench import expected_cases
from port_registry import verify_runtime_contract_bijection

class SourceAdapterTests(unittest.TestCase):
    def test_numeric_separators_characters_and_strings(self):
        text='''// TEST(fake, no) { }
TEST(numbers, One) { auto a=0b0010'0101; auto x=1'234.5e+1'2_suffix;
char brace='}'; const char* x="TEST(fake, no) {"; EXPECT_EQ(a,0x2'5); }
TEST(numbers, Two) { auto x='\\''; /* } */ EXPECT_EQ(1,1); }
'''
        cases=list(extract(text));self.assertEqual([c[0] for c in cases],['numbers.One','numbers.Two']);self.assertEqual([c[2] for c in cases],[2,4])
        self.assertIn("0b0010'0101",cases[0][1]);self.assertIn("char brace='}'",cases[0][1])
    def test_raw_strings_cannot_invent_cases(self):
        text='const char* a=R"tag(TEST(fake, bad) { })tag";\nTEST(real, yes) { f("(", 10\'000); }'
        self.assertEqual([c[0] for c in extract(text)],['real.yes'])
    def test_split_and_call_preserve_literal_content(self):
        self.assertEqual(split_args('f(1,2), "a,b", 1\'234'),['f(1,2)','"a,b"',"1'234"])
        text='f("f(ignored)", 1\'234)';self.assertEqual(rewrite_calls(text,'f(',lambda a:'g('+a+')'),'g("f(ignored)", 1\'234)')
    def test_unbalanced_call_fails_closed(self):
        with self.assertRaises(ValueError):rewrite_calls('f(10\'000','f(',str)
    def test_all_source_cases_and_assertion_sites_are_preserved(self):
        for manifest in ('string-ref-ports.json','bit-span-ports.json'):
            cases=json.loads((ROOT/'compatibility'/manifest).read_text())['cases']
            for path in {c['path'] for c in cases}:
                source=ROOT/'tests/upstream/blender'/Path(path).name
                discovered=list(extract(source.read_text()));mapped=[c for c in cases if c['path']==path]
                self.assertEqual([(c[0],c[2]) for c in discovered],[(c['id'],c['line']) for c in mapped])
                self.assertTrue(all(c['source_sha256']==hashlib.sha256(source.read_bytes()).hexdigest() for c in mapped))
    def test_current_runtime_universe(self):
        cases,_=expected_cases();self.assertEqual(len(cases),624)
        self.assertEqual(sum(c['expected_runtime_assertions'] for c in cases),3196774)
        self.assertEqual([c['id'] for c in cases if c['expected_runtime_assertions']==0],['bit_span.SetEmpty','span.ImplicitConversions'])
    def test_removed_group_fails_reviewed_bijection(self):
        cases,_=expected_cases()
        with self.assertRaises(ValueError):verify_runtime_contract_bijection(ROOT,[c for c in cases if c['group']!='strings'])
    def test_constexpr_is_not_silently_replaced_by_runtime(self):
        code=(ROOT/'crates/blended-core/src/string_ref_cases.rs').read_text()
        self.assertEqual(code.count('const _: () = assert!'),4)
        self.assertEqual(code.count('const COMPILES:'),2)
    def test_empty_span_case_retains_both_calls(self):
        code=(ROOT/'crates/blended-core/src/bit_span_cases.rs').read_text().split('pub fn bit_span__SetEmpty()',1)[1].split('// source/',1)[0]
        self.assertIn('m::MutableBitSpan::empty().set_all(true);',code);self.assertIn('m::MutableBitSpan::empty().set_all(false);',code)

class CaseBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.expected=[{'id':'zero.case','expected_runtime_assertions':0}]
        self.rows=[{'case':'zero.case','kind':'CASE_BEGIN','passed':True,'values':[]},{'case':'zero.case','kind':'CASE_END','passed':True,'values':[]}]
    def test_executed_assertion_free_case(self):
        r=compare(self.rows,self.rows,self.expected,require_boundaries=True)
        self.assertEqual(r['assertion_free_cases'],['zero.case']);self.assertEqual(r['assertions_compared'],0);self.assertTrue(r['case_boundaries_verified'])
    def test_empty_transcript_never_proves_execution(self):
        with self.assertRaises(ValueError):compare(self.rows,[],self.expected,require_boundaries=True)
    def test_unfinished_case(self):
        with self.assertRaises(ValueError):compare(self.rows,self.rows[:1],self.expected,require_boundaries=True)
    def test_duplicate_case(self):
        with self.assertRaises(ValueError):compare(self.rows,self.rows*2,self.expected,require_boundaries=True)
    def test_failed_case(self):
        rows=copy.deepcopy(self.rows);rows[-1]['passed']=False
        with self.assertRaises(ValueError):compare(self.rows,rows,self.expected,require_boundaries=True)
    def test_assertion_outside_case(self):
        rows=[{'case':'zero.case','kind':'TRUE','passed':True,'values':['b:1']}]+self.rows
        with self.assertRaises(ValueError):compare(self.rows,rows,self.expected,require_boundaries=True)
if __name__=='__main__':unittest.main()
