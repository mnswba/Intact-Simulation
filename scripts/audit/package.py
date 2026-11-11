"""Package private audit evidence and editable model exports, excluding raw account logs."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from catalog import CASES

REPO=Path(__file__).resolve().parents[2]
OUT=REPO/'outputs/50-model-audit'
target=REPO/'outputs/Intact-Simulation-0.8-Audit.zip'
files=set()
for pattern in ('*.html','review-*.png','*-report.json','summary.json','AUDIT_REPORT.md','backend-tests.xml','backend-tests.log'):
    files.update(OUT.glob(pattern))
files.add(OUT/'host/report.json')
for case in CASES:
    folder=OUT/case['key']
    for name in ('native.png','native.json','ai.json','release.json'):
        files.add(folder/name)
    files.update((folder/'release').glob('*'))
with ZipFile(target,'w',ZIP_DEFLATED,compresslevel=6) as archive:
    archive.writestr('README.txt','Intact Simulation 0.8 — private audit evidence\n\nOpen gallery.html to review all 50 designs before and after real AI edits.\nEach model folder includes editable Python, STEP/STL/GLB/3MF and project JSON exports.\nInteractive viewer links need the local Intact runtime on this computer.\nSee AUDIT_REPORT.md for test methods, fixes, installation and simulation limits.\nRaw account execution logs and credentials are excluded.\n')
    for path in sorted(files):
        if path.is_file():archive.write(path,path.relative_to(OUT))
    for name in ('intact-cad-50.jsonl','intact-cad-routing.json'):
        archive.write(REPO/'evals'/name,'evals/'+name)
with ZipFile(target) as archive:
    assert archive.testzip() is None
    print(f'{target}: {len(archive.namelist())} verified entries, {target.stat().st_size/1024**2:.1f} MiB')
