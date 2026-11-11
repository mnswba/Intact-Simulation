"""50 varied advanced geometry/export cases; regression evaluation, not AI training."""
import concurrent.futures,json,math,time
from pathlib import Path
import trimesh
from intact_backend.projects import ProjectService
from intact_backend.advanced import Advanced
from intact_backend.component_library import insert,catalog
from intact_backend.validation import validate_model
ROOT=Path.home()/'.local/share/intact-simulation/priority23-matrix';OUT=Path(__file__).resolve().parents[2]/'outputs/priority23-audit';cases=[]
for family in ('gyroid','schwarz_p','diamond','neovius','lidinoid','split_p'):
 for size in ((6,6,6),(8,6,5)):
  for thickness in (1.4,1.8):cases.append(('lattice',{'family':family,'size':size,'cell_size':8,'thickness_mm':thickness,'samples_per_cell':24}))
for op in ('union','difference','intersection'):
 for x in (0,2):cases.append(('hybrid',{'part_id':'body','operation':op,'translation':[x,0,0],'size':[10,10,10],'cell_size':8,'thickness_mm':1.6,'samples_per_cell':24}))
for c in catalog()['components']:cases.append(('component',{'id':c['id']}))
for scale in (.6,.8,1,1.2,1.5,2):cases.append(('loft',{'scale':scale}))
for kind in ('revolute','slider'):
 for axis in ((1,0,0),(0,1,0),(0,0,1)):cases.append(('joint',{'kind':kind,'axis':axis}))
for angle in (45,120):cases.append(('sheet',{'angle_deg':angle,'k_factor':.35}))
assert len(cases)==50

def run(item):
 index,(kind,settings)=item;s=ProjectService(ROOT);a=Advanced(s);extra={};started=time.monotonic()
 try:
  if kind=='lattice':r=a.lattice(settings)
  elif kind=='hybrid':
   base=s.build('import build123d as bd\ndef build(params):\n    return {"body":bd.Box(8,8,8)}',{});r=a.hybrid(base['model_id'],settings);volume=r['geometry']['parts'][0]['volume_mm3'];assert volume>=512-1e-3 if settings['operation']=='union' else 0<volume<=512+1e-3
  elif kind=='component':r=insert(s,settings['id'],length_mm=18)['model']
  elif kind=='loft':
   q=settings['scale'];r=a.freeform({'sections':[[[-5*q,-5*q,0],[5*q,-5*q,0],[5*q,5*q,0],[-5*q,5*q,0]],[[-3*q,-3*q,10],[3*q,-3*q,10],[3*q,3*q,10],[-3*q,3*q,10]]]})
  elif kind=='joint':
   base=s.build('import build123d as bd\ndef build(params):\n    return {"base":bd.Box(3,3,3),"moving":bd.Pos(20,0,0)*bd.Box(2,4,6)}',{});motion=a.assembly(base['model_id'],{'joints':[{'id':'joint','parent':'base','child':'moving','kind':settings['kind'],'axis':settings['axis'],'value':35 if settings['kind']=='revolute' else 8}]});r=motion['model'];assert motion['motion']['all_passed'];p=next(p for p in r['spec']['parts'] if p['id']=='moving');assert p['measurements']['volume_mm3']==math.prod((2,4,6))
  else:
   sheet=a.sheet(settings);r=sheet['model'];flat=sheet['flat_model'];expected=sheet['developed_length_mm']*30*2;assert math.isclose(flat['geometry']['parts'][0]['volume_mm3'],expected,rel_tol=1e-8)
  key=r['model_id'];validation=validate_model(s,key);assert validation['passed'],validation
  source_volume=sum(p['volume_mm3'] for p in r['geometry']['parts'])
  for name in ('model.stl','model.glb','model.3mf'):
   mesh=trimesh.load(s.artifact(key,name),force='mesh',process=True);mesh.merge_vertices(merge_tex=True,merge_norm=True);volume=mesh.volume*(1e9 if name.endswith('.glb') else 1);assert mesh.is_volume and math.isclose(volume,source_volume,rel_tol=.01),(name,mesh.is_volume,volume,source_volume)
  return str(index),{'status':'passed','kind':kind,'settings':settings,'model_id':key,'volume_mm3':source_volume,'engine':r['geometry']['engine'],'elapsed_seconds':round(time.monotonic()-started,2)}
 except Exception as e:return str(index),{'status':'failed','kind':kind,'settings':settings,'error':str(e)[-3500:]}
report={'cases':{}}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 for key,value in pool.map(run,enumerate(cases,1)):
  report['cases'][key]=value;report['passed']=sum(c['status']=='passed' for c in report['cases'].values());report['failed']=sum(c['status']=='failed' for c in report['cases'].values());(OUT/'matrix-report.json').write_text(json.dumps(report,indent=2));print(value['status'].upper(),key,value['kind'],value.get('error','')[-250:],flush=True)
assert report['failed']==0,report['failed']
