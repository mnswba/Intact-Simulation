import json,math,tempfile
from pathlib import Path
import pytest
from test_priority1 import disk,CIRCLE,PAD
from intact_backend.projects import ProjectService
from intact_backend.feature_graph import FeatureService
from intact_backend.design_checks import verify_design
from intact_backend.stable_references import bind,resolve
from intact_backend.isolated_worker import run_worker

def test_accuracy_at_refinement_floor_does_not_claim_convergence(disk):
    from intact_backend.accuracy import set_accuracy,check_accuracy
    s,f,key=disk
    set_accuracy(s,key,{'linear_deflection_mm':.0001,'angular_deflection_rad':.01})
    result=check_accuracy(s,key)
    assert not result['passed']
    assert next(c for c in result['checks'] if c['check']=='mesh convergence')['status']=='unverified'

def test_revolve_creates_torus_with_analytic_volume(tmp_path):
    s=ProjectService(tmp_path);f=FeatureService(s);r=f.create_sketch(None,{'id':'profile','geometry':[{'id':'circle','kind':'circle','center':[10,0],'radius':3}],'constraints':[{'id':'locked','kind':'lock','entities':['circle']}]})
    r=f.edit(r['model_id'],[{'id':'revolve','kind':'revolve','sketch_id':'profile','part_id':'torus','params':{'axis':[0,1,0],'angle_deg':360}}])
    assert r['spec']['parts'][0]['measurements']['volume_mm3']==pytest.approx(2*math.pi**2*10*3**2,rel=1e-7)

def test_unique_plane_tracks_extrusion_change_but_ambiguous_planes_fail(disk):
    s,f,key=disk;r=s.load(key);top=json.loads(s.artifact(key,'topology.json').read_text());face=next(f for f in top['parts'][0]['faces'] if f.get('normal')==[0,0,1])
    bound=bind(s,key,face['ref'],'top',r['spec']['revision'],r['spec']['program']['artifact_id']);s.parameters(key,{'thickness':8},expected_revision=bound['revision']);assert resolve(s,key,['stable:top'])['references'][0]['center'][2]==pytest.approx(8)
    f.edit(key,[{'id':'pattern','kind':'pattern','base':'pad','part_id':'disk','params':{'count':2,'step':[50,0,0]}}],mode='upsert')
    with pytest.raises(ValueError,match='ambiguous'):resolve(s,key,['stable:top'])

def test_colliding_parts_and_failed_clearance_are_detected(disk):
    s,f,key=disk;r=f.edit(key,[{'id':'copy','kind':'transform','base':'pad','part_id':'other','params':{'translation':[10,0,0]}}],mode='upsert')
    f.requirements(key,{'checks':[{'id':'collision','kind':'interference','part_id':'disk','other_part':'other','expected':{'max_volume_mm3':0}},{'id':'gap','kind':'clearance','part_id':'disk','other_part':'other','expected':{'min_mm':1}}]})
    result=verify_design(s,key);assert not result['passed'] and all(c['status']=='fail' for c in result['checks'])

def test_missing_and_malformed_criteria_are_unverified(disk):
    s,f,key=disk;assert not verify_design(s,key)['passed']
    f.requirements(key,{'checks':[{'id':'typo','kind':'bounds','part_id':'disk','expected':{'unknown_dimension':1}}]});assert verify_design(s,key)['checks'][0]['status']=='unverified'

def test_small_sampled_wall_is_a_real_failure(disk):
    s,f,key=disk;f.requirements(key,{'checks':[{'id':'thin','kind':'wall_thickness','part_id':'disk','expected':{'min_mm':6,'allow_sampled':True}}]});result=verify_design(s,key);assert not result['passed'] and result['checks'][0]['status']=='fail'

def test_self_contained_freecad_export_runs_without_input_step(disk,tmp_path):
    s,f,key=disk;source=s.artifact(key,'program.py')
    with tempfile.TemporaryDirectory() as tmp:
        directory=Path(tmp);i=directory/'input';o=directory/'output';i.mkdir();o.mkdir();runtime=f.runtime
        report=run_worker(s.programs,source,i,o,python=runtime.python(),mounts=[runtime.root],env={'PYTHONHOME':str(runtime.root/'usr'),'PYTHONPATH':str(runtime.root/'usr/lib')+':'+str(runtime.root/'usr/Mod'),'LD_LIBRARY_PATH':str(runtime.root/'usr/lib')})
        assert report['part_ids']==['disk'] and (o/'model.step').is_file() and (o/'design.FCStd').is_file()

@pytest.mark.parametrize('constraints,geometry,dof',[
    ([{'id':'a','kind':'angle','entities':['line'],'value':30},{'id':'length','kind':'length','entities':['line'],'value':10},{'id':'x','kind':'distance_x','entities':['line'],'points':[1],'value':0},{'id':'y','kind':'distance_y','entities':['line'],'points':[1],'value':0}],[{'id':'line','kind':'line','start':[0,0],'end':[8.66,5]}],0),
    ([{'id':'radius','kind':'radius','entities':['circle'],'value':5},{'id':'x','kind':'distance_x','entities':['circle'],'points':[3],'value':0},{'id':'y','kind':'distance_y','entities':['circle'],'points':[3],'value':0}],[{'id':'circle','kind':'circle','radius':5}],0),
    ([{'id':'fix','kind':'lock','entities':['circle']},{'id':'touch','kind':'point_on_object','entities':['line','circle'],'points':[1]}],[{'id':'circle','kind':'circle','radius':2},{'id':'line','kind':'line','start':[0,2],'end':[5,3]}],3),
    ([{'id':'fix','kind':'lock','entities':['circle']},{'id':'length','kind':'length','entities':['line'],'value':10},{'id':'horizontal','kind':'horizontal','entities':['line']},{'id':'tangent','kind':'tangent','entities':['line','circle']}],[{'id':'circle','kind':'circle','center':[0,2],'radius':2},{'id':'line','kind':'line','start':[-5,0],'end':[5,0]}],1),
])
def test_additional_constraint_kinds_use_the_actual_solver(tmp_path,constraints,geometry,dof):
    f=FeatureService(ProjectService(tmp_path));r=f.create_sketch(None,{'id':'test','geometry':geometry,'constraints':constraints});result=f.solve(r['model_id'])['sketches']['test'];assert result['solver_code']==0 and result['degrees_of_freedom']==dof
