"""Exercise real sandbox previews, transactional configurations and AI view scope."""
import json, math
import pytest
from mcp import Client
from intact_backend.mcp_server import IntactMCP, create_server
from intact_backend.interactive import parameter_values, view_command, parameter_command
from intact_backend.view_settings import ViewSettings
from intact_backend.ask_ai import scoped_engine
from intact_backend.edit_requests import EditRequests

SOURCE='import build123d as bd\ndef build(params):\n    return {"box":bd.Box(params["length"],params["width"],params["height"])}'

@pytest.mark.parametrize('change',[{'length':'width*2','width':'height+3'},{'length':'-(2+3)/2'}])
def test_bounded_arithmetic(change):
    values=parameter_values({'length':12.,'width':6.,'height':3.},change)
    assert all(math.isfinite(v) for v in values.values())
    if 'width' in change:assert values['length']==12 and values['width']==6
    else:assert values['length']==-2.5

@pytest.mark.parametrize('value',['__import__("os").system("id")','width.real','width[0]','2**999','1/0','length+1','nan','[2]','2'*301])
def test_reject_unsafe_arithmetic(value):
    with pytest.raises(ValueError):parameter_values({'length':12.,'width':6.},{'length':value})

@pytest.mark.parametrize('value',[float('nan'),float('inf')])
def test_camera_finite(value):
    with pytest.raises(ValueError):ViewSettings(camera=[value,1,1,0,0,0])

def test_real_scratch_configurations_and_views(tmp_path):
    engine=IntactMCP(tmp_path);p=engine.projects
    built=p.build(SOURCE,{'length':12.,'width':6.,'height':3.});key=built['model_id'];original=p.path(key).read_bytes()
    preview=parameter_command(p,key,'preview',{'length':'width*3'},expected_revision=1)
    assert not preview['committed'] and preview['parts'][0]['dimensions_mm']['length']==pytest.approx(18)
    assert p.path(key).read_bytes()==original and len(p.revisions(key))==1
    with pytest.raises(Exception):parameter_command(p,key,'preview',{'width':0.})
    assert p.path(key).read_bytes()==original
    parameter_command(p,key,'save',{'length':'width*3'},'Long',1)
    assert p.load(key)['spec']['revision']==1
    saved=p.path(key).read_bytes()
    with pytest.raises(ValueError):parameter_command(p,key,'apply',name='Long',expected_revision=2)
    assert p.path(key).read_bytes()==saved
    updated=parameter_command(p,key,'apply',name='Long',expected_revision=1)
    assert updated['spec']['revision']==2 and updated['spec']['parts'][0]['params']['length']==pytest.approx(18)
    v=view_command(p,key,'update',{'cut':'z','grid':False},expected_view_revision=0)
    assert v['view_revision']==1 and v['cad_revision']==2
    view_command(p,key,'save',name='Section',expected_view_revision=1)
    view_command(p,key,'update',{'grid':True},expected_view_revision=1)
    with pytest.raises(ValueError):view_command(p,key,'update',{'explode':30},expected_view_revision=1)
    v=view_command(p,key,'restore',name='Section',expected_view_revision=2)
    assert not v['settings']['grid'] and v['settings']['cut']=='z'
    with pytest.raises(ValueError):view_command(p,key,'update',{'hidden':['nonexistent']})
    assert p.load(key)['spec']['revision']==2 and len(p.revisions(key))==2
    p.parameters(key,{'length':20.})
    with pytest.raises(ValueError,match='earlier geometry'):view_command(p,key,'restore',name='Section')
    assert 'Long' in p.load(key)['parameter_configurations']
    view_command(p,key,'update',{'hidden':['box']})
    p.build(SOURCE.replace('\"box\"','\"replacement\"'),{'length':20.,'width':6.,'height':3.},model_id=key,expected_revision=3)
    assert p.load(key)['view']['hidden']==[]
    view_command(p,key,'update',{'grid':False})

async def test_actual_mcp_schemas_and_catalog(tmp_path):
    engine=IntactMCP(tmp_path)
    async with Client(create_server(engine)) as client:
        tools={t.name for t in (await client.list_tools()).tools}
        r=await client.call_tool('list_commands');listed={t['name'] for t in r.structured_content['commands']}
        assert listed==tools
        r=await client.call_tool('describe_command',{'command':'preview_parameters'})
        assert 'parameters' in r.structured_content['input_schema']['properties']
        invalid=await client.call_tool('control_view',{'model_id':'bad','settings':{'camera':[1,2]}})
        assert invalid.is_error

async def test_scoped_discovery_and_new_write_guards(tmp_path):
    from mcp.server.mcpserver.exceptions import ToolError
    p=IntactMCP(tmp_path).projects;r=p.build(SOURCE,{'length':12.,'width':6.,'height':3.});key=r['model_id']
    edit=EditRequests(p).create(key,{'instructions':'What is its width?','intent':'question','references':['box'],'revision':1,'artifact_id':r['spec']['program']['artifact_id']})
    engine=scoped_engine(tmp_path,key,edit['request_id'])
    async with Client(create_server(engine)) as client:
        catalog=(await client.call_tool('list_commands',{'model_id':key})).structured_content
        names={c['name'] for c in catalog['commands']}
        assert 'preview_parameters' in names and 'control_view' in names
        assert 'apply_configuration' not in names and 'build_model' not in names
        assert (await client.call_tool('control_view',{'model_id':'0'*32})).is_error
        result=await client.call_tool('control_view',{'model_id':key,'action':'update','settings':{'cut':'x','grid':False},'expected_view_revision':0})
        assert not result.is_error,result
        assert result.structured_content['cad_revision']==1
        assert (await client.call_tool('apply_configuration',{'model_id':key,'name':'x','expected_revision':1})).is_error
        response=await client.call_tool('respond_to_edit_request',{'model_id':key,'request_id':edit['request_id'],'message':'The width is 6 mm.'})
        assert not response.is_error,response
        assert (await client.call_tool('respond_to_edit_request',{'model_id':key,'request_id':'0'*32,'message':'Wrong request'})).is_error
    assert p.load(key)['spec']['revision']==1
