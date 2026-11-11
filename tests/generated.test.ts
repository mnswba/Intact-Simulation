import test from 'node:test';
import assert from 'node:assert/strict';
import {validateSpec,specFromDesign} from '../lib/engineering/spec.ts';
import {presets} from '../lib/engineering/model.ts';
import {partGeometry,validateMesh,generatedPythonExport} from '../lib/engineering/generated.ts';
function generated(){const spec=specFromDesign(presets.beam);spec.parts[0].template='custom';spec.parts[0].measurements={volume_mm3:42,surface_area_mm2:60,solid_count:1,face_count:6};spec.program={source:'import build123d as bd\ndef build(params):\n    return bd.Box(params["size"],2,3)',parameters:{size:7},artifact_id:'a'.repeat(64)};return spec;}
test('generated imports require source and finite measured geometry',()=>{const spec=generated();assert.equal(validateSpec(spec).parts[0].measurements?.volume_mm3,42);delete spec.parts[0].measurements;assert.throws(()=>validateSpec(spec),/measurements/);});
test('generated geometry never silently falls back to a template box',()=>{const spec=generated();assert.throws(()=>partGeometry(spec,'main'),/mesh is not loaded/);const mesh=validateMesh({version:1,units:'mm',coordinate_system:'viewer_y_up',parts:[{id:'main',positions:[0,0,0,1,0,0,0,1,0],indices:[0,1,2]}]});const geometry=partGeometry(spec,'main',mesh);assert.equal(geometry.getAttribute('position').count,3);geometry.dispose();mesh.parts[0].indices=[0,1,10];assert.throws(()=>validateMesh(mesh),/limits/);});
test('generated Python export preserves the actual program and parameter values',()=>{const spec=generated();const source=generatedPythonExport(spec);assert.ok(source.startsWith(spec.program!.source));assert.ok(source.includes('"size":7'));assert.ok(source.includes('bd.export_step'));});
