import test from 'node:test';
import assert from 'node:assert/strict';
// @ts-ignore Browser-neutral workflow helper.
import {saveAndDispatchAI,dispatchAI,hasDirectChat} from '../scripts/viewer/direct-ai.mjs';
const data={request_id:'request',model_id:'model',revision:10,intent:'simulation',instructions:'Apply 1000N force from the top and analyze its deflection'};
test('persists references before sending a ChatGPT follow-up; does not open annotations or run twice',async()=>{
 const calls:string[]=[];let sent:any;
 const host={openai:{async sendFollowUpMessage(value:any){calls.push('send');sent=value;}},document:{oai:{annotation:{request(){throw Error('Annotation must not open');}}}}};
 assert(hasDirectChat(host));const result=await saveAndDispatchAI(data,{save:async(r:any)=>{calls.push('save');return r;},host,run:async()=>{calls.push('run');}});
 assert.deepEqual(calls,['save','send']);assert.equal(result.transport,'chatgpt');assert(sent.scrollToBottom);assert(sent.prompt.includes('read_edit_request'));assert(sent.prompt.includes('1000N'));assert(sent.prompt.includes('request_id=request'));
});
test('annotation-only browser automatically starts local AI, with no annotation editor',async()=>{
 let count=0;const host={document:{oai:{annotation:{request(){throw Error('Annotation must not open');}}}}};
 assert(!hasDirectChat(host));assert.equal(await dispatchAI(data,{host,run:async r=>{assert.deepEqual(r,data);count++;}}),'local');assert.equal(count,1);
});
test('failed save never sends, failed host send never starts a duplicate local task',async()=>{
 let sent=0,run=0;const host={openai:{async sendFollowUpMessage(){sent++;throw Error('Host failed');}}};
 await assert.rejects(saveAndDispatchAI(data,{save:async()=>{throw Error('Stale reference');},host,run:async()=>run++}),/Stale/);assert.equal(sent,0);
 await assert.rejects(saveAndDispatchAI(data,{save:async()=>data,host,run:async()=>run++}),/Host failed/);assert.equal(sent,1);assert.equal(run,0);
});
