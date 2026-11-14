import contextlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
import unittest.mock
from pathlib import Path

SPEC=importlib.util.spec_from_file_location('installer',Path(__file__).resolve().parents[1]/'scripts/install.py')
install=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(install)

class InstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name).resolve();self.root=self.base/'repo';self.live=self.base/'home with spaces'/'.claude';self.mcp=self.base/'global.json'
        (self.root/'config').mkdir(parents=True)
        (self.root/'commands').mkdir();(self.root/'hooks').mkdir()
        (self.root/'CLAUDE.md').write_text('repo guidance',encoding='utf-8')
        (self.root/'statusline.js').write_text('// status',encoding='utf-8')
        (self.root/'commands'/'owned.md').write_text('new command',encoding='utf-8')
        (self.root/'hooks'/'owned.js').write_text('// new hook',encoding='utf-8')
        defaults={'env':{'LOCAL_PROVIDER':'default','AUTH_VALUE':'<SET_LOCALLY: own key>','NEW_FLAG':'1'},'permissions':{'allow':['example']},'enabledPlugins':{'example@market':True},'statusLine':{'command':'node "__CLAUDE_HOME__/statusline.js"'}}
        self.write(self.root/'config/settings.example.json',defaults)
        self.write(self.root/'config/mcp-servers.example.json',{'mcpServers':{'example':{'disabled':True},'ready':{'command':'node','args':[]}}})
    def write(self,path,obj):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj),encoding='utf-8')
    def run_install(self,**kwargs):
        with contextlib.redirect_stdout(io.StringIO()):install.install(self.root,self.live,self.mcp,**kwargs)
    def test_preserves_local_files_provider_and_revoked_grants(self):
        self.write(self.live/'settings.json',{'env':{'LOCAL_PROVIDER':'local'},'permissions':{'allow':[]},'enabledPlugins':{'local@market':False}})
        (self.live/'commands').mkdir();(self.live/'commands'/'local.md').write_text('mine')
        (self.live/'commands'/'owned.md').write_text('edited locally')
        self.run_install()
        settings=json.loads((self.live/'settings.json').read_text())
        self.assertEqual(settings['env']['LOCAL_PROVIDER'],'local');self.assertNotIn('AUTH_VALUE',settings['env'])
        self.assertEqual(settings['permissions']['allow'],[]);self.assertEqual(settings['enabledPlugins'],{'local@market':False})
        self.assertEqual((self.live/'commands'/'owned.md').read_text(),'edited locally');self.assertTrue((self.live/'commands'/'local.md').exists())
        self.assertIn('node "',settings['statusLine']['command']);self.assertNotIn('__CLAUDE_HOME__',settings['statusLine']['command'])
    def test_explicit_overwrite_backs_up_and_keeps_unrelated(self):
        (self.live/'hooks').mkdir(parents=True);(self.live/'hooks'/'owned.js').write_text('// old');(self.live/'hooks'/'local.js').write_text('// mine')
        self.run_install(overwrite_files=True)
        backups=list((self.live/'hooks').glob('owned.js.bak-*'));self.assertEqual(len(backups),1);self.assertEqual(backups[0].read_text(),'// old')
        self.assertTrue((self.live/'hooks'/'local.js').exists())
    def test_dry_run_writes_nothing(self):
        self.run_install(dry_run=True,overwrite_files=True);self.assertFalse(self.live.exists());self.assertFalse(self.mcp.exists())
    def test_invalid_mcp_aborts_before_files(self):
        self.mcp.write_text('{bad json')
        with self.assertRaises(ValueError):self.run_install()
        self.assertFalse(self.live.exists())
    def test_idempotent_and_disabled_example_not_installed(self):
        self.run_install();before={str(p):p.read_bytes() for p in self.base.rglob('*') if p.is_file()};self.run_install(overwrite_files=True)
        after={str(p):p.read_bytes() for p in self.base.rglob('*') if p.is_file()};self.assertEqual(before,after)
        self.assertNotIn('example',json.loads(self.mcp.read_text())['mcpServers'])
    def test_missing_environment_server_is_deferred(self):
        self.write(self.root/'config/mcp-servers.example.json',{'mcpServers':{'later':{'env':{'VALUE':'${CLAUDE_CONFIG_TEST_MISSING_VALUE}'}}}})
        with unittest.mock.patch.dict(os.environ,{},clear=True):self.run_install()
        self.assertFalse(self.mcp.exists())
    def test_provider_environment_does_not_receive_foreign_model_defaults(self):
        defaults={'env':{'ANTHROPIC_BASE_URL':'provider-default','ANTHROPIC_MODEL':'foreign-model','CLAUDE_CODE_SUBAGENT_MODEL':'foreign-model','SAFE_FLAG':'1'},'model':'sonnet'}
        self.write(self.root/'config/settings.example.json',defaults)
        self.write(self.live/'settings.json',{'env':{'ANTHROPIC_AUTH_TOKEN':'local-fixture'}})
        self.run_install()
        settings=json.loads((self.live/'settings.json').read_text())
        self.assertNotIn('ANTHROPIC_MODEL',settings['env']);self.assertNotIn('CLAUDE_CODE_SUBAGENT_MODEL',settings['env']);self.assertNotIn('model',settings)
        self.assertEqual(settings['env']['SAFE_FLAG'],'1')
    def test_desktop_restore_is_explicit_and_backed_up(self):
        source=self.base/'desktop-local.json';target=self.base/'desktop-live.json'
        self.write(source,{'mcpServers':{}});self.write(target,{'old':True})
        self.run_install(desktop_source=source,desktop_target=target)
        self.assertEqual(json.loads(target.read_text()),{'mcpServers':{}});self.assertEqual(len(list(self.base.glob('desktop-live.json.bak-*'))),1)
    def test_cloud_provider_flags_do_not_receive_foreign_provider_defaults(self):
        self.write(self.root/'config/settings.example.json',{'env':{'ANTHROPIC_BASE_URL':'foreign','ANTHROPIC_MODEL':'foreign'},'model':'sonnet'})
        for provider in ['CLAUDE_CODE_USE_BEDROCK','CLAUDE_CODE_USE_VERTEX','CLAUDE_CODE_USE_FOUNDRY']:
            self.write(self.live/'settings.json',{'env':{provider:'1'}})
            self.run_install()
            result=json.loads((self.live/'settings.json').read_text())
            self.assertNotIn('ANTHROPIC_BASE_URL',result['env']);self.assertNotIn('ANTHROPIC_MODEL',result['env']);self.assertNotIn('model',result)
    def test_shell_provider_selection_is_preserved(self):
        self.write(self.root/'config/settings.example.json',{'env':{'ANTHROPIC_BASE_URL':'foreign'},'model':'sonnet'})
        with unittest.mock.patch.dict(os.environ,{'CLAUDE_CODE_USE_BEDROCK':'true'}):self.run_install()
        settings=json.loads((self.live/'settings.json').read_text())
        self.assertNotIn('ANTHROPIC_BASE_URL',settings.get('env',{}));self.assertNotIn('model',settings)
    def test_concurrent_settings_and_mcp_edits_are_preserved(self):
        for target in ['settings','mcp']:
            with self.subTest(target=target):
                path=self.live/'settings.json' if target=='settings' else self.mcp
                self.write(path,{'before':True})
                real_write=install.write_file
                changed=False
                def concurrent(file,content,**kwargs):
                    nonlocal changed
                    if not changed:
                        self.write(path,{'new_owner_value':True});changed=True
                    return real_write(file,content,**kwargs)
                with unittest.mock.patch.object(install,'write_file',side_effect=concurrent):
                    with self.assertRaises(RuntimeError):self.run_install(overwrite_files=True)
                self.assertEqual(json.loads(path.read_text()),{'new_owner_value':True})
    def test_linked_destination_is_rejected_before_any_write(self):
        outside=self.base/'outside';outside.mkdir();self.live.mkdir(parents=True)
        try:(self.live/'commands').symlink_to(outside,target_is_directory=True)
        except OSError:self.skipTest('OS does not permit test symlinks')
        with self.assertRaises(ValueError):self.run_install(overwrite_files=True)
        self.assertFalse((self.live/'CLAUDE.md').exists());self.assertEqual(list(outside.iterdir()),[])

if __name__=='__main__':unittest.main()
