"""Independent geometry and PDE checks for the priority 2/3 adapter."""
import json,math,threading,time
from pathlib import Path
import numpy as np
import pytest
from intact_backend.projects import ProjectService
from intact_backend.advanced import Advanced
from intact_backend.component_library import insert,catalog
from intact_backend.engineering_jobs import submit,status,cancel

@pytest.fixture
def native(tmp_path):
 s=ProjectService(tmp_path);r=s.build('import build123d as bd\ndef build(params):\n    return {"body":bd.Box(params["length"],10,10)}',{'length':20});return s,Advanced(s),r['model_id']

@pytest.mark.parametrize('family',['gyroid','schwarz_p','diamond','neovius','lidinoid','split_p'])
def test_distance_offset_tpms_closed_and_reports_uncertainty(tmp_path,family):
 s=ProjectService(tmp_path);r=Advanced(s).lattice({'family':family,'size':[10,10,10],'cell_size':8,'thickness_mm':1.6,'samples_per_cell':24});p=r['geometry']['parts'][0];assert p['watertight'] and p['volume_mm3']>0;assert p['lattice']['target_thickness_mm']==1.6 and p['lattice']['distance_uncertainty_mm']>0

def test_underresolved_wall_fails_without_mutating_native(native):
 s,a,key=native;before=s.load(key)
 with pytest.raises(ValueError,match='under-resolved'):a.lattice({'thickness_mm':.1},model_id=key)
 assert s.load(key)==before

@pytest.mark.parametrize('operation',['union','difference','intersection'])
def test_mesh_native_boolean_is_real_and_preserves_other_parts(native,operation):
 s,a,key=native;r=a.hybrid(key,{'part_id':'body','operation':operation,'size':[12,12,12],'cell_size':8,'thickness_mm':1.6,'samples_per_cell':24});volume=r['geometry']['parts'][0]['volume_mm3'];assert r['geometry']['engine']=='implicit_mesh';assert volume>2000 if operation=='union' else 0<volume<2000

def test_adaptive_refinement_never_claims_one_level_convergence(tmp_path):
 a=Advanced(ProjectService(tmp_path));r=a.adaptive({'size':[10,10,10],'cell_size':8,'thickness_mm':1.6,'samples_per_cell':24,'maximum_samples_per_cell':24});assert len(r['levels'])==1 and not r['converged']

def test_faceted_step_reopens_with_same_volume_and_honest_representation(native):
 s,a,key=native;r=a.convert(key,100);assert r['conversion']['relative_volume_error']<1e-6;assert 'planar' in r['conversion']['representation'];assert r['model']['geometry']['engine']=='build123d'

def test_conversion_budget_fails_atomically(native):
 s,a,key=native;count=len(s.list())
 with pytest.raises(ValueError,match='budget'):a.convert(key,4)
 assert len(s.list())==count

def test_joint_motion_limits_preserve_rest_placement(tmp_path):
 s=ProjectService(tmp_path);r=s.build('import build123d as bd\ndef build(params):\n    return {"base":bd.Box(10,10,10),"slider":bd.Pos(0,20,0)*bd.Box(2,2,2)}',{});key=r['model_id'];a=Advanced(s)
 motion=a.assembly(key,{'joints':[{'id':'travel','kind':'slider','parent':'base','child':'slider','axis':[1,0,0],'minimum':0,'maximum':20,'value':10}]});p=next(p for p in motion['model']['spec']['parts'] if p['id']=='slider');assert p['position'][0]==pytest.approx(10);assert motion['motion']['all_passed']
 changed=s.parameters(key,{'travel':5});assert next(p for p in changed['spec']['parts'] if p['id']=='slider')['position'][0]==pytest.approx(5)
 before=s.load(key)
 with pytest.raises(ValueError,match='motion limit'):s.parameters(key,{'travel':25})
 assert s.load(key)==before

