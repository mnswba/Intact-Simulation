import base64,csv,io,json,subprocess
from pathlib import Path
import pytest
from PIL import Image
from pptx import Presentation
import ezdxf
from intact_backend.projects import ProjectService
from intact_backend.project_exports import create,read_file,dwg_binary
from intact_backend.view_settings import ViewSettings
SOURCE='import build123d as bd\ndef build(params):\n return {"plate":bd.Box(20,10,3)-bd.Cylinder(2,6),"lid":bd.Pos(0,0,10)*bd.Box(20,10,1)}'
@pytest.fixture
def model(tmp_path):
 s=ProjectService(tmp_path);r=s.build(SOURCE,{})
 return s,r

def payload(record,kind,**extra):return {'kind':kind,'revision':record['spec']['revision'],'artifact_id':record['spec']['program']['artifact_id'],**extra}
def test_bom_has_all_components_and_safe_spreadsheet_names(model):
 s,r=model;key=r['model_id'];s.appearance(key,'plate',name='=HYPERLINK("example")');r=s.load(key);out=create(s,key,payload(r,'bom'))
 path=read_file(s,key,out['export_id'],out['filename'])
 with path.open(encoding='utf-8-sig',newline='') as stream:rows=list(csv.DictReader(stream))
 assert len(rows)==2 and rows[0]['component'].startswith("'=")
 assert all(row['quantity']=='1' and float(row['volume_mm3'])>0 for row in rows)
 assert s.load(key)['spec']['revision']==r['spec']['revision']
def test_deck_is_real_pptx_with_snapshot_and_component_data(model):
 s,r=model;image=io.BytesIO();Image.new('RGB',(320,180),'steelblue').save(image,format='PNG');url='data:image/png;base64,'+base64.b64encode(image.getvalue()).decode()
 result=create(s,r['model_id'],payload(r,'deck',images=[{'name':'Current viewport','data_url':url}]))
 prs=Presentation(read_file(s,r['model_id'],result['export_id'],result['filename']))
 assert len(prs.slides)==3 and prs.slides[0].shapes.title.text==r['name']
 assert any(shape.shape_type==13 for shape in prs.slides[1].shapes)
 assert 'plate' in '\n'.join(shape.text for shape in prs.slides[-1].shapes if shape.has_text_frame).lower()
def test_dxf_has_actual_three_view_edges_in_mm(model):
 s,r=model;result=create(s,r['model_id'],payload(r,'dxf'));doc=ezdxf.readfile(read_file(s,r['model_id'],result['export_id'],result['filename']))
 assert doc.units==4 and not doc.audit().has_errors
 assert len(doc.modelspace().query('LWPOLYLINE'))==result['edge_entities']>10
 assert {entity.dxf.layer for entity in doc.modelspace().query('LWPOLYLINE')}=={'View_1','View_2','View_3'}
def test_dwg_round_trips_through_actual_libredwg(model,tmp_path):
 if not dwg_binary() or not dwg_binary('dwgread'):pytest.skip('Install GNU LibreDWG project tools')
 s,r=model;result=create(s,r['model_id'],payload(r,'dwg'));path=read_file(s,r['model_id'],result['export_id'],result['filename'])
 assert path.read_bytes().startswith(b'AC1015')
 out=tmp_path/'readback.json';p=subprocess.run([dwg_binary('dwgread'),'-O','JSON','-o',str(out),str(path)],capture_output=True,timeout=30)
 assert p.returncode==0 and len(json.loads(out.read_text())['OBJECTS'])>10
@pytest.mark.parametrize('change',[{'revision':999},{'artifact_id':'0'*64},{'kind':'shell'},{'revision':True},{'kind':[]}])
def test_exports_reject_stale_or_unknown_operations(model,change):
 s,r=model
 with pytest.raises(ValueError):create(s,r['model_id'],{**payload(r,'bom'),**change})
def test_export_paths_cannot_escape_project(model):
 s,r=model
 for identifier,filename in [('../bad','bom.csv'),('0'*32,'../../private'),('0'*32,'auth.json')]:
  with pytest.raises(ValueError):read_file(s,r['model_id'],identifier,filename)
def test_text_anchor_persists_without_cad_revision_and_rejects_stale(model):
 s,r=model;annotation={'id':'note','tool':'text','points':[[.5,.5]],'color':'#ff0000','width':2,'text':'Hole','anchor':{'part_id':'plate','point':[1,2,1.5],'artifact_id':r['spec']['program']['artifact_id']}}
 view=s.save_view(r['model_id'],{'annotations':[annotation],'annotation_artifact':r['spec']['program']['artifact_id'],'component_names':True,'camera_zoom':2,'camera_span':42})
 assert view['camera_span']==42 and view['camera_zoom']==2 and view['annotations'][0]['anchor']==annotation['anchor'] and s.load(r['model_id'])['spec']['revision']==1
 stale={**annotation,'anchor':{**annotation['anchor'],'artifact_id':'0'*64}}
 with pytest.raises(ValueError,match='stale'):s.save_view(r['model_id'],{'annotations':[stale]})
 for point in ([True,0,0],[float('nan'),0,0],[0,0]):
  with pytest.raises(ValueError):ViewSettings(annotations=[{**annotation,'anchor':{**annotation['anchor'],'point':point}}])
def test_isolation_can_hide_127_of_128_parts():
 assert len(ViewSettings(hidden=['part_'+str(i) for i in range(127)]).hidden)==127


def test_project_export_http_respects_origin_history_and_download_scope(model):
 from urllib.request import Request,urlopen
 from urllib.error import HTTPError
 from urllib.parse import urlsplit
 from intact_backend.viewer_server import viewer_url
 from test_mcp import stop_viewer
 s,r=model;url=viewer_url(s.root,r['model_id']);base=url.rsplit('/',1)[0]+'/'
 origin='http://localhost:'+str(urlsplit(url).port);body=json.dumps(payload(r,'bom')).encode()
 try:
  for suffix,headers,expected in [('project-export',{},403),('project-export?revision=1',{'Origin':origin},400)]:
   with pytest.raises(HTTPError) as caught:urlopen(Request(base+suffix,data=body,headers={'Content-Type':'application/json',**headers}),timeout=20)
   assert caught.value.code==expected
  result=json.load(urlopen(Request(base+'project-export',data=body,headers={'Content-Type':'application/json','Origin':origin}),timeout=20))
  response=urlopen(base+result['download'],timeout=20);assert 'bom.csv' in response.headers['Content-Disposition'] and b'plate' in response.read()
 finally:stop_viewer(s.root)
