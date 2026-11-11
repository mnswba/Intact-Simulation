import * as THREE from 'three';
import {makeGeometry} from './geometry.ts';
import {designFromSpec} from './spec.ts';
import type {DesignSpec} from './spec.ts';
export type GeneratedMesh={version:1;units:'mm';coordinate_system:'viewer_y_up';parts:{id:string;positions:number[];indices:number[]}[]};
export function validateMesh(value:unknown):GeneratedMesh{
  if(!value||typeof value!=='object')throw new Error('The generated mesh is missing.');const m=value as GeneratedMesh;
  if(m.version!==1||m.units!=='mm'||m.coordinate_system!=='viewer_y_up'||!Array.isArray(m.parts)||!m.parts.length||m.parts.length>128)throw new Error('Unsupported generated mesh.');
  let vertices=0,triangles=0;const ids=new Set<string>();
  for(const p of m.parts){
    if(!/^[a-z][a-z0-9_]{0,47}$/.test(p.id)||ids.has(p.id)||!Array.isArray(p.positions)||p.positions.length%3||!p.positions.length||!Array.isArray(p.indices)||p.indices.length%3||!p.indices.length)throw new Error('Invalid generated part mesh.');ids.add(p.id);
    vertices+=p.positions.length/3;triangles+=p.indices.length/3;
    if(vertices>750000||triangles>1200000||p.positions.some(v=>!Number.isFinite(v)||Math.abs(v)>2e6)||p.indices.some(i=>!Number.isInteger(i)||i<0||i>=p.positions.length/3))throw new Error('Generated mesh exceeds its geometry limits.');
  }return m;
}
export function partGeometry(spec:DesignSpec,id:string,mesh?:GeneratedMesh|null){
  const part=spec.parts.find(p=>p.id===id)!;if(part.template!=='custom')return makeGeometry(designFromSpec(spec,id));
  const data=mesh?.parts.find(p=>p.id===id);if(!data)throw new Error('The generated CAD mesh is not loaded.');
  const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(data.positions,3));geometry.setIndex(data.indices);geometry.computeVertexNormals();return geometry;
}
function database():Promise<IDBDatabase>{return new Promise((resolve,reject)=>{const request=indexedDB.open('intact-generated-meshes',1);request.onupgradeneeded=()=>request.result.createObjectStore('meshes');request.onsuccess=()=>resolve(request.result);request.onerror=()=>reject(request.error);});}
export async function cacheMesh(id:string,mesh:GeneratedMesh){const db=await database();try{await new Promise<void>((resolve,reject)=>{const tx=db.transaction('meshes','readwrite');tx.objectStore('meshes').put(mesh,id);tx.oncomplete=()=>resolve();tx.onerror=()=>reject(tx.error);});}finally{db.close();}}
export async function readCachedMesh(id:string):Promise<GeneratedMesh|null>{const db=await database();try{return await new Promise((resolve,reject)=>{const request=db.transaction('meshes').objectStore('meshes').get(id);request.onsuccess=()=>resolve(request.result?validateMesh(request.result):null);request.onerror=()=>reject(request.error);});}finally{db.close();}}
export function generatedPythonExport(spec:DesignSpec){
  if(!spec.program)throw new Error('There is no CAD program.');
  if(spec.parts.some(p=>p.engine==='implicit_mesh'))throw new Error('Download the self-contained Python export from the Intact plugin viewer; TPMS also requires trimesh and scikit-image.');
  return spec.program.source+'\n\n# Reproduce this saved model in a build123d Python environment.\nif __name__ == "__main__":\n    import build123d as bd\n    params = '+JSON.stringify(spec.program.parameters)+'\n    result = build(params)\n    shapes = list(result.values()) if isinstance(result, dict) else list(result) if isinstance(result, (list, tuple)) else [result]\n    model = bd.Compound(children=shapes)\n    bd.export_step(model, "model.step")\n    bd.export_stl(model, "model.stl")\n';
}
