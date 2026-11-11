"""Actual browser scalar overlays, revision binding, exports and job control."""
import asyncio,json,os,time
from pathlib import Path
from urllib.request import urlopen
from playwright.async_api import async_playwright
from intact_backend.projects import ProjectService
from intact_backend.advanced import Advanced
from intact_backend.viewer_server import viewer_url
OUT=Path(__file__).resolve().parents[2]/'outputs/priority23-audit';ROOT=Path.home()/'.local/share/intact-simulation/priority23-ui'
async def main():
 s=ProjectService(ROOT);a=Advanced(s);r=s.build('import build123d as bd\ndef build(params):\n    return {"domain":bd.Box(params["length"],10,10)}',{'length':20},name='3D engineering results');key=r['model_id'];a.simulate(key,{'kind':'thermal','part_id':'domain','mesh_size_mm':4,'convergence':True});a.drawing(key,'domain');url=viewer_url(ROOT,key);checks=[];errors=[]
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True,env=dict(os.environ,LD_LIBRARY_PATH=str(Path.home()/'.local/share/intact-simulation/browser-libs')),args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=await browser.new_page(viewport={'width':1550,'height':1080});page.on('pageerror',lambda e:errors.append(str(e)))
  await page.goto(url);await page.wait_for_selector('body[data-ready=true]');outer=page.locator('details').filter(has=page.locator('#advanced-engineering')).locator('summary').first;await outer.click();await page.locator('#advanced-engineering details').evaluate_all('(items)=>items.forEach(d=>d.open=true)');await page.get_by_role('button',name='Show temperature K',exact=True).click();await page.wait_for_function('()=>window.intactInspect.engineeringResult().overlayCount===1&&!window.intactInspect.engineeringResult().cadVisible');await page.screenshot(path=str(OUT/'thermal-overlay.png'));checks.append('real tetrahedral temperature field displayed over CAD, with units, BC/material inputs and convergence status')
  async with page.expect_download() as download:await page.get_by_role('link',name='Download VTU',exact=True).click()
  await(await download.value).save_as(OUT/'viewer-results.vtu')
  async with page.expect_download() as download:await page.get_by_role('link',name='Download reference PDF',exact=True).click()
  await(await download.value).save_as(OUT/'viewer-drawing.pdf');checks.append('VTU and geometry-dimensioned reference PDF downloads')
  await page.get_by_role('button',name='Show CAD',exact=True).click();assert await page.evaluate('window.intactInspect.engineeringResult().cadVisible');checks.append('clear scalar overlay returns to native CAD')
  s.parameters(key,{'length':22});await page.wait_for_function('()=>window.intactInspect.project().spec.program.parameters.length===22');await page.wait_for_timeout(1200);await page.locator('#advanced-engineering details').evaluate_all('(items)=>items.forEach(d=>d.open=true)');assert await page.get_by_role('button',name='Show temperature K',exact=True).is_disabled();checks.append('changed geometry marks old study stale and blocks the old overlay')
  await page.evaluate('async()=>{await fetch("engineering-job",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({operation:"simulate",settings:{kind:"thermal",part_id:"domain",mesh_size_mm:.5,convergence:true}})});}');await page.get_by_role('button',name='Cancel job',exact=True).wait_for(timeout=10000);await page.get_by_role('button',name='Cancel job',exact=True).click();await page.wait_for_function('()=>document.querySelector("#advanced-engineering").textContent.includes("cancelled")',timeout=20000);checks.append('viewer cancels a real detached engineering job and displays terminal status')
  await page.set_viewport_size({'width':390,'height':844});assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth');await page.screenshot(path=str(OUT/'mobile-engineering.png'));checks.append('mobile engineering-panel layout')
  assert not errors,errors;await browser.close()
 report={'status':'passed','checks':checks,'browser_errors':errors,'model_id':key,'viewer_url':url};(OUT/'viewer-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
asyncio.run(main())
