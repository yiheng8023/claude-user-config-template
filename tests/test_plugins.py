import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
SPEC=importlib.util.spec_from_file_location('plugins',Path(__file__).resolve().parents[1]/'scripts/plugins.py')
plugins=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(plugins)
class PluginTests(unittest.TestCase):
    def test_project_scope_does_not_satisfy_user_install(self):
        result=type('Result',(),{'returncode':0,'stdout':json.dumps([{'id':'p@market','scope':'project','enabled':True}])})()
        with patch.object(plugins,'run_claude',return_value=result):self.assertEqual(plugins.installed_from_cli(),{})
    def test_optional_set_requires_explicit_selection(self):
        with tempfile.TemporaryDirectory() as td:
            file=Path(td)/'manifest.json';file.write_text(json.dumps({'plugins':['core@market'],'optionalPlugins':['cloud@market']}))
            with patch.object(plugins,'MANIFEST',file):
                self.assertEqual(plugins.load_manifest(),['core@market']);self.assertEqual(plugins.load_manifest(True),['core@market','cloud@market'])
    def test_empty_template_needs_no_cli(self):
        with patch.object(plugins,'load_manifest',return_value=[]),patch.object(plugins,'installed_plugins',side_effect=AssertionError('CLI should not run')):
            self.assertEqual(plugins.main(),0)
if __name__=='__main__':unittest.main()
