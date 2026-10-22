// SPDX-License-Identifier: GPL-3.0-or-later
const $ = id => document.getElementById(id);
let ports;
window.__blendedTestResults = { status: 'not_run', passed: 0, cases: [] };
const studio = $('open-studio');
studio.addEventListener('click', e => { if (studio.getAttribute('aria-disabled') === 'true') e.preventDefault(); });
async function json(path) {
  const r = await fetch(new URL(path, document.baseURI), {cache:'no-store'});
  if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
  return r.json();
}
function status(text, cls='') { $('run-status').textContent=text; $('run-status').className=`status ${cls}`; }
try {
  const [manifest,build]=await Promise.all([json('compat/ports.json'),json('build.json')]);
  ports=manifest;
  $('ported').textContent=String(ports.cases.length);
  for (const entry of ports.cases) {
    const tr=document.createElement('tr');
    for (const text of [entry.id,'Written; see CI for native results','Not run']) {
      const td=document.createElement('td'); td.textContent=text; tr.append(td);
    }
    tr.dataset.case=String(entry.wasm_index); $('case-list').append(tr);
  }
  $('solarxy-sha').textContent=build.upstreams.solarxy.commit;
  $('build-status').textContent=build.studio_built?'Diagnostic build; scene-rendering acceptance is failing':'Studio has not been built';
  $('build-id').textContent=build.source_commit?`Build ${build.source_commit.slice(0,12)}`:'No deployment verified';
  if(build.studio_built===true){studio.setAttribute('aria-disabled','false');studio.classList.remove('disabled');}
} catch(error) {
  $('error').hidden=false; $('error').textContent=`Could not read project status: ${error.message}`; $('run-checks').disabled=true;
}
$('run-checks').addEventListener('click',async()=>{
  $('run-checks').disabled=true; $('passed').textContent='0'; status('Running');
  window.__blendedTestResults={status:'running',passed:0,cases:[]};
  try {
    const r=await fetch(new URL('compat/blended_core.wasm',document.baseURI),{cache:'no-store'});
    if(!r.ok)throw new Error(`Rust WASM unavailable: HTTP ${r.status}`);
    const {instance}=await WebAssembly.instantiate(await r.arrayBuffer(),{});
    const api=instance.exports;
    if(api.blended_abi_version()!==1||api.blended_case_count()!==ports.cases.length)throw new Error('WASM ABI or manifest mismatch');
    if(api.blended_run_case(4294967295)!==-1)throw new Error('Unknown case incorrectly accepted');
    const cases=ports.cases.map(entry=>{
      const actual=api.blended_run_case(entry.wasm_index),passed=actual===1;
      const cell=document.querySelector(`tr[data-case="${entry.wasm_index}"]`).lastElementChild;
      cell.textContent=passed?'Passed':'Failed'; cell.className=passed?'result-passed':'result-failed';
      return {id:entry.id,passed,return_code:actual};
    });
    const passed=cases.filter(c=>c.passed).length,all=passed===ports.cases.length;
    $('passed').textContent=String(passed); status(`${passed} / ${ports.cases.length} passed`,all?'passed':'failed');
    window.__blendedTestResults={status:all?'passed':'failed',passed,cases,scope:'Standalone maths slice, not full Blender parity'};
  }catch(error){status('Blocked: WASM checks not completed','failed');$('error').hidden=false;$('error').textContent=error.message;window.__blendedTestResults={status:'blocked',passed:0,cases:[],reason:error.message};}
  finally{$('run-checks').disabled=false;}
});
