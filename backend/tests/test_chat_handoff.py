"""Real CAD request threading and native ChatGPT answer publication."""
import json, uuid
import pytest
from mcp import Client
from intact_backend.projects import ProjectService
from intact_backend.edit_requests import EditRequests
from intact_backend.mcp_server import IntactMCP, create_server
from intact_backend.ask_ai import scoped_engine

SOURCE='import build123d as bd\ndef build(params):\n    return {"camera":bd.Pos(params["x"],0,0)*bd.Cylinder(3,2)}'
@pytest.fixture
def conversation(tmp_path):
 s=ProjectService(tmp_path);r=s.build(SOURCE,{'x':5});q=EditRequests(s);key=r['model_id']
 def create(text='Put camera both sides',**extra):
  r=s.load(key)
  return q.create(key,dict(instructions=text,references=[],revision=r['spec']['revision'],artifact_id=r['spec']['program']['artifact_id'],**extra))
 return s,q,key,create

def test_existing_answers_accept_replies_with_history_and_selection(conversation):
 s,q,key,create=conversation
 r=s.load(key);first=q.create(key,dict(instructions='Put camera both sides',references=['camera'],revision=1,artifact_id=r['spec']['program']['artifact_id']))
 # Simulate the old single-turn answer shown in the user's screenshot.
 path=q.path(key,first['request_id']);record=json.loads(path.read_text());record.update(status='succeeded',answer='Replace the indicator, or keep it?');path.write_text(json.dumps(record))
 reply=create('Keep it and add the second camera elsewhere.',parent_request_id=first['request_id'])
 data=q.read(key,reply['request_id'])
 assert data['context']['references'][0]['ref']=='camera'
 assert [m['role'] for m in data['conversation']]==['user','assistant','user']
 assert data['conversation'][1]['content']=='Replace the indicator, or keep it?'
 assert data['conversation_id']==first['request_id'] and not data['stale']
 assert s.load(key)['spec']['revision']==1

def test_stale_replies_do_not_inherit_old_native_ids(conversation):
 s,q,key,create=conversation
 first=create();q.respond(key,first['request_id'],'Which side?',True)
 s.parameters(key,{'x':10})
 reply=create('The back side.',parent_request_id=first['request_id'])
 data=q.read(key,reply['request_id']);assert data['context']['revision']==2 and not data['context']['references']
 assert data['conversation'][0]['revision']==1

def test_client_id_is_validated_and_cannot_overwrite(conversation):
 s,q,key,create=conversation;rid=uuid.uuid4().hex
 result=create('x'*4000,request_id=rid);assert result['request_id']==rid
 assert len(q.read(key,rid)['instructions'])==4000
 with pytest.raises(ValueError,match='already exists'):create('overwrite',request_id=rid)
 with pytest.raises(ValueError,match='Invalid edit request'):create(request_id='../bad')
 assert q.read(key,rid)['instructions']=='x'*4000

def test_cannot_reply_to_unanswered_or_foreign_request(conversation):
 s,q,key,create=conversation;first=create()
 with pytest.raises(ValueError,match='Wait for'):create('yes',parent_request_id=first['request_id'])
 other=s.build(SOURCE,{'x':2})
 with pytest.raises(ValueError,match='not found'):q.create(other['model_id'],dict(instructions='yes',parent_request_id=first['request_id']))

async def test_native_mcp_answer_and_reply_edit(conversation):
 s,q,key,create=conversation;first=create()
 async with Client(create_server(IntactMCP(s.root))) as client:
  result=await client.call_tool('respond_to_edit_request',dict(model_id=key,request_id=first['request_id'],message='Place the other camera at X=-5 mm?',needs_reply=True))
  assert not result.is_error,result
  assert q.read(key,first['request_id'])['status']=='awaiting_reply'
  reply=create('Yes, move this camera to X=-5 mm.',parent_request_id=first['request_id'])
  result=await client.call_tool('apply_edit_request',dict(model_id=key,request_id=reply['request_id'],source=SOURCE,parameters={'x':-5.0}))
  assert not result.is_error,result
  result=await client.call_tool('respond_to_edit_request',dict(model_id=key,request_id=reply['request_id'],message='Camera is now at X=-5 mm.'))
  assert not result.is_error,result
 assert s.load(key)['spec']['program']['parameters']['x']==-5
 assert q.read(key,reply['request_id'])['geometry_changed']
 from test_mcp import stop_viewer
 stop_viewer(s.root)

def test_scoped_local_client_cannot_publish_native_answers(conversation):
 s,q,key,create=conversation;first=create();engine=scoped_engine(s.root,key,first['request_id'])
 with pytest.raises(Exception,match='not allowed|unavailable|not available|scope'):engine.authorize('respond_to_edit_request',dict(model_id=key,request_id=first['request_id']))
