import json
import numpy as np
import pytest
from intact_backend.projects import ProjectService
from intact_backend.advanced import Advanced
from intact_backend.simulation_workspace import configure,workspace
from intact_backend.preview_schema import PreviewStudy
from intact_backend.edit_requests import EditRequests

@pytest.fixture
def rod(tmp_path):
 s=ProjectService(tmp_path);r=s.build('import build123d as b\ndef build(params):\n return {"rod": b.Box(20,10,10)}',{});return s,Advanced(s),r

def guard(r):return {'source_revision':r['spec']['revision'],'source_artifact':r['spec']['program']['artifact_id']}

def test_flux_temperature_exact_rod_and_csv(rod):
 s,a,r=rod;settings={'kind':'thermal','part_id':'rod','mesh_size_mm':4,'conductivity_w_mk':200,'convergence':True,'boundary_conditions':[{'id':'cold','kind':'temperature','side':'low','value':300},{'id':'hot','kind':'heat_flux','side':'high','value':10000}],**guard(r)}
 before=s.load(r['model_id']);configure(s,r['model_id'],settings,'simulate');report=a.simulate(r['model_id'],settings)
 assert report['minimum']==pytest.approx(300);assert report['maximum']==pytest.approx(301,abs=1e-7)
 assert report['heat_input_w']==pytest.approx(1);assert report['relative_balance_error']<1e-8
 assert (a.root/report['report_id']/'results.csv').is_file();assert s.load(r['model_id'])==before
 assert workspace(s,r['model_id'])['reports'][0]['kind']=='thermal'

def test_face_temperatures_and_stale_guard(rod):
 s,a,r=rod;topo=json.loads(s.artifact(r['model_id'],'topology.json').read_text());faces=topo['parts'][0]['faces'];low=min(faces,key=lambda f:f['center'][0]);high=max(faces,key=lambda f:f['center'][0]);settings={'kind':'thermal','part_id':'rod','mesh_size_mm':4,'convergence':False,**guard(r),'boundary_conditions':[{'id':'cold','kind':'temperature','selector':'faces','references':[low['ref']],'value':300},{'id':'hot','kind':'temperature','selector':'faces','references':[high['ref']],'value':350}]}
 report=a.simulate(r['model_id'],settings);assert report['maximum']==pytest.approx(350);assert len(report['boundary_assignments'])==2
 settings['source_revision']+=1
 with pytest.raises(ValueError,match='stale'):a.simulate(r['model_id'],settings)

def test_structural_uniform_stress_patch(rod):
 s,a,r=rod;settings={'kind':'structural','part_id':'rod','mesh_size_mm':4,'young_modulus_pa':1e9,'poisson_ratio':0,'force_n':[100,0,0],'convergence':True,**guard(r)};report=a.simulate(r['model_id'],settings)
 assert report['maximum']==pytest.approx(.02,rel=1e-6);assert report['maximum_von_mises_pa']==pytest.approx(1e6,rel=1e-6)
 assert report['reaction_force_n']==pytest.approx([-100,0,0],abs=1e-6);assert 'von_mises_Pa' in report['fields'];assert report['stress_convergence']['passed']

def test_convection_flux_and_no_support_rejected(rod):
 s,a,r=rod;report=a.simulate(r['model_id'],{'kind':'thermal','part_id':'rod','convergence':False,'conductivity_w_mk':200,'boundary_conditions':[{'id':'cool','kind':'convection','side':'low','h_w_m2k':100,'ambient_k':300},{'id':'heat','kind':'heat_flux','side':'high','value':10000}]})
 assert report['minimum']==pytest.approx(400,abs=1e-6);assert report['maximum']==pytest.approx(401,abs=1e-6)
 with pytest.raises(ValueError,match='supports'):a.simulate(r['model_id'],{'kind':'structural','part_id':'rod','boundary_conditions':[{'id':'load','kind':'force','side':'high','vector':[1,0,0]}]})

def test_simulation_ai_preserves_design(rod):
 s,a,r=rod;q=EditRequests(s);request=q.create(r['model_id'],{'intent':'simulation','instructions':'Run thermal study','revision':r['spec']['revision'],'artifact_id':guard(r)['source_artifact']})
 with pytest.raises(ValueError,match='preserves'):q.apply(r['model_id'],request['request_id'],'',{})
 from intact_backend.ask_ai import scoped_engine
 engine=scoped_engine(s.root,r['model_id'],request['request_id'])
 with pytest.raises(Exception,match='preserves'):engine.call('update_parameters',{'model_id':r['model_id'],'parameters':{}})
 with pytest.raises(Exception,match='limited'):engine.call('submit_engineering_job',{'model_id':r['model_id'],'operation':'assembly','settings':{}})
 assert engine.call('get_simulation_workspace',{'model_id':r['model_id']})['model_id']==r['model_id']

@pytest.mark.parametrize('mode',['pressure','displacement'])
def test_pressure_and_prescribed_displacement_reactions(rod,mode):
 s,a,r=rod;bc=[{'id':'support','kind':'fixed','side':'low'}]
 bc.append({'id':'pressure','kind':'pressure','side':'high','value':1e6} if mode=='pressure' else {'id':'travel','kind':'displacement','side':'high','components':[0],'vector':[.01,0,0]})
 report=a.simulate(r['model_id'],{'kind':'structural','part_id':'rod','young_modulus_pa':1e9,'poisson_ratio':0,'convergence':False,'boundary_conditions':bc})
 assert report['maximum']==pytest.approx(.02 if mode=='pressure' else .01,rel=1e-6)
 assert report['maximum_von_mises_pa']==pytest.approx(1e6 if mode=='pressure' else .5e6,rel=1e-6)
 assert report['relative_balance_error']<1e-7