def test_cycles_rejected_before_any_commit(tmp_path):
 s=ProjectService(tmp_path);r=s.build('import build123d as bd\ndef build(params):\n    return {"a":bd.Box(1,1,1),"b":bd.Pos(3,0,0)*bd.Box(1,1,1)}',{});before=s.load(r['model_id'])
 with pytest.raises(ValueError,match='cycle'):Advanced(s).assembly(r['model_id'],{'joints':[{'id':'a_to_b','kind':'fixed','parent':'a','child':'b'},{'id':'b_to_a','kind':'fixed','parent':'b','child':'a'}]})
 assert s.load(r['model_id'])==before

def test_freeform_loft_positive_volume(tmp_path):
 a=Advanced(ProjectService(tmp_path));r=a.freeform({'sections':[[[-5,-5,0],[5,-5,0],[5,5,0],[-5,5,0]],[[-3,-3,10],[3,-3,10],[3,3,10],[-3,3,10]]]});assert r['geometry']['parts'][0]['volume_mm3']>0

def test_sheet_bend_and_flat_analytic_volume(tmp_path):
 a=Advanced(ProjectService(tmp_path));r=a.sheet({});length=30+20+math.pi/2*(3+.4*2);assert r['developed_length_mm']==pytest.approx(length);assert r['flat_model']['geometry']['parts'][0]['volume_mm3']==pytest.approx(length*30*2);assert r['model']['geometry']['parts'][0]['volume_mm3']==pytest.approx((30+20)*30*2+math.pi/2*((3+2)**2-3**2)/2*30,rel=1e-6)

@pytest.mark.parametrize('component',[p['id'] for p in catalog()['components']])
def test_catalog_dimensions_provenance_and_native_exports(tmp_path,component):
 s=ProjectService(tmp_path);r=insert(s,component);assert r['provenance']['source_url'].startswith('https://');assert s.artifact(r['model']['model_id'],'model.step').is_file()

def test_drawing_uses_native_dimensions_and_pdf_header(native):
 s,a,key=native;r=a.drawing(key,'body');assert r['dimensions_mm']==pytest.approx([20,10,10]);assert (a.root/r['report_id']/'drawing.pdf').read_bytes().startswith(b'%PDF')

@pytest.mark.parametrize('process',['cnc','molding','additive'])
def test_manufacturing_screening_declares_its_limits(native,process):
 s,a,key=native;r=a.manufacture(key,{'part_id':'body','process':process});assert not r['certified'];assert any(f['check']=='sampled wall thickness' for f in r['findings'])

def test_silhouette_calibration_reports_inferred_depth(tmp_path):
 from PIL import Image,ImageDraw
 p=tmp_path/'outline.png';im=Image.new('RGB',(100,80),'white');ImageDraw.Draw(im).rectangle((20,20,80,60),fill='black');im.save(p);s=ProjectService(tmp_path/'state');r=Advanced(s).reconstruct({'mode':'silhouette','path':str(p),'width_mm':30,'depth_mm':5});assert r['model']['spec']['parts'][0]['params']['length']==pytest.approx(30,rel=.02);assert r['reconstruction']['inferred']

@pytest.mark.parametrize('kind',['thermal','structural','stokes'])
def test_pde_benchmarks_against_independent_solutions(native,kind):
 s,a,key=native;r=a.simulate(key,{'kind':kind,'part_id':'body','mesh_size_mm':4,'convergence':True,'convergence_tolerance':.15});assert r['relative_residual']<1e-7 and r['relative_balance_error']<1e-6;assert r['convergence']['passed'],r['convergence'];assert r['verified']
 assert r['audit']['mode']=='headless' and all(c['passed'] for c in r['audit']['numerical_checks'])
 if kind=='thermal':
  points=np.asarray(r['positions_mm']);expected=300+(points[:,0]+10)/20*50;assert np.max(abs(np.asarray(r['values'])-expected))<1e-6
 elif kind=='structural':assert r['maximum']==pytest.approx(1*.02/(70e9*.01*.01)*1000,rel=.08);assert r['maximum_von_mises_pa']>0
 else:
  series=sum(math.tanh(n*math.pi/2)/n**5 for n in range(1,101,2));expected=.01**4/(12*.02)*(1-192/math.pi**5*series);assert r['outlet_flow_m3_s']==pytest.approx(expected,rel=.15)

