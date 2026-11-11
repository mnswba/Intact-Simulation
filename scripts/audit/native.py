"""50-model audit through the installed MCP manifest. Run with installed Python."""
import argparse,asyncio,ast,base64,hashlib,io,json,math,os,sys,time,zipfile
from pathlib import Path
from urllib.request import urlopen
from mcp import Client,StdioServerParameters
from catalog import CASES
REPO=Path(__file__).resolve().parents[2];OUT=REPO/'outputs/50-model-audit';OUT.mkdir(parents=True,exist_ok=True)
ROOT=Path.home()/'.local/share/intact-simulation/audit-50'
parser=argparse.ArgumentParser();parser.add_argument('--only',nargs='*');args=parser.parse_args()

def save(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2));tmp.replace(path)
def unpack(result):
 if result.is_error:raise AssertionError('\n'.join(c.text for c in result.content if hasattr(c,'text')))
 return result.structured_content
async def main():
 server=json.loads((Path.home()/'.codex/plugins/intact-simulation/.mcp.json').read_text())['mcpServers']['intact']
 params=StdioServerParameters(command=server['command'],args=server['args'],env={**os.environ,'INTACT_STATE_DIR':str(ROOT)})
 summary={'phase':'native CAD','state_root':str(ROOT),'total':50,'finished':0,'passed':0,'failed':0,'cases':{}}
 async with Client(params,read_timeout_seconds=150) as client:
  tools=(await client.list_tools()).tools;save(OUT/'tool-schemas.json',{t.name:t.model_dump(mode='json') for t in tools})
  for case in CASES:
   key=case['key'];path=OUT/key/'native.json'
   if args.only and key not in args.only:
    if path.exists():summary['cases'][key]=json.loads(path.read_text())
    continue
   folder=path.parent;folder.mkdir(exist_ok=True);started=time.monotonic();entry={'name':case['name'],'key':key,'category':case['category'],'status':'running','checks':[]}
   save(path,entry)
   try:
    old=json.loads(path.read_text());existing=None
    # Reuse a previous audit document only; never edit the user's main projects.
    previous_path=folder/'model.json'
    if previous_path.exists():existing=json.loads(previous_path.read_text()).get('model_id')
    payload={'source':case['source'],'parameters':case['parameters'],'name':'Audit · '+case['name']}
    if existing:payload['model_id']=existing
    result=unpack(await client.call_tool('build_model',payload));save(previous_path,result)
    entry.update(model_id=result['model_id'],viewer_url=result['viewer_url'],revision=result['revision'],artifact_id=result['geometry']['artifact_id'])
    measured=unpack(await client.call_tool('measure_model',{'model_id':result['model_id']}));parts=measured['parts'];entry['measurements']=measured
    assert all(p['volume_mm3']>0 and p['solid_count']>=1 for p in parts)
    if case['parts']:assert len(parts)==case['parts'],f"Expected {case['parts']} named parts, got {len(parts)}"
    volume=sum(p['volume_mm3'] for p in parts)
    if case['volume'] is not None:assert math.isclose(volume,case['volume'],rel_tol=1e-6,abs_tol=1e-5),f"Independent volume: {volume} != {case['volume']}"
    entry['checks'].append('kernel validity, positive solids, exact measurements and independent volume where applicable')
    for kind,url in result['downloads'].items():
     data=await asyncio.to_thread(lambda url=url:urlopen(url,timeout=20).read());filename={'step':'model.step','stl':'model.stl','glb':'model.glb','3mf':'model.3mf','python':'program.py','project':'project.json'}[kind];(folder/filename).write_bytes(data)
     if kind=='step':
      import build123d as bd
      shape=bd.import_step(folder/filename)
      assert shape.is_valid and len(shape.solids())==sum(p['solid_count'] for p in parts)
      assert math.isclose(shape.volume,volume,rel_tol=1e-6,abs_tol=1e-5)
      assert math.isclose(shape.area,sum(p['surface_area_mm2'] for p in parts),rel_tol=1e-6,abs_tol=1e-4)
     if kind=='stl':assert len(data)>84
     if kind=='glb':assert data[:4]==b'glTF' and int.from_bytes(data[4:8],'little')==2 and int.from_bytes(data[8:12],'little')==len(data)
     if kind=='3mf':
      with zipfile.ZipFile(io.BytesIO(data)) as archive:assert any(p.endswith('.model') for p in archive.namelist())
     if kind=='python':ast.parse(data.decode())
     if kind=='project':
      portable=json.loads(data);assert portable['spec']['program']['source']==case['source'];assert len(portable['mesh']['parts'])==len(parts)
    entry['checks'].append('all six exports, STEP solid/volume/surface round trip, GLB length/version, 3MF archive, executable source syntax, portable project')
    base=result['viewer_url'].removesuffix('view');topology=json.loads(urlopen(base+'topology.json').read());mesh=json.loads(urlopen(base+'mesh.json').read())
    (folder/'topology.json').write_text(json.dumps(topology));(folder/'mesh.json').write_text(json.dumps(mesh))
    refs=[]
    for part,preview in zip(topology['parts'],mesh['parts']):
     count=len(preview['indices'])//3;assert sum(g['count'] for g in preview['face_groups'])==count
     assert all(0<=i<len(preview['positions'])//3 for i in preview['indices'])
     assert all(math.isfinite(n) for n in preview['positions'])
     assert all(f['area_mm2']>0 for f in part['faces'])
     refs.extend([part['faces'][0]['ref'],part['edges'][0]['ref']])
    resolved=unpack(await client.call_tool('resolve_references',{'model_id':result['model_id'],'references':refs[:64],'revision':result['revision'],'artifact_id':result['geometry']['artifact_id']}));assert resolved['references']
    entry['checks'].append('native topology, contiguous face triangle ranges, finite valid mesh, revision-bound face/edge resolution')
    snapshot=await client.call_tool('snapshot_model',{'model_id':result['model_id'],'view':'iso'});assert not snapshot.is_error,snapshot
    images=[c for c in snapshot.content if c.type=='image'];assert images;png=base64.b64decode(images[0].data);assert png.startswith(b'\x89PNG\r\n\x1a\n');(folder/'native.png').write_bytes(png)
    entry['checks'].append('real installed MCP viewer PNG')
    entry.update(status='passed',elapsed_seconds=round(time.monotonic()-started,2),source_sha256=hashlib.sha256(case['source'].encode()).hexdigest())
    print(f"PASS {key} ({entry['elapsed_seconds']}s)",flush=True)
   except Exception as exc:
    entry.update(status='failed',error=str(exc)[:5000],elapsed_seconds=round(time.monotonic()-started,2));print('FAIL '+key+': '+str(exc)[:300],flush=True)
   save(path,entry);summary['cases'][key]=entry;summary['finished']=len(summary['cases']);summary['passed']=sum(c['status']=='passed' for c in summary['cases'].values());summary['failed']=sum(c['status']=='failed' for c in summary['cases'].values());save(OUT/'native-report.json',summary)
 summary['phase']='complete';save(OUT/'native-report.json',summary);print(f"NATIVE: {summary['passed']}/50 passed, {summary['failed']} failed",flush=True)
asyncio.run(main())
