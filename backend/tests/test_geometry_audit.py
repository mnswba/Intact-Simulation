"""Real pre-display audit gate, bounded repairs, and rollback on failed V&V."""
import pytest
import json,shutil
from pathlib import Path
from intact_backend.isolated_worker import run_worker
from intact_backend.projects import ProjectService
from intact_backend.feature_graph import FeatureService
from intact_backend.geometry_audit import audit_model
from intact_backend.geometry_audit_worker import same_geometry

BOX='import build123d as bd\ndef build(p):\n    return {"block":bd.Box(p["length"],10,5)}'

def test_reversed_native_orientation_repaired_before_export(tmp_path):
    p=ProjectService(tmp_path)
    r=p.build('import build123d as bd\ndef build(p):\n    s=bd.Box(20,10,5)\n    s.wrapped.Reverse()\n    return {"block":s}',{})
    audit=r['geometry']['audit']
    assert audit['status']=='passed' and audit['repairs_count']==1
    assert audit['parts'][0]['repair_invariants']['bounds_max_deviation_mm']<=1e-6
    assert r['geometry']['parts'][0]['volume_mm3']==pytest.approx(1000)
    assert all(c['passed'] for c in audit['export_checks'])
    assert (p.programs.root/r['spec']['program']['artifact_id']/'audit.json').is_file()
    # Downloaded Python must reproduce the repaired solid as well, inside isolation.
    input_dir=tmp_path/'export-input';output=tmp_path/'export-output';input_dir.mkdir();output.mkdir()
    shutil.copyfile(p.artifact(r['model_id'],'program.py'),input_dir/'program.py')
    worker=tmp_path/'export_worker.py';worker.write_text('import runpy,json\nfrom pathlib import Path\nrunpy.run_path("/input/program.py",run_name="__main__")\nimport build123d as bd\ns=bd.import_step("/work/model.step")\nPath("/work/report.json").write_text(json.dumps({"valid":s.is_valid,"volume":s.volume}))')
    exported=run_worker(p.programs,worker,input_dir,output)
    assert exported['valid'] and exported['volume']==pytest.approx(1000)
    before=p.path(r['model_id']).read_bytes()
    with pytest.raises(ValueError,match='geometry audit rejected'):
        p.build('import build123d as bd\ndef build(p):\n    return {"block":bd.Rectangle(20,10)}',{},model_id=r['model_id'],expected_revision=1)
    assert p.path(r['model_id']).read_bytes()==before and len(p.revisions(r['model_id']))==1

def test_known_failed_requirements_block_commit_but_valid_change_succeeds(tmp_path):
    p=ProjectService(tmp_path);r=p.build(BOX,{'length':20.});key=r['model_id']
    FeatureService(p).requirements(key,{'checks':[{'id':'required_length','kind':'bounds','part_id':'block','expected':{'length':20.}}]})
    rev=p.load(key)['spec']['revision'];before=p.path(key).read_bytes()
    with pytest.raises(ValueError,match='Pre-display V&V rejected'):
        p.parameters(key,{'length':30.},expected_revision=rev)
    assert p.path(key).read_bytes()==before
    good=p.parameters(key,{'length':20.},expected_revision=rev)
    assert good['spec']['revision']==rev+1
    assert good['geometry']['audit']['design_verification']['status']=='passed'
    result=audit_model(p,key);assert result['design_verification']['status']=='passed'
    # No saved criteria is explicitly unverified, rather than a design-quality pass.
    assert r['geometry']['audit']['design_verification']['status']=='not_specified'

def test_repair_invariants_reject_geometric_or_topology_changes():
    before={'bounds_mm':[0,0,0,10,10,10],'solid_count':1,'face_count':6,'absolute_volume_mm3':1000.,'surface_area_mm2':600.}
    assert same_geometry(before,before)
    for change in [{'face_count':5},{'solid_count':2},{'absolute_volume_mm3':900.},{'bounds_mm':[0,0,0,11,10,10]}]:
        assert not same_geometry(before,{**before,**change})
