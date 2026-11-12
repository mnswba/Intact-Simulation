"""Precommit requirements gate and AI-readable V&V evidence."""
from copy import deepcopy
from hashlib import sha256
import json,shutil,tempfile
from pathlib import Path
from .engineering_schema import Engineering
from .isolated_worker import run_worker


def requirements_hash(engineering):
    return sha256(json.dumps(Engineering.model_validate(engineering or {}).requirements.model_dump(mode='json'),sort_keys=True).encode()).hexdigest()


def precommit_checks(programs,report,engineering,cancel_event=None):
    report=deepcopy(report);e=Engineering.model_validate(engineering or {});audit=report['audit'];criteria=e.requirements.checks
    audit['requirements_hash']=requirements_hash(engineering)
    if not criteria:
        audit['design_verification']={'status':'not_specified','checks':[],'note':'No acceptance criteria saved; design intent and physical performance are not verified.'};return report
    if report['engine']=='implicit_mesh':
        audit['design_verification']={'status':'unverified','checks':[],'note':'Saved native-CAD requirements need an explicit mesh-compatible verification workflow.'};return report
    with tempfile.TemporaryDirectory(prefix='intact-precommit-checks-') as tmp:
        folder=Path(tmp);input_dir=folder/'input';output=folder/'output';input_dir.mkdir();output.mkdir()
        shutil.copyfile(programs.root/report['artifact_id']/'model.step',input_dir/'model.step')
        (input_dir/'request.json').write_text(json.dumps({'checks':[c.model_dump(mode='json') for c in criteria],'tolerance_mm':e.accuracy.dimensional_tolerance_mm}))
        result=run_worker(programs,Path(__file__).with_name('native_checks_worker.py'),input_dir,output,timeout=100,cancel_event=cancel_event)
    failed=[c for c in result['checks'] if c['status']=='fail']
    if failed:raise ValueError('Pre-display V&V rejected the proposed design: '+json.dumps(failed)[:2200]+'. No CAD revision was published. Fix the source or explicitly revise the requirements with the user; never weaken checks merely to pass.')
    audit['design_verification']={'status':'passed' if result['all_passed'] else 'unverified',**result}
    return report


def audit_model(projects,key,verify_requirements=True):
    record=projects.ensure_ready(key);audit=deepcopy(record['geometry']['audit'])
    if verify_requirements and record.get('engineering',{}).get('requirements',{}).get('checks'):
        from .design_checks import verify_design
        result=verify_design(projects,key);audit['design_verification']={'status':'passed' if result['passed'] else 'failed' if any(c['status']=='fail' for c in result['checks']) else 'unverified',**result}
    elif not record.get('engineering',{}).get('requirements',{}).get('checks'):
        audit['design_verification']={'status':'not_specified','checks':[],'note':'No design acceptance criteria saved.'}
    elif audit.get('requirements_hash')!=requirements_hash(record.get('engineering')):
        audit['design_verification']={'status':'not_evaluated','note':'Requirements changed after this build; run audit_model with verify_requirements=true.'}
    audit.update(model_id=key,revision=record['spec']['revision'],artifact_id=record['spec']['program']['artifact_id'])
    return audit
