"""Regression for the 1000 N request and isolation of unrelated study results."""
import pytest
from intact_backend.p23_schema import Simulation
from intact_backend.simulation_workspace import compact
from intact_backend.projects import ProjectService
from intact_backend.advanced import Advanced
DESCRIPTION='Apply 1000N force from the top and analyze its deflection'
def test_deflection_cannot_be_configured_as_thermal_or_flow():
 for kind in ['thermal','stokes']:
  with pytest.raises(ValueError,match='structural study'):Simulation.model_validate({'kind':kind,'part_id':'body','user_request':DESCRIPTION})
 assert Simulation.model_validate({'kind':'structural','part_id':'body','user_request':DESCRIPTION}).kind=='structural'
def test_workspace_keeps_request_identity_without_sending_heavy_settings():
 for field in ['settings','study_definition']:
  summary=compact({'kind':'structural',field:{'user_request':DESCRIPTION,'part_id':'body'},'values':[1,2]})
  assert summary['user_request']==DESCRIPTION and summary['part_id']=='body'
  assert field not in summary and 'values' not in summary

def test_real_1000n_top_load_deflection_and_reaction(tmp_path):
 s=ProjectService(tmp_path);r=s.build('import build123d as b\ndef build(params):\n return {"body":b.Box(10,10,20)}',{});key=r['model_id'];before=s.load(key)
 # Exact compression patch: 100 mm² area, 20 mm height, E=10 GPa, nu=0. u=FL/EA=0.02 mm.
 settings={'user_request':DESCRIPTION+'; fixed bottom, E=10 GPa, nu=0, uniform top load on body.', 'kind':'structural','part_id':'body','axis':2,'mesh_size_mm':.1,'auto_mesh':True,'young_modulus_pa':1e10,'poisson_ratio':0,'convergence':True,'source_revision':r['spec']['revision'],'source_artifact':r['spec']['program']['artifact_id'],'boundary_conditions':[{'id':'support','kind':'fixed','axis':2,'side':'low'},{'id':'top_force','kind':'force','axis':2,'side':'high','vector':[0,0,-1000]}]}
 report=Advanced(s).simulate(key,settings)
 assert report['kind']=='structural' and report['maximum']==pytest.approx(.02,rel=1e-6)
 assert report['reaction_force_n']==pytest.approx([0,0,1000],abs=1e-5)
 assert report['maximum_von_mises_pa']==pytest.approx(10e6,rel=1e-6)
 assert report['relative_residual']<1e-8 and report['relative_balance_error']<1e-8
 assert report['regime_valid'] and report['verified']
 assert report['convergence']['passed'] and report['stress_convergence']['passed']
 assert report['vertices']<=6000 and report['tetrahedra']<=18000
 assert report['mesh_adaptation']['effective_mm']>.1
 assert s.load(key)==before
 assert (s.root/'engineering'/report['report_id']/'results.csv').is_file()

def test_answer_without_solver_evidence_is_not_analysis_success(tmp_path):
 from types import SimpleNamespace
 from intact_backend.ask_ai import simulation_completion
 s=SimpleNamespace(root=tmp_path)
 assert simulation_completion(s,'0'*32,{})[0]=='awaiting_reply'

def test_failed_or_nonconverged_analysis_never_claims_success(tmp_path,monkeypatch):
 import intact_backend.engineering_jobs as jobs
 from types import SimpleNamespace
 from intact_backend.ask_ai import simulation_completion
 s=SimpleNamespace(root=tmp_path)
 monkeypatch.setattr(jobs,'status',lambda *args:{'status':'failed','error':'No valid supports'})
 status,progress=simulation_completion(s,'0'*32,{'simulation_job_ids':['1'*32]})
 assert status=='needs_review' and 'No valid supports' in progress
 monkeypatch.setattr(jobs,'status',lambda *args:{'status':'succeeded','result':{'convergence':{'passed':False}}})
 assert simulation_completion(s,'0'*32,{'simulation_job_ids':['1'*32]})[0]=='needs_review'


def test_earlier_success_does_not_hide_a_later_failed_run(tmp_path,monkeypatch):
 import intact_backend.engineering_jobs as jobs
 import json
 from types import SimpleNamespace
 from intact_backend.ask_ai import simulation_completion
 folder=tmp_path/'engineering'/'old';folder.mkdir(parents=True);(folder/'report.json').write_text(json.dumps({'convergence':{'passed':True}}))
 monkeypatch.setattr(jobs,'status',lambda *args:{'status':'failed','error':'Newest job failed'})
 r={'simulation_report_ids':['old'],'simulation_job_ids':['1'*32],'last_simulation_action':'job'}
 assert simulation_completion(SimpleNamespace(root=tmp_path),'0'*32,r)[0]=='needs_review'
 r['last_simulation_action']='error';r['simulation_error']='Latest synchronous run failed'
 assert 'Latest synchronous run failed' in simulation_completion(SimpleNamespace(root=tmp_path),'0'*32,r)[1]
