"""Create a private evidence/model bundle without account logs or credentials."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from catalog_09 import CASES
REPO=Path(__file__).resolve().parents[2];OUT=REPO/'outputs/0.9-audit';target=REPO/'outputs/Intact-Simulation-0.9-Models-and-Audit.zip'
files=set()
for pattern in ('*.html','*-report.json','summary.json','*.md','*.png','backend-tests.xml','backend-tests.log','website-tests.log'):
    files.update(OUT.glob(pattern))
for c in CASES:files.update(p for p in (OUT/c['id']).glob('*') if p.is_file())
files.add(OUT/'host/report.json');files.add(OUT/'host/gallery.html')
for label in ('phone','gyroid'):files.update((OUT/'host'/label).glob('*'))
with ZipFile(target,'w',ZIP_DEFLATED,compresslevel=5) as archive:
    archive.writestr('README.txt','Intact Simulation 0.9 — private model and audit bundle\n\nOpen gallery.html to review 200 authored regression configurations.\nOpen host/gallery.html for two models generated through the live OpenAI plugin client.\nRead AUDIT_REPORT.md and AI_CAD_COMPARISON.md for checks, fixes and limits.\nEach model folder has actual exports, editable Python, validation facts and an actual PNG.\nInteractive viewer links need Intact running on this computer.\nTPMS Python needs build123d, numpy, trimesh and scikit-image; its helper is embedded.\nSampled TPMS geometry exports STL/GLB/3MF, not exact STEP; band is not mm wall thickness.\nThis is an evidence/model bundle, not a standalone installer or trained AI model.\nRaw account execution logs and credentials are excluded.\n')
    for p in sorted(files):
        if p.is_file():archive.write(p,p.relative_to(OUT))
    for name in ('intact-cad-200.jsonl','intact-cad-routing.json'):archive.write(REPO/'evals'/name,'evals/'+name)
    for p in (REPO/'plugin/skills/intact-cad').rglob('*'):
        if p.is_file():archive.write(p,'plugin-guidance/'+str(p.relative_to(REPO/'plugin/skills/intact-cad')))
with ZipFile(target) as archive:
    assert archive.testzip() is None
    print(f'{target}: {len(archive.namelist())} verified entries; {target.stat().st_size/1024**2:.1f} MiB')
