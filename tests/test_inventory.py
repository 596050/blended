import tempfile
import unittest
import hashlib
from pathlib import Path
from tools.inventory import scan_cpp,scan_python,scan_rust,inventory,summary
class InventoryTests(unittest.TestCase):
    def test_cpp_simple_case(self):
        c=scan_cpp('TEST(math_vector, Clamp) {}','v.cc')[0]
        self.assertEqual(c['identity'],'math_vector.Clamp');self.assertEqual(c['kind'],'TEST')
    def test_cpp_multiline_case(self):
        self.assertEqual(scan_cpp('TEST_F(\n Fixture,\n Case\n) {}','a.cc')[0]['identity'],'Fixture.Case')
    def test_cpp_comments_and_strings(self):
        text='// TEST(a,b)\n/* TEST(c,d) */\nconst char*x="TEST(e,f)";\nTEST(g,h){}'
        self.assertEqual([c['identity'] for c in scan_cpp(text,'a.cc')],['g.h'])
    def test_parameters_are_not_expanded(self):
        self.assertTrue(scan_cpp('TEST_P(Suite, Param) {}','a.cc')[0]['requires_runtime_expansion'])
    def test_static_assert_separate(self):
        self.assertEqual([c['kind'] for c in scan_cpp('static_assert(1==1);\nTEST(X,Y){}','a.cc')],['static_assert','TEST'])
    def test_python_classes(self):
        text='class One:\n def test_a(self): pass\nclass Two:\n def test_a(self): pass\n'
        self.assertEqual([c['identity'] for c in scan_python(text,'a.py')],['One.test_a','Two.test_a'])
    def test_python_syntax_failure(self):
        with self.assertRaises(SyntaxError):scan_python('def test_a(:','a.py')
    def test_python_decorators(self):
        self.assertTrue(scan_python('@parametrize("x",[1,2])\ndef test_a(x):pass','a.py')[0]['requires_runtime_expansion'])
    def test_rust_case(self):
        self.assertEqual(scan_rust('#[test]\nfn clamp_case() {}','lib.rs')[0]['identity'],'clamp_case')
    def test_lifetimes_do_not_hide_tests(self):
        text="fn before<'a>() {}\n#[test]\nfn real_case() {}\nfn after<'b>() {}"
        self.assertEqual([c['identity'] for c in scan_rust(text,'lib.rs')],['real_case'])
    def test_discovery_is_not_execution(self):
        self.assertEqual(scan_cpp('TEST(X,Y){}','a.cc')[0]['execution'],'not_run')
    def test_lfs_pointer_not_fixture(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'demo.blend').write_text('version https://git-lfs.github.com/spec/v1\noid sha256:abc\nsize 100\n')
            r=inventory(p,'example','0'*40)
            self.assertEqual(r['fixtures'][0]['status'],'lfs_pointer');self.assertFalse(r['fixtures_available']);self.assertFalse(r['runtime_enumeration_complete'])
    def test_absent_fixture_is_visible(self):
        with tempfile.TemporaryDirectory() as d:self.assertFalse(inventory(Path(d),'blender','0'*40)['fixtures_available'])
    def test_missing_never_passes(self):
        r=summary([{'execution':'not_run'},{'execution':'blocked'},{'execution':'passed'}])
        self.assertEqual(r['passed'],1);self.assertEqual(r['not_run'],1);self.assertEqual(r['blocked'],1)
    def test_invalid_status_rejected(self):
        with self.assertRaises(ValueError):summary([{'execution':'probably_ok'}])
    def test_source_path_and_line(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'math_test.cc').write_text('\nTEST(A,B){}')
            c=inventory(p,'blender','0'*40)['cases'][0]
            self.assertEqual(c['path'],'math_test.cc');self.assertEqual(c['line'],2);self.assertEqual(c['upstream_commit'],'0'*40)
    def test_declared_fixture_roots_include_non_blend_assets_and_reference_outputs(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);assets=root/'tests/files';assets.mkdir(parents=True)
            payload=b'fixture texture bytes'
            (assets/'texture.png').write_bytes(payload)
            (assets/'reference.exr').write_bytes(b'reference bytes')
            (root/'unrelated.png').write_bytes(b'not a declared fixture')
            result=inventory(root,'blender','0'*40,fixture_roots=['tests/files'])
            by_path={f['path']:f for f in result['fixtures']}
            self.assertEqual(set(by_path),{'tests/files/texture.png','tests/files/reference.exr'})
            self.assertEqual(by_path['tests/files/texture.png']['sha256'],hashlib.sha256(payload).hexdigest())
            self.assertEqual(by_path['tests/files/texture.png']['status'],'present_unvalidated')
            self.assertEqual(result['fixture_completeness'],'unknown')
            self.assertFalse(result['runtime_enumeration_complete'])
    def test_non_blend_lfs_pointer_does_not_count_as_available_payload(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);assets=root/'tests/files';assets.mkdir(parents=True)
            pointer='version https://git-lfs.github.com/spec/v1\noid sha256:'+'b'*64+'\nsize 123456\n'
            (assets/'audio.wav').write_text(pointer)
            result=inventory(root,'blender','0'*40,fixture_roots=['tests/files'])
            fixture=result['fixtures'][0]
            self.assertEqual(fixture['status'],'lfs_pointer')
            self.assertEqual(fixture['lfs_oid_sha256'],'b'*64)
            self.assertEqual(fixture['lfs_declared_size'],123456)
            self.assertFalse(result['fixtures_available'])
    def test_missing_declared_fixture_root_is_explicit(self):
        with tempfile.TemporaryDirectory() as d:
            result=inventory(Path(d),'blender','0'*40,fixture_roots=['tests/files'])
            self.assertEqual(result['fixture_roots'],[{'path':'tests/files','status':'missing','files_discovered':0}])
            self.assertFalse(result['fixtures_available'])
    def test_fixture_roots_cannot_escape_the_checkout(self):
        with tempfile.TemporaryDirectory() as d:
            for root in ('../outside','/tmp','tests/../files'):
                with self.subTest(root=root),self.assertRaises(ValueError):
                    inventory(Path(d),'blender','0'*40,fixture_roots=[root])
    def test_symlinked_fixture_bytes_are_never_followed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);assets=root/'tests/files';assets.mkdir(parents=True)
            (root/'outside.png').write_bytes(b'not an in-root payload')
            (assets/'texture.png').symlink_to(root/'outside.png')
            result=inventory(root,'blender','0'*40,fixture_roots=['tests/files'])
            fixture=result['fixtures'][0]
            self.assertEqual(fixture['status'],'symlink_unverified')
            self.assertNotIn('sha256',fixture)
            self.assertFalse(result['fixtures_available'])
    def test_unparseable_source_keeps_content_hash_and_unresolved_error(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);raw=b'def test_incomplete(:\n';(root/'bad.py').write_bytes(raw)
            result=inventory(root,'blender','0'*40)
            self.assertEqual(len(result['unreadable_files']),1)
            self.assertEqual(result['files'][0]['sha256'],hashlib.sha256(raw).hexdigest())
            self.assertEqual(result['files'][0]['discovery_status'],'unresolved')
if __name__=='__main__':unittest.main()
