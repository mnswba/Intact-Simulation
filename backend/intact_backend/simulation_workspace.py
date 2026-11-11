"""Persist simulation definitions separately from immutable CAD revision artifacts."""
import json
from .projects import atomic_json
from .p23_schema import Simulation
from .simulation_schema import Motion
HEAVY={'frames','positions_mm','triangles','values','scalar_fields','fields','vectors','settings','study_definition'}
def compact(r):return {k:v for k,v in r.items() if k not in HEAVY and k!='result'}
def workspace(projects,key):
 r=projects.load(key);folder=projects.root/'simulation-workspaces';path=folder/(key+'.json')
 saved=json.loads(path.read_text()) if path.exists() else {'studies':{}}
 reports=[]
 for p in (projects.root/'engineering').glob(key+'-*.json'):
  report=json.loads(p.read_text())
  if report.get('kind') in ('thermal','structural','stokes','motion'):
   reports.append({**compact(report),'stale':report.get('artifact_id')!=r['spec']['program']['artifact_id']})
 from .engineering_jobs import status
 jobs=[]
 for p in (projects.root/'engineering-jobs').glob('*.json'):
  job=json.loads(p.read_text())
  if job.get('model_id')==key and job.get('operation') in ('simulate','motion'):
   job=status(projects,p.stem,key);jobs.append({**compact(job),'report_id':job.get('result',{}).get('report_id')})
 return {**saved,'model_id':key,'revision':r['spec']['revision'],'artifact_id':r['spec']['program']['artifact_id'],'parts':r['spec']['parts'],'reports':reports,'jobs':sorted(jobs,key=lambda x:x['created_at'],reverse=True)[:20]}
def configure(projects,key,settings,operation):
 if operation not in ('simulate','motion'):raise ValueError('Choose mechanical or virtual analysis.')
 r=projects.ensure_ready(key);s=(Motion if operation=='motion' else Simulation).model_validate(settings)
 if s.source_revision!=r['spec']['revision'] or s.source_artifact!=r['spec']['program']['artifact_id']:raise ValueError('Read current geometry and supply matching source_revision and source_artifact.')
 ids={p['id'] for p in r['spec']['parts']}
 if operation=='motion':
  if {b.part_id for b in s.bodies}!=ids:raise ValueError('Configure every model part exactly once.')
 elif s.part_id not in ids:raise ValueError('Select a current native part.')
 elif any(b.selector=='faces' for b in s.boundary_conditions):
  topology=json.loads(projects.record_artifact(r,'topology.json').read_text());part=next(p for p in topology['parts'] if p['id']==s.part_id);refs={f['ref'] for f in part['faces']}
  if any(ref not in refs for b in s.boundary_conditions if b.selector=='faces' for ref in b.references):raise ValueError('Boundary faces must belong to the selected current solid.')
 folder=projects.root/'simulation-workspaces';folder.mkdir(exist_ok=True);path=folder/(key+'.json')
 import fcntl
 with (folder/(key+'.lock')).open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);saved=json.loads(path.read_text()) if path.exists() else {'studies':{}}
  saved['studies']['motion' if operation=='motion' else s.kind]=s.model_dump(mode='json');atomic_json(path,saved)
 return workspace(projects,key)
