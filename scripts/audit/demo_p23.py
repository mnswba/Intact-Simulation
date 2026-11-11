"""Installed three-physics demo and browser verification of retained result sets."""
import asyncio,json,os
from pathlib import Path
from playwright.async_api import async_playwright
from intact_backend.projects import ProjectService
from intact_backend.advanced import Advanced
from intact_backend.viewer_server import viewer_url
ROOT=Path.home()/'.local/share/intact-simulation/priority23-demo';OUT=Path(__file__).resolve().parents[2]/'outputs/priority23-audit'
async def main():
 s=ProjectService(ROOT);a=Advanced(s);r=s.build('import build123d as bd\ndef build(params):\n    return {"domain":bd.Box(20,10,10)}',{},name='Independent 3D study demos');key=r['model_id'];studies={}
 for kind in ('thermal','structural','stokes'):
  study=a.simulate(key,{'kind':kind,'part_id':'domain','mesh_size_mm':4,'convergence':True,'convergence_tolerance':.15});assert study['verified'],study['convergence'];studies[kind]={k:v for k,v in study.items() if k not in ('positions_mm','triangles','values')}
 assert {r.get('kind') for r in a.evidence(key)['reports']}=={'thermal','structural','stokes'}
 url=viewer_url(ROOT,key);errors=[]
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,env=dict(os.environ,LD_LIBRARY_PATH=str(Path.home()/'.local/share/intact-simulation/browser-libs')),args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=await b.new_page(viewport={'width':1500,'height':1000});page.on('pageerror',lambda e:errors.append(str(e)));await page.goto(url);await page.wait_for_selector('body[data-ready=true]');await page.locator('details').filter(has=page.locator('#advanced-engineering')).locator('summary').first.click();await page.locator('#advanced-engineering details').evaluate_all('(items)=>items.forEach(d=>d.open=true)')
  for kind,label in [('thermal','Show temperature K'),('structural','Show displacement mm'),('stokes','Show speed m s')]:
   await page.get_by_role('button',name=label,exact=True).click();await page.wait_for_function('()=>window.intactInspect.engineeringResult().overlayCount===1');assert await page.locator('#cut').is_disabled() and await page.locator('#explode').is_disabled();await page.screenshot(path=str(OUT/(kind+'-demo.png')))
  await page.get_by_role('button',name='Show CAD',exact=True).click();assert not await page.locator('#cut').is_disabled() and not await page.locator('#explode').is_disabled()
  # Leave the tutorial viewer in the thermal field, clearly independent of other study types.
  await page.get_by_role('button',name='Show temperature K',exact=True).click();assert not errors;await b.close()
 report={'status':'passed','model_id':key,'viewer_url':url,'studies':studies,'checks':['all three physics result sets retained for one unchanged domain','temperature, displacement and velocity overlays switched in installed viewer'],'browser_errors':errors,'scope':'Independent tutorial load cases on the same domain; not coupled multiphysics.'};(OUT/'demo-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='studies'},indent=2))
asyncio.run(main())
