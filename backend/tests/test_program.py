import json
from pathlib import Path
import pytest
from intact_backend.program import ProgramService,ProgramBuildError,SandboxUnavailable
from intact_backend.program_policy import validate_source,validate_parameters,ProgramPolicyError
from intact_backend.generated import generated_spec

FLANGE='''import build123d as bd
import math
def build(params):
    d=params["diameter"]
    t=params["thickness"]
    body=bd.Cylinder(d/2,t,align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN))
    body-=bd.Cylinder(params["bore"]/2,t+2,align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN))
    for i in range(int(params["bolt_count"])):
        a=2*math.pi*i/params["bolt_count"]
        body-=bd.Pos(params["bolt_circle"]/2*math.cos(a),params["bolt_circle"]/2*math.sin(a),-1)*bd.Cylinder(params["bolt_diameter"]/2,t+2,align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN))
    return {"flange":body}
'''
PARAMS={'diameter':80,'thickness':8,'bore':24,'bolt_count':6,'bolt_circle':60,'bolt_diameter':6}

def test_policy_rejects_io_private_access_and_invalid_parameters():
    for source in ['import os\ndef build(params): return os.getcwd()','def build(params): return params.__class__','def build(params): return open("/etc/passwd")']:
        with pytest.raises(ProgramPolicyError):validate_source(source)
    with pytest.raises(ProgramPolicyError):validate_parameters({'height':float('nan')})
    with pytest.raises(ProgramPolicyError):validate_parameters({'height':True})
    assert validate_source(FLANGE)==FLANGE

def test_no_sandbox_means_no_execution(tmp_path,monkeypatch):
    service=ProgramService(tmp_path,binary='/missing/bwrap')
    monkeypatch.setattr(service,'available',lambda:False)
    with pytest.raises(SandboxUnavailable):service.build(FLANGE,PARAMS)

def test_freeform_flange_uses_real_cad_and_exports_actual_mesh(tmp_path,beam):
    service=ProgramService(tmp_path)
    assert service.available(),'The local free-form integration test requires a working rootless sandbox.'
    result=service.build(FLANGE,PARAMS);part=result['parts'][0]
    assert result['valid'] and part['part']['template']=='custom'
    assert part['solid_count']==1 and part['part']['params']['length']==pytest.approx(80)
    assert part['volume_mm3']>0
    root=tmp_path/result['artifact_id'];mesh=json.loads((root/'mesh.json').read_text())
    assert len(mesh['parts'][0]['positions'])>30 and len(mesh['parts'][0]['indices'])>30
    assert (root/'model.step').stat().st_size>1000
    assert service.build(FLANGE,PARAMS)['cached']
    # A partially missing export must never be treated as a successful cache hit.
    (root/'model.glb').unlink()
    repaired=service.build(FLANGE,PARAMS)
    assert not repaired['cached'] and (root/'model.glb').read_bytes()[:4]==b'glTF'
    spec=generated_spec(FLANGE,PARAMS,result,beam);assert spec.parts[0].id=='flange' and spec.program

def test_bad_program_preserves_original_spec(tmp_path,beam):
    service=ProgramService(tmp_path)
    if not service.available():pytest.skip('Sandbox not available on this host.')
    before=beam.model_dump_json()
    with pytest.raises(ProgramBuildError):service.build('def build(params):\n    raise ValueError("invalid CAD operation")',{})
    assert beam.model_dump_json()==before
