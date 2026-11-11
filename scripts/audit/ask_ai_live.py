"""Click the real Ask AI button, ask a question, then change and verify native CAD."""
import asyncio,json,os,time
from pathlib import Path
from playwright.async_api import async_playwright
from intact_backend.projects import ProjectService
from intact_backend.feature_graph import FeatureService
from intact_backend.viewer_server import viewer_url
from intact_backend.edit_requests import EditRequests
from p1_examples import CIRCLE,PAD
OUT=Path(__file__).resolve().parents[2]/'outputs/ask-ai-audit';ROOT=Path.home()/'.local/share/intact-simulation/ask-ai-audit'
async def main():
 s=ProjectService(ROOT);f=FeatureService(s);draft=f.create_sketch(None,CIRCLE,name='Ask AI live test',parameters={'diameter':40,'thickness':8,'bore_diameter':6});key=draft['model_id']
 f.edit(key,[PAD,{'id':'bores','kind':'hole','base':'pad','part_id':'disk','params':{'diameter':{'parameter':'bore_diameter'},'centers':[[-10,0,0],[10,0,0]],'through':True}}]);f.requirements(key,{'source_text':'Disk diameter40 thickness8 with two through bores diameter6','checks':[{'id':'size','kind':'bounds','part_id':'disk','expected':{'length':40,'width':40,'height':8}},{'id':'holes','kind':'hole_pattern','part_id':'disk','expected':{'count':2,'diameter_mm':6,'through':True,'centers_mm':[[-10,0,0],[10,0,0]]}}]})
 url=viewer_url(ROOT,key);checks=[];errors=[];q=EditRequests(s)
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True,env=dict(os.environ,LD_LIBRARY_PATH=str(Path.home()/'.local/share/intact-simulation/browser-libs')),args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=await browser.new_page(viewport={'width':1500,'height':1000});page.on('pageerror',lambda e:errors.append(str(e)))
  await page.goto(url);await page.wait_for_selector('body[data-ready=true]');assert await page.locator('#chatgpt-prompt').count()==0 and await page.locator('#chatgpt-handoff').count()==0;assert await page.locator('#run-ai').inner_text()=='Ask AI';checks.append('Ask AI button replaces generated prompt/copy-paste controls')
  await page.locator('.part[data-part=disk] button').click();await page.locator('#toggle-edit').click()
  async def ask(intent,text):
   await page.select_option('#ai-intent',intent);await page.locator('#edit-prompt').fill(text);before={r['request_id'] for r in q.list(key)};await page.locator('#run-ai').click();deadline=time.monotonic()+320;last=''
   while time.monotonic()<deadline:
    items=[r for r in q.list(key) if r['request_id'] not in before]
    if items:
     r=items[0]
     if r.get('progress')!=last:last=r.get('progress');print(intent,r['status'],last,flush=True)
     if r['status'] not in ('pending','processing'):
      assert r['status']=='succeeded',r
      await page.wait_for_function('()=>!!document.querySelector("#ai-answer").textContent',timeout=10000);return q.read(key,r['request_id'])
    await asyncio.sleep(1)
   raise AssertionError('Ask AI timed out')
  before=s.load(key);question=await ask('question','What are the diameter and thickness of the selected disk, and the diameter of its two through holes? Answer using native geometry in mm.');assert s.load(key)['spec']['revision']==before['spec']['revision'];assert question['answer'] and not question['geometry_changed'];assert question['context']['references'][0]['part_id']=='disk';checks.append('Real signed-in AI answers selected-geometry question; revision unchanged; screenshot context attached');await page.screenshot(path=str(OUT/'question-answer.png'))
  edit=await ask('edit','Increase bore_diameter from 6 to 8 mm for the two mounting holes. Keep the disk diameter 40 mm, thickness 8 mm and hole centers unchanged. Update the saved hole-diameter requirement to the intentionally requested 8 mm, rebuild and verify. Preserve the constrained sketch and editable feature graph.')
  current=s.load(key);assert current['engineering']['attached'] and current['engineering']['parameters']['bore_diameter']==8;assert current['spec']['parts'][0]['measurements']['volume_mm3']<before['spec']['parts'][0]['measurements']['volume_mm3'];assert edit['validation']['passed'];await page.wait_for_selector('body[data-revision="'+str(current['spec']['revision'])+'"]');checks.append('Real AI edits parameter, preserves feature history, rebuilds native CAD, verifies and refreshes viewer');await page.screenshot(path=str(OUT/'edited-model.png'))
  for r in (question,edit):
   assert r['screenshot'] and not any(e['tool'] in ('exec_command','shell') for e in r.get('tool_events',[]))
  assert not errors,errors;await browser.close()
 report={'status':'passed','checks':checks,'browser_errors':errors,'viewer_url':url,'model_id':key,'question':q.summary(question),'edit':q.summary(edit)};(OUT/'live-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({'status':'passed','checks':checks,'url':url},indent=2))
asyncio.run(main())
