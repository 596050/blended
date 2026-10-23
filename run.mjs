const response=await fetch('./manifest.json');
if(!response.ok)throw Error('Manifest fetch failed');
const manifest=await response.json();
const tbody=document.querySelector('#cases');
document.querySelector('#provenance').textContent=`Source ${manifest.source_commit}; Blender reference ${manifest.reference_commit}.`;
const groups=manifest.groups;
if(!Array.isArray(groups)||new Set(groups).size!==groups.length)throw Error('Malformed group registry');
const all=groups.flatMap(group=>manifest[group].map((c,index)=>({...c,index,group})));
if(new Set(all.map(c=>c.id)).size!==all.length)throw Error('Duplicate case identity');
for(const c of all){const tr=document.createElement('tr');for(const text of [c.id,c.expected_runtime_assertions??c.assertion_count??'Original case','Not run']){const td=document.createElement('td');td.textContent=text;tr.append(td);}tbody.append(tr);}
document.querySelector('#status').textContent=`${all.length} translated cases ready. Full-suite completeness remains unverified.`;
document.querySelector('#run').addEventListener('click',async()=>{
 const result={source_commit:manifest.source_commit,reference_commit:manifest.reference_commit,status:'failed',complete_test_port:false,passed:0,vector_assertions:0,additional_assertions:0,structure_assertions:0,collection_assertions:0,cases:[],errors:[]};
 for(const key of Object.values(manifest.total_keys))result[key]=0;
 const button=document.querySelector('#run');button.disabled=true;
 try{
  const response=await fetch('./blended_core.wasm');if(!response.ok)throw Error('WASM fetch failed');
  const bytes=await response.arrayBuffer();
  const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),x=>x.toString(16).padStart(2,'0')).join('');
  if(digest!==manifest.wasm_sha256)throw Error('WASM hash/manifest mismatch');
  result.wasm_sha256=digest;
  const {instance}=await WebAssembly.instantiate(bytes,{});const w=instance.exports;
  const registries=Object.fromEntries(groups.map(g=>[g,manifest.abi[g].map(name=>{if(typeof w[name]!=='function')throw Error('Missing ABI '+name);return w[name];})]));
  for(const group of groups){if(registries[group][0]()!==manifest[group].length)throw Error(`Registry/manifest count mismatch: ${group}`);}
  for(const [i,c] of all.entries()){
   const [,run,count]=registries[c.group];const code=run(c.index);const assertions=count?count(c.index):null;
   result[manifest.total_keys[c.group]]+=assertions;
   const expected=c.expected_runtime_assertions??c.assertion_count;
   const passed=code===1&&assertions===expected;
   result.cases.push({id:c.id,group:c.group,passed,code,assertions});if(passed)result.passed++;
   const td=tbody.children[i].lastElementChild;td.textContent=passed?'Passed':'Failed';td.className=passed?'pass':'fail';
  }
  result.invalid_index_rejected=groups.every(g=>registries[g][1](0xffffffff)===-1);
  if(result.passed===all.length&&result.invalid_index_rejected)result.status='passed';
 }catch(e){result.errors.push(String(e));}
 document.querySelector('#status').textContent=`${result.passed}/${all.length} passed. Full Blender test-port completeness: not established.`;
 window.__portResults=result;button.disabled=false;
});