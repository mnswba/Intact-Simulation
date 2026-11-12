/** Disposable fixture only. --live uses the signed-in local client; host bridge is contract-tested separately. */
import fs from 'node:fs';import assert from 'node:assert/strict';
const {chromium}=await import(process.env.INTACT_PLAYWRIGHT_MODULE||'playwright');
const base=process.argv[2];if(!base?.endsWith('/'))throw Error('Supply disposable fixture base URL ending in /.');
async function until(check,timeout=20000){const deadline=Date.now()+timeout;while(Date.now()<deadline){if(await check())return;await new Promise(r=>setTimeout(r,500));}throw Error('Timed out waiting for AI/solver evidence.');}
const live=process.argv.includes('--live'),browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']}),page=await browser.newPage({viewport:{width:1400,height:1000}}),errors=[];
page.on('pageerror',e=>errors.push(e.message));let localRuns=0;
await page.addInitScript(()=>{window.annotationCalls=0;document.oai={annotation:{request(){window.annotationCalls++;throw Error('Ask AI must never open Annotation');}}};});
if(!live){await page.addInitScript(()=>{window.sent=[];window.openai={sendFollowUpMessage:async message=>{const rows=await fetch('requests.json').then(r=>r.json());if(!rows.requests.some(r=>message.prompt.includes(r.request_id)))throw Error('Request not saved before host message');window.sent.push(message);}};});await page.route('**/run-edit',route=>{localRuns++;return route.fulfill({json:{status:'processing'}});});}
try{
 await page.goto(base+'view');await page.waitForSelector('body[data-ready=true]');assert(await page.locator('#brand img').isVisible());assert.equal(await page.locator('#brand img').getAttribute('alt'),'Intact Simulation');
 await page.locator('#workspace-simulation').click();assert.equal(await page.locator('#sim-run').count(),0);assert.equal(await page.getByRole('button',{name:'Run Analysis',exact:true}).count(),0);
 const description='Apply 1000N force from the top and analyze its deflection. Analyze body only: E=10 GPa, Poisson ratio 0, fixed bottom face (CAD Z minimum), total force [0,0,-1000] N uniformly distributed on top face (Z maximum). Run structural analysis with automatic mesh sizing and refinement; report displacement, stress and reactions.';
 await page.locator('#sim-description').fill(description);if(!process.argv.includes('--resume'))await page.locator('#sim-ai').click();await until(()=>page.evaluate(async()=>{const rows=await fetch('requests.json').then(r=>r.json());return rows.requests.length>0;}));
 assert.equal(await page.evaluate(()=>window.annotationCalls),0);assert(await page.locator('#sim-ai-context').isHidden());assert(await page.locator('#ai-chat-context').isHidden());
 if(live){
  await until(()=>page.evaluate(async()=>{const rows=await fetch('requests.json').then(r=>r.json());return rows.requests[0]?.direct_run===true;}));
  await until(()=>page.evaluate(async()=>{const rows=await fetch('requests.json').then(r=>r.json());return ['succeeded','needs_review','failed','awaiting_reply'].includes(rows.requests[0]?.status);}),360000);
  const result=await page.evaluate(async()=>{const rows=await fetch('requests.json').then(r=>r.json());const w=await fetch('simulation.json').then(r=>r.json());return {request:rows.requests[0],workspace:w};});
  if(result.request.status!=='succeeded')throw Error(JSON.stringify({status:result.request.status,error:result.request.error,answer:result.request.answer,progress:result.request.progress}));
  await page.waitForSelector('#sim-field',{timeout:15000});assert.match(await page.locator('#sim-range').textContent(),/displacement_mm/);
  const report=await page.evaluate(async()=>{const w=await fetch('simulation.json').then(r=>r.json());const r=w.reports.find(r=>r.kind==='structural');return fetch('engineering-file?report_id='+r.report_id+'&file=report.json').then(r=>r.json());});assert(Math.abs(report.maximum-.02)<1e-6);assert(Math.abs(report.reaction_force_n[2]-1000)<1e-5);assert(report.convergence.passed);
  fs.mkdirSync('outputs/ask-ai-016',{recursive:true});fs.writeFileSync('outputs/ask-ai-016/live-result.json',JSON.stringify({status:result.request.status,answer:result.request.answer,kind:report.kind,displacement_mm:report.maximum,reaction_force_n:report.reaction_force_n,convergence:report.convergence,stress_convergence:report.stress_convergence,vertices:report.vertices,tetrahedra:report.tetrahedra,errors},null,2));await page.screenshot({path:'outputs/ask-ai-016/live-result.png'});
  // Editing the brief must immediately clear the old field and unrelated prepared studies.
  await page.locator('#sim-description').fill('New thermal request with other boundaries');assert(await page.locator('#sim-result').isHidden());assert.equal(await page.locator('#sim-plan').textContent(),'');
 }else{await page.waitForFunction(()=>window.sent?.length===1);assert.equal(localRuns,0);assert.match(await page.evaluate(()=>window.sent[0].prompt),/1000N/);assert.match(await page.evaluate(()=>window.sent[0].prompt),/submit a simulate engineering job/);}
 assert.deepEqual(errors,[]);console.log('PASS',live?'Live signed-in AI → real 1000 N structural solver → fields/results, and stale result clearing':'Persisted request → direct ChatGPT bridge contract, no Annotation, no duplicate local run', 'logo and single Mechanical Ask AI button.');
}finally{await browser.close();}
