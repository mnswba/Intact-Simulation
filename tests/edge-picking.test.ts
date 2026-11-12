import test from 'node:test';
import assert from 'node:assert/strict';
import {closestEdgeCandidates} from '../scripts/viewer/edge-picking.mjs';
const edge=(ref:string,y=0)=>({ref,partId:'part',a:[0,y,0,1],b:[100,y,0,1],worldA:[0,0,0],worldB:[100,0,0]});
test('edge picking accepts a near miss outside the solid silhouette in CSS pixels',()=>{
 assert.equal(closestEdgeCandidates([edge('part.e1')],40,-15,16)[0].ref,'part.e1');
 assert.equal(closestEdgeCandidates([edge('part.e1')],40,-17,16).length,0);
});
test('segments deduplicate by native reference and candidates order by distance',()=>{
 const hits=closestEdgeCandidates([edge('part.e2',4),edge('part.e1'),edge('part.e1',2)],50,0);
 assert.deepEqual(hits.map(x=>x.ref),['part.e1','part.e2']);
});
test('3D candidate points use perspective-correct interpolation',()=>{
 const e=edge('part.e1');e.b[3]=2;
 assert.ok(Math.abs(closestEdgeCandidates([e],50,0)[0].world[0]-100/3)<1e-9);
});
test('behind-camera and nonfinite segments cannot select hidden or invalid references',()=>{
 const behind=edge('part.e1');behind.a[3]=-1;const invalid=edge('part.e2');invalid.b[0]=NaN;
 assert.deepEqual(closestEdgeCandidates([behind,invalid],50,0),[]);
});
test('coincident and short edges remain selectable and tie-break deterministically',()=>{
 const a=edge('part.e2');a.b=[0,0,0,1];const b={...a,ref:'part.e1'};
 assert.deepEqual(closestEdgeCandidates([a,b],0,0).map(x=>x.ref),['part.e1','part.e2']);
});
