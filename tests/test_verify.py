import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
SPEC=importlib.util.spec_from_file_location('verify',Path(__file__).resolve().parents[1]/'scripts/verify.py')
verify=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(verify)
class VerifyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        for rel in verify.REQUIRED:
            file=self.root/rel;file.parent.mkdir(parents=True,exist_ok=True);file.write_text('{}' if file.suffix=='.json' else 'placeholder',encoding='utf-8')
        self.write('config/settings.example.json',{});self.write('config/plugins.example.json',{'plugins':[]})
    def write(self,rel,obj):(self.root/rel).write_text(json.dumps(obj),encoding='utf-8')
    def test_clean_public_fixture(self):self.assertEqual(verify.validate(self.root,True),[])
    def test_private_memory_is_public_only_failure(self):
        (self.root/'memory').mkdir();(self.root/'memory'/'personal.md').write_text('private note')
        self.assertTrue(any('private memory' in e for e in verify.validate(self.root,True)));self.assertEqual(verify.validate(self.root,False),[])
    def test_mixed_case_memory_is_rejected(self):
        (self.root/'Memory').mkdir();(self.root/'Memory'/'personal.md').write_text('private note')
        self.assertTrue(any('private memory' in e for e in verify.validate(self.root,True)))
    def test_machine_path_is_rejected(self):
        file=self.root/'note.md';file.write_text('X'+':/Users/'+'fixture/private')
        self.assertTrue(any('machine path' in e for e in verify.validate(self.root,True)))
    def test_plugin_drift_and_invalid_json(self):
        self.write('config/plugins.example.json',{'plugins':['missing@market']})
        self.assertIn('plugin manifest and enabledPlugins differ',verify.validate(self.root,False))
        (self.root/'config/plugins.example.json').write_text('{broken')
        self.assertTrue(any('invalid JSON' in e for e in verify.validate(self.root,False)))
    def test_secret_diagnostic_never_contains_payload(self):
        secret='sk-'+'A'*32;(self.root/'note.md').write_text(secret)
        errors=verify.validate(self.root,False);self.assertTrue(errors);self.assertTrue(all(secret not in e for e in errors))
if __name__=='__main__':unittest.main()
