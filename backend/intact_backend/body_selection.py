"""Artifact-bound native body selection cache; does not alter model records."""
import json,shutil,tempfile
from pathlib import Path
from .projects import atomic_json
from .isolated_worker import run_worker

def bodies(projects,record,part_id=None):
 artifact=record['spec']['program']['artifact_id'];folder=projects.root/'body-selection';folder.mkdir(exist_ok=True);cache=folder/(artifact+('-'+part_id if part_id else '')+'.json')
 if part_id and part_id not in {p['id'] for p in record['spec']['parts']}:raise ValueError('Unknown selected part.')
 with projects.programs.artifact_lock('bodies-'+artifact):
  if cache.exists():return json.loads(cache.read_text())
  if record['geometry']['engine']=='implicit_mesh':
   result={'bodies':[{'ref':p['id']+'.b1','kind':'body','part_id':p['id'],'index':1,'face_refs':[],'provenance':'Whole mesh component; native solids unavailable'} for p in record['spec']['parts'] if part_id is None or p['id']==part_id]}
  else:
   with tempfile.TemporaryDirectory(prefix='intact-bodies-') as tmp:
    src=Path(tmp)/'input';out=Path(tmp)/'output';src.mkdir();out.mkdir()
    for name in ('model.step','topology.json'):shutil.copyfile(projects.record_artifact(record,name),src/name)
    if part_id:
     topology=json.loads((src/'topology.json').read_text());topology['parts']=[p for p in topology['parts'] if p['id']==part_id];(src/'topology.json').write_text(json.dumps(topology))
    result=run_worker(projects.programs,Path(__file__).with_name('body_worker.py'),src,out,timeout=100)
  result.update(artifact_id=artifact);atomic_json(cache,result);return result
