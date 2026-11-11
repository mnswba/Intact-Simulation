"""Live LiteLLM edits for all 50 audited CAD designs, through the viewer Run API."""
import argparse,asyncio,base64,json,math,os,sys,time
from pathlib import Path
from urllib.request import Request,urlopen
from mcp import Client,StdioServerParameters
from catalog import CASES
REPO=Path(__file__).resolve().parents[2];OUT=REPO/'outputs/50-model-audit';ROOT=Path.home()/'.local/share/intact-simulation/audit-50'
parser=argparse.ArgumentParser();parser.add_argument('--only',nargs='*');args=parser.parse_args()

def save(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_suffix('.tmp');temp.write_text(json.dumps(data,indent=2));temp.replace(path)
def api(url,data=None):
 if data is None:return json.loads(urlopen(url,timeout=30).read())
 from urllib.parse import urlsplit
 origin=urlsplit(url);request=Request(url,json.dumps(data).encode(),{'Content-Type':'application/json','Origin':origin.scheme+'://'+origin.netloc})
 try:return json.loads(urlopen(request,timeout=45).read())
 except Exception as exc:
  body=exc.read().decode() if hasattr(exc,'read') else str(exc)
  raise ValueError(body[:3000]) from exc
async def http(url,data=None):return await asyncio.to_thread(api,url,data)
async def main():
 raise RuntimeError('This is the historical 0.8 provider audit. Model-service inference was removed in 0.9; use the installed ChatGPT plugin and host_09.py.')
 from intact_backend.program import ProgramService
 if not ModelConnection(ROOT).status()['configured']:ModelConnection(ROOT).connect_codex()
 service=ProgramService(ROOT/'programs');queue=asyncio.Queue();report={'phase':'live AI','total':50,'passed':0,'failed':0,'cases':{}}
 server=json.loads((Path.home()/'.codex/plugins/intact-simulation/.mcp.json').read_text())['mcpServers']['intact']
 params=StdioServerParameters(command=server['command'],args=server['args'],env={**os.environ,'INTACT_STATE_DIR':str(ROOT)})
 async with Client(params,read_timeout_seconds=150) as client:
  def summary():
   for c in CASES:
    path=OUT/c['key']/'ai.json'
    if path.exists():report['cases'][c['key']]=json.loads(path.read_text())
   report['passed']=sum(c['status']=='passed' for c in report['cases'].values());report['failed']=sum(c['status']=='failed' for c in report['cases'].values());save(OUT/'ai-report.json',report)
  async def producer():
   remaining={c['key']:c for c in CASES if not args.only or c['key'] in args.only}
   while remaining:
    for key,c in list(remaining.items()):
     path=OUT/key/'native.json'
     if not path.exists():continue
     native=json.loads(path.read_text())
     if native['status']=='passed':
      old=OUT/key/'ai.json'
      if old.exists() and json.loads(old.read_text())['status']=='passed' and not args.only:remaining.pop(key);continue
      await queue.put((c,native));remaining.pop(key)
     elif native['status']=='failed':
      save(OUT/key/'ai.json',{'status':'blocked_native','key':key,'error':native.get('error')});remaining.pop(key)
    await asyncio.sleep(.5)
   await queue.put(None);await queue.put(None)
  async def worker():
   while True:
    job=await queue.get()
    if job is None:queue.task_done();return
    c,native=job;key=c['key'];folder=OUT/key;started=time.monotonic();entry={'key':key,'name':c['name'],'status':'running','instructions':c['edit'],'checks':[]};save(folder/'ai.json',entry)
    try:
     base=native['viewer_url'].removesuffix('view');state=await http(base+'state.json')
     assert state['spec']['program']['source']==c['source'],'Baseline source changed before the AI audit. Reset this audit model.'
     before=state['spec']['revision'];artifact=state['spec']['program']['artifact_id'];topology=await http(base+'topology.json');ref=topology['parts'][0]['faces'][0]['ref']
     screenshot='data:image/png;base64,'+base64.b64encode((folder/'native.png').read_bytes()).decode()
     edit=await http(base+'edit-request',{'instructions':c['edit']+' Preserve existing public parameter names and every unrelated feature. Rebuild and finish after CAD validation.','references':[ref],'revision':before,'artifact_id':artifact,'screenshot':screenshot})
     entry['request_id']=edit['request_id'];entry['model_id']=native['model_id'];save(folder/'ai.json',entry)
     accepted=await http(base+'run-edit',{'request_id':edit['request_id']});assert accepted['accepted']
     while time.monotonic()-started<650:
      requests=(await http(base+'requests.json'))['requests'];current=next(r for r in requests if r['request_id']==edit['request_id']);entry['progress']=current.get('progress');save(folder/'ai.json',entry)
      if current['status'] in ('succeeded','failed','cancelled','stale'):
       assert current['status']=='succeeded',current.get('error') or current['status'];break
      await asyncio.sleep(1)
     else:raise AssertionError('Live AI edit did not finish within the ten-minute job budget.')
     state=await http(base+'state.json');assert state['spec']['revision']>before;program=state['spec']['program']
     for name,value in c['expected_parameters'].items():assert math.isclose(program['parameters'].get(name,float('nan')),value,rel_tol=1e-9),f"Expected editable {name}={value}, got {program['parameters']}"
     target={**c['parameters'],**c['expected_parameters']};source=c['source']
     if key=='engraved_plate':source=source.replace("'INTACT'","'CAD LAB'")
     reference=await asyncio.to_thread(service.build,source,target)
     expected={p['part']['id']:p for p in reference['parts']};actual={p['id']:p for p in state['spec']['parts']};assert set(expected)==set(actual),'Unrelated assembly part IDs changed'
     for name,p in expected.items():
      current=actual[name]
      for metric in ('volume_mm3','surface_area_mm2'):assert math.isclose(current['measurements'][metric],p[metric],rel_tol=1e-5,abs_tol=1e-4),f"{name} {metric}: AI {current['measurements'][metric]}, expected {p[metric]}"
      for dim in ('length','width','height'):assert math.isclose(current['params'][dim],p['part']['params'][dim],rel_tol=1e-5,abs_tol=1e-4),f'{name} changed dimension {dim} unexpectedly'
     entry['checks']+=['real model through LiteLLM and viewer Run API','selected native reference and real model PNG delivered','validated new revision and expected public parameters','all part IDs, native volume, surface area and bounds match intended edit']
     (folder/'ai-source.py').write_text(program['source']);save(folder/'ai-spec.json',state['spec'])
     png=await client.call_tool('snapshot_model',{'model_id':native['model_id'],'view':'iso'});assert not png.is_error,png
     image=next(c for c in png.content if c.type=='image');(folder/'ai.png').write_bytes(base64.b64decode(image.data))
     entry.update(status='passed',elapsed_seconds=round(time.monotonic()-started,2),revision=state['spec']['revision'],viewer_url=native['viewer_url'])
     print('AI PASS '+key+f" ({entry['elapsed_seconds']}s)",flush=True)
    except Exception as exc:entry.update(status='failed',error=str(exc)[:5000],elapsed_seconds=round(time.monotonic()-started,2));print('AI FAIL '+key+': '+str(exc)[:300],flush=True)
    save(folder/'ai.json',entry);summary();queue.task_done()
  await asyncio.gather(producer(),worker(),worker());report['phase']='complete';summary();print(f"AI: {report['passed']}/50 passed, {report['failed']} failed",flush=True)
asyncio.run(main())
