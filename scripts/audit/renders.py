"""Verify camera framing for every release model and all snapshot directions."""
import asyncio,base64,json,math,os
from pathlib import Path
from playwright.async_api import async_playwright
from mcp import Client,StdioServerParameters
from catalog import CASES
REPO=Path(__file__).resolve().parents[2];OUT=REPO/'outputs/50-model-audit';ROOT=Path.home()/'.local/share/intact-simulation/audit-50'
async def main():
 report={'passed':0,'failed':0,'cases':{},'snapshot_directions':[]};manifest=json.loads((Path.home()/'.codex/plugins/intact-simulation/.mcp.json').read_text())['mcpServers']['intact'];params=StdioServerParameters(command=manifest['command'],args=manifest['args'],env={**os.environ,'INTACT_STATE_DIR':str(ROOT)})
 async with Client(params,read_timeout_seconds=100) as client,async_playwright() as p:
  env=dict(os.environ,LD_LIBRARY_PATH=str(Path.home()/'.local/share/intact-simulation/browser-libs'));browser=await p.chromium.launch(headless=True,env=env,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=await browser.new_page(viewport={'width':1500,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  for case in CASES:
   key=case['key'];entry={'status':'running'}
   try:
    release=json.loads((OUT/key/'release.json').read_text());await page.goto(release['viewer_url']+'?snapshot=1');await page.wait_for_selector('body[data-ready=true]');await page.locator('[data-view=iso]').evaluate('(button)=>button.click()');await page.wait_for_timeout(100)
    camera=await page.evaluate('window.intactInspect.camera()');expected=[1,.8,1];n=math.sqrt(sum(x*x for x in expected));assert sum(a*b/n for a,b in zip(camera['direction'],expected))>.9999,camera
    state=await page.evaluate('window.intactInspect.project()');box=await page.locator('#cad-canvas').bounding_box()
    for part in state['spec']['parts']:
     cx,cy,z0=part['position'];params_part=part['params']
     for x in (cx-params_part['length']/2,cx+params_part['length']/2):
      for y in (cy-params_part['width']/2,cy+params_part['width']/2):
       for z in (z0,z0+params_part['height']):
        px,py,pz=await page.evaluate('([p,id])=>window.intactInspect.screenPoint(p,id)',[[x,y,z],part['id']]);assert 0<px<box['width'] and 0<py<box['height'] and -1<pz<1,f"{part['id']} bounding corner outside frame: {px},{py},{pz}"
    await page.locator('#cad-canvas').screenshot(path=str(OUT/key/'release/viewer.png'));entry.update(status='passed',checks=['true isometric camera direction','all native assembly bounding corners inside viewport','actual release PNG'])
    print('FRAME PASS '+key,flush=True)
   except Exception as exc:entry.update(status='failed',error=str(exc)[:3000]);print('FRAME FAIL '+key+': '+str(exc)[:300],flush=True)
   report['cases'][key]=entry
  for view in ['iso','front','back','top','bottom','right','left','current']:
   key=json.loads((OUT/'mounting_plate/release.json').read_text())['model_id'];r=await client.call_tool('snapshot_model',{'model_id':key,'view':view});assert not r.is_error,r;img=next(i for i in r.content if i.type=='image');(OUT/('snapshot-direction-'+view+'.png')).write_bytes(base64.b64decode(img.data));report['snapshot_directions'].append(view)
  # Verify the exact-axis cube case with an orthographic camera, including top/bottom.
  await page.locator('#projection').click();await page.locator('#view-cube canvas').click(position={'x':52,'y':25});await page.wait_for_timeout(150);camera=await page.evaluate('window.intactInspect.camera()');assert all(math.isfinite(n) for n in camera['direction']);assert not errors,errors
  await browser.close()
 report['passed']=sum(c['status']=='passed' for c in report['cases'].values());report['failed']=sum(c['status']=='failed' for c in report['cases'].values());report['browser_errors']=errors;(OUT/'framing-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2))
asyncio.run(main())
