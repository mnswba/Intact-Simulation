"""Native priority-1 regression checks; all CAD/FreeCAD code runs isolated."""
import json,math
from copy import deepcopy
from pathlib import Path
import pytest
from intact_backend.projects import ProjectService
from intact_backend.feature_graph import FeatureService
from intact_backend.design_checks import verify_design
from intact_backend.accuracy import set_accuracy,check_accuracy
from intact_backend.stable_references import bind,resolve
from intact_backend.validation import validate_model

CIRCLE={'id':'outline','geometry':[{'id':'circle','kind':'circle','radius':20}], 'constraints':[{'id':'diameter','kind':'diameter','entities':['circle'],'value':{'parameter':'diameter'}},{'id':'cx','kind':'distance_x','entities':['circle'],'points':[3],'value':0},{'id':'cy','kind':'distance_y','entities':['circle'],'points':[3],'value':0}]}
PAD={'id':'pad','kind':'extrude','part_id':'disk','sketch_id':'outline','params':{'height':{'parameter':'thickness'}}}
@pytest.fixture
def disk(tmp_path):
    s=ProjectService(tmp_path);f=FeatureService(s);r=f.create_sketch(None,CIRCLE,parameters={'diameter':40,'thickness':5});key=r['model_id'];r=f.edit(key,[PAD]);return s,f,key

def test_empty_design_requirements_do_not_create_placeholder_solids(tmp_path):
    s=ProjectService(tmp_path);f=FeatureService(s);r=f.requirements(None,{'checks':[{'id':'parts','kind':'part_count','expected':{'count':1}}]},name='Intent first')
    assert r['draft'] and not r['geometry_available'] and not s.path(r['model_id']).exists()

def test_constraint_solver_reports_real_dof_without_saving_geometry(tmp_path):
    s=ProjectService(tmp_path);f=FeatureService(s);r=f.create_sketch(None,{'id':'line','geometry':[{'id':'edge','kind':'line'}]});key=r['model_id'];before=f.draft_path(key).read_bytes()
    report=f.solve(key);assert report['sketches']['line']['degrees_of_freedom']==4
    assert not report['sketches']['line']['fully_constrained'] and f.draft_path(key).read_bytes()==before

def test_conflicting_constraints_are_reported_and_cannot_publish(tmp_path):
    s=ProjectService(tmp_path);f=FeatureService(s);sketch=deepcopy(CIRCLE);sketch['constraints'][0]['value']=40;sketch['constraints'].append({'id':'contradiction','kind':'diameter','entities':['circle'],'value':50})
    r=f.create_sketch(None,sketch);key=r['model_id'];report=f.solve(key);assert report['sketches']['outline']['conflict']
    with pytest.raises(ValueError,match='conflicting'):f.edit(key,[PAD],{'thickness':5})
    assert not s.path(key).exists()

def test_constrained_feature_rebuild_and_dimensions_change_preserve_constraints(disk):
    s,f,key=disk;r=s.load(key);assert r['spec']['parts'][0]['measurements']['volume_mm3']==pytest.approx(math.pi*20**2*5)
    assert r['engineering']['diagnostics']['sketches']['outline']['degrees_of_freedom']==0
    changed=s.parameters(key,{'diameter':50,'thickness':8},expected_revision=r['spec']['revision'])
    assert changed['spec']['parts'][0]['measurements']['volume_mm3']==pytest.approx(math.pi*25**2*8)
    assert changed['engineering']['diagnostics']['sketches']['outline']['fully_constrained']
    assert validate_model(s,key,{'disk':{'length':50,'width':50,'height':8}},['disk'])['passed']

def test_failed_feature_and_stale_revision_preserve_valid_graph(disk):
    s,f,key=disk;before=s.load(key)
    with pytest.raises(ValueError):f.edit(key,[{'id':'bad','kind':'hole','base':'pad','part_id':'disk','params':{'diameter':100,'centers':[[0,0,0]],'through':True}}],mode='upsert')
    assert s.load(key)==before
    with pytest.raises(ValueError,match='changed'):f.rebuild(key,expected_revision=1)

def test_native_hole_count_location_depth_through_and_negative_expectations(disk):
    s,f,key=disk;f.edit(key,[{'id':'holes','kind':'hole','base':'pad','part_id':'disk','params':{'diameter':6,'centers':[[10,0,0],[-10,0,0]],'through':True}}],mode='upsert')
    req={'checks':[{'id':'bores','kind':'hole_pattern','part_id':'disk','expected':{'count':2,'diameter_mm':6,'depth_mm':5,'through':True,'centers_mm':[[10,0,0],[-10,0,0]]}}]}
    f.requirements(key,req);before=s.load(key)['spec']['revision'];assert verify_design(s,key)['passed'];assert s.load(key)['spec']['revision']==before
    req['checks'][0]['expected']['diameter_mm']=7;f.requirements(key,req);result=verify_design(s,key);assert not result['passed'] and result['checks'][0]['status']=='fail'

def test_blind_hole_is_not_reported_as_through(disk):
    s,f,key=disk;f.edit(key,[{'id':'blind','kind':'hole','base':'pad','part_id':'disk','params':{'diameter':6,'centers':[[0,0,5]],'axis':[0,0,-1],'depth':3,'through':False}}],mode='upsert')
    f.requirements(key,{'checks':[{'id':'blind_depth','kind':'hole_pattern','part_id':'disk','expected':{'count':1,'diameter_mm':6,'depth_mm':3,'through':False}}]});assert verify_design(s,key)['passed']

