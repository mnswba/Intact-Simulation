"""Regression contracts discovered during the 50-model audit."""
import json
from pathlib import Path
import pytest
from intact_backend.projects import ProjectService
from intact_backend.program import ProgramService

SOURCE='''import build123d as bd
def build(params):
    return {'base':bd.Box(params['length'],20,5),'lid':bd.Pos(0,0,12)*bd.Box(30,20,2)}
'''
@pytest.fixture
def project(tmp_path):
    s=ProjectService(tmp_path);r=s.build(SOURCE,{'length':30},name='Audit contracts');return s,r

def test_zero_expected_revision_cannot_edit_the_latest_model(project):
    s,r=project
    with pytest.raises(ValueError,match='revision'):s.parameters(r['model_id'],{'length':40},expected_revision=0)
    assert s.load(r['model_id'])['spec']['revision']==1

def test_invalid_import_is_atomic_and_does_not_leave_an_extra_project(project,tmp_path):
    s,r=project;data=s.portable(r['model_id']);data['view']={'opacity':1000};path=tmp_path/'invalid.json';path.write_text(json.dumps(data));before=len(s.list())
    with pytest.raises(ValueError):s.import_project(path)
    assert len(s.list())==before

def test_import_preserves_disabled_components(project,tmp_path):
    s,r=project;data=s.portable(r['model_id']);data['spec']['parts'][1]['enabled']=False;path=tmp_path/'disabled.json';path.write_text(json.dumps(data));imported=s.import_project(path)
    assert imported['spec']['parts'][1]['enabled'] is False

@pytest.mark.parametrize('filename,broken',[('mesh.json','{"broken":true}'),('manifest.json','[]'),('manifest.json','{"sha256":[],"valid":true}')])
def test_corrupted_mesh_is_rebuilt_instead_of_served_as_a_cache_hit(project,filename,broken):
    s,r=project;path=s.artifact(r['model_id'],filename);path.write_text(broken)
    report=s.programs.build(SOURCE,{'length':30})
    assert not report['cached']
    assert json.loads(s.artifact(r['model_id'],'mesh.json').read_text())['parts']

def test_restore_recreates_missing_geometry(project):
    s,r=project;key=r['model_id'];old=s.artifact(key,'mesh.json');s.parameters(key,{'length':35});old.unlink();restored=s.restore(key,1)
    assert s.artifact(key,'mesh.json').is_file()

