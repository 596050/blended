// SPDX-License-Identifier: GPL-3.0-or-later
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {TransformControls} from 'three/addons/controls/TransformControls.js';
import {OBJLoader} from 'three/addons/loaders/OBJLoader.js';
import {STLLoader} from 'three/addons/loaders/STLLoader.js';
import {OBJExporter} from 'three/addons/exporters/OBJExporter.js';
import {STLExporter} from 'three/addons/exporters/STLExporter.js';
import {History,validateDocument} from './model.mjs';
const $=id=>document.getElementById(id),host=$('canvas-host');
let wasm,registry,history,selected=null,ready=false,dirty=false;
let scene,camera,renderer,orbit,gizmo,models,grid;const meshes=new Map();
const status=(text,error=false)=>{$('status').textContent=text;$('status').className=error?'error':'';};
const safe=fn=>(...args)=>{try{const value=fn(...args);if(value?.catch)value.catch(e=>status(e.message,true));}catch(e){status(e.message,true);}};
function download(blob,name){const u=URL.createObjectURL(blob),a=document.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),10000);}
function rustGeometry(kind){const ok=kind==='cube'?wasm.blended_make_box(2,2,2):wasm.blended_make_plane(4,4);if(ok!==1)throw new Error('Rust rejected the primitive dimensions');
 const pp=wasm.blended_positions_ptr()>>>0,pl=wasm.blended_positions_len(),ip=wasm.blended_indices_ptr()>>>0,il=wasm.blended_indices_len();
 return {positions:Array.from(new Float32Array(wasm.memory.buffer,pp,pl)),indices:Array.from(new Uint32Array(wasm.memory.buffer,ip,il))};}
function geometryData(g){const positions=Array.from(g.getAttribute('position').array);const indices=g.index?Array.from(g.index.array):Array.from({length:positions.length/3},(_,i)=>i);return {positions,indices};}
function object(name,data){return {id:crypto.randomUUID(),name,...data,position:[0,0,0],rotation:[0,0,0],scale:[1,1,1],colour:'#c68052',roughness:.48,metalness:.08};}
function commit(doc,label){if(history.commit(doc)){dirty=true;renderDocument();status(label);}}
function modify(fn,label){const d=history.current;fn(d);commit(d,label);}
function active(){return history.current.objects.find(o=>o.id===selected);}
function select(id){selected=id;updateInspector();updateOutliner();const mesh=meshes.get(id);if(mesh)gizmo.attach(mesh);else gizmo.detach();}
function updateOutliner(){const d=history.current;$('outliner').replaceChildren();for(const o of d.objects){const b=document.createElement('button');b.textContent='◇  '+o.name;b.dataset.id=o.id;b.className=o.id===selected?'selected':'';b.onclick=()=>select(o.id);$('outliner').append(b);}$('object-count').textContent=d.objects.length;}
function updateInspector(){const o=active();for(const input of $('inspector').querySelectorAll('input'))input.disabled=!o;
 $('duplicate').disabled=$('delete').disabled=!o;
 if(!o)return;$('object-name').value=o.name;$('colour').value=o.colour;$('roughness').value=o.roughness;$('metalness').value=o.metalness;
 for(const key of ['position','rotation','scale'])for(let i=0;i<3;i++){const value=key==='rotation'?THREE.MathUtils.radToDeg(o[key][i]):o[key][i];$(`${key}-${i}`).value=Number(value.toFixed(5));}}
function renderDocument(){gizmo.detach();for(const m of meshes.values()){m.geometry.dispose();m.material.dispose();}models.clear();meshes.clear();
 const d=history.current;let verts=0,triangles=0;
 for(const o of d.objects){const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(o.positions,3));g.setIndex(o.indices);g.computeVertexNormals();g.computeBoundingSphere();const material=new THREE.MeshStandardMaterial({color:o.colour,roughness:o.roughness,metalness:o.metalness,side:THREE.DoubleSide,wireframe:$('wire').checked});const m=new THREE.Mesh(g,material);m.name=o.name;m.userData.id=o.id;m.position.fromArray(o.position);m.rotation.set(...o.rotation);m.scale.fromArray(o.scale);models.add(m);meshes.set(o.id,m);verts+=o.positions.length/3;triangles+=o.indices.length/3;}
 if(!meshes.has(selected))selected=d.objects[0]?.id??null;select(selected);
 $('stats').textContent=`${d.objects.length} objects · ${verts.toLocaleString()} vertices · ${triangles.toLocaleString()} triangles`;
 $('undo').disabled=!history.canUndo;$('redo').disabled=!history.canRedo;renderer.render(scene,camera);}
