const manifest=await (await fetch('./manifest.json')).json();
const tbody=document.querySelector('#cases');
document.querySelector('#provenance').textContent=`Source ${manifest.source_commit}; Blender reference ${manifest.reference_commit}.`;
const all=[...manifest.legacy.map((c,i)=>({...c,index:i,group:'legacy'})),...manifest.additional.map((c,i)=>({...c,index:i,group:'additional'}))];
for(const c of all){const tr=document.createElement('tr');for(const text of [c.id,c.assertion_count??'Original case','Not run']){const td=document.createElement('td');td.textContent=text;tr.append(td);}tbody.append(tr);}
document.querySelector('#status').textContent=`${all.length} translated cases ready. Full-suite completeness remains unverified.`;
document.querySelector('#run').addEventListener('click',async()=>{
 const result={source_commit:manifest.source_commit,reference_commit:manifest.reference_commit,status:'failed',complete_test_port:false,passed:0,additional_assertions:0,cases:[],errors:[]};
 const button=document.querySelector('#run');button.disabled=true;
 try{
  const response=await fetch('./blended_core.wasm');if(!response.ok)throw Error('WASM fetch failed');
  const {instance}=await WebAssembly.instantiate(await response.arrayBuffer(),{});const w=instance.exports;
  if(w.blended_case_count()!==manifest.legacy.length||w.blended_additional_case_count()!==manifest.additional.length)throw Error('Registry/manifest count mismatch');
  for(const [i,c] of all.entries()){
   let code,assertions=null;if(c.group==='legacy'){code=w.blended_run_case(c.index);}else{code=w.blended_additional_run_case(c.index);assertions=w.blended_additional_assertion_count(c.index);result.additional_assertions+=assertions;}
   const passed=code===1&&(c.group==='legacy'||assertions===c.assertion_count);result.cases.push({id:c.id,passed,code,assertions});if(passed)result.passed++;
   const td=tbody.children[i].lastElementChild;td.textContent=passed?'Passed':'Failed';td.className=passed?'pass':'fail';
  }
  result.invalid_index_rejected=w.blended_run_case(0xffffffff)===-1&&w.blended_additional_run_case(0xffffffff)===-1;
  if(result.passed===all.length&&result.invalid_index_rejected)result.status='passed';
 }catch(e){result.errors.push(String(e));}
 document.querySelector('#status').textContent=`${result.passed}/${all.length} passed. Full Blender test-port completeness: not established.`;
 window.__portResults=result;button.disabled=false;
});