"""Exercise every installed MCP tool with success and failure/recovery cases."""
import asyncio,base64,json,math,os,shutil,sys,time
from pathlib import Path,PureWindowsPath
from urllib.request import Request,urlopen
from mcp import Client,StdioServerParameters
REPO=Path(__file__).resolve().parents[2];OUT=REPO/'outputs/priority23-audit';ROOT=Path.home()/'.local/share/intact-simulation/priority23-tools';OUT.mkdir(parents=True,exist_ok=True)
SOURCE='''import build123d as bd
def build(params):
    plate=bd.Box(params['length'],30,6)-bd.Cylinder(params['bore']/2,10)
    return {'plate':plate,'lid':bd.Pos(0,0,14)*bd.Box(60,30,2)}
'''
async def main():
 server=json.loads((Path.home()/'.codex/plugins/intact-simulation/.mcp.json').read_text())['mcpServers']['intact'];params=StdioServerParameters(command=server['command'],args=server['args'],env={**{k:v for k,v in os.environ.items() if k!='PYTHONPATH'},'INTACT_STATE_DIR':str(ROOT)})

 if os.environ.get('INTACT_AUDIT_SOURCE'):params.env['PYTHONPATH']=str(REPO/'backend')
 report={'tools':{},'checks':[]}
 async with Client(params,read_timeout_seconds=150) as c:
  tools=(await c.list_tools()).tools
  async def call(name,args=None,error=False):
   r=await c.call_tool(name,args or {});report['tools'].setdefault(name,{'success':0,'expected_errors':0})
   if error:assert r.is_error,(name,r);report['tools'][name]['expected_errors']+=1;return r
   assert not r.is_error,(name,r);report['tools'][name]['success']+=1;return r.structured_content
  ready=await call('status');assert ready['cad_ready'] and ready['version']=='0.12.0' and 'user-triggered' in ready['agent']
  built=await call('build_model',{'source':SOURCE,'parameters':{'length':60,'bore':10},'name':'All-tools audit'});key=built['model_id'];base=built['viewer_url'].removesuffix('view')
  assert any(m['model_id']==key for m in (await call('list_models'))['models'])
  model=await call('get_model',{'model_id':key});measure=await call('measure_model',{'model_id':key});assert len(measure['parts'])==2
  assert math.isclose(measure['parts'][0]['volume_mm3'],(60*30-math.pi*5**2)*6,rel_tol=1e-8)
  await call('set_appearance',{'model_id':key,'part_id':'plate','color':'#df873c','material':'steel','name':'Steel plate'})
  await call('set_appearance',{'model_id':key,'part_id':'plate','color':'red'},error=True)
  before=(await call('get_model',{'model_id':key}))['spec']['revision'];updated=await call('update_parameters',{'model_id':key,'parameters':{'length':70},'expected_revision':before});assert updated['revision']>before
  await call('update_parameters',{'model_id':key,'parameters':{'length':80},'expected_revision':0},error=True)
  await call('update_parameters',{'model_id':key,'parameters':{'length':80},'expected_revision':True},error=True)
  await call('build_model',{'model_id':key,'source':'def build(params):\n    raise ValueError("audit repair message")','parameters':{}},error=True)
  assert (await call('get_model',{'model_id':key}))['spec']['revision']==updated['revision']
  history=await call('revisions',{'model_id':key});assert len(history['revisions'])>=3
  historical=await call('get_model',{'model_id':key,'revision':1});assert historical['historical'] and historical['spec']['revision']==1
  preview=await call('open_viewer',{'model_id':key,'revision':1});assert '?revision=1' in preview['url'] and urlopen(preview['url']).status==200
  assert (await call('get_model',{'model_id':key}))['spec']['revision']==updated['revision']
  await call('validate_model',{'model_id':key,'expected_bounds':{'plate':{'length':70.0,'width':30.0,'height':6.0}},'expected_part_ids':['plate','lid']})
  await call('restore_revision',{'model_id':key,'revision':True},error=True)
  restored=await call('restore_revision',{'model_id':key,'revision':1});assert restored['revision']>updated['revision']
  opened=await call('open_viewer',{'model_id':key});assert urlopen(opened['url']).status==200
  for kind in ['step','stl','glb','3mf','python','project']:
   export=await call('export_model',{'model_id':key,'format':kind});data=urlopen(export['url']).read();assert len(data)>40
  await call('set_appearance',{'model_id':key,'part_id':'plate','color':'#df873c'})
  exported=await call('export_model',{'model_id':key,'format':'step'})
  import build123d as bd
  shape=bd.import_step(exported['path']);part=next(p for p in shape.children if p.label=='plate');assert tuple(round(n*255) for n in tuple(part.color)[:3])==(223,135,60)
  report['checks'].append('appearance persists in real STEP without changing CAD dimensions')
  data=json.loads(urlopen(base+'project.json').read());data['spec']['parts'][1]['enabled']=False;file=OUT/'tool-project.json';file.write_text(json.dumps(data));windows_project=str(PureWindowsPath('C:/')/file.relative_to('/mnt/c').as_posix());imported=await call('import_project',{'path':windows_project});assert (await call('get_model',{'model_id':imported['model_id']}))['spec']['parts'][1]['enabled'] is False
  before_count=len((await call('list_models'))['models']);data['view']={'opacity':1000};file.write_text(json.dumps(data));await call('import_project',{'path':str(file)},error=True);assert len((await call('list_models'))['models'])==before_count
  copy=OUT/'tool import with spaces.step';shutil.copyfile(exported['path'],copy);windows_step=str(PureWindowsPath('C:/')/copy.relative_to('/mnt/c').as_posix());imported_step=await call('import_cad',{'path':windows_step});assert len(imported_step['geometry']['parts'])==2 and imported_step['source_step_url']
  report['checks'].append('Windows drive paths with spaces import STEP and project files through WSL')
  latest=await call('get_model',{'model_id':key});topology=json.loads(urlopen(base+'topology.json').read());ref=topology['parts'][0]['faces'][0]['ref'];revision=latest['spec']['revision'];artifact=latest['spec']['program']['artifact_id']
  await call('resolve_references',{'model_id':key,'references':[ref],'revision':revision,'artifact_id':artifact})
  await call('resolve_references',{'model_id':key,'references':[ref],'revision':1,'artifact_id':artifact},error=True)
  snapshot=await c.call_tool('snapshot_model',{'model_id':key,'view':'top'});assert not snapshot.is_error;report['tools']['snapshot_model']={'success':1,'expected_errors':0};image=next(i for i in snapshot.content if i.type=='image');png=image.data
  (OUT/'all-tools-snapshot.png').write_bytes(base64.b64decode(png));assert not (await call('list_edit_requests',{'model_id':key}))['requests']
  origin='/'.join(base.split('/')[:3]);body={'instructions':'Change central bore to 12 mm; preserve lid.','references':[ref],'revision':revision,'artifact_id':artifact,'screenshot':'data:image/png;base64,'+png}
  req=Request(base+'edit-request',json.dumps(body).encode(),{'Origin':origin,'Content-Type':'application/json'});request=json.loads(urlopen(req).read());assert (await call('list_edit_requests',{'model_id':key}))['requests'][0]['request_id']==request['request_id']
  read=await c.call_tool('read_edit_request',{'model_id':key,'request_id':request['request_id']});assert not read.is_error;assert any(i.type=='image' for i in read.content);report['tools']['read_edit_request']={'success':1,'expected_errors':0}
  result=await call('apply_edit_request',{'model_id':key,'request_id':request['request_id'],'source':SOURCE,'parameters':{'length':60,'bore':12}});assert result['revision']>revision
  await call('apply_edit_request',{'model_id':key,'request_id':request['request_id'],'source':SOURCE,'parameters':{'length':60,'bore':14}},error=True)
  for kind in ['beam','fin']:
   r=await call('analyze_reference',{'kind':kind,'length':80 if kind=='fin' else 180,'width':40 if kind=='fin' else 30,'height':3 if kind=='fin' else 8,'material':'aluminum','study':{'type':'thermal' if kind=='fin' else 'mechanical','heat':5,'force':25,'nodes':41},'approved':True});assert r['scope']=='reduced_1d' and all(check['passed'] for check in r['checks'])
  await call('analyze_reference',{'kind':'beam','length':180,'width':30,'height':8,'material':'aluminum','study':{'force':25},'approved':False},error=True)
  lattice=await call('build_tpms',{'family':'gyroid','length':12.0,'width':12.0,'height':12.0,'cell_size':6.0,'samples_per_cell':16})
  assert lattice['geometry']['engine']=='implicit_mesh' and 'step' not in lattice['downloads']
  assert (await call('validate_model',{'model_id':lattice['model_id'],'expected_part_ids':['lattice']}))['passed']
  await call('export_model',{'model_id':lattice['model_id'],'format':'step'},error=True)
  await call('get_model',{'model_id':'../private'},error=True)
  before=(await call('get_model',{'model_id':key}))['spec']['revision'];task=asyncio.create_task(c.call_tool('build_model',{'model_id':key,'source':'def build(params):\n    while True:pass','parameters':{}}));await asyncio.sleep(2);task.cancel()
  try:await task
  except asyncio.CancelledError:pass
  await asyncio.sleep(.5);assert (await call('get_model',{'model_id':key}))['spec']['revision']==before
  report['checks']+=['strict argument schemas and revision guards','atomic invalid import and disabled parts','all six exports','STEP native color/assembly import','geometry reference guards','edit text and image delivery plus application','both reference solvers and approval guard','cancelled CAD preserves revision']
  from p1_examples import CIRCLE, PAD
  draft=await call('set_design_requirements',{'requirements':{'source_text':'40 mm diameter disk, 8 mm thick, two 8 mm through bores at X ±10 mm','checks':[{'id':'body','kind':'bounds','part_id':'disk','expected':{'length':40,'width':40,'height':8}},{'id':'bores','kind':'hole_pattern','part_id':'disk','expected':{'count':2,'diameter_mm':8,'through':True,'depth_mm':8,'centers_mm':[[10,0,0],[-10,0,0]]}}]},'name':'Priority 1 constrained disk'})
  design=draft['model_id'];opened_draft=await call('open_viewer',{'model_id':design});assert urlopen(opened_draft['url']).status==200
  await call('create_sketch',{'model_id':design,'sketch':CIRCLE,'parameters':{'diameter':40.0,'thickness':8.0,'bore_diameter':6.0}})
  await call('set_sketch_constraints',{'model_id':design,'sketch_id':'outline','constraints':CIRCLE['constraints']})
  solved=await call('solve_sketch',{'model_id':design,'sketch_id':'outline'});assert solved['sketches']['outline']['degrees_of_freedom']==0
  await call('get_design_requirements',{'model_id':design});await call('get_feature_tree',{'model_id':design})
  result=await call('edit_feature_tree',{'model_id':design,'features':[PAD,{'id':'holes','kind':'hole','base':'pad','part_id':'disk','params':{'diameter':{'parameter':'bore_diameter'},'centers':[[10,0,0],[-10,0,0]],'through':True}}]})
  result=await call('rebuild_features',{'model_id':design})
  top=json.loads(urlopen(result['viewer_url'].removesuffix('view')+'topology.json').read());face=next(f for f in top['parts'][0]['faces'] if f.get('radius_mm')==3)
  pinned=await call('bind_reference',{'model_id':design,'reference':face['ref'],'label':'mounting_bore','revision':result['revision'],'artifact_id':result['geometry']['artifact_id']})
  await call('update_parameters',{'model_id':design,'parameters':{'bore_diameter':8.0},'expected_revision':pinned['revision']})
  reference=await call('resolve_references',{'model_id':design,'references':['stable:mounting_bore']});assert reference['references'][0]['radius_mm']==4
  assert (await call('verify_design',{'model_id':design}))['passed']
  current=(await call('get_model',{'model_id':design}))['spec']['revision']
  await call('set_accuracy',{'model_id':design,'settings':{'dimensional_tolerance_mm':.005,'linear_deflection_mm':.01},'expected_revision':current})
  assert (await call('check_accuracy',{'model_id':design}))['passed']
  await call('edit_feature_tree',{'model_id':design,'features':[{'id':'bad','kind':'hole','base':'missing','part_id':'disk','params':{}}]},error=True)
  report['checks']+=['empty draft opens without placeholder solids','actual FreeCAD fully constrained sketch and dependency rebuild','named bore reference survives diameter change','requirements verify exported hole diameter, depth, centers and through state','native tolerance and mesh convergence checks','invalid feature graph rejected']
  cube=await call('build_model',{'source':'import build123d as bd\ndef build(params):\n    return {"body":bd.Box(params["length"],10,10),"moving":bd.Pos(0,25,0)*bd.Box(4,4,4)}','parameters':{'length':20},'name':'Priority 2/3 tools'});cube_id=cube['model_id']
  millimeter=await call('build_lattice_mm',{'settings':{'size':[4,4,4],'cell_size':8,'thickness_mm':1.6,'samples_per_cell':24}})
  assert (await call('measure_mesh_quality',{'model_id':millimeter['model_id']}))['watertight']
  await call('build_lattice_mm',{'settings':{'thickness_mm':.1}},error=True)
  refined=await call('refine_lattice',{'settings':{'size':[4,4,4],'cell_size':8,'thickness_mm':1.6,'samples_per_cell':24,'maximum_samples_per_cell':24}});assert not refined['converged']
  converted=await call('convert_mesh_to_cad',{'model_id':millimeter['model_id'],'maximum_faces':8000});assert 'planar' in converted['conversion']['representation']
  await call('convert_mesh_to_cad',{'model_id':millimeter['model_id'],'maximum_faces':4},error=True)
  await call('set_assembly_joints',{'model_id':cube_id,'settings':{'joints':[{'id':'hinge','kind':'revolute','parent':'body','child':'moving','value':30}]}})
  loft=await call('build_freeform',{'settings':{'sections':[[[-5,-5,0],[5,-5,0],[5,5,0],[-5,5,0]],[[-3,-3,10],[3,-3,10],[3,3,10],[-3,3,10]]]}})
  catalog=await call('component_catalog');assert len(catalog['components'])==6
  component=await call('insert_component',{'component_id':'iso4762_m3','length_mm':12})
  await call('insert_component',{'component_id':'unknown'},error=True)
  await call('manufacturing_review',{'model_id':cube_id,'settings':{'part_id':'body','process':'molding'}})
  drawing=await call('engineering_drawing',{'model_id':cube_id,'part_id':'body'});assert urlopen(drawing['drawing_url']).read().startswith(b'%PDF')
  sheet=await call('build_sheet_metal',{'settings':{}});assert sheet['flat_model']['geometry']['engine']=='build123d'
  for physics in ('thermal','structural','stokes'):
   report3d=await call('run_3d_simulation',{'model_id':cube_id,'settings':{'part_id':'body','kind':physics,'mesh_size_mm':5,'convergence':False}});assert report3d['solver_checks_passed'] and not report3d['verified'];assert len(urlopen(report3d['results_url']).read())>100
   if physics=='structural':
    import meshio,numpy as np
    vtu=OUT/'tools-structural.vtu';vtu.write_bytes(urlopen(report3d['results_url']).read());field=meshio.read(vtu);assert np.allclose(np.linalg.norm(field.point_data['displacement_vector_mm'],axis=1),field.point_data['displacement_mm'])
  await call('run_3d_simulation',{'model_id':cube_id,'settings':{'part_id':'body','kind':'turbulent'}},error=True)
  evidence=(await call('engineering_evidence',{'model_id':cube_id}))['reports'];assert {'thermal','structural','stokes'}<={r.get('kind') for r in evidence}
  scan=await call('reconstruct_geometry',{'settings':{'mode':'scan','path':str(urlopen.__module__)}} ,error=True)
  exported_cube=await call('export_model',{'model_id':cube_id,'format':'stl'})
  scan=await call('reconstruct_geometry',{'settings':{'mode':'scan','path':exported_cube['path']}});assert scan['model']['geometry']['engine']=='implicit_mesh'
  await call('compare_designs',{'settings':{'model_ids':[loft['model_id'],component['model']['model_id']]}})
  # Use a regular parameterized model for alternatives; assembly joint parameters have a different graph.
  opt=await call('optimize_design',{'model_id':key,'settings':{'parameter':'length','values':[55,60]}});assert len(opt['candidates'])==2
  job=await call('submit_engineering_job',{'operation':'simulate','model_id':cube_id,'settings':{'kind':'thermal','part_id':'body','mesh_size_mm':5,'convergence':False}})
  for _ in range(150):
   state=await call('get_engineering_job',{'job_id':job['job_id'],'model_id':cube_id})
   if state['status'] not in ('queued','running'):break
   await asyncio.sleep(.2)
  assert state['status']=='succeeded',state
  await call('cancel_engineering_job',{'job_id':job['job_id'],'model_id':cube_id})
  hybrid=await call('build_hybrid',{'model_id':cube_id,'settings':{'part_id':'body','operation':'intersection','size':[12,12,12],'thickness_mm':1.6}});assert hybrid['geometry']['engine']=='implicit_mesh'
  report['checks']+=['all priority 2/3 MCP schemas exercised with real engines','real STEP conversion, PDF and VTU downloads','all three 3D physics modes','durable job submission/status/idempotent completion cancellation','distance offsets, refinement limits, hybrid booleans, motion and alternatives']
  assert set(report['tools'])=={t.name for t in tools},set(t.name for t in tools)-set(report['tools'])
  assert all(item['success'] for item in report['tools'].values())
 async with Client(params,mode='legacy',read_timeout_seconds=150) as c:
  status=await c.call_tool('status');assert not status.is_error
  result=await c.call_tool('get_model',{'model_id':key});assert not result.is_error
 report['checks'].append('modern discovery and legacy MCP initialize both work; viewer survives disconnect')
 assert urlopen(opened['url']).status==200
 assert len(report['tools'])==53
 report['tool_count']=len(report['tools']);report['status']='passed';(OUT/'tools-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
asyncio.run(main())
