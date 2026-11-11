import {test} from 'node:test';
import assert from 'node:assert/strict';
import {makeGeometry} from '../lib/engineering/geometry.ts';
import {presets,volume} from '../lib/engineering/model.ts';
for(const d of Object.values(presets))test(`${d.kind} mesh has the declared dimensions, volume and closed edges`,()=>{
  const geometry=makeGeometry(d);geometry.computeBoundingBox();const b=geometry.boundingBox!;
  for(const [actual,expected] of [[b.max.x-b.min.x,d.length],[b.max.y-b.min.y,d.height],[b.max.z-b.min.z,d.width]])assert.ok(Math.abs(actual-expected)<1e-4);
  const g=geometry.index?geometry.toNonIndexed():geometry,p=g.getAttribute('position');let signed=0;const edges=new Map<string,number>();
  const vertex=(i:number)=>[p.getX(i),p.getY(i),p.getZ(i)];const key=(v:number[])=>v.map(x=>Math.round(x*10000)).join(',');
  for(let i=0;i<p.count;i+=3){const a=vertex(i),b=vertex(i+1),c=vertex(i+2);signed+=(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6;for(const [u,v] of [[a,b],[b,c],[c,a]]){const edge=[key(u),key(v)].sort().join('|');edges.set(edge,(edges.get(edge)||0)+1);}}
  assert.ok(Math.abs(Math.abs(signed)-volume(d))/volume(d)<.0001);
  assert.ok([...edges.values()].every(count=>count===2));
  g.dispose();geometry.dispose();
});
