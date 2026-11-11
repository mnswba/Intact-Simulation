import test from 'node:test';
import assert from 'node:assert/strict';
import {recentModels} from '../scripts/viewer/navigation.mjs';
const current={model_id:'current',name:'Current design'};
test('current model stays first even when it is the oldest model',()=>{
 const items=Array.from({length:8},(_,i)=>({model_id:String(i),name:'Example '+i,updated_at:i}));
 const result=recentModels([...items,{...current,updated_at:-100}],current);
 assert.deepEqual(result.map(m=>m.model_id),['current','7','6','5','4']);
});
test('current model is included when missing from library and uses its live name',()=>{
 assert.deepEqual(recentModels([],current),[current]);
 assert.equal(recentModels([{...current,name:'Old name'}],current)[0].name,'Current design');
});
test('duplicate models do not consume recent slots',()=>{
 const other={model_id:'other',name:'Other',updated_at:3};
 assert.deepEqual(recentModels([current,current,other,other],current).map(m=>m.model_id),['current','other']);
});
test('recent models are ordered by save time rather than name',()=>{
 const result=recentModels([{model_id:'a',name:'A old',updated_at:1},{model_id:'z',name:'Z new',updated_at:10}],current);
 assert.deepEqual(result.map(m=>m.model_id),['current','z','a']);
});
test('models without timestamps have a stable order and still obey the limit',()=>{
 const items=['f','b','e','a','c','d'].map(model_id=>({model_id,name:model_id}));
 assert.deepEqual(recentModels(items,current).map(m=>m.model_id),['current','a','b','c','d']);
});
