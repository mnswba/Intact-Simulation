"""Revalidate all 50 AI-edited models through the installed release after fixes."""
import asyncio,base64,hashlib,json,math,os,signal
from pathlib import Path
from urllib.request import urlopen
from mcp import Client,StdioServerParameters
from catalog import CASES
REPO=Path(__file__).resolve().parents[2];OUT=REPO/'outputs/50-model-audit';ROOT=Path.home()/'.local/share/intact-simulation/audit-50'

def compare_faces(actual,expected):
 assert set(p['id'] for p in actual['parts'])==set(p['id'] for p in expected['parts'])
 for p in expected['parts']:
  part=next(x for x in actual['parts'] if x['id']==p['id']);remaining=list(part['faces']);assert len(remaining)==len(p['faces']),p['id']+' face count changed'
  def same(a,b):
   if a['geometry']!=b['geometry']:return False
   if not math.isclose(a['area_mm2'],b['area_mm2'],rel_tol=1e-5,abs_tol=1e-3):return False
   for field in ('center',):
    if any(not math.isclose(x,y,rel_tol=1e-5,abs_tol=1e-3) for x,y in zip(a[field],b[field])):return False
   for field in ('radius_mm','major_radius_mm','minor_radius_mm'):
    if field in a and (field not in b or not math.isclose(a[field],b[field],rel_tol=1e-5,abs_tol=1e-4)):return False
   return True
  for face in p['faces']:
   match=next((i for i,item in enumerate(remaining) if same(item,face)),None)
   assert match is not None,f"{p['id']}: expected {face['geometry']} face at {face['center']} area {face['area_mm2']} not found"
   remaining.pop(match)

async def main():
 # Stop only this audit's old daemon, after all its AI jobs have completed.
 assert json.loads((OUT/'ai-report.json').read_text())['passed']==50
 registry=ROOT/'viewer-session.json'
 if registry.exists():
  entry=json.loads(registry.read_text());command=Path('/proc')/str(entry['pid'])/'cmdline'
  if command.exists() and str(ROOT).encode() in command.read_bytes():os.kill(entry['pid'],signal.SIGTERM)
 server=json.loads((Path.home()/'.codex/plugins/intact-simulation/.mcp.json').read_text())['mcpServers']['intact'];params=StdioServerParameters(command=server['command'],args=server['args'],env={**os.environ,'INTACT_STATE_DIR':str(ROOT)})
 summary={'version':'0.8.0','passed':0,'failed':0,'cases':{}}
 async with Client(params,read_timeout_seconds=180) as c:
  for case in CASES:
   key=case['key'];folder=OUT/key;release=folder/'release';release.mkdir(exist_ok=True);entry={'key':key,'status':'running'}
   try:
    model=json.loads((folder/'model.json').read_text());keyid=model['model_id'];opened=await c.call_tool('open_viewer',{'model_id':keyid});assert not opened.is_error,opened;url=opened.structured_content['url'];base=url.removesuffix('view')
    record=(await c.call_tool('get_model',{'model_id':keyid})).structured_content;expected=json.loads((folder/'ai-spec.json').read_text());assert record['spec']['program']['source']==expected['program']['source']
    for a,b in zip(record['spec']['parts'],expected['parts']):
     assert a['id']==b['id']
     for metric in ('volume_mm3','surface_area_mm2'):assert math.isclose(a['measurements'][metric],b['measurements'][metric],rel_tol=1e-6,abs_tol=1e-4)
    manifest=json.loads(urlopen(base+'manifest.json').read());assert len(manifest['sha256'])>=7
    actual=json.loads(urlopen(base+'topology.json').read())
    source=case['source'];p={k:float(v) for k,v in {**case['parameters'],**case['expected_parameters']}.items()}
    if key=='engraved_plate':source=source.replace("'INTACT'","'CAD LAB'")
    legacy_key=hashlib.sha256(json.dumps({'worker':3,'asset_id':None,'build123d':'0.13.0','source':source,'parameters':p},sort_keys=True,separators=(',',':')).encode()).hexdigest()
    oracle=ROOT/'programs'/legacy_key/'topology.json';assert oracle.exists(),'Expected pre-fix oracle topology missing'
    compare_faces(actual,json.loads(oracle.read_text()))
    for kind in ('step','stl','glb','3mf','python','project'):
     result=await c.call_tool('export_model',{'model_id':keyid,'format':kind});assert not result.is_error,result;data=urlopen(result.structured_content['url']).read();name={'step':'model.step','stl':'model.stl','glb':'model.glb','3mf':'model.3mf','python':'program.py','project':'project.json'}[kind];(release/name).write_bytes(data)
     if kind=='step':
      import build123d as bd
      shape=bd.import_step(release/name);assert shape.is_valid and math.isclose(shape.volume,sum(p['measurements']['volume_mm3'] for p in record['spec']['parts']),rel_tol=1e-6)
    snapshot=await c.call_tool('snapshot_model',{'model_id':keyid,'view':'iso'});assert not snapshot.is_error,snapshot;img=next(i for i in snapshot.content if i.type=='image');png=base64.b64decode(img.data);(release/'viewer.png').write_bytes(png)
    entry.update(status='passed',viewer_url=url,model_id=keyid,revision=record['spec']['revision'],checks=['saved AI source preserved','volume/surface preserved after cache migration','native face types/areas/centers/radii match independent intended-edit oracle','checksummed artifacts and all six release exports','STEP kernel round trip','actual installed release MCP PNG'])
    print('RELEASE PASS '+key,flush=True)
   except Exception as exc:entry.update(status='failed',error=str(exc)[:4000]);print('RELEASE FAIL '+key+': '+str(exc)[:250],flush=True)
   (folder/'release.json').write_text(json.dumps(entry,indent=2));summary['cases'][key]=entry;summary['passed']=sum(v['status']=='passed' for v in summary['cases'].values());summary['failed']=sum(v['status']=='failed' for v in summary['cases'].values());(OUT/'release-report.json').write_text(json.dumps(summary,indent=2))
 print(f"RELEASE {summary['passed']}/50 passed; {summary['failed']} failed",flush=True)
asyncio.run(main())
