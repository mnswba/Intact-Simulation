"""Behavioral regression checks for ChatGPT-only editing, history and TPMS exports."""
import json,math,sys,subprocess,os
from pathlib import Path
import pytest
from intact_backend.projects import ProjectService
from intact_backend.lattice_tools import build_tpms
from intact_backend.validation import validate_model
from intact_backend.intact_lattice import FAMILIES,field,tpms
from intact_backend.program import ProgramBuildError

SOURCE="import build123d as bd\ndef build(params):\n    return {'plate':bd.Box(params['length'],20,5)}"

@pytest.fixture
def history(tmp_path):
    service=ProjectService(tmp_path);r=service.build(SOURCE,{'length':30});service.parameters(r['model_id'],{'length':40});return service,r['model_id']

def test_browsing_history_and_current_restore_do_not_create_revisions(history):
    s,key=history;before=s.revisions(key)
    old=s.read_revision(key,1)
    assert old['spec']['program']['parameters']['length']==30
    assert old['spec']['revision']==1 and old['historical']
    assert s.load(key)['spec']['program']['parameters']['length']==40 and s.revisions(key)==before
    s.restore(key,2);assert s.revisions(key)==before
    recovered=s.restore(key,1);assert recovered['spec']['revision']==3
    s.restore(key,1);assert s.load(key)['spec']['revision']==3

def test_cache_repair_is_not_a_design_revision(history):
    s,key=history;before=s.revisions(key);s.artifact(key,'mesh.json').unlink();s.ensure_ready(key)
    assert s.revisions(key)==before

def test_old_revision_exports_match_old_geometry_without_changes(history):
    import build123d as bd
    s,key=history;before=s.revisions(key);old=s.read_revision(key,1)
    assert bd.import_step(s.record_artifact(old,'model.step')).volume==pytest.approx(30*20*5)
    assert s.portable(key,revision=1)['spec']['program']['parameters']['length']==30
    assert s.revisions(key)==before

def test_design_assertions_catch_wrong_dimensions(history):
    s,key=history
    assert validate_model(s,key,{'plate':{'length':40}},['plate'])['passed']
    assert not validate_model(s,key,{'plate':{'length':30}},['plate'])['passed']
    assert not validate_model(s,key,expected_part_ids=['wrong'])['passed']

@pytest.mark.parametrize('family',FAMILIES)
@pytest.mark.parametrize('mode',['sheet','solid'])
def test_tpms_families_produce_real_closed_exportable_meshes(tmp_path,family,mode):
    import trimesh
    bands={'neovius':1.5,'lidinoid':.8,'split_p':.7}
    s=ProjectService(tmp_path);r=build_tpms(s,{'family':family,'mode':mode,'length':16,'width':16,'height':16,'cell_size':8,'band':bands.get(family,.5),'samples_per_cell':16});key=r['model_id']
    assert r['geometry']['engine']=='implicit_mesh'
    m=r['spec']['parts'][0]['measurements'];assert m['provenance']=='validated triangle mesh' and m['watertight'] and 0<m['relative_density']<1
    assert validate_model(s,key,expected_part_ids=['lattice'])['passed']
    for name in ('model.stl','model.glb','model.3mf'):
        mesh=trimesh.load(s.artifact(key,name),force='mesh',process=True)
        assert mesh.is_watertight and mesh.is_volume
        assert math.isclose(mesh.volume*(1e9 if name.endswith('.glb') else 1),m['volume_mm3'],rel_tol=1e-5)
    with pytest.raises(ValueError,match='exact STEP'):s.artifact(key,'model.step')
    data=s.portable(key);path=tmp_path/'project.json';path.write_text(json.dumps(data));copy=s.import_project(path)
    assert copy['spec']['parts'][0]['measurements']==m

def test_tpms_periodicity_and_gyroid_equation():
    import numpy as np
    x,y,z=.31,.82,1.21
    assert field('gyroid',x,y,z)==pytest.approx(math.sin(x)*math.cos(y)+math.sin(y)*math.cos(z)+math.sin(z)*math.cos(x))
    for family in FAMILIES:assert field(family,x,y,z)==pytest.approx(field(family,x+2*np.pi,y-2*np.pi,z+4*np.pi))

def test_lattice_budget_is_checked_before_allocation():
    with pytest.raises(ValueError,match='budget'):tpms(size=(1000,1000,1000),cell_size=.1,samples_per_cell=64)
    with pytest.raises(ValueError,match='integer'):tpms(samples_per_cell=16.5)

def test_lattice_parameter_edit_preserves_previous_design_on_failure(tmp_path):
    s=ProjectService(tmp_path);r=build_tpms(s,{'length':12,'width':12,'height':12,'cell_size':6,'samples_per_cell':16});key=r['model_id'];before=s.load(key)
    with pytest.raises(ProgramBuildError):s.parameters(key,{'cell_size':.1,'samples_per_cell':64})
    assert s.load(key)==before
    after=s.parameters(key,{'band':.5},expected_revision=1)
    assert after['spec']['parts'][0]['measurements']['volume_mm3']>before['spec']['parts'][0]['measurements']['volume_mm3']

def test_tpms_saved_colors_and_standalone_python_export(tmp_path):
    import importlib.util,zipfile
    spec=importlib.util.spec_from_file_location('export_check',Path(__file__).resolve().parents[2]/'scripts/audit/export_check.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    s=ProjectService(tmp_path);r=build_tpms(s,{'length':12,'width':12,'height':12,'cell_size':6,'samples_per_cell':16});key=r['model_id']
    s.appearance(key,'lattice',color='#ff8800')
    with zipfile.ZipFile(s.artifact(key,'model.3mf')) as archive:assert '#FF8800FF' in archive.read('3D/3dmodel.model').decode()
    result=module.verify_python_export(s.artifact(key,'program.py'))
    assert result['valid'] and result['colors']['lattice']==(255,136,0)
    assert result['volume']==pytest.approx(r['spec']['parts'][0]['measurements']['volume_mm3'],rel=1e-5)


def test_repeated_shape_occurrences_keep_distinct_step_names_and_colors(tmp_path):
    import build123d as bd
    s=ProjectService(tmp_path)
    source="import build123d as bd\ndef build(params):\n    shared=bd.Box(10,8,4)\n    return {'first':shared,'second':bd.Pos(20,0,0)*shared}"
    r=s.build(source,{});assert validate_model(s,r['model_id'],expected_part_ids=['first','second'])['passed']
    s.appearance(r['model_id'],'first',color='#ff8800')
    shape=bd.import_step(s.artifact(r['model_id'],'model.step'));parts={p.label:p for p in shape.children}
    assert set(parts)=={'first','second'} and tuple(round(c*255) for c in tuple(parts['first'].color)[:3])==(255,136,0)
    assert tuple(parts['first'].color)!=tuple(parts['second'].color)

def test_mixed_lattice_and_native_curves_validate_against_sampled_export(tmp_path):
    s=ProjectService(tmp_path)
    source="import build123d as bd\nfrom intact_lattice import tpms\ndef build(params):\n    return {'core':tpms('gyroid',size=(12,12,12),cell_size=6,band=.4,samples_per_cell=16),'ring':bd.Pos(0,0,-8)*(bd.Cylinder(10,2)-bd.Cylinder(6,3))}"
    r=s.build(source,{});result=validate_model(s,r['model_id'])
    assert result['passed'] and result['reference_mesh_volume_mm3']>0
    assert result['reference_mesh_volume_mm3']!=pytest.approx(sum(p['measurements']['volume_mm3'] for p in r['spec']['parts']),rel=1e-5)
