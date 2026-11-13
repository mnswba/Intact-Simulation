"""Read native solid membership without rebuilding or changing a CAD artifact."""
import json,sys,traceback
from pathlib import Path
from worker_context import resource,worker_path
resource.setrlimit(resource.RLIMIT_CPU,(80,80));resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3))
import build123d as bd
import numpy as np

def main():
 model=bd.import_step(worker_path('/input/model.step'));parts={p.label:p for p in model.children};topology=json.loads(Path(worker_path('/input/topology.json')).read_text());result=[]
 for part in topology['parts']:
  shape=parts.get(part['id'])
  if shape is None:raise ValueError('Native part is missing: '+part['id'])
  solids=list(shape.solids());assigned=set()
  for i,solid in enumerate(solids):
   refs=[]
   if len(solids)==1:refs=[f['ref'] for f in part['faces']]
   else:
    for face in solid.faces():
     center=face.center(bd.CenterOf.MASS);c=np.array([center.X,center.Y,center.Z]);matches=[f for f in part['faces'] if abs(f['area_mm2']-face.area)<=max(1,face.area)*1e-6 and np.linalg.norm(c-f['center'])<1e-5]
     if len(matches)!=1:raise ValueError('Body membership is ambiguous; cannot safely select this solid.')
     refs.append(matches[0]['ref'])
   if assigned.intersection(refs):raise ValueError('Body face membership overlaps ambiguously.')
   assigned.update(refs);bounds=solid.bounding_box();xyz=lambda p:[float(p.X),float(p.Y),float(p.Z)]
   result.append({'ref':part['id']+'.b'+str(i+1),'kind':'body','part_id':part['id'],'index':i+1,'face_refs':refs,'volume_mm3':float(solid.volume),'bounds':{'min':xyz(bounds.min),'max':xyz(bounds.max),'size':xyz(bounds.size)},'provenance':'Native STEP solid / OpenCASCADE'})
  if assigned!={f['ref'] for f in part['faces']}:raise ValueError('Some faces do not belong to a unique solid.')
 Path(worker_path('/work/report.json')).write_text(json.dumps({'bodies':result}))
try:main()
except BaseException as exc:Path(worker_path('/work/error.json')).write_text(json.dumps({'error':str(exc),'traceback':traceback.format_exc()[-2000:]}));sys.exit(1)
