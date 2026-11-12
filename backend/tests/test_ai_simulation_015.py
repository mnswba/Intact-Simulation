import json
from pathlib import Path
import pytest
from intact_backend.projects import ProjectService
from intact_backend.advanced import Advanced
from intact_backend.simulation_workspace import configure
from intact_backend.preview_schema import PreviewStudy
from intact_backend.picogk import build,readiness

def test_automatic_mesh_sizing_recovers_without_changing_cad(tmp_path):
 s=ProjectService(tmp_path);r=s.build('import build123d as b\ndef build(params):\n return {"rod":b.Box(80,40,20)}',{});before=s.load(r['model_id']);report=Advanced(s).simulate(r['model_id'],{'kind':'thermal','part_id':'rod','mesh_size_mm':.1,'auto_mesh':True,'convergence':True})
 assert report['mesh_adaptation']['coarsened'];assert report['mesh_adaptation']['effective_mm']>.1;assert report['vertices']<=6000 and report['tetrahedra']<=18000;assert report['minimum']==pytest.approx(300);assert report['maximum']==pytest.approx(350);assert s.load(r['model_id'])==before

def test_preview_requires_real_part_bindings_and_preserves_revisions(tmp_path):
 s=ProjectService(tmp_path);r=s.build('import build123d as b\ndef build(params):\n return {"body":b.Box(20,10,3),"wheel":b.Pos(5,0,0)*b.Box(2,2,2)}',{});before=s.load(r['model_id']);plan={'kind':'vehicle','wheels':[{'id':'wheel','part_ids':['wheel'],'pivot_m':[.005,0,0]}],'source_revision':r['spec']['revision'],'source_artifact':r['spec']['program']['artifact_id']};result=configure(s,r['model_id'],plan,'preview');assert result['studies']['preview']['moving_part_ids']==['body','wheel'];assert s.load(r['model_id'])==before
 plan['wheels'][0]['part_ids']=['unknown']
 with pytest.raises(ValueError,match='part IDs'):configure(s,r['model_id'],plan,'preview')
 from intact_backend.engineering_jobs import submit
 with pytest.raises(ValueError):submit(s,'motion',{},r['model_id'])

@pytest.mark.parametrize('family',['gyroid','schwarz_p'])
def test_real_picogk_native_mesh_export(tmp_path,family):
 if not readiness()['available']:pytest.skip('Optional PicoGK bridge not installed.')
 s=ProjectService(tmp_path);result=build(s,{'family':family,'size':[8,8,8],'cell_size':4,'thickness_mm':1.2,'voxel_mm':.3});r=result['model'];assert result['picogk']['engine']=='PicoGK' and result['picogk']['watertight'];assert result['picogk']['volume_mm3']>0;assert s.artifact(r['model_id'],'model.glb').is_file()
 with pytest.raises(ValueError,match='STEP'):s.artifact(r['model_id'],'model.step')