def test_downloaded_python_preserves_named_parts_and_all_exports(project):
    import importlib.util
    spec=importlib.util.spec_from_file_location('export_check',Path(__file__).resolve().parents[2]/'scripts/audit/export_check.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    s,r=project;result=module.verify_python_export(s.artifact(r['model_id'],'program.py'))
    assert result['valid'] and result['solid_count']==2 and set(result['labels'])=={'base','lid'}

def test_measurement_context_is_attached_to_the_edit_request(project):
    from intact_backend.edit_requests import EditRequests
    s,r=project;artifact=r['spec']['program']['artifact_id'];m={'id':'quote" dimension','a':[-15,-10,-2.5],'b':[15,-10,-2.5],'artifact_id':artifact,'snap_a':'Exact vertex','snap_b':'Exact vertex'}
    queue=EditRequests(s);request=queue.create(r['model_id'],{'instructions':'Make this measured length 40 mm','revision':1,'artifact_id':artifact,'measurements':[m]})
    assert queue.read(r['model_id'],request['request_id'])['context']['measurements']['items'][0]['a']==m['a']
    m['artifact_id']='a'*64
    with pytest.raises(ValueError,match='stale'):queue.create(r['model_id'],{'instructions':'Edit it','revision':1,'artifact_id':artifact,'measurements':[m]})

def test_revision_boolean_is_not_a_valid_geometry_reference(project):
    from intact_backend.edit_requests import EditRequests
    s,r=project
    with pytest.raises(ValueError,match='integer'):EditRequests(s).resolve(r['model_id'],[],True,r['spec']['program']['artifact_id'])

def test_saved_colors_are_present_in_step_exports_without_changing_geometry(project):
    import build123d as bd
    s,r=project;key=r['model_id'];artifact=r['spec']['program']['artifact_id'];s.appearance(key,'base',color='#ff8800')
    shape=bd.import_step(s.artifact(key,'model.step'));base=next(p for p in shape.children if p.label=='base')
    assert base.color is not None
    assert tuple(round(c*255) for c in tuple(base.color)[:3])==(255,136,0)
    assert s.load(key)['spec']['program']['artifact_id']==artifact
    assert s.load(key)['spec']['parts'][0]['measurements']==r['spec']['parts'][0]['measurements']
    import zipfile,struct,importlib.util
    with zipfile.ZipFile(s.artifact(key,'model.3mf')) as archive:
        xml=archive.read(next(n for n in archive.namelist() if n.endswith('.model'))).decode()
        assert '#FF8800FF' in xml.upper()
    glb=s.artifact(key,'model.glb').read_bytes();length,_=struct.unpack('<II',glb[12:20]);document=json.loads(glb[20:20+length]);expected=(1,((136/255+.055)/1.055)**2.4,0)
    assert any(all(abs(a-b)<1e-6 for a,b in zip(m.get('pbrMetallicRoughness',{}).get('baseColorFactor',[]),expected)) for m in document['materials'])
    spec=importlib.util.spec_from_file_location('export_check',Path(__file__).resolve().parents[2]/'scripts/audit/export_check.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert module.verify_python_export(s.artifact(key,'program.py'))['colors']['base']==(255,136,0)


def test_corrupted_import_asset_is_detected_before_cached_geometry_is_reused(project):
    s,r=project;imported=s.import_cad(s.artifact(r['model_id'],'model.step'));p=imported['spec']['program'];asset=s.programs.root/'assets'/p['asset_id']/'input.step';asset.write_bytes(asset.read_bytes()+b'\n')
    with pytest.raises(ValueError,match='damaged'):s.programs.build(p['source'],p['parameters'],asset_id=p['asset_id'])

async def test_named_snapshots_freeze_presentation_and_preserve_saved_view(project,tmp_path):
    from intact_backend.snapshot import snapshot
    from intact_backend.viewer_server import viewer_url
    from test_mcp import stop_viewer
    s,r=project;key=r['model_id'];s.save_view(key,{'preview':True,'orbit_speed':5,'camera':[130,90,110,0,0,0]});before=s.load(key)['view']
    try:
        url=viewer_url(s.root,key)
        for view in ('front','top'):
            png=await snapshot(url,tmp_path/(view+'.png'),view)
            assert png.startswith(b'\x89PNG\r\n\x1a\n') and len(png)>1000
        assert s.load(key)['view']==before
    finally:stop_viewer(s.root)

def test_native_measurements_do_not_present_template_defaults_as_measured_features(project):
    from intact_backend.mcp_server import IntactMCP
    s,r=project;result=IntactMCP(s.root).call('measure_model',{'model_id':r['model_id']})
    assert result['program_parameters']=={'length':30}
    assert set(result['parts'][0]['bounds'])=={'length','width','height'}

def test_windows_desktop_paths_import_step_and_projects_through_wsl(project):
    import tempfile,shutil
    from pathlib import PureWindowsPath
    s,r=project;workspace=Path(__file__).resolve().parents[2]/'outputs';workspace.mkdir(exist_ok=True)
    if not str(workspace).startswith('/mnt/c/'):pytest.skip('Windows drive bridge integration needs the mounted C drive.')
    with tempfile.TemporaryDirectory(prefix='windows-path-',dir=workspace) as directory:
        folder=Path(directory);step=folder/'part with spaces.step';shutil.copyfile(s.artifact(r['model_id'],'model.step'),step)
        windows_step=str(PureWindowsPath('C:/')/PureWindowsPath(step.relative_to('/mnt/c').as_posix()))
        imported=s.import_cad(windows_step);assert len(imported['spec']['parts'])==2
        file=folder/'project with spaces.json';file.write_text(json.dumps(s.portable(r['model_id'])))
        windows_project=str(PureWindowsPath('C:/')/PureWindowsPath(file.relative_to('/mnt/c').as_posix()))
        assert len(s.import_project(windows_project)['spec']['parts'])==2
