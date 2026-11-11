import {test} from 'node:test';
import assert from 'node:assert/strict';
import {presets} from '../lib/engineering/model.ts';
import {defaultStudy} from '../lib/engineering/analysis.ts';
import {specFromDesign,validateSpec,designFromSpec,replaceDesign,replaceStudy,localSpecKey,proposedBoundaries} from '../lib/engineering/spec.ts';
test('legacy designs round-trip through the canonical spec for every template',()=>{for(const d of Object.values(presets)){const spec=validateSpec(specFromDesign(d));assert.deepEqual(designFromSpec(spec),d);assert.equal(spec.units,'mm');assert.equal(spec.parts[0].engine,'build123d');}});
test('spec edits preserve identity, increment revision and invalidate approval',()=>{const s=specFromDesign(presets.beam);s.simulation.approved_fingerprint='a'.repeat(64);const next=replaceDesign(s,{...presets.beam,height:10});assert.equal(next.parts[0].id,s.parts[0].id);assert.equal(next.revision,2);assert.equal(next.simulation.approved_fingerprint,null);assert.notEqual(localSpecKey(s),localSpecKey(next));assert.equal(s.parts[0].params.height,8);});
test('loads change the spec and proposed named-face conditions',()=>{const s=specFromDesign(presets.beam);const next=replaceStudy(s,{...defaultStudy,force:100});assert.equal(proposedBoundaries(next)[1].value,'100 N ↓');assert.notEqual(localSpecKey(next),localSpecKey(s));});
test('spec imports reject invalid placements, duplicate IDs and nonfinite physics',()=>{const s=specFromDesign(presets.fin);assert.throws(()=>validateSpec({...s,parts:[s.parts[0],s.parts[0]]}),/identity/);assert.throws(()=>validateSpec({...s,parts:[{...s.parts[0],position:[Infinity,0,0]}]}),/placement/);assert.throws(()=>replaceStudy(s,{...defaultStudy,force:NaN}),/force/);});
