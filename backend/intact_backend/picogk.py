"""Optional PicoGK TPMS engine with actual native runtime, never a silent fallback."""
import json,math,tempfile,os
from pathlib import Path
from pydantic import Field,StrictFloat,model_validator
from .p23_schema import LatticeMM
from .isolated_worker import run_worker
from .projects import atomic_json
class PicoGKSettings(LatticeMM):
 voxel_mm:StrictFloat|None=Field(default=None,ge=.025,le=2)
 @model_validator(mode='after')
 def valid_pico(self):
  if any(not 0<x<=128 for x in self.size):raise ValueError('PicoGK extents must be positive and <=128 mm.')
  voxel=self.voxel_mm or self.cell_size/self.samples_per_cell
  if math.prod(math.ceil(x/voxel)+4 for x in self.size)>4000000:raise ValueError('PicoGK sampling budget: <=4 million bounding voxels. Increase voxel_mm.')
  if self.thickness_mm*(1-abs(self.gradient))<3*voxel:raise ValueError('Use at least three voxels across the thinnest nominal wall.')
  return self

def paths():
 base=Path.home()/'.local/share/intact-simulation';return base/'dotnet',base/'picogk'
def readiness():
 dotnet,bridge=paths();return {'available':(dotnet/'dotnet').is_file() and (bridge/'Intact.PicoGK.dll').is_file(),'package':'PicoGK 2.4.0-alpha04','scope':'Optional voxel TPMS, mesh output, pinned Linux prerelease.'}
def build(projects,settings,cancel=None):
 s=PicoGKSettings.model_validate(settings);dotnet,bridge=paths()
 if not readiness()['available']:raise ValueError('PicoGK is not installed. Run scripts/install-picogk.py; the built-in TPMS engine remains available.')
 payload=s.model_dump(mode='json');payload['voxel_mm']=s.voxel_mm or s.cell_size/s.samples_per_cell
 with tempfile.TemporaryDirectory(prefix='intact-picogk-') as tmp:
  i=Path(tmp)/'input';o=Path(tmp)/'output';i.mkdir();o.mkdir();(i/'request.json').write_text(json.dumps(payload))
  import sys
  mounts=[str(Path(sys.base_prefix)),str(Path(sys.base_prefix).resolve()),str(Path(sys.prefix).resolve()),str(Path(sys.executable).resolve().parent.parent),str(Path(os.readlink(Path(sys.prefix)/'bin/python')).parent.parent)]
  # Bridge is published as a complete directory. Mounts expose only installed runtime binaries.
  # run_worker uses identical source/destination paths, so bridge aliases are created in private input.
  worker=Path(__file__).with_name('picogk_worker.py');script=i/'pico_worker.py';script.write_text(worker.read_text().replace('/pico-dotnet',str(dotnet)).replace('/pico-bridge',str(bridge)))
  report=run_worker(projects.programs,script,i,o,mounts=mounts+[str(dotnet),str(bridge)],cancel_event=cancel,timeout=170)
  model=projects.import_mesh_bytes((o/'result.stl').read_bytes(),'PicoGK '+s.family+' TPMS',cancel)
  report.update(model_id=model['model_id'],artifact_id=model['spec']['program']['artifact_id']);folder=projects.root/'picogk-reports';folder.mkdir(exist_ok=True);atomic_json(folder/(model['model_id']+'.json'),report)
  return {'model':model,'picogk':report}
