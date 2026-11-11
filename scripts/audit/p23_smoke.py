import json,sys
from pathlib import Path
from intact_backend.projects import ProjectService
from intact_backend.advanced import Advanced
root=Path.home()/'.local/share/intact-simulation/p23-smoke';s=ProjectService(root);a=Advanced(s);reports={}
source='import build123d as bd\ndef build(params):\n    return {"body":bd.Box(params["length"],10,10),"moving":bd.Pos(0,25,0)*bd.Box(5,5,5)}'
r=s.build(source,{'length':20},name='Advanced smoke');key=r['model_id']
cases={
'lattice':lambda:a.lattice({'size':[12,12,12],'cell_size':8,'thickness_mm':1.5,'samples_per_cell':24}),
'freeform':lambda:a.freeform({'sections':[[[-5,-5,0],[5,-5,0],[5,5,0],[-5,5,0]],[[-3,-3,12],[3,-3,12],[3,3,12],[-3,3,12]]]}),
'sheet':lambda:a.sheet({}),
'assembly':lambda:a.assembly(key,{'joints':[{'id':'hinge','kind':'revolute','parent':'body','child':'moving','value':45}]}),
'drawing':lambda:a.drawing(key,'body'),
'manufacturing':lambda:a.manufacture(key,{'part_id':'body','process':'cnc'}),
'convert':lambda:a.convert(key,maximum_faces=400),
}
for name,run in cases.items():
 try:
  value=run();reports[name]={'status':'passed','model_id':value.get('model_id') or value.get('model',{}).get('model_id')};print('PASS',name,flush=True)
 except Exception as e:reports[name]={'status':'failed','error':str(e)};print('FAIL',name,str(e)[-1800:],flush=True)
for kind in ('thermal','structural','stokes'):
 try:
  result=a.simulate(key,{'part_id':'body','kind':kind,'mesh_size_mm':5,'convergence':False});reports[kind]={'status':'passed','maximum':result['maximum'],'residual':result['relative_residual'],'balance':result['relative_balance_error']};print('PASS',kind,reports[kind],flush=True)
 except Exception as e:reports[kind]={'status':'failed','error':str(e)};print('FAIL',kind,str(e)[-1800:],flush=True)
Path('outputs/priority23-audit/smoke.json').write_text(json.dumps(reports,indent=2));sys.exit(any(v['status']=='failed' for v in reports.values()))
