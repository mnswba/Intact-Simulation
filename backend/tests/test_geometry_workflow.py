import asyncio,base64,json,math
from pathlib import Path
import pytest
from mcp import Client
from intact_backend.projects import ProjectService
from intact_backend.edit_requests import EditRequests
from intact_backend.mcp_server import IntactMCP,create_server
from intact_backend.view_settings import ViewSettings

SOURCE='''import build123d as bd
def build(params):
    body=bd.Box(40,20,8)-bd.Cylinder(params['bore']/2,10)
    body.color=bd.Color('#f08040')
    return {'body':body,'lid':bd.Pos(0,0,12)*bd.Box(40,20,2)}
'''
PNG='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9Zl1sAAAAASUVORK5CYII='
@pytest.fixture(scope='module')
def project(tmp_path_factory):
    s=ProjectService(tmp_path_factory.mktemp('workflow'));r=s.build(SOURCE,{'bore':4},name='Workflow test');return s,r

def test_native_face_mapping_and_exact_geometry(project):
    s,r=project;key=r['model_id'];top=json.loads(s.artifact(key,'topology.json').read_text());mesh=json.loads(s.artifact(key,'mesh.json').read_text())
    body=top['parts'][0];cyl=next(f for f in body['faces'] if f['geometry']=='cylinder')
    assert cyl['radius_mm']==pytest.approx(2)
    assert cyl['area_mm2']==pytest.approx(2*math.pi*2*8)
    assert len(body['vertices'])>0
    m=mesh['parts'][0];assert sum(f['count'] for f in m['face_groups'])*3==len(m['indices'])
    assert r['spec']['parts'][0]['color']=='#f08040'
    refs=EditRequests(s).resolve(key,[cyl['ref']],r['spec']['revision'],r['spec']['program']['artifact_id'])
    assert refs['references'][0]['radius_mm']==2
    with pytest.raises(ValueError,match='Stale'):EditRequests(s).resolve(key,[cyl['ref']],99,r['spec']['program']['artifact_id'])

def test_view_settings_validation_is_independent_of_revision(project):
    s,r=project;key=r['model_id'];before=s.load(key)['spec']['revision']
    s.save_view(key,{'projection':'orthographic','mode':'render','theme':'light','palette':['#113355'],'floor':True,'opacity':75})
    assert s.load(key)['spec']['revision']==before
    for bad in ({'opacity':101},{'edge_color':'red'},{'camera':[0,0,float('nan'),0,0,0]},{'unknown':True},{'palette':[]}):
        with pytest.raises(ValueError):s.save_view(key,bad)

async def test_request_images_failure_repair_and_stale_rejection(project):
    s,initial=project;r=s.load(initial['model_id']);key=r['model_id'];queue=EditRequests(s)
    data={'instructions':'Increase bore to 6 mm; preserve lid.','references':['body.f1'],'revision':r['spec']['revision'],'artifact_id':r['spec']['program']['artifact_id'],'screenshot':PNG,'images':[{'name':'reference.png','data_url':PNG}],'annotations':[{'id':'arrow','tool':'arrow','points':[[.1,.2],[.3,.4]],'width':3,'color':'#ff8855'}]}
    req=queue.create(key,data)
    async with Client(create_server(IntactMCP(s.root))) as c:
        read=await c.call_tool('read_edit_request',{'model_id':key,'request_id':req['request_id']})
        assert not read.is_error,read
        assert sum(item.type=='image' for item in read.content)==2
        before=s.load(key)['spec']['revision']
        bad=await c.call_tool('apply_edit_request',{'model_id':key,'request_id':req['request_id'],'source':'def build(params):\n    raise ValueError("repair this")','parameters':{}})
        assert bad.is_error and s.load(key)['spec']['revision']==before
        assert queue.read(key,req['request_id'])['status']=='failed'
        result=await c.call_tool('apply_edit_request',{'model_id':key,'request_id':req['request_id'],'source':SOURCE,'parameters':{'bore':6}})
        assert not result.is_error,result
        assert queue.read(key,req['request_id'])['status']=='succeeded'
        assert s.load(key)['spec']['parts'][1]['measurements']==r['spec']['parts'][1]['measurements']
        stale=await c.call_tool('apply_edit_request',{'model_id':key,'request_id':req['request_id'],'source':SOURCE,'parameters':{'bore':7}})
        assert stale.is_error
    from test_mcp import stop_viewer
    stop_viewer(s.root)

def test_step_import_edit_and_portable_roundtrip(project,tmp_path):
    s,r=project;source=s.artifact(r['model_id'],'model.step');imported=s.import_cad(source)
    assert len(imported['spec']['parts'])==2 and imported['spec']['program']['asset_id']
    program='import build123d as bd\ndef build(params):\n    parts=dict(imported_parts)\n    parts["body"]-=bd.Cylinder(params["bore"]/2,20)\n    return parts'
    edited=s.build(program,{'bore':8},model_id=imported['model_id'])
    assert edited['spec']['parts'][0]['measurements']['volume_mm3']<imported['spec']['parts'][0]['measurements']['volume_mm3']
    assert edited['spec']['parts'][1]['measurements']==imported['spec']['parts'][1]['measurements']
    portable=s.portable(edited['model_id']);file=tmp_path/'project.json';file.write_text(json.dumps(portable));other=ProjectService(tmp_path/'other');restored=other.import_project(file)
    assert restored['spec']['parts'][0]['measurements']==edited['spec']['parts'][0]['measurements']
    assert restored['spec']['program']['asset_id']==edited['spec']['program']['asset_id']

def test_old_project_export_migration_keeps_study_and_settings(project):
    s,original=project;r=s.load(original['model_id']);key=r['model_id']
    r['analysis']={'scope':'reduced 1D reference','marker':'retained metadata'}
    r=s.commit(r,r['spec']['revision']);s.save_view(key,{'cut':'x','slice':45})
    s.artifact(key,'topology.json').unlink()
    upgraded=s.ensure_ready(key)
    assert upgraded['analysis']==r['analysis']
    assert upgraded['view']['cut']=='x'
    assert s.artifact(key,'topology.json').is_file()
