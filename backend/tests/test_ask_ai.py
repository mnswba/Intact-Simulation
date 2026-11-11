"""Model scoping, read-only questions and actual added geometry capabilities."""
import json
import pytest
from mcp import Client
from mcp.server.mcpserver.exceptions import ToolError
from intact_backend.projects import ProjectService
from intact_backend.edit_requests import EditRequests
from intact_backend.ask_ai import scoped_engine,start
from intact_backend.mcp_server import create_server
from intact_backend.feature_graph import FeatureService
from intact_backend.design_checks import verify_design

SOURCE='import build123d as bd\ndef build(params):\n    return {"body":bd.Pos(params["x"],0,0)*bd.Box(20,10,5)}'
@pytest.fixture
def scoped(tmp_path):
 s=ProjectService(tmp_path);r=s.build(SOURCE,{'x':0});key=r['model_id']
 def request(intent='edit'):
  current=s.load(key)
  return EditRequests(s).create(key,{'instructions':'Move body to X=10 mm','intent':intent,'references':['body'],'revision':current['spec']['revision'],'artifact_id':current['spec']['program']['artifact_id']})
 return s,key,request

def test_question_mode_cannot_mutate_through_tools_or_legacy_apply(scoped):
 s,key,request=scoped;r=request('question');engine=scoped_engine(s.root,key,r['request_id']);before=s.load(key)
 with pytest.raises(ToolError,match='read-only'):engine.call('update_parameters',{'model_id':key,'parameters':{'x':10}})
 with pytest.raises(ValueError,match='read-only'):EditRequests(s).apply(key,r['request_id'],SOURCE,{'x':10})
 assert s.load(key)==before

async def test_direct_image_and_request_tools_enforce_model_scope(scoped):
 s,key,request=scoped;r=request();engine=scoped_engine(s.root,key,r['request_id'])
 async with Client(create_server(engine)) as c:
  for name,args in [('snapshot_model',{'model_id':'0'*32}),('read_edit_request',{'model_id':'0'*32,'request_id':r['request_id']}),('read_edit_request',{'model_id':key,'request_id':'0'*32}),('list_models',{}),('import_cad',{'path':'/tmp/other.step'})]:
   result=await c.call_tool(name,args);assert result.is_error,(name,result)
  assert not (await c.call_tool('get_model',{'model_id':key})).is_error

def test_task_forces_revision_guards_and_can_perform_sequential_edits(scoped):
 s,key,request=scoped;r=request();engine=scoped_engine(s.root,key,r['request_id'])
 engine.call('update_parameters',{'model_id':key,'parameters':{'x':10}})
 engine.call('update_parameters',{'model_id':key,'parameters':{'x':12}})
 assert s.load(key)['spec']['program']['parameters']['x']==12
 s.parameters(key,{'x':14})
 with pytest.raises(ToolError,match='outside'):engine.call('update_parameters',{'model_id':key,'parameters':{'x':16}})
 assert s.load(key)['spec']['program']['parameters']['x']==14

def test_stale_selection_does_not_start_a_task(scoped):
 s,key,request=scoped;r=request();s.parameters(key,{'x':3})
 with pytest.raises(ValueError,match='Geometry changed'):start(s,key,r['request_id'])

def test_concentric_circles_are_solved_by_freecad(tmp_path):
 f=FeatureService(ProjectService(tmp_path));r=f.create_sketch(None,{'id':'rings','geometry':[{'id':'outer','kind':'circle','center':[0,0],'radius':10},{'id':'inner','kind':'circle','center':[2,3],'radius':4}],'constraints':[{'id':'fixed_outer','kind':'lock','entities':['outer']},{'id':'shared_center','kind':'concentric','entities':['outer','inner']},{'id':'inner_radius','kind':'radius','entities':['inner'],'value':4}]})
 result=f.solve(r['model_id'])['sketches']['rings'];assert result['degrees_of_freedom']==0 and result['solver_code']==0
 assert result['geometry'][1]['center']==pytest.approx([0,0])

def test_component_placement_checks_actual_step(scoped):
 s,key,_=scoped;f=FeatureService(s);f.requirements(key,{'checks':[{'id':'body_placement','kind':'placement','part_id':'body','expected':{'center_mm':[0,0,0],'min_mm':[-10,-5,-2.5]}}]})
 assert verify_design(s,key)['passed']
 s.parameters(key,{'x':10})
 assert not verify_design(s,key)['passed']

def test_unknown_intent_is_rejected_without_queueing(scoped):
 s,key,_=scoped;r=s.load(key)
 with pytest.raises(ValueError,match='Choose edit or question'):EditRequests(s).create(key,{'instructions':'hello','intent':'unknown','revision':1,'artifact_id':r['spec']['program']['artifact_id']})
 assert not EditRequests(s).list(key)

def test_cancelled_task_stops_client_and_preserves_geometry(scoped,monkeypatch):
 import threading,time,sys
 import intact_backend.ask_ai as ai
 s,key,request=scoped;r=request();rid=r['request_id'];ai.update(s,key,rid,status='processing',direct_run=True)
 monkeypatch.setattr(ai,'command',lambda *args:[sys.executable,'-c','import sys,time;sys.stdin.read();time.sleep(30)'])
 t=threading.Thread(target=ai.run,args=(s.root,key,rid));t.start();time.sleep(.4);ai.cancel(s,key,rid);t.join(6)
 assert not t.is_alive();assert EditRequests(s).read(key,rid)['status']=='cancelled';assert s.load(key)['spec']['revision']==1

def test_failed_client_is_never_reported_as_success(scoped,monkeypatch):
 import sys
 import intact_backend.ask_ai as ai
 s,key,request=scoped;r=request();monkeypatch.setattr(ai,'command',lambda *args:[sys.executable,'-c','import sys;sys.stdin.read();sys.exit(1)'])
 ai.run(s.root,key,r['request_id']);result=EditRequests(s).read(key,r['request_id']);assert result['status']=='failed' and result['error'];assert s.load(key)['spec']['revision']==1

def test_empty_ai_answer_is_not_reported_as_success(scoped,monkeypatch):
 import sys
 import intact_backend.ask_ai as ai
 s,key,request=scoped;r=request();monkeypatch.setattr(ai,'command',lambda *args:[sys.executable,'-c','import sys;sys.stdin.read()'])
 ai.run(s.root,key,r['request_id']);result=EditRequests(s).read(key,r['request_id']);assert result['status']=='failed' and 'no answer' in result['error']

def test_busy_ai_task_does_not_start_a_second_client(scoped):
 import fcntl
 s,key,request=scoped;r=request()
 with (s.root/'ask-ai.lock').open('a') as gate:
  fcntl.flock(gate,fcntl.LOCK_EX|fcntl.LOCK_NB)
  with pytest.raises(ValueError,match='already running'):start(s,key,r['request_id'])
 assert EditRequests(s).read(key,r['request_id'])['status']=='pending'
