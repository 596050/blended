"""Source and supplemental-oracle checks, not additional Blender runtime cases."""
from pathlib import Path
import hashlib,json,struct,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from port_pixel_format_tests import FILES,extract,translate
from port_workbench import expected_cases
from verify_pixel_formats_oracle import corpus,sections,compare_bytes,fbits,half_value
from verify_pixel_formats_sensitivity import MUTATIONS
class PixelFormatPortTests(unittest.TestCase):
 def setUp(self):
  self.manifest=json.loads((ROOT/'compatibility/pixel-format-ports.json').read_text())
  self.target=(ROOT/'crates/blended-core/src/pixel_format_cases.rs').read_text()
 def test_original_source_hashes_and_enabled_identities(self):
  actual=[]
  for name,digest in FILES.items():
   raw=(ROOT/'tests/upstream/blender'/name).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),digest)
   actual.extend((i,l) for i,_,l in extract(raw.decode().split('#ifdef DO_PERF_TESTS',1)[0]))
  self.assertEqual(actual,[(c['id'],c['line']) for c in self.manifest['cases']]);self.assertEqual(len(actual),9)
 def test_performance_conditions_are_not_counted_as_passes(self):
  remaining=self.manifest['conditional_unported_cases'];self.assertEqual(len(remaining),5)
  self.assertTrue(all(c['status']=='unported_conditional_performance_case' and not c['enabled_in_reference_config'] for c in remaining))
  self.assertFalse({c['id'] for c in remaining}&{c['id'] for c in self.manifest['cases']})
 def test_every_enabled_original_body_reproduces(self):
  for name in FILES:
   text=(ROOT/'tests/upstream/blender'/name).read_text().split('#ifdef DO_PERF_TESTS',1)[0]
   for identity,body,line in extract(text):
    code,count=translate(body,name);self.assertIn(code,self.target);c=next(c for c in self.manifest['cases'] if c['id']==identity)
    self.assertEqual(count,c['expected_runtime_assertions']);self.assertEqual(hashlib.sha256(body.encode()).hexdigest(),c['source_body_sha256'])
 def test_assertion_counts_and_total_universe(self):
  self.assertEqual(sum(c['expected_runtime_assertions'] for c in self.manifest['cases']),169)
  cases,_=expected_cases();self.assertEqual(len(cases),512);self.assertEqual(sum(c['expected_runtime_assertions'] for c in cases),1661546)
 def test_actual_fp_guard_not_a_browser_capability_claim(self):
  self.assertIn('let _flush_to_zero=m::ScopedFlushToZero::new();',self.target)
  code=(ROOT/'crates/blended-core/src/pixel_formats.rs').read_text()
  self.assertIn('stmxcsr',code);self.assertIn('ldmxcsr',code);self.assertIn('cfg!(target_arch="x86_64")',code)
  self.assertIn('blended_pixel_formats_hardware_fp_control',(ROOT/'crates/blended-core/src/lib.rs').read_text())
 def test_complete_half_boundary_input_corpus(self):
  floats,norm=corpus();self.assertEqual(len(floats),291054);self.assertEqual(len(norm),2183);values=set(floats)
  for h in range(0x7c00):
   lower=half_value(h);upper=half_value(h+1) if h<0x7bff else 65536.0
   b=fbits((lower+upper)*0.5)
   for v in (fbits(lower),b-1,b,b+1):self.assertIn(v,values);self.assertIn(v|0x80000000,values)
  self.assertIn(0x7f800001,values);self.assertIn(0xff800001,values)
 def test_binary_layout_is_complete_and_contiguous(self):
  layout=sections(291054,2183);self.assertEqual(sum(s['word_count'] for s in layout),2944570)
  end=0
  for s in layout:self.assertEqual(s['word_offset'],end);end+=s['word_count']
 def test_binary_comparator_detects_last_word_and_truncation(self):
  with tempfile.TemporaryDirectory() as d:
   a=Path(d)/'a';b=Path(d)/'b';data=struct.pack('<4I',0,0x80000000,0x7fc00000,1);a.write_bytes(data);b.write_bytes(data)
   layout=[dict(name='bits',word_offset=0,word_count=4)]
   self.assertEqual(compare_bytes(a,b,layout),4)
   b.write_bytes(data[:-4]+struct.pack('<I',2))
   with self.assertRaisesRegex(ValueError,'word 3'):compare_bytes(a,b,layout)
   b.write_bytes(data[:-1])
   with self.assertRaises(ValueError):compare_bytes(a,b,layout)
 def test_mutation_targets_are_exact_and_independent(self):
  code=(ROOT/'crates/blended-core/src/pixel_formats.rs').read_text();ids={c['id'] for c in self.manifest['cases']}
  for name,file,kind,old,new,target,control in MUTATIONS:
   self.assertEqual(code.count(old),1);self.assertIn(target,ids);self.assertIn(control,ids);self.assertNotEqual(target,control)
if __name__=='__main__':unittest.main()