function frameAll(){models.updateMatrixWorld(true);const box=new THREE.Box3().setFromObject(models);if(box.isEmpty())return;const sphere=box.getBoundingSphere(new THREE.Sphere());orbit.target.copy(sphere.center);const dist=Math.max(2,sphere.radius*2.9);camera.position.copy(sphere.center).add(new THREE.Vector3(1,.75,1).normalize().multiplyScalar(dist));camera.near=Math.max(.001,dist/10000);camera.far=Math.max(1000,dist*100);camera.updateProjectionMatrix();orbit.update();}
function add(kind){let data;if(kind==='sphere'){const g=new THREE.SphereGeometry(1,32,20);data=geometryData(g);g.dispose();}else data=rustGeometry(kind);const o=object(kind[0].toUpperCase()+kind.slice(1),data);selected=o.id;modify(d=>d.objects.push(o),`Added ${kind}`);}
function duplicate(){const o=active();if(!o)return;o.id=crypto.randomUUID();o.name=(o.name+' copy').slice(0,120);o.position[0]+=2.5;selected=o.id;modify(d=>d.objects.push(o),'Duplicated object');}
function remove(){if(!selected)return;modify(d=>{d.objects=d.objects.filter(o=>o.id!==selected);},'Deleted object');}
function undo(){if(history.undo()){dirty=true;renderDocument();status('Undo');}}
function redo(){if(history.redo()){dirty=true;renderDocument();status('Redo');}}
function updateProperty(key,value){modify(d=>{const o=d.objects.find(o=>o.id===selected);if(o)o[key]=value;},'Updated '+key);}
async function importModel(file){if(!file)return;if(file.size>20*1024*1024)throw new Error('This alpha limits imports to 20 MB');const added=[];
 if(file.name.toLowerCase().endsWith('.obj')){const group=new OBJLoader().parse(await file.text());group.updateMatrixWorld(true);group.traverse(m=>{if(m.isMesh){const g=m.geometry.clone().applyMatrix4(m.matrixWorld);added.push(object((m.name||file.name).slice(0,120),geometryData(g)));g.dispose();m.geometry.dispose();}});}
 else if(file.name.toLowerCase().endsWith('.stl')){const g=new STLLoader().parse(await file.arrayBuffer());added.push(object(file.name.slice(0,120),geometryData(g)));g.dispose();}
 else throw new Error('Only standalone OBJ and STL meshes are supported');
 if(!added.length)throw new Error('No triangle meshes were found');selected=added[0].id;modify(d=>d.objects.push(...added),'Imported '+file.name);frameAll();}
