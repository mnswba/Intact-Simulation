"""Run 200 isolated model configurations; authored regression fixtures, not AI training."""
import concurrent.futures,json,math,sys,time
from pathlib import Path
from catalog_09 import CASES
from intact_backend.projects import ProjectService
from intact_backend.lattice_tools import build_tpms
from intact_backend.validation import validate_model

REPO=Path(__file__).resolve().parents[2];OUT=REPO/'outputs/0.9-audit';OUT.mkdir(parents=True,exist_ok=True)
ROOT=Path.home()/'.local/share/intact-simulation/audit-09'
report_path=OUT/'models-report.json'
report=json.loads(report_path.read_text()) if report_path.exists() else {'version':'0.9.0','total':200,'cases':{}}

def run(case):
    key=case['id'];s=ProjectService(ROOT);folder=OUT/key;folder.mkdir(exist_ok=True);started=time.monotonic()
    try:
        previous=report['cases'].get(key,{})
        if previous.get('status')=='passed' and previous.get('validation_version')==2:
            record=s.load(previous['model_id']);p=record['spec']['program']
            if p['artifact_id']==s.programs.key(p['source'],p['parameters'],p.get('asset_id')) and s.programs.cached_report(p['artifact_id']):return key,previous
        r=build_tpms(s,case['lattice']) if 'lattice' in case else s.build(case['source'],case['parameters'],name=case['name'])
        model_id=r['model_id'];parts=r['spec']['parts'];validation=validate_model(s,model_id)
        assert validation['passed'],validation
        if case.get('parts') is not None:assert len(parts)==case['parts']
        if case.get('volume') is not None:assert math.isclose(sum(p['measurements']['volume_mm3'] for p in parts),case['volume'],rel_tol=1e-6)
        mesh_mode=r['geometry']['engine']=='implicit_mesh'
        formats=['model.stl','model.glb','model.3mf','program.py']+([] if mesh_mode else ['model.step'])
        if mesh_mode:
            import trimesh
            expected=validation['reference_mesh_volume_mm3']
            for filename in ('model.glb','model.3mf'):
                m=trimesh.load(s.artifact(model_id,filename),force='mesh',process=True)
                volume=m.volume*(1e9 if filename.endswith('.glb') else 1)
                assert m.is_watertight and m.is_volume and math.isclose(volume,expected,rel_tol=1e-5,abs_tol=1e-5),(filename,m.is_watertight,volume,expected)
        for filename in formats:
            import shutil
            shutil.copyfile(s.artifact(model_id,filename),folder/filename)
        (folder/'validation.json').write_text(json.dumps(validation,indent=2))
        entry={'validation_version':2,'status':'passed','name':case['name'],'category':case['category'],'model_id':model_id,'engine':r['geometry']['engine'],'parts':len(parts),'solid_count':sum(p['measurements']['solid_count'] for p in parts),'triangles':r['geometry']['triangles'],'volume_mm3':sum(p['measurements']['volume_mm3'] for p in parts),'exports':formats,'elapsed_seconds':round(time.monotonic()-started,2)}
        if 'lattice' in case:entry['lattice']=r['geometry']['parts'][0]['lattice']
        return key,entry
    except Exception as exc:return key,{'status':'failed','name':case['name'],'category':case['category'],'error':str(exc)[-4000:]}

started=time.monotonic()
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
    futures=[pool.submit(run,c) for c in CASES]
    for future in concurrent.futures.as_completed(futures):
        key,entry=future.result();report['cases'][key]=entry
        report['passed']=sum(c['status']=='passed' for c in report['cases'].values());report['failed']=sum(c['status']=='failed' for c in report['cases'].values());report['elapsed_seconds']=round(time.monotonic()-started,1)
        report_path.write_text(json.dumps(report,indent=2));print(f"{entry['status'].upper()} {key} [{report['passed']} pass, {report['failed']} fail]"+((': '+entry.get('error','')[-400:]) if entry['status']=='failed' else ''),flush=True)
print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2))
sys.exit(bool(report['failed']))
