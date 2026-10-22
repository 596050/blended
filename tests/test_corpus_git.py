import hashlib,json,subprocess,tempfile,unittest
from pathlib import Path
from tools.corpus_git import stage_raw_corpus
class RawCorpusTests(unittest.TestCase):
    def test_attributes_never_rewrite_original_blobs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'source';repo=root/'repo';source.mkdir()
            subprocess.run(['git','init','-q',str(repo)],check=True)
            subprocess.run(['git','-C',str(repo),'config','core.autocrlf','true'],check=True)
            files={'original/.gitattributes':b'*.obj text eol=lf\n*.bin filter=broken\n',
                   'original/scene.obj':b'v 0 0 0\r\nv 1 0 0\r\n',
                   'original/bytes.bin':b'\xff\x00\r\n',
                   'original/link':b'../target'}
            records=[]
            for path,data in files.items():
                p=source/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
                records.append({'path':path.removeprefix('original/'),'included_in_corpus':True,'mode':'100644','sha256':hashlib.sha256(data).hexdigest(),'git_oid':hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()})
            (source/'tracked-files.json').write_text(json.dumps(records))
            report=stage_raw_corpus(source,repo)
            self.assertEqual(report['original_blobs_verified'],4)
            tree=subprocess.check_output(['git','-C',str(repo),'write-tree'],text=True).strip()
            for path,data in files.items():
                self.assertEqual(subprocess.check_output(['git','-C',str(repo),'cat-file','blob',f'{tree}:{path}']),data)
    def test_corrupt_original_is_rejected_before_index_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'src';repo=root/'repo';source.mkdir();(source/'original').mkdir()
            subprocess.run(['git','init','-q',str(repo)],check=True)
            (source/'original/test.py').write_bytes(b'bad')
            (source/'tracked-files.json').write_text(json.dumps([{'path':'test.py','included_in_corpus':True,'sha256':'a'*64,'git_oid':'b'*40}]))
            with self.assertRaises(ValueError):stage_raw_corpus(source,repo)
            self.assertEqual(subprocess.check_output(['git','-C',str(repo),'ls-files']),b'')
    def test_symlink_cannot_escape_corpus(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/'src';repo=root/'repo';source.mkdir()
            subprocess.run(['git','init','-q',str(repo)],check=True)
            (source/'tracked-files.json').write_text('[]');(source/'escape').symlink_to('/etc/passwd')
            with self.assertRaises(ValueError):stage_raw_corpus(source,repo)
if __name__=='__main__':unittest.main()
