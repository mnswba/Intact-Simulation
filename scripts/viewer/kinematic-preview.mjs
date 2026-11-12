import * as THREE from 'three';
import {createVehicleDriveController} from './vendor/scout-driving-controller.mjs';
// Display adapter: CAD metres (+X forward, +Y left, +Z up) → viewer mm, Y up.
export function createKinematicPreview({parent,parts,plan,onChange=()=>{}}){
 const displayScale=parent.getWorldScale(new THREE.Vector3());if(Math.max(...displayScale.toArray())-Math.min(...displayScale.toArray())>1e-8)throw Error('Kinematic preview requires a uniformly scaled display frame.');
 const ids=plan.moving_part_ids?.length?plan.moving_part_ids:[...parts.keys()];
 const moving=ids.map(id=>{const object=parts.get(id);if(!object?.parent)throw Error('Missing preview part: '+id);return object;});
 const bound=[...(plan.wheels||[]).flatMap(w=>w.part_ids),...(plan.joints||[]).map(j=>j.part_id)];
 if(new Set(bound).size!==bound.length||bound.some(id=>!ids.includes(id)))throw Error('Invalid or duplicate part bindings.');
 const rest=moving.map(object=>{if(object.matrixAutoUpdate)object.updateMatrix();return {object,parent:object.parent,index:object.parent.children.indexOf(object),position:object.position.clone(),quaternion:object.quaternion.clone(),scale:object.scale.clone(),matrix:object.matrix.clone(),auto:object.matrixAutoUpdate};});
 const adapter=new THREE.Group(),root=new THREE.Group();adapter.name='__kinematic_display_adapter';adapter.userData.previewOnly=true;adapter.rotation.x=-Math.PI/2;adapter.scale.setScalar(1000);parent.add(adapter);adapter.add(root);parent.updateWorldMatrix(true,true);let inner,disposed=false;const temporaryGroups=[];
 function restore(){for(const saved of rest){saved.parent.add(saved.object);saved.object.position.copy(saved.position);saved.object.quaternion.copy(saved.quaternion);saved.object.scale.copy(saved.scale);saved.object.matrix.copy(saved.matrix);saved.object.matrixAutoUpdate=saved.auto;const children=saved.parent.children;children.splice(children.indexOf(saved.object),1);children.splice(Math.min(saved.index,children.length),0,saved.object);}for(const group of temporaryGroups)group.removeFromParent();adapter.removeFromParent();parent.updateWorldMatrix(true,true);}
 try{
  for(const object of moving)root.attach(object);
  if(plan.kind==='vehicle'){
   inner=createVehicleDriveController({THREE,root,wheelAssemblies:plan.wheels.map(w=>({id:w.id,pivot:w.pivot_m,parts:w.part_ids.map(id=>parts.get(id))})),radius:plan.radius_m,speed:plan.speed_m_s,onChange});
   // Supplied drive controller uses CAD +X. Rotate direction only; wheel axle stays CAD +Y.
   if(plan.direction&&new THREE.Vector3(...plan.direction).normalize().distanceTo(new THREE.Vector3(1,0,0))>1e-6)throw Error('Vehicle driving uses CAD +X; orient the plan/model frame explicitly before driving.');
  }else{
   const pivots=new Map(),jointPlans=plan.joints||[];
   for(const j of jointPlans){const pivot=new THREE.Group();pivot.userData.previewOnly=true;temporaryGroups.push(pivot);pivot.position.fromArray(j.pivot_m);root.add(pivot);pivots.set(j.part_id,{pivot,j});}
   for(const j of jointPlans){const entry=pivots.get(j.part_id);if(j.parent_id){const target=pivots.get(j.parent_id)?.pivot||parts.get(j.parent_id);if(!target)throw Error('Missing parent: '+j.parent_id);target.attach(entry.pivot);}entry.pivot.attach(parts.get(j.part_id));entry.axis=new THREE.Vector3(...j.axis).normalize();entry.restQ=entry.pivot.quaternion.clone();}
   let time=0,playing=false;const duration=plan.duration_s,direction=new THREE.Vector3(...plan.direction).normalize();
   const state=()=>({time,duration,playing,distance:['walk','translate'].includes(plan.kind)?plan.speed_m_s*time:0,speed:plan.speed_m_s,mode:'kinematic-preview'});
   function setTime(value){if(!Number.isFinite(value))throw Error('Preview time must be finite.');time=THREE.MathUtils.clamp(value,0,duration);root.position.copy(direction).multiplyScalar(['walk','translate'].includes(plan.kind)?plan.speed_m_s*time:0);root.quaternion.identity();if(plan.kind==='rotate')root.quaternion.setFromAxisAngle(direction,time/duration*Math.PI*2);for(const {pivot,j,axis,restQ} of pivots.values()){const angle=THREE.MathUtils.degToRad(j.amplitude_deg)*Math.sin(2*Math.PI*j.frequency_hz*time+THREE.MathUtils.degToRad(j.phase_deg));pivot.quaternion.copy(restQ).multiply(new THREE.Quaternion().setFromAxisAngle(axis,angle));}root.updateMatrixWorld(true);onChange(state());return state();}
   inner={duration,getState:state,setTime,play(){if(time>=duration)setTime(0);playing=true;return state();},pause(){playing=false;return state();},update(dt){if(!Number.isFinite(dt)||dt<0)throw Error('Invalid frame delta.');if(playing){setTime(time+dt);if(time>=duration)playing=false;}return state();},dispose(){playing=false;}};setTime(0);
  }
 }catch(e){restore();throw e;}
 return {getState:()=>inner.getState(),play:()=>inner.play(),pause:()=>inner.pause(),seek(t){inner.pause();return inner.setTime(t);},replay(){inner.setTime(0);return inner.play();},update(dt){if(!disposed)return inner.update(dt);},dispose(){if(disposed)return;try{inner.dispose();}finally{restore();disposed=true;}}};
}
