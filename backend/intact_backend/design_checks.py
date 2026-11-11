# SPDX-License-Identifier: Apache-2.0
"""Requirements-backed verification, without changing design revisions."""
import json,shutil,tempfile
from pathlib import Path
from .engineering_schema import Engineering
from .isolated_worker import run_worker
from .projects import atomic_json

def verify_design(projects,model_id):
    from .validation import validate_model
    r=projects.ensure_ready(model_id);e=Engineering.model_validate(r.get('engineering',{}));base=validate_model(projects,model_id)
    if not e.requirements.checks:result={'checks':[],'all_passed':False,'reason':'No design acceptance criteria have been saved.'}
    elif r['geometry']['engine']=='implicit_mesh':result={'checks':[{'id':c.id,'kind':c.kind,'status':'unverified','reason':'This requirement requires native CAD geometry; the model includes an implicit mesh.'} for c in e.requirements.checks],'all_passed':False}
    else:
        with tempfile.TemporaryDirectory(prefix='intact-checks-') as tmp:
            folder=Path(tmp);input_dir=folder/'input';output=folder/'output';input_dir.mkdir();output.mkdir();shutil.copyfile(projects.artifact(model_id,'model.step'),input_dir/'model.step')
            (input_dir/'request.json').write_text(json.dumps({'checks':[c.model_dump(mode='json') for c in e.requirements.checks],'tolerance_mm':e.accuracy.dimensional_tolerance_mm}))
            result=run_worker(projects.programs,Path(__file__).with_name('native_checks_worker.py'),input_dir,output,timeout=100)
    result.update(model_id=model_id,revision=r['spec']['revision'],artifact_id=r['spec']['program']['artifact_id'],export_validation=base,passed=base['passed'] and result['all_passed'],assumptions=e.requirements.assumptions)
    if e.diagnostics.get('needs_rebuild'):
        result['passed']=False;result['all_passed']=False;result['reason']='Sketch/feature edits are waiting for rebuild. Saved geometry is from the previous graph.'
    atomic_json(projects.root/'verification'/str(model_id+'.json'),result)
    return result
