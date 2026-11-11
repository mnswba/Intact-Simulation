"""Real browser checks for solved drafts, feature editing and history safety."""
import asyncio,json,os
from pathlib import Path
from playwright.async_api import async_playwright
from intact_backend.projects import ProjectService
from intact_backend.feature_graph import FeatureService
from intact_backend.viewer_server import viewer_url
from p1_examples import CIRCLE,PAD
ROOT=Path.home()/'.local/share/intact-simulation/priority23-p1-ui';OUT=Path(__file__).resolve().parents[2]/'outputs/priority23-audit';OUT.mkdir(parents=True,exist_ok=True)

async def main():
 s=ProjectService(ROOT);f=FeatureService(s);draft=f.create_sketch(None,CIRCLE,name='Constrained sketch and feature editing',parameters={'diameter':40,'thickness':5});key=draft['model_id'];f.edit(key,[PAD],rebuild=False);url=viewer_url(ROOT,key);errors=[];checks=[]
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True,env=dict(os.environ,LD_LIBRARY_PATH=str(Path.home()/'.local/share/intact-simulation/browser-libs')),args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=await browser.new_page(viewport={'width':1450,'height':1050});page.on('pageerror',lambda e:errors.append(str(e)))
  await page.goto(url);await page.wait_for_selector('body[data-ready=true]');assert await page.locator('#cad-canvas').count()==0
  await page.get_by_role('button',name='Solve sketch',exact=True).click();await page.get_by_text('Fully constrained · 0 degrees of freedom',exact=True).wait_for();await page.screenshot(path=str(OUT/'draft-solved.png'))
  checks.append('draft is a real 2D sketch without a placeholder solid; solver reports zero DoF')
  input=page.get_by_role('spinbutton',name='Constraint outline diameter',exact=True);await input.fill('50');await input.press('Tab');await page.wait_for_function("()=>document.querySelector('#status').textContent.includes('Draft revision')");await page.wait_for_timeout(250)
  await page.get_by_role('button',name='Solve sketch',exact=True).click();await page.wait_for_function("()=>Number(document.querySelector('svg circle').getAttribute('r'))===25");assert f.get(key)['engineering']['parameters']['diameter']==50
  checks.append('dimension edits preserve parameter links and update solved geometry')
  await page.get_by_role('button',name='Rebuild features',exact=True).click();await page.wait_for_selector('#cad-canvas');await page.wait_for_selector('body[data-ready=true]');initial=s.load(key)['spec']['revision']
  await page.locator('details').filter(has=page.locator('#engineering')).locator('summary').first.click();await page.get_by_role('spinbutton',name='Feature pad height',exact=True).fill('8');await page.get_by_role('spinbutton',name='Feature pad height',exact=True).press('Tab')
  await page.wait_for_function('()=>window.intactInspect.project().spec.parts[0].params.height===8');assert s.load(key)['spec']['program']['parameters']['thickness']==8
  checks.append('draft publishes real STEP-backed solid; numeric feature edits rebuild it')
  r=f.edit(key,[{'id':'bore','kind':'hole','base':'pad','part_id':'disk','params':{'diameter':6,'centers':[[0,0,0]],'through':True}}],mode='upsert');await page.wait_for_selector('body[data-revision="'+str(r['spec']['revision'])+'"]');before=r['spec']['parts'][0]['measurements']['volume_mm3']
  await page.get_by_role('checkbox',name='Enable feature bore',exact=True).uncheck();await page.wait_for_function('()=>window.intactInspect.project().engineering.features.at(-1).suppressed');assert s.load(key)['spec']['parts'][0]['measurements']['volume_mm3']>before
  f.requirements(key,{'checks':[{'id':'body','kind':'bounds','part_id':'disk','expected':{'length':50,'width':50,'height':8}}]});await page.wait_for_selector('body[data-revision="'+str(s.load(key)['spec']['revision'])+'"]');await page.get_by_role('button',name='Verify design',exact=True).click();await page.get_by_text('body: pass',exact=True).wait_for();await page.screenshot(path=str(OUT/'feature-editor.png'))
  checks.append('feature suppression changes actual geometry; exported design checks show pass')
  async with page.expect_download() as download:await page.get_by_role('link',name='Download native feature document',exact=True).click()
  await(await download.value).save_as(OUT/'viewer-native-document.FCStd');assert (OUT/'viewer-native-document.FCStd').stat().st_size>100
  current=s.load(key)['spec']['revision'];await page.goto(url+'?revision='+str(initial));await page.wait_for_selector('body[data-ready=true][data-historical=true]');await page.locator('details').filter(has=page.locator('#engineering')).locator('summary').first.click();assert await page.get_by_role('spinbutton',name='Feature pad height',exact=True).is_disabled();assert s.load(key)['spec']['revision']==current;await page.screenshot(path=str(OUT/'historical-features.png'))
  checks.append('native document downloads; historical feature controls are read-only and add no revision')
  assert not errors,errors;await browser.close()
 report={'status':'passed','checks':checks,'browser_errors':errors,'viewer_url':url,'model_id':key};(OUT/'priority1-viewer-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
asyncio.run(main())