def test_unrequested_convergence_is_not_verified(native):
 _,a,key=native;r=a.simulate(key,{'kind':'thermal','part_id':'body','mesh_size_mm':5,'convergence':False});assert not r['verified'] and r['solver_checks_passed']

def test_noncreeping_flow_not_certified_even_if_equations_converge(native):
 _,a,key=native;r=a.simulate(key,{'kind':'stokes','part_id':'body','mesh_size_mm':5,'viscosity_pa_s':.001,'pressure_drop_pa':100,'convergence':False});assert r['estimated_reynolds']>.1 and not r['regime_valid'] and not r['verified']

def test_report_becomes_stale_after_geometry_edit(native):
 s,a,key=native;a.simulate(key,{'kind':'thermal','part_id':'body','mesh_size_mm':5,'convergence':False});assert not a.evidence(key)['reports'][0]['stale'];s.parameters(key,{'length':22});assert a.evidence(key)['reports'][0]['stale']

def test_parameter_alternatives_preserve_original_and_use_measured_volume(native):
 s,a,key=native;before=s.load(key);r=a.optimize(key,{'parameter':'length','values':[15,20,25]});assert r['best']['parameter_value']==15;assert s.load(key)==before;comparison=a.compare({'model_ids':[c['model_id'] for c in r['candidates']]});assert [c['volume_mm3'] for c in comparison['alternatives']]==pytest.approx([1500,2000,2500])

def test_background_job_survives_tool_return_and_reports_failure(native):
 s,a,key=native;r=submit(s,'simulate',{'kind':'thermal','part_id':'body','mesh_size_mm':5,'convergence':False},key);deadline=time.monotonic()+45
 while time.monotonic()<deadline:
  r=status(s,r['job_id'],key)
  if r['status'] not in ('queued','running'):break
  time.sleep(.2)
 assert r['status']=='succeeded',r;assert r['result']['solver_checks_passed']
 with pytest.raises(ValueError,match='another model'):status(s,r['job_id'],'0'*32)

def test_scan_import_portable_and_source_mesh_roundtrip(native,tmp_path):
 s,a,key=native;path=s.artifact(key,'model.stl');r=a.reconstruct({'mode':'scan','path':str(path)});scan=r['model'];assert scan['geometry']['engine']=='implicit_mesh' and scan['geometry']['asset_name']=='input.stl'
 exported=s.artifact(scan['model_id'],'program.py').read_text();assert 'input.stl' in exported and 'input_mesh' in exported
 data=s.portable(scan['model_id']);assert data['asset']['format']=='stl';file=tmp_path/'portable.json';file.write_text(json.dumps(data));other=ProjectService(tmp_path/'other');copy=other.import_project(file);assert copy['geometry']['parts'][0]['volume_mm3']==pytest.approx(2000)
 assert other.artifact(copy['model_id'],'input.stl').is_file()

def test_calibrated_three_view_hull_is_closed_and_declares_inference(tmp_path):
 from PIL import Image,ImageDraw
 p=tmp_path/'view.png';im=Image.new('L',(80,80),255);ImageDraw.Draw(im).rectangle((10,10,70,70),fill=0);im.save(p);s=ProjectService(tmp_path/'state');r=Advanced(s).reconstruct({'mode':'orthographic_hull','views':{k:str(p) for k in ('front','top','right')},'size_mm':[20,15,10],'voxel_resolution':24});assert r['model']['geometry']['parts'][0]['volume_mm3']==pytest.approx(3000,rel=.01);assert len(r['reconstruction']['views'])==3 and r['reconstruction']['inferred']

