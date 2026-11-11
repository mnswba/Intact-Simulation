"""Real browser -> queued sketch -> MCP native geometry -> isolated CAD -> live refresh."""
import argparse,asyncio,json,math,os,sys
from pathlib import Path
from mcp import Client,StdioServerParameters
from playwright.async_api import async_playwright

REPO=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--state-dir',type=Path,default=Path('/tmp/intact-workflow-dev'));parser.add_argument('--model-id');parser.add_argument('--installed',action='store_true');args=parser.parse_args()
ROOT=args.state_dir;OUT=REPO/'outputs/workflow-audit';OUT.mkdir(parents=True,exist_ok=True)

async def main():
 entry=json.loads((ROOT/'viewer-session.json').read_text());key=args.model_id or json.loads(Path('/tmp/intact-workflow-model.json').read_text())['model_id'];url=f"http://127.0.0.1:{entry['port']}/{entry['token']}/{key}/view"
 env=dict(os.environ,LD_LIBRARY_PATH=str(Path.home()/'.local/share/intact-simulation/browser-libs'))
 params=StdioServerParameters(command=sys.executable,args=['-m','intact_backend.mcp_server'],env={**os.environ,'PYTHONPATH':str(REPO/'backend'),'INTACT_STATE_DIR':str(ROOT)})
 if args.installed:
  server=json.loads((Path.home()/'.codex/plugins/intact-simulation/.mcp.json').read_text())['mcpServers']['intact']
  params=StdioServerParameters(command=server['command'],args=server['args'],env={**os.environ,'INTACT_STATE_DIR':str(ROOT)})
 report={'model_id':key,'url':url,'checks':[]}
 async with Client(params,read_timeout_seconds=100) as client,async_playwright() as p:
  async def tool(name,arguments):
   r=await client.call_tool(name,arguments)
   assert not r.is_error,(name,r)
   return r
  # Reset only this disposable audit model to its original imported STEP.
  current=(await tool('get_model',{'model_id':key})).structured_content
  if current['spec']['program']['source']!='def build(params):\n    return dict(imported_parts)':
   await tool('build_model',{'model_id':key,'source':'def build(params):\n    return dict(imported_parts)','parameters':{}})
  b=await p.chromium.launch(headless=True,env=env,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  page=await b.new_page(viewport={'width':1500,'height':1000},permissions=['clipboard-read','clipboard-write']);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  await page.goto(url);await page.wait_for_selector('body[data-ready=true]');await page.wait_for_timeout(300)
  async def state():return await page.evaluate('window.intactInspect.project()')
  async def screenshot(name):await page.screenshot(path=str(OUT/(name+'.png')))
  async def click_point(point,part='titanium_frame'):
   x,y,z=await page.evaluate('([p,id])=>window.intactInspect.screenPoint(p,id)',[point,part]);box=await page.locator('#cad-canvas').bounding_box();assert -1<z<1
   await page.mouse.click(box['x']+x,box['y']+y);await page.wait_for_timeout(150)
  assert await page.locator('.part').count()==23
  assert await page.locator('.tree-group>summary').all_text_contents()==['Components (14)','lens ring (3)','lens glass (3)','lens optic (3)']
  await page.locator('.part[data-part=titanium_frame] button').click();await page.locator('#isolate').click()
  await page.locator('[data-view=top]').evaluate('(button)=>button.click()');await page.locator('#projection').click();await page.wait_for_timeout(300)
  topo=await page.evaluate('window.intactInspect.topology()');frame=next(t for t in topo['parts'] if t['id']=='titanium_frame')
  top=next(f for f in frame['faces'] if f['geometry']=='plane' and f.get('normal',[0,0,0])[2]>.99 and f['area_mm2']>1000)
  await page.select_option('#selection-mode','face');await click_point(top['center']);selected=await page.evaluate('window.intactInspect.selected()');assert selected==[top['ref']],selected
  report['checks'].append('actual face ray picking and native inspector')
  edge=next(e for e in frame['edges'] if e['geometry']=='line' and abs(e['start'][0]-35.75)<.01 and abs(e['end'][0]-35.75)<.01 and abs(e['start'][2]-3.9)<.01 and e['length_mm']>100)
  await page.select_option('#selection-mode','edge');await click_point([(a+b)/2 for a,b in zip(edge['start'],edge['end'])]);selected=await page.evaluate('window.intactInspect.selected()');assert selected==[edge['ref']],selected
  report['checks'].append('actual native edge picking')
  vertices=[v['point'] for v in frame['vertices']];pair=None
  for a in vertices:
   for c in vertices:
    if abs(c[0]-a[0]-71.5)<1e-5 and abs(c[1]-a[1])<1e-5 and abs(c[2]-a[2])<1e-5 and abs(a[2]-3.9)<.01:pair=[a,c];break
   if pair:break
  assert pair
  await page.locator('#measure').click();await page.select_option('#snap-mode','vertex');await click_point(pair[0]);await click_point(pair[1]);dims=await page.locator('.dimension').all_text_contents();assert any('71.50 mm' in text for text in dims),dims
  await screenshot('snapped-width');await page.locator('#measure').click();report['checks'].append('71.50 mm width snapped to native vertices')
  # Per-part visibility and palette groups remain independently navigable.
  await page.locator('#show-all').click();await page.locator('#reset').click();await page.locator('#clear-selection').click()
  await page.locator('#toggle-settings').click()
  for mode in ['solid','render','xray','hidden-line','wireframe','grid']:
   await page.select_option('#mode',mode);await page.wait_for_timeout(150);await screenshot('mode-'+mode)
  await page.select_option('#mode','solid')
  for theme in ['light','medium-light','medium','dark']:
   await page.select_option('#setting-theme',theme);await page.wait_for_timeout(100);await screenshot('theme-'+theme);assert await page.locator('body').get_attribute('data-theme')==theme
  await page.locator('#settings-panel details').evaluate_all('(items)=>items.forEach(d=>d.open=true)')
  settings={'theme':'light','projection':'orthographic','surface':'flat','color_mode':'part','edge_visibility':'all','quality':'final','floor_position':'origin'}
  for name,value in settings.items():await page.select_option('#setting-'+name,value)
  for name in ['floor','axes']:await page.locator('#setting-'+name).check()
  for name,value in {'opacity':'75','exposure':'.5','light_rotation':'120','softbox':'90','fill':'60','orbit_speed':'1.5'}.items():await page.locator('#setting-'+name).fill(value);await page.locator('#setting-'+name).dispatch_event('input')
  for name,color in {'single_color':'#557799','edge_color':'#1a3150','grid_color':'#778899','axes_color':'#ff8844','background_color':'#e7edf4','floor_color':'#b9c8d5'}.items():await page.locator('#setting-'+name).fill(color);await page.locator('#setting-'+name).dispatch_event('input')
  await page.locator('#palette-add').click();assert await page.locator('#palette-colors input').count()==6
  for name in ['lighting','background','edges','grid']:await page.locator('#setting-'+name).uncheck();await page.locator('#setting-'+name).check()
  await page.locator('#setting-preview').check();await page.wait_for_timeout(500);await page.locator('#setting-preview').uncheck();await screenshot('settings-light')
  await page.wait_for_timeout(750);await page.reload();await page.wait_for_selector('body[data-ready=true]');saved=await page.evaluate('window.intactInspect.view()');assert saved['theme']=='light' and saved['projection']=='orthographic' and saved['floor'] and saved['quality']=='final' and len(saved['palette'])==6,saved
  report['checks'].append('all six view modes, projection, surfaces, palette, lighting, environment and saved preferences')
  await page.locator('#toggle-settings').click();await page.locator('#reset-settings').click();await page.locator('#toggle-settings').click()
  # Select the speaker bore through the tree and attach a real annotated screenshot/reference.
  detail=page.locator('.part[data-part=titanium_frame] + details');await detail.locator('summary').first.click();cyl=next(f for f in frame['faces'] if f.get('radius_mm')==.65 and abs(f['center'][0]+24)<.01)
  button=page.locator(f'[data-ref="{cyl["ref"]}"]');await button.locator('..').locator('summary').click();await button.click();assert 'Ø 1.300' in await page.locator('#selection').inner_text()
  await page.locator('#toggle-edit').click();await page.locator('#edit-prompt').fill('Enlarge the selected speaker bore to diameter 1.8 mm. Preserve depth, port and every other component.')
  await page.locator('#toggle-draw').click();await page.locator('[data-tool=arrow]').click();box=await page.locator('#annotations').bounding_box();await page.mouse.move(box['x']+box['width']*.3,box['y']+box['height']*.7);await page.mouse.down();await page.mouse.move(box['x']+box['width']*.45,box['y']+box['height']*.5,steps=8);await page.mouse.up();assert await page.locator('#annotations [data-id]').count()==1
  await page.locator('#drawing-undo').click();assert await page.locator('#annotations [data-id]').count()==0
  await page.locator('#drawing-redo').click();assert await page.locator('#annotations [data-id]').count()==1
  await page.locator('#toggle-draw').click();await screenshot('geometry-edit-request')
  ref=OUT/'reference.png';await page.locator('#cad-canvas').screenshot(path=str(ref));await page.locator('#reference-files').set_input_files(str(ref));await page.wait_for_selector('#reference-previews img')
  await page.locator('#chatgpt-handoff summary').click();await page.locator('#queue-edit').click();await page.get_by_text('Edit request saved with geometry and references. Copy its prompt into ChatGPT.',exact=True).wait_for()
  await page.locator('#copy-prompt').click();await page.wait_for_timeout(150);copied=await page.evaluate('navigator.clipboard.readText()');assert 'read_edit_request' in copied and key in copied
  queued=(await tool('list_edit_requests',{'model_id':key})).structured_content['requests'][0];assert queued['status']=='pending'
  read=await tool('read_edit_request',{'model_id':key,'request_id':queued['request_id']});assert len([c for c in read.content if c.type=='image'])==2
  payload=json.loads(next(c.text for c in read.content if c.type=='text'));assert payload['context']['references'][0]['radius_mm']==.65 and len(payload['annotations'])==1
  before=await state();revision=before['spec']['revision']
  source='''import build123d as bd
def build(params):
    parts=dict(imported_parts)
    cutter=bd.Pos(-24,-73.6,0)*bd.Rot(-90,0,0)*bd.Cylinder(params['speaker_diameter']/2,2.7,align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN))
    parts['titanium_frame']=parts['titanium_frame']-cutter
    return parts
'''
  result=(await tool('apply_edit_request',{'model_id':key,'request_id':queued['request_id'],'source':source,'parameters':{'speaker_diameter':1.8}})).structured_content
  await page.wait_for_function('(rev)=>Number(document.body.dataset.revision)>rev',arg=revision,timeout=20000)
  after=await state();newtopo=await page.evaluate('window.intactInspect.topology()');frameafter=next(t for t in newtopo['parts'] if t['id']=='titanium_frame');assert any(abs(f.get('radius_mm',0)-.9)<1e-6 for f in frameafter['faces'])
  beforeparts={p['id']:p for p in before['spec']['parts']};afterparts={p['id']:p for p in after['spec']['parts']};assert len(afterparts)==23
  for pid in beforeparts:
   if pid!='titanium_frame':assert beforeparts[pid]['measurements']==afterparts[pid]['measurements'],pid
  difference=beforeparts['titanium_frame']['measurements']['volume_mm3']-afterparts['titanium_frame']['measurements']['volume_mm3'];assert abs(difference-math.pi*(.9**2-.65**2)*2.6)<.03,difference
  assert not await page.evaluate('window.intactInspect.selected()')
  stale=await client.call_tool('resolve_references',{'model_id':key,'revision':revision,'artifact_id':before['spec']['program']['artifact_id'],'references':[cyl['ref']]});assert stale.is_error
  await page.get_by_text('succeeded',exact=True).first.wait_for(timeout=10000);await screenshot('edit-rebuilt')
  report['checks'].append('browser sketch/reference -> MCP text and images -> isolated imported STEP edit -> automatic refresh')
  report['checks'].append('1.3 to 1.8 mm bore; exact removed volume; other 22 components unchanged; stale references rejected')
  snap=await tool('snapshot_model',{'model_id':key,'view':'front'});assert any(c.type=='image' for c in snap.content)
  await page.set_viewport_size({'width':390,'height':844});await page.wait_for_timeout(300);assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth');await screenshot('mobile')
  report['checks'].append('MCP PNG snapshot, mobile layout')
  assert not errors,errors
  report.update(revision=after['spec']['revision'],removed_volume_mm3=difference,request_id=queued['request_id'],preserved_components=22)
  (OUT/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));await b.close()
asyncio.run(main())
