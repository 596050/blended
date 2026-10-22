// SPDX-License-Identifier: GPL-3.0-or-later
/** Validate before changing application state or allocating GPU geometry. */
export function validateDocument(doc){
 const fail=message=>{throw new Error(message);};
 if(!doc||doc.schema!==1||!Array.isArray(doc.objects)||doc.objects.length>100)fail('Unsupported or oversized scene');
 let total=0;const ids=new Set();
 const vector=(v,positive=false)=>Array.isArray(v)&&v.length===3&&v.every(x=>Number.isFinite(x)&&Math.abs(x)<=1e9&&(!positive||x>1e-6));
 for(const o of doc.objects){
  if(!o||typeof o.id!=='string'||!o.id||o.id.length>128||ids.has(o.id))fail('Invalid or duplicate object identity');ids.add(o.id);
  if(typeof o.name!=='string'||o.name.length>120)fail('Invalid object name');
  if(!Array.isArray(o.positions)||o.positions.length<9||o.positions.length%3||o.positions.length>900000||!o.positions.every(x=>Number.isFinite(x)&&Math.abs(x)<=1e9))fail('Invalid geometry positions');
  if(!Array.isArray(o.indices)||!o.indices.length||o.indices.length%3||o.indices.length>1800000||!o.indices.every(x=>Number.isInteger(x)&&x>=0&&x<o.positions.length/3))fail('Invalid geometry indices');
  if(!vector(o.position)||!vector(o.rotation)||!vector(o.scale,true))fail('Invalid object transform');
  if(typeof o.colour!=='string'||!/^#[a-f0-9]{6}$/i.test(o.colour))fail('Invalid material colour');
  for(const key of ['roughness','metalness'])if(!Number.isFinite(o[key])||o[key]<0||o[key]>1)fail('Invalid material parameter');
  total+=o.positions.length;if(total>1800000)fail('Scene exceeds the current geometry budget');
 }
 return true;
}
/** Bounded, immutable command history. This early implementation snapshots
 * geometry; it does not claim Blender-scale memory efficiency. */
export class History{
 constructor(doc,limit=30){validateDocument(doc);this._states=[structuredClone(doc)];this._index=0;this._limit=Math.max(2,limit);}
 get current(){return structuredClone(this._states[this._index]);}
 get canUndo(){return this._index>0;}
 get canRedo(){return this._index+1<this._states.length;}
 commit(doc){validateDocument(doc);if(JSON.stringify(doc)===JSON.stringify(this._states[this._index]))return false;
  this._states=this._states.slice(0,this._index+1);this._states.push(structuredClone(doc));
  if(this._states.length>this._limit)this._states.shift();this._index=this._states.length-1;return true;}
 undo(){if(!this.canUndo)return false;this._index--;return true;}
 redo(){if(!this.canRedo)return false;this._index++;return true;}
}