def test_mesh_wall_samples_on_box_match_native_thickness(native):
 _,a,key=native;r=a.mesh_quality(key);assert r['positive_volume'];assert r['thickness']['minimum_sampled_mm']==pytest.approx(10,abs=.01);assert r['thickness']['maximum_sampled_mm']==pytest.approx(20,abs=.01)

def test_cancel_background_solve_is_terminal_and_keeps_original(native):
 s,a,key=native;before=s.load(key);r=submit(s,'simulate',{'kind':'thermal','part_id':'body','mesh_size_mm':.5,'convergence':True},key);cancel(s,r['job_id'],key);deadline=time.monotonic()+20
 while time.monotonic()<deadline:
  r=status(s,r['job_id'],key)
  if r['status'] not in ('queued','running'):break
  time.sleep(.2)
 assert r['status']=='cancelled',r;assert s.load(key)==before

def test_invalid_job_reports_failure_without_model_mutation(native):
 s,a,key=native;before=s.load(key);r=submit(s,'simulate',{'kind':'turbulent','part_id':'body'},key);deadline=time.monotonic()+15
 while time.monotonic()<deadline:
  r=status(s,r['job_id'],key)
  if r['status'] not in ('queued','running'):break
  time.sleep(.2)
 assert r['status']=='failed' and r['error'];assert s.load(key)==before

def test_simulation_unknown_part_cannot_fall_back_to_other_solid(native):
 s,a,key=native
 with pytest.raises(ValueError,match='part not found'):a.simulate(key,{'kind':'thermal','part_id':'other'})

def test_feature_rebuild_reuses_unchanged_nodes_and_invalidates_dependents(tmp_path):
 from intact_backend.feature_graph import FeatureService
 from test_priority1 import CIRCLE,PAD
 s=ProjectService(tmp_path);f=FeatureService(s);draft=f.create_sketch(None,CIRCLE,parameters={'diameter':40,'thickness':8,'bore':6});key=draft['model_id'];f.edit(key,[PAD,{'id':'hole','kind':'hole','base':'pad','part_id':'disk','params':{'diameter':{'parameter':'bore'},'centers':[[0,0,0]]}}]);r=s.parameters(key,{'bore':8});features=r['engineering']['diagnostics']['features'];assert features[0]['reused_cached_geometry'] and not features[1]['reused_cached_geometry'];assert r['spec']['parts'][0]['measurements']['volume_mm3']==pytest.approx(math.pi*(20**2-4**2)*8)

def test_optimization_respects_saved_requirements_and_needs_physics_for_constraints(native):
 from intact_backend.feature_graph import FeatureService
 s,a,key=native;FeatureService(s).requirements(key,{'checks':[{'id':'length','kind':'bounds','part_id':'body','expected':{'length':20}}]});result=a.optimize(key,{'parameter':'length','values':[15,20,25]});assert result['best']['parameter_value']==20;assert [c['feasible'] for c in result['candidates']]==[False,True,False]
 with pytest.raises(ValueError,match='constraints require'):a.optimize(key,{'parameter':'length','values':[15,20],'max_displacement_mm':.01})

def test_coincident_hybrid_survives_real_stl_and_glb_roundtrips(tmp_path):
 import trimesh
 from intact_backend.validation import validate_model
 s=ProjectService(tmp_path);r=s.build('import build123d as bd\ndef build(params):\n    return {"body":bd.Box(8,8,8)}',{});r=Advanced(s).hybrid(r['model_id'],{'part_id':'body','operation':'union','size':[10,10,10],'cell_size':8,'thickness_mm':1.6,'samples_per_cell':24});assert validate_model(s,r['model_id'])['passed'];metadata=r['geometry']['parts'][0]['lattice'];assert 'alignment_perturbation_mm' in metadata
 for name in ('model.stl','model.glb','model.3mf'):
  mesh=trimesh.load(s.artifact(r['model_id'],name),force='mesh',process=True);mesh.merge_vertices(merge_tex=True,merge_norm=True);assert mesh.is_volume
