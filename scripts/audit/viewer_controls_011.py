"""Exercise every viewer control family on a disposable audit model."""
import asyncio,base64,json,os
from pathlib import Path
from playwright.async_api import async_playwright
REPO=Path(__file__).resolve().parents[2];OUT=REPO/'outputs/ask-ai-audit';ROOT=Path.home()/'.local/share/intact-simulation/ask-ai-viewer-full'
async def main():
 from intact_backend.projects import ProjectService
 from intact_backend.viewer_server import ensure_viewer
 service=ProjectService(ROOT);r=service.build('import build123d as bd\ndef build(params):\n    return {"base":bd.Box(60,30,6)-bd.Cylinder(5,10),"lid":bd.Pos(0,0,14)*bd.Box(60,30,2)}',{},name='Viewer audit')
 session=ensure_viewer(ROOT);url=f"http://127.0.0.1:{session['port']}/{session['token']}/{r['model_id']}/view";checks=[];failures=[]
 async with async_playwright() as p:
  env=dict(os.environ,LD_LIBRARY_PATH=str(Path.home()/'.local/share/intact-simulation/browser-libs'))
  b=await p.chromium.launch(headless=True,env=env,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=await b.new_page(viewport={'width':1500,'height':1000},permissions=['clipboard-read','clipboard-write']);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  failed_mesh=False
  async def transient(route):
   nonlocal failed_mesh
   if not failed_mesh:failed_mesh=True;await route.abort()
   else:await route.continue_()
  await page.route('**/mesh.json',transient)
  await page.goto(url);await page.wait_for_selector('body[data-ready=true]',timeout=20000);checks.append('automatic recovery after an initial mesh fetch failure');await page.wait_for_function('()=>!!window.intactInspect')
  async def test(name,operation):
   try:await operation();checks.append(name);print('UI PASS '+name,flush=True)
   except Exception as e:failures.append({'check':name,'error':str(e)[:2000]});print('UI FAIL '+name+': '+str(e)[:200],flush=True)
  async def themes():
   await page.locator('#toggle-settings').click();await page.locator('#settings details').evaluate_all('(items)=>items.forEach(d=>d.open=true)')
   for theme in ['light','medium-light','medium','dark']:await page.select_option('#setting-theme',theme);assert await page.locator('body').get_attribute('data-theme')==theme
   for mode in ['solid','render','xray','hidden-line','wireframe','grid']:await page.select_option('#mode',mode)
   for surface in ['shaded','flat','hidden','off']:await page.select_option('#setting-surface',surface)
   for projection in ['orthographic','perspective']:await page.select_option('#setting-projection',projection)
   for color in ['original','single','part']:await page.select_option('#setting-color_mode',color)
   for visibility in ['visible','all']:await page.select_option('#setting-edge_visibility',visibility)
   for quality in ['preview','final']:await page.select_option('#setting-quality',quality)
   for floor in ['origin','lowest']:await page.select_option('#setting-floor_position',floor)
   for name in ['edges','grid','axes','lighting','background','floor','preview']:
    await page.locator('#setting-'+name).uncheck();await page.locator('#setting-'+name).check()
   for name,value in {'opacity':'70','exposure':'.5','light_rotation':'210','softbox':'100','fill':'60','orbit_speed':'2'}.items():await page.locator('#setting-'+name).fill(value);await page.locator('#setting-'+name).dispatch_event('input')
   for name in ['single_color','edge_color','grid_color','axes_color','background_color','floor_color']:await page.locator('#setting-'+name).fill('#6c8398');await page.locator('#setting-'+name).dispatch_event('input')
   count=await page.locator('#palette-colors input').count();await page.locator('#palette-add').click();assert await page.locator('#palette-colors input').count()==count+1;await page.locator('#palette-colors button').last.click();assert await page.locator('#palette-colors input').count()==count
   await page.wait_for_function("()=>document.body.dataset.viewSaved==='true'");await page.reload();await page.wait_for_selector('body[data-ready=true]');v=await page.evaluate('window.intactInspect.view()');assert v['theme']=='dark' and v['quality']=='final' and v['floor'] and v['opacity']==70
   await page.locator('#toggle-settings').click();await page.locator('#reset-settings').click();await page.locator('#toggle-settings').click()
  await test('themes, all render/surface/color/projection modes, lights, environment, palettes and preference persistence',themes)
  async def cuts():
   for axis in ['x','y','z']:await page.select_option('#cut',axis);await page.locator('#slice').fill('40');await page.locator('#slice').dispatch_event('input');await page.locator('#flip').check();await page.locator('#cap').uncheck();await page.locator('#cap').check();await page.locator('#flip').uncheck()
   await page.select_option('#cut','none');await page.locator('#explode').fill('60');await page.locator('#explode').dispatch_event('input');await page.get_by_label('Show Lid',exact=True).uncheck();await page.locator('#show-all').click();await page.locator('.part[data-part=base] button').click();await page.locator('#isolate').click();assert await page.evaluate("window.intactInspect.view().hidden.includes('lid')");await page.locator('#show-all').click();await page.locator('#reset').click()
   for view in ['front','back','left','right','top','bottom','iso']:await page.locator('[data-view='+view+']').evaluate('(button)=>button.click()')
   await page.locator('#part-filter').fill('lid');assert await page.locator('.part').count()==1;await page.locator('#part-filter').fill('');assert await page.locator('.part').count()==2
  await test('X/Y/Z cuts, cap/reverse, explosion, visibility/isolation/filter, six views and fit/reset',cuts)
  async def drawings():
   await page.locator('#toggle-draw').click();box=await page.locator('#annotations').bounding_box()
   for i,tool in enumerate(['pen','line','arrow','rectangle','ellipse','text','fill']):
    await page.locator('[data-tool='+tool+']').click()
    if tool=='text':await page.locator('#drawing-text').fill('Audit note')
    x=box['x']+box['width']*(.2+i*.07);y=box['y']+box['height']*.25
    await page.mouse.move(x,y);await page.mouse.down();await page.mouse.move(x+65,y+40,steps=5);await page.mouse.up()
   assert await page.locator('#annotations [data-id]').count()==7
   await page.locator('#drawing-undo').click();assert await page.locator('#annotations [data-id]').count()==6;await page.locator('#drawing-redo').click();assert await page.locator('#annotations [data-id]').count()==7
   await page.locator('#drawing-color').fill('#ff3344');await page.locator('#drawing-color').dispatch_event('input');await page.locator('#drawing-width').fill('7');await page.locator('#drawing-width').dispatch_event('input')
   await page.locator('[data-tool=move]').click();rect=page.locator('#annotations rect').first;old=await rect.get_attribute('x');br=await rect.bounding_box();await page.mouse.move(br['x']+3,br['y']+3);await page.mouse.down();await page.mouse.move(br['x']+33,br['y']+23,steps=5);await page.mouse.up();assert await page.locator('#annotations rect').first.get_attribute('x')!=old
   await page.locator('[data-tool=eraser]').click();rect=page.locator('#annotations rect').first;br=await rect.bounding_box();await page.mouse.click(br['x']+1,br['y']+1);assert await page.locator('#annotations [data-id]').count()==6
   async with page.expect_download() as download:await page.locator('#screenshot').click()
   file=await download.value;await file.save_as(OUT/'viewer-drawing-export.png');await page.locator('#copy-drawing').click();await page.locator('#drawing-clear').click();assert await page.locator('#annotations [data-id]').count()==0
   await page.locator('#toggle-draw').click()
  await test('all sketch primitives, move/erase, color/width, undo/redo/clear and PNG/clipboard',drawings)
  async def pan_exit():
   await page.locator('#toggle-draw').click();await page.locator('[data-tool=pan]').click();await page.locator('#toggle-draw').click();before=await page.evaluate('window.intactInspect.view()')
   box=await page.locator('#cad-canvas').bounding_box();await page.mouse.move(box['x']+box['width']*.45,box['y']+box['height']*.55);await page.mouse.down();await page.mouse.move(box['x']+box['width']*.45+60,box['y']+box['height']*.55+10,steps=8);await page.mouse.up();await page.wait_for_timeout(450)
   v=await page.evaluate('window.intactInspect.view()');a=before.get('camera') or v['camera'];c=v['camera'];target_change=sum(abs(a[i]-c[i]) for i in [3,4,5]);assert target_change<.01,'Closing drawing Pan left normal drag in pan mode instead of orbit'
  await test('closing drawing Pan returns normal orbit controls',pan_exit)
  async def dimensions():
   current=service.load(r['model_id']);artifact=current['spec']['program']['artifact_id'];service.save_view(r['model_id'],{'measurements':[{'id':'quote" dimension','a':[-30,-15,-3],'b':[30,-15,-3],'artifact_id':artifact,'snap_a':'Exact vertex','snap_b':'Exact vertex'}]})
   await page.reload();await page.wait_for_selector('body[data-ready=true]');assert '60.00 mm' in await page.locator('.dimension').inner_text()
   await page.locator('#toggle-edit').click();await page.locator('#edit-prompt').fill('Increase the measured plate length to 70 mm, keep its other dimensions.')
   await page.route('**/run-edit',lambda route:route.fulfill(status=200,content_type='application/json',body='{}'));await page.locator('#run-ai').click();await page.wait_for_function("()=>document.querySelector('#ai-progress').textContent==='Sending to AI…'");assert await page.locator('#chatgpt-prompt').count()==0
   from intact_backend.edit_requests import EditRequests
   q=EditRequests(service);item=q.list(r['model_id'])[0];context=q.read(r['model_id'],item['request_id']);assert context['context']['measurements']['items'][0]['a']==[-30,-15,-3]
   await page.locator('#quick-edit').evaluate('(e)=>e.hidden=true')
   async with page.expect_download() as download:await page.locator('#screenshot').click()
   await(await download.value).save_as(OUT/'dimension-export.png')
   await page.locator('.dimension button').click();assert await page.locator('.dimension').count()==0
  await test('quoted dimension IDs, native-coordinate edit context, annotated PNG export and individual deletion',dimensions)
  await page.screenshot(path=str(OUT/'viewer-controls.png'));await page.set_viewport_size({'width':390,'height':844});await page.wait_for_timeout(150);assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth');checks.append('mobile layout')
  await b.close()
 report={'passed':checks,'failures':failures,'browser_errors':errors,'model_id':r['model_id'],'url':url};(OUT/'viewer-controls-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
asyncio.run(main())
