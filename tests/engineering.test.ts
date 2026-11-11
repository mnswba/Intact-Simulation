import {test} from 'node:test';
import assert from 'node:assert/strict';
import {runAnalysis,defaultStudy,signature} from '../lib/engineering/analysis.ts';
import {presets,materials,guidedDesign,validateDesign,volume} from '../lib/engineering/model.ts';
test('cantilever FEM agrees with the analytical tip displacement and stress',()=>{
  const d=presets.beam,s={...defaultStudy,nodes:21};const r=runAnalysis(d,s);
  const L=d.length/1000,b=d.width/1000,h=d.height/1000,I=b*h**3/12;
  const exact=s.force*L**3/(3*materials[d.material].E*I)*1000;
  assert.ok(Math.abs(r.tip-exact)/exact<1e-7);
  assert.ok(Math.abs(r.peak-6*s.force*L/(b*h*h)/1e6)<1e-9);
  assert.equal(r.points[0].displacement,0);assert.equal(r.points.at(-1)!.value,0);
  assert.equal(r.signature,signature(d,s));
});
test('beam displacement scales linearly with load and inversely with thickness cubed',()=>{
  const base=runAnalysis(presets.beam,defaultStudy);
  const doubled=runAnalysis(presets.beam,{...defaultStudy,force:defaultStudy.force*2});
  const thick=runAnalysis({...presets.beam,height:presets.beam.height*2},defaultStudy);
  assert.ok(Math.abs(doubled.tip/base.tip-2)<1e-7);assert.ok(Math.abs(thick.tip/base.tip-.125)<1e-7);
});
test('thermal finite volumes conserve energy and converge toward the analytical fin',()=>{
  const s={...defaultStudy,type:'thermal' as const};const coarse=runAnalysis(presets.fin,{...s,nodes:21}),fine=runAnalysis(presets.fin,{...s,nodes:81});
  assert.ok(fine.balanceError!<1e-8);assert.ok(fine.referenceError<coarse.referenceError);assert.ok(fine.referenceError<.001);
  assert.ok(fine.peak>fine.tip&&fine.tip>s.ambient);assert.ok(fine.refinementError!<.001);
  assert.ok(fine.points.every((p,i)=>i===0||p.value<=fine.points[i-1].value));
});
test('temperature rise doubles when heat input doubles',()=>{
  const s={...defaultStudy,type:'thermal' as const};const a=runAnalysis(presets.fin,s),b=runAnalysis(presets.fin,{...s,heat:2*s.heat});assert.ok(Math.abs((b.peak-s.ambient)/(a.peak-s.ambient)-2)<1e-8);
});
test('unsupported geometries and nonphysical settings are refused',()=>{
  assert.throws(()=>runAnalysis(presets.heatsink,defaultStudy),/cantilever/);
  assert.throws(()=>runAnalysis(presets.beam,{...defaultStudy,force:NaN}),/Tip load/);
  assert.throws(()=>runAnalysis(presets.fin,{...defaultStudy,type:'thermal',convection:0}),/positive/);
  assert.throws(()=>runAnalysis(presets.fin,{...defaultStudy,type:'thermal',nodes:1}),/nodes/);
});
test('guided commands produce validated specs and do not claim unrestricted generation',()=>{
  const r=guidedDesign('Create a copper fin 80 x 40 x 3 mm',presets.heatsink);assert.equal(r.design.kind,'fin');assert.equal(r.design.material,'copper');assert.equal(r.design.height,3);
  const b=guidedDesign('width to 45',presets.beam);assert.equal(b.design.width,45);
  assert.equal(guidedDesign('heat sink 100 x 80 x 35 mm with 12 fins',presets.beam).design.finCount,12);
  assert.throws(()=>guidedDesign('Design an entire jet engine',presets.beam),/Guided mode/);
  assert.throws(()=>guidedDesign('beam 0 x 30 x 8',presets.beam),/Dimensions/);
});
test('project import rejects malicious enum fields, huge dimensions and nonfinite values',()=>{
  assert.throws(()=>validateDesign({...presets.beam,material:'__proto__'}),/Unsupported/);
  assert.throws(()=>validateDesign({...presets.beam,length:1e9}),/Dimensions/);
  assert.throws(()=>validateDesign({...presets.beam,height:NaN}),/Dimensions/);
  assert.throws(()=>validateDesign({...presets.heatsink,finCount:1000}),/fins/);
  assert.equal(volume(presets.beam),presets.beam.length*presets.beam.width*presets.beam.height);
});
test('invalid model assumptions produce visible warnings',()=>{
  assert.ok(runAnalysis({...presets.beam,height:30},defaultStudy).warnings.some(w=>w.includes('shear')));
  assert.ok(runAnalysis(presets.beam,{...defaultStudy,force:1e5}).warnings.some(w=>w.includes('yield')));
});
