"""Revision-bound project deliverables built from saved geometry, never AI estimates."""
import base64,csv,io,json,math,re,shutil,subprocess,uuid
from pathlib import Path
from .projects import atomic_json
from .edit_requests import EditRequests
FILES={'bom':'bom.csv','deck':'slides.pptx','dxf':'drawing.dxf','dwg':'drawing.dwg'}
def dwg_binary(name='dwgwrite'):
 path=Path.home()/'.local/share/intact-simulation/libredwg-0.14/bin'/name
 return str(path) if path.is_file() else shutil.which(name)
def bom_rows(record):
 rows=[]
 for p in record['spec']['parts']:
  rows.append({'part_id':p['id'],'component':p['name'],'quantity':1,'length_mm':p['params']['length'],'width_mm':p['params']['width'],'height_mm':p['params']['height'],'material':p.get('material','unspecified'),'volume_mm3':p['measurements']['volume_mm3'],'surface_area_mm2':p['measurements']['surface_area_mm2'],'representation':p.get('engine','native'),'revision':record['spec']['revision']})
 return rows

def write_dxf(topology,path):
 import ezdxf
 doc=ezdxf.new('R2000');doc.units=4;space=doc.modelspace()
 points=[point for part in topology['parts'] for edge in part['edges'] for point in edge['samples']]
 if not points:raise ValueError('DXF/DWG projections require native CAD edges. A triangle-only model has no native drawing edges.')
 if len(points)>500000:raise ValueError('Drawing exceeds the 500,000 sampled edge point limit. Simplify the assembly first.')
 low=[min(p[i] for p in points) for i in range(3)];high=[max(p[i] for p in points) for i in range(3)];size=[high[i]-low[i] for i in range(3)];gap=max(max(size)*.2,10)
 views=[('Front X-Z',0,2,0,0),('Top X-Y',0,1,0,size[2]+gap),('Right Y-Z',1,2,size[0]+gap,0)]
 entities=0
 for index,(name,h,v,ox,oy) in enumerate(views):
  layer='View_'+str(index+1);doc.layers.add(layer)
  space.add_text(name+' (mm)',dxfattribs={'height':max(max(size)*.03,1),'insert':(ox,oy-gap*.35),'layer':layer})
  for part in topology['parts']:
   for edge in part['edges']:
    projected=[(p[h]-low[h]+ox,p[v]-low[v]+oy) for p in edge['samples']]
    if len(projected)<2 or all(math.dist(projected[0],p)<1e-9 for p in projected[1:]):continue
    space.add_lwpolyline(projected,dxfattribs={'layer':layer});entities+=1
 if not entities:raise ValueError('No non-degenerate drawing edges were found.')
 doc.saveas(path)
 check=ezdxf.readfile(path)
 if check.audit().has_errors:raise ValueError('DXF validation failed.')
 return {'units':'mm','views':['front','top','right'],'edge_entities':entities,'scope':'2D wireframe projections of native edge samples; curves are polylines, with no hidden-line removal or manufacturing dimensions.'}

def create(projects,key,data):
 kind=data.get('kind')
 if not isinstance(kind,str) or kind not in FILES:raise ValueError('Choose BOM, slide deck, DXF or DWG.')
 revision=data.get('revision')
 if not isinstance(revision,int) or isinstance(revision,bool) or revision<1:raise ValueError('Export revision must be a positive integer.')
 with projects.lock(key):
  record=projects.load(key)
  if data.get('revision')!=record['spec']['revision'] or data.get('artifact_id')!=record['spec']['program']['artifact_id']:raise ValueError('Geometry changed. Refresh before exporting the project.')
  topology=json.loads(projects.record_artifact(record,'topology.json').read_text()) if kind in ('dxf','dwg') else None
 identifier=uuid.uuid4().hex;folder=projects.root/'project-exports'/key/identifier;folder.mkdir(parents=True)
 target=folder/FILES[kind];scope={}
 if kind=='bom':
  rows=bom_rows(record)
  with target.open('w',encoding='utf-8-sig',newline='') as stream:
   writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader()
   # Spreadsheet cells must never execute a user-supplied component name as a formula.
   for row in rows:writer.writerow({k:("'"+v if isinstance(v,str) and v.startswith(('=','+','-','@','\t','\r')) else v) for k,v in row.items()})
  scope={'components':len(rows),'scope':'One row per saved named component; quantity 1 per unique instance. Not a supplier-priced procurement BOM.'}
 elif kind=='deck':
  from .presentation import build_deck
  scope=build_deck(projects,record,data,target)
 else:
  scope=write_dxf(topology,folder/'drawing.dxf')
  if kind=='dwg':
   binary=dwg_binary()
   if not binary:raise ValueError('GNU LibreDWG is missing. Run scripts/install-project-tools.py, or export DXF.')
   result=subprocess.run([binary,'--as','r2000','-y','-o',str(target),str(folder/'drawing.dxf')],capture_output=True,timeout=90)
   if result.returncode or not target.is_file() or target.read_bytes()[:6]!=b'AC1015':raise ValueError('LibreDWG could not validate/write the R2000 DWG drawing. Use DXF for interchange.')
   reader=dwg_binary('dwgread');validated=False
   if reader:
    output=folder/'dwg-readback.json';check=subprocess.run([reader,'-O','JSON','-o',str(output),str(target)],capture_output=True,timeout=90)
    if check.returncode or not output.is_file() or not json.loads(output.read_text()).get('OBJECTS'):raise ValueError('DWG read-back validation failed. Use the DXF export.')
    validated=True;output.unlink()
   scope.update(readback_validated=validated,format='DWG R2000',compatibility='GNU LibreDWG writer; independent CAD application compatibility is not certified.')
 with projects.lock(key):
  current=projects.load(key)
  if current['spec']['revision']!=revision or current['spec']['program']['artifact_id']!=record['spec']['program']['artifact_id']:raise ValueError('Geometry changed while creating the deliverable. Refresh and retry; no mixed-revision file was published.')
 report={'export_id':identifier,'kind':kind,'model_id':key,'revision':record['spec']['revision'],'artifact_id':record['spec']['program']['artifact_id'],'filename':FILES[kind],**scope};atomic_json(folder/'report.json',report)
 return {**report,'download':'project-file?export_id='+identifier+'&file='+FILES[kind]}

def read_file(projects,key,identifier,filename):
 projects.path(key)
 if not isinstance(identifier,str) or not re.fullmatch('[a-f0-9]{32}',identifier) or filename not in FILES.values():raise ValueError('Invalid project export path.')
 folder=projects.root/'project-exports'/key/identifier;report=json.loads((folder/'report.json').read_text())
 if report['model_id']!=key:raise ValueError('Export belongs to another model.')
 return folder/filename
