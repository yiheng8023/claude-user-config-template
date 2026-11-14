const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('fs'),os=require('os'),path=require('path');
const {mergeGuarded,atomicWrite,run}=require('../hooks/settings-guard.js');
test('repair only absent env; preserve explicit disabled values and permission revocation',()=>{
 const original={env:{FLAG:'0'},permissions:{allow:[]}};
 const result=mergeGuarded(original,{env:{FLAG:'1',NEW:'1'},permissions_allow:[]});
 assert.equal(result.settings.env.FLAG,'0');assert.equal(result.settings.env.NEW,'1');assert.deepEqual(result.settings.permissions.allow,[]);assert.deepEqual(original,{env:{FLAG:'0'},permissions:{allow:[]}});
});
test('old declarations that auto-grant permissions are rejected',()=>{
 assert.throws(()=>mergeGuarded({}, {permissions_allow:['arbitrary grant']}));
});
test('atomic write refuses stale baseline and creates recoverable backup',()=>{
 const root=fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(),'settings-guard-test-')));
 try{const file=path.join(root,'settings.json');fs.writeFileSync(file,'old');assert.throws(()=>atomicWrite(file,'new','stale'));assert.equal(fs.readFileSync(file,'utf8'),'old');atomicWrite(file,'new','old');assert.equal(fs.readFileSync(file,'utf8'),'new');assert.equal(fs.readdirSync(root).filter(n=>n.includes('.bak-')).length,1);}finally{fs.rmSync(root,{recursive:true,force:true});}
});
test('deprecated install does not write config or deploy files',()=>{
 const root=fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(),'settings-guard-test-')));
 try{fs.writeFileSync(path.join(root,'settings.json'),'{}');assert.equal(run(['--install'],root,root),2);assert.deepEqual(fs.readdirSync(root),['settings.json']);}finally{fs.rmSync(root,{recursive:true,force:true});}
});