async function openScene(file){if(!file)return;if(file.size>20*1024*1024)throw new Error('Scene file is too large');const d=JSON.parse(await file.text());validateDocument(d);selected=d.objects[0]?.id??null;commit(d,'Opened scene');frameAll();}
async function runTests(){const rows=registry.cases.map(c=>({id:c.id,passed:wasm.blended_run_case(c.wasm_index)===1}));const result={status:rows.every(x=>x.passed)?'passed':'failed',passed:rows.filter(x=>x.passed).length,cases:rows,scope:'17 upstream mathematical cases, not full Blender parity'};window.__blendedCompatibility=result;return result;}
function wireUI(){for(const key of ['position','rotation','scale']){const div=document.createElement('div');div.className='transform';const p=document.createElement('p');p.textContent=key==='position'?'Location · metres':key==='rotation'?'Rotation · degrees':'Scale';div.append(p);const row=document.createElement('div');row.className='triple';for(let i=0;i<3;i++){const label=document.createElement('label');label.textContent=['X','Y','Z'][i];const input=document.createElement('input');input.type='number';input.id=`${key}-${i}`;input.step=key==='rotation'?'1':'0.1';input.setAttribute('aria-label',`${key} ${['X','Y','Z'][i]}`);input.onchange=safe(()=>{const o=active();if(!o)return;const value=Number(input.value);o[key][i]=key==='rotation'?THREE.MathUtils.degToRad(value):value;updateProperty(key,o[key]);});label.append(input);row.append(label);}div.append(row);$('transform-fields').append(div);}
 document.querySelectorAll('[data-add]').forEach(b=>b.onclick=safe(()=>add(b.dataset.add)));
 document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{gizmo.setMode(b.dataset.mode);document.querySelectorAll('[data-mode]').forEach(x=>x.classList.toggle('active',x===b));});
 for(const [id,fn] of Object.entries({duplicate,delete:remove,undo,redo,frame:frameAll}))$(id).onclick=safe(fn);
 $('object-name').onchange=safe(()=>updateProperty('name',$('object-name').value));$('colour').onchange=safe(()=>updateProperty('colour',$('colour').value));
 for(const key of ['roughness','metalness'])$(key).onchange=safe(()=>updateProperty(key,Number($(key).value)));
 $('wire').onchange=()=>{for(const m of meshes.values())m.material.wireframe=$('wire').checked;};$('grid').onchange=()=>grid.visible=$('grid').checked;
 $('save').onclick=safe(()=>{download(new Blob([JSON.stringify(history.current)],{type:'application/json'}),'scene.blended.json');dirty=false;status('Scene downloaded');});
 $('open').onclick=()=>$('open-file').click();$('open-file').onchange=safe(async()=>{await openScene($('open-file').files[0]);$('open-file').value='';});
 $('import').onclick=()=>$('import-file').click();$('import-file').onchange=safe(async()=>{await importModel($('import-file').files[0]);$('import-file').value='';});
 $('export-obj').onclick=safe(()=>{models.updateMatrixWorld(true);download(new Blob([new OBJExporter().parse(models)],{type:'text/plain'}),'scene.obj');status('OBJ geometry exported; materials are not exported');});
 $('export-stl').onclick=safe(()=>{models.updateMatrixWorld(true);const data=new STLExporter().parse(models,{binary:true});download(new Blob([data],{type:'application/octet-stream'}),'scene.stl');status('STL geometry exported');});
 $('image').onclick=safe(()=>{gizmo.getHelper().visible=false;renderer.render(scene,camera);renderer.domElement.toBlob(blob=>{if(blob)download(blob,'blended.png');gizmo.getHelper().visible=true;},'image/png');});
 $('tests').onclick=safe(async()=>{const r=await runTests();$('test-results').replaceChildren();for(const c of r.cases){const row=document.createElement('div');row.textContent=(c.passed?'PASS  ':'FAIL  ')+c.id;$('test-results').append(row);}$('test-dialog').showModal();status(`${r.passed} / ${r.cases.length} Rust WASM checks passed`);});$('close-tests').onclick=()=>$('test-dialog').close();
 window.addEventListener('keydown',safe(e=>{if(['INPUT','TEXTAREA'].includes(document.activeElement?.tagName))return;if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='z'){e.preventDefault();e.shiftKey?redo():undo();}else if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='y'){e.preventDefault();redo();}else if(e.key==='Delete')remove();}));
 window.addEventListener('beforeunload',e=>{if(dirty){e.preventDefault();e.returnValue='';}});
}
async function boot(){const [binary,manifest]=await Promise.all([fetch('./compat/blended_core.wasm'),fetch('./compat/ports.json')]);if(!binary.ok||!manifest.ok)throw new Error('Missing Rust compatibility build');registry=await manifest.json();wasm=(await WebAssembly.instantiate(await binary.arrayBuffer(),{})).instance.exports;
 if(wasm.blended_case_count()!==17||typeof wasm.blended_make_box!=='function')throw new Error('Incorrect Rust ABI');
 scene=new THREE.Scene();scene.background=new THREE.Color('#1b272e');camera=new THREE.PerspectiveCamera(45,1,.01,1000);camera.position.set(6,4.5,7);
 renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.3;renderer.domElement.id='viewport';host.append(renderer.domElement);
 scene.add(new THREE.HemisphereLight(0xdceaf3,0x6c604d,2));const key=new THREE.DirectionalLight(0xffe7cf,3.5);key.position.set(5,8,6);scene.add(key);const fill=new THREE.DirectionalLight(0xb3d5ff,1.7);fill.position.set(-5,3,-4);scene.add(fill);
 grid=new THREE.GridHelper(20,20,0x667f88,0x344951);grid.position.y=-1.01;scene.add(grid);models=new THREE.Group();scene.add(models);
 orbit=new OrbitControls(camera,renderer.domElement);orbit.enableDamping=true;gizmo=new TransformControls(camera,renderer.domElement);gizmo.setSize(.8);scene.add(gizmo.getHelper());
 gizmo.addEventListener('dragging-changed',e=>{orbit.enabled=!e.value;});gizmo.addEventListener('mouseUp',safe(()=>{const m=meshes.get(selected);if(!m)return;modify(d=>{const o=d.objects.find(o=>o.id===selected);o.position=m.position.toArray();o.rotation=[m.rotation.x,m.rotation.y,m.rotation.z];o.scale=m.scale.toArray();},'Transformed object');}));
 const ray=new THREE.Raycaster();let start=null;renderer.domElement.addEventListener('pointerdown',e=>{start=[e.clientX,e.clientY];});renderer.domElement.addEventListener('pointerup',e=>{if(!start||gizmo.axis||Math.hypot(e.clientX-start[0],e.clientY-start[1])>4)return;const r=renderer.domElement.getBoundingClientRect();ray.setFromCamera(new THREE.Vector2((e.clientX-r.left)/r.width*2-1,1-(e.clientY-r.top)/r.height*2),camera);const hit=ray.intersectObjects(models.children,false)[0];if(hit)select(hit.object.userData.id);});
 wireUI();history=new History({schema:1,objects:[object('Cube',rustGeometry('cube'))]});renderDocument();
 const resize=()=>{const w=host.clientWidth,h=host.clientHeight;if(!w||!h)return;camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h);};new ResizeObserver(resize).observe(host);resize();
 renderer.setAnimationLoop(()=>{orbit.update();renderer.render(scene,camera);});$('loading').remove();ready=true;status('Ready · cube and plane geometry generated in Rust');
 window.__blended={ready:true,getDocument:()=>history.current,runCompatibility:runTests,getRenderStats:()=>({...renderer.info.render}),getPrimitiveBounds:()=>{const data=rustGeometry('cube');return [Math.min(...data.positions),Math.max(...data.positions)];}};
}
boot().catch(e=>{$('loading').textContent='Could not start: '+e.message;status(e.message,true);window.__blended={ready:false,error:e.message};console.error(e);});
