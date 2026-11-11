"""Bundle reviewable evidence and the demo project without account/client logs."""
import json,shutil,zipfile
from pathlib import Path
from intact_backend.projects import ProjectService
REPO=Path(__file__).resolve().parents[2];OUT=REPO/'outputs/priority1-audit';report=json.loads((OUT/'host/geometry-review.json').read_text());s=ProjectService(Path.home()/'.local/share/intact-studio');key=report['model_id'];demo=OUT/'demo';demo.mkdir(exist_ok=True)
for filename in ('model.step','model.stl','model.glb','model.3mf','program.py','design.FCStd'):
 shutil.copyfile(s.artifact(key,filename),demo/filename)
(demo/'project.json').write_text(json.dumps(s.portable(key),indent=2));(demo/'engineering.json').write_text(json.dumps(s.load(key)['engineering'],indent=2))
with zipfile.ZipFile(OUT/'Intact-Simulation-0.10-evidence.zip','w',zipfile.ZIP_DEFLATED) as z:
 for name in ('installation-report.json','tools-report.json','viewer-report.json','viewer-controls-report.json','summary.json','backend-tests.log','backend-tests.xml','refinement-floor.log','refinement-floor.xml','final-native-tests.log','final-native-tests.xml','draft-solved.png','feature-editor.png','historical-features.png','viewer-controls.png'):
  p=OUT/name
  if p.exists():z.write(p,'audit/'+name)
 for p in demo.iterdir():z.write(p,'demo/'+p.name)
 for name in ('LICENSE-PRIORITY1.txt','docs/PRIORITY1_AUDIT.md','docs/PRIORITY1_OPEN_SOURCE.md','plugin/skills/intact-cad/references/structured-modeling.md'):
  z.write(REPO/name,name)
 host=OUT/'host/report.json'
 if host.exists():z.writestr('audit/host-summary.json',json.dumps({k:v for k,v in json.loads(host.read_text()).items() if k!='final'},indent=2))
 for name in ('geometry-review.json','view-1.png','view-2.png'):
  p=OUT/'host'/name
  if p.exists():z.write(p,'audit/host/'+name)
print(OUT/'Intact-Simulation-0.10-evidence.zip')
