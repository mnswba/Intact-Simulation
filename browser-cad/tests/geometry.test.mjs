import {test} from 'node:test';
import assert from 'node:assert/strict';
import Module from 'manifold-3d';
import {buildRecipe,parseRecipe,validateRecipe,EXAMPLES,auditMesh} from '../core.mjs';
const api=await Module();api.setup();
const recipe=(nodes,result=nodes.at(-1).id)=>({format:'intact-browser-1',name:'Test',units:'mm',nodes,result});
test('Box has independently known volume, area and dimensions',()=>{
  const {report}=buildRecipe(api,recipe([{id:'box',type:'box',size:[40,30,20]}]));
  assert.deepEqual(report.dimensions,[40,30,20]);assert.equal(report.volume,24000);assert.equal(report.area,5200);assert.equal(report.closed,true);
  assert.equal(buildRecipe(api,recipe([{id:'box',type:'box',size:[40,30,20],translate:[10000,10000,10000]}])).report.volume,24000);
});
test('Boolean subtraction and translation produce known volume and bounds',()=>{
  const {report}=buildRecipe(api,recipe([{id:'a',type:'box',size:[20,20,20],translate:[5,0,0]},{id:'b',type:'box',size:[10,10,30],translate:[5,0,0]},{id:'c',type:'subtract',inputs:['a','b']}]));
  assert.equal(report.volume,6000);assert.deepEqual(report.bounds,{min:[-5,-10,-10],max:[15,10,10]});assert.equal(report.closed,true);
});
test('Union and intersection match exact rectangular overlap',()=>{
  const nodes=[{id:'a',type:'box',size:[10,10,10]},{id:'b',type:'box',size:[10,10,10],translate:[5,0,0]}];
  for(const [type,volume] of [['union',1500],['intersect',500]])assert.ok(Math.abs(buildRecipe(api,recipe([...nodes,{id:'out',type,inputs:['a','b']}])).report.volume-volume)<1e-8);
});
test('Sphere volume converges toward analytic reference with resolution',()=>{
  const v=n=>buildRecipe(api,recipe([{id:'ball',type:'sphere',radius:10,segments:n}])).report.volume;
  const target=4/3*Math.PI*1000,coarse=v(16),fine=v(128);
  assert.ok(Math.abs(fine-target)<Math.abs(coarse-target));assert.ok(Math.abs(fine/target-1)<.003);
});
test('Flange matches polygonal cylinder formula minus six polygonal holes',()=>{
  const result=buildRecipe(api,EXAMPLES.flange);
  const area=(r,n)=>n*r*r*Math.sin(2*Math.PI/n)/2;
  const expected=8*(area(40,96)-area(12,96)-6*area(3,32));
  assert.ok(Math.abs(result.report.volume-expected)<.1);assert.deepEqual(result.report.dimensions,[80,80,8]);assert.equal(result.report.closed,true);
});
test('Bracket example is closed, rotated box changes correct axes',()=>{
  assert.equal(buildRecipe(api,EXAMPLES.bracket).report.closed,true);
  const r=buildRecipe(api,recipe([{id:'a',type:'box',size:[20,10,6],rotate:[90,0,0]}])).report;
  for(const [i,target] of [20,6,10].entries())assert.ok(Math.abs(r.dimensions[i]-target)<1e-5);
});
test('Reject executable strings, foreign keys, forward refs, oversized recipes and nonfinite numbers',()=>{
  assert.throws(()=>parseRecipe('alert(1)'));
  assert.throws(()=>parseRecipe(' '.repeat(65537)));
  const good=recipe([{id:'a',type:'box',size:[1,2,3]}]);
  for(const bad of [{...good,url:'https://example.com'},{...good,units:'in'},{...good,nodes:[{id:'a',type:'box',size:[1,NaN,3]}]},{...good,nodes:[{id:'a',type:'subtract',inputs:['x','y']}]},{...good,nodes:Array(65).fill(good.nodes[0])}])assert.throws(()=>validateRecipe(bad));
  assert.deepEqual(parseRecipe('```json\n'+JSON.stringify(good)+'\n```'),good);
});
test('Empty booleans fail; repeated builds leave kernel usable',()=>{
  const same=[{id:'a',type:'box',size:[5,5,5]},{id:'b',type:'box',size:[5,5,5]},{id:'out',type:'subtract',inputs:['a','b']}];
  assert.throws(()=>buildRecipe(api,recipe(same)),/empty/);
  for(let i=0;i<30;i++)assert.equal(buildRecipe(api,recipe([{id:'a',type:'box',size:[2,3,4]}])).report.volume,24);
});
test('Independent mesh edge audit rejects an open triangle',()=>{
  const r=auditMesh(new Float32Array([0,0,0,1,0,0,0,1,0]),new Uint32Array([0,1,2]));assert.equal(r.closed,false);
});