@pytest.mark.parametrize('kind,params',[('fillet',{'radius':1,'edges':[{'geometry':'circle','radius':20,'at':[20,0,5]}]}),('chamfer',{'distance':1,'edges':[{'geometry':'circle','radius':20,'at':[20,0,5]}]})])
def test_edge_features_and_suppression_are_real_geometry(disk,kind,params):
    s,f,key=disk;initial=s.load(key)['spec']['parts'][0]['measurements']['volume_mm3']
    r=f.edit(key,[{'id':'finish','kind':kind,'base':'pad','part_id':'disk','params':params}],mode='upsert');assert r['spec']['parts'][0]['measurements']['volume_mm3']<initial
    feature=r['engineering']['features'][-1];feature['suppressed']=True;r=f.edit(key,[feature],mode='upsert');assert r['spec']['parts'][0]['measurements']['volume_mm3']==pytest.approx(initial)

def test_ambiguous_edge_selector_does_not_choose_an_edge(disk):
    s,f,key=disk;before=s.load(key)
    with pytest.raises(ValueError,match='ambiguous'):f.edit(key,[{'id':'finish','kind':'fillet','base':'pad','part_id':'disk','params':{'radius':1,'edges':[{'geometry':'circle','radius':20}]}}],mode='upsert')
    assert s.load(key)==before

def test_pattern_transform_and_nonoverlap_checks(disk):
    s,f,key=disk;pad=deepcopy(PAD);pad['part_id']=None
    r=f.edit(key,[pad,{'id':'array','kind':'pattern','base':'pad','part_id':'pair','params':{'count':2,'step':[50,0,0]}},{'id':'move','kind':'transform','base':'pad','part_id':'third','params':{'translation':[0,60,0]}}])
    assert {p['id'] for p in r['spec']['parts']}=={'pair','third'}
    pair=next(p for p in r['spec']['parts'] if p['id']=='pair');assert pair['measurements']['solid_count']==2
    f.requirements(key,{'checks':[{'id':'gap','kind':'clearance','part_id':'pair','other_part':'third','expected':{'min_mm':19.9}},{'id':'collision','kind':'interference','part_id':'pair','other_part':'third','expected':{'max_volume_mm3':0}}]});assert verify_design(s,key)['passed']
    s.appearance(key,'pair',color='#ff8800');assert validate_model(s,key)['passed']

def test_boolean_cut_matches_independent_circle_overlap(disk):
    s,f,key=disk;pad=deepcopy(PAD);pad['part_id']=None
    r=f.edit(key,[pad,{'id':'tool','kind':'transform','base':'pad','params':{'translation':[20,0,0]}},{'id':'cut','kind':'boolean','base':'pad','tool':'tool','part_id':'crescent','params':{'operation':'cut'}}])
    overlap=2*20**2*math.acos(.5)-.5*20*math.sqrt(4*20**2-20**2)
    assert r['spec']['parts'][0]['measurements']['volume_mm3']==pytest.approx((math.pi*20**2-overlap)*5,rel=1e-7)

def test_semantic_bore_reference_tracks_diameter_change(disk):
    s,f,key=disk;r=f.edit(key,[{'id':'bore','kind':'hole','base':'pad','part_id':'disk','params':{'diameter':{'parameter':'bore_diameter'},'centers':[[0,0,0]],'through':True}}],{'bore_diameter':6},mode='upsert')
    topology=json.loads(s.artifact(key,'topology.json').read_text());face=next(face for face in topology['parts'][0]['faces'] if face.get('radius_mm')==3)
    bound=bind(s,key,face['ref'],'mounting_bore',r['spec']['revision'],r['spec']['program']['artifact_id']);s.parameters(key,{'bore_diameter':8},expected_revision=bound['revision'])
    current=resolve(s,key,['stable:mounting_bore']);assert current['references'][0]['radius_mm']==4 and current['references'][0]['matched_by']=='feature anchor'
    feature=s.load(key)['engineering']['features'][-1];feature['suppressed']=True;f.edit(key,[feature],mode='upsert')
    with pytest.raises(ValueError,match='missing'):resolve(s,key,['stable:mounting_bore'])

def test_project_v3_roundtrip_keeps_constraints_and_can_rebuild(disk,tmp_path):
    s,f,key=disk;portable=s.portable(key);assert portable['version']==3
    file=tmp_path/'project.json';file.write_text(json.dumps(portable));other=ProjectService(tmp_path/'other');r=other.import_project(file)
    assert r['engineering']['sketches']==s.load(key)['engineering']['sketches']
    rebuilt=FeatureService(other).parameters(r['model_id'],{'thickness':9})
    assert rebuilt['spec']['parts'][0]['params']['height']==pytest.approx(9)

def test_accuracy_settings_and_convergence_are_measured_without_editing(disk):
    s,f,key=disk;r=set_accuracy(s,key,{'linear_deflection_mm':.01,'dimensional_tolerance_mm':.005});revision=r['spec']['revision']
    assert r['spec']['program']['meshing']['linear_deflection_mm']==.01
    result=check_accuracy(s,key);assert result['passed'] and result['geometry_revision_unchanged'];assert s.load(key)['spec']['revision']==revision

def test_global_wall_thickness_is_not_certified_by_samples(disk):
    s,f,key=disk;f.requirements(key,{'checks':[{'id':'wall','kind':'wall_thickness','part_id':'disk','expected':{'min_mm':4}}]})
    result=verify_design(s,key);assert result['checks'][0]['status']=='unverified' and not result['passed']

def test_native_document_and_self_contained_feature_python_export(disk):
    s,f,key=disk;assert s.artifact(key,'design.FCStd').stat().st_size>100
    python=s.artifact(key,'program.py').read_text();assert 'PARAMETERS =' in python and 'FreeCAD' in python and '/input/request.json' not in python
