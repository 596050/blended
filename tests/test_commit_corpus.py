import subprocess,tempfile,unittest
from pathlib import Path
from tools.commit_corpus import commit_staged_corpus
class CommitObjectTests(unittest.TestCase):
    def test_identity_and_parent_are_explicit_and_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo=Path(tmp)/'repo';subprocess.run(['git','init','-q',str(repo)],check=True)
            (repo/'a').write_bytes(b'raw\r\n');subprocess.run(['git','-C',str(repo),'add','a'],check=True)
            first=commit_staged_corpus(repo,'Original tests',timestamp=1792695600)
            self.assertEqual(subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip(),first)
            second=commit_staged_corpus(repo,'Preserve another audit',timestamp=1792695601)
            raw=subprocess.check_output(['git','-C',str(repo),'cat-file','commit',second],text=True)
            self.assertIn('parent '+first+'\n',raw)
            self.assertIn('author github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com> 1792695601 +0000\n',raw)
            subprocess.run(['git','-C',str(repo),'fsck','--strict'],check=True,capture_output=True)
    def test_invalid_message_is_rejected(self):
        with self.assertRaises(ValueError):commit_staged_corpus(Path('/missing'),'bad\0message')
if __name__=='__main__':unittest.main()
