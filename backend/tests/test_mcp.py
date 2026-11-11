import asyncio, json, os, signal, sys, zipfile
from pathlib import Path
from urllib.request import urlopen,Request
import pytest
from mcp import Client,StdioServerParameters
from intact_backend.mcp_server import IntactMCP,create_server

SOURCE='''import build123d as bd
def build(params):
    ring=bd.Cylinder(params["radius"],8)-bd.Cylinder(8,10)
    lid=bd.Pos(0,0,16)*bd.Cylinder(params["radius"],3)
    return {"ring":ring,"lid":lid}
'''

def stop_viewer(root):
    path=root/'viewer-session.json'
    if path.exists():
        try:os.kill(json.loads(path.read_text())['pid'],signal.SIGTERM)
        except ProcessLookupError:pass

async def test_reference_approval_and_scope(tmp_path):
    engine=IntactMCP(tmp_path)
    async with Client(create_server(engine)) as client:
        args={'kind':'beam','length':180,'width':30,'height':8,'material':'aluminum','study':{'force':25},'approved':False}
        response=await client.call_tool('analyze_reference',args);assert response.is_error
        invalid=await client.call_tool('analyze_reference',{**args,'kind':'CFD','approved':True});assert invalid.is_error
        response=await client.call_tool('status');assert response.structured_content['cad_ready']

@pytest.mark.parametrize('mode',['auto','legacy'])
async def test_real_stdio_build_edits_revisions_exports_and_persistent_viewer(tmp_path,mode):
    params=StdioServerParameters(command=sys.executable,args=['-m','intact_backend.mcp_server'],env={**os.environ,'INTACT_STATE_DIR':str(tmp_path)})
    url=None
    try:
        async with Client(params,mode=mode,read_timeout_seconds=100) as client:
            tools=(await client.list_tools()).tools
            assert {'build_model','update_parameters','open_viewer','export_model','restore_revision'}<={t.name for t in tools}
            for t in tools:assert 'ctx' not in t.input_schema.get('properties',{})
            events=[]
            async def progress(value,total,message):events.append(message)
            built=await client.call_tool('build_model',{'source':SOURCE,'parameters':{'radius':25},'name':'Two-part ring'},progress_callback=progress)
            assert not built.is_error,built
            result=built.structured_content;key=result['model_id'];assert len(result['geometry']['parts'])==2
            url=result['viewer_url'];assert 'Geometry workspace' in urlopen(url).read().decode()
            assert events and 'Finished' in events[-1]
            project=json.loads(urlopen(url.replace('/view','/project.json')).read());assert project['format']=='intact-project' and len(project['mesh']['parts'])==2
            assert project['spec']['program']['source']==SOURCE
            for kind,link in result['downloads'].items():
                body=urlopen(link).read();assert len(body)>40
                if kind=='glb':assert body[:4]==b'glTF'
                if kind=='3mf':
                    import io
                    with zipfile.ZipFile(io.BytesIO(body)) as z:assert any(n.endswith('.model') for n in z.namelist())
                if kind=='python':assert b'if __name__' in body and b'"model.step"' in body
            await client.call_tool('set_appearance',{'model_id':key,'part_id':'ring','color':'#df873c'})
            updated=await client.call_tool('update_parameters',{'model_id':key,'parameters':{'radius':30}})
            assert not updated.is_error,updated
            saved=(await client.call_tool('get_model',{'model_id':key})).structured_content
            assert saved['name']=='Two-part ring' and saved['spec']['parts'][0]['color']=='#df873c'
            assert saved['spec']['parts'][0]['params']['length']==pytest.approx(60)
            old_revision=saved['spec']['revision']
            invalid=await client.call_tool('build_model',{'source':'def build(params):\n    raise ValueError("bad shape")','parameters':{},'model_id':key})
            assert invalid.is_error
            assert any('bad shape' in c.text for c in invalid.content if hasattr(c,'text'))
            saved=(await client.call_tool('get_model',{'model_id':key})).structured_content;assert saved['spec']['revision']==old_revision
            history=(await client.call_tool('revisions',{'model_id':key})).structured_content['revisions'];assert len(history)==3
            restored=await client.call_tool('restore_revision',{'model_id':key,'revision':1});assert not restored.is_error
            assert restored.structured_content['revision']>old_revision
            saved=(await client.call_tool('get_model',{'model_id':key})).structured_content;assert saved['spec']['program']['parameters']['radius']==25
            bad_id=await client.call_tool('get_model',{'model_id':'../config'});assert bad_id.is_error
            bad_shape=await client.call_tool('build_model',{'source':SOURCE,'parameters':{'radius':[]}});assert bad_shape.is_error
            bad_bool=await client.call_tool('build_model',{'source':SOURCE,'parameters':{'radius':True}});assert bad_bool.is_error
        # A normal ChatGPT connection closing must not make the viewer link disappear.
        assert urlopen(url).status==200
        async with Client(params,mode=mode,read_timeout_seconds=30) as client:
            reopened=await client.call_tool('open_viewer',{'model_id':key})
            assert reopened.structured_content['url']==url
        assert urlopen(url).status==200
    finally:stop_viewer(tmp_path)
