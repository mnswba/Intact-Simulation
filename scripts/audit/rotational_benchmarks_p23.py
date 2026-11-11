"""Independent heat, axial elasticity and duct-flow benchmarks on all CAD axes."""
import json,math
from pathlib import Path
import numpy as np
from intact_backend.projects import ProjectService
from intact_backend.advanced import Advanced
ROOT=Path.home()/'.local/share/intact-simulation/priority23-physics';OUT=Path(__file__).resolve().parents[2]/'outputs/priority23-audit';s=ProjectService(ROOT);a=Advanced(s);results=[]
for axis in range(3):
 dims=[10,10,10];dims[axis]=20;source='import build123d as bd\ndef build(params):\n    return {"domain":bd.Box('+','.join(map(str,dims))+')}'
 model=s.build(source,{},name='Axis '+str(axis)+' PDE benchmark')
 for kind in ('thermal','structural','stokes'):
  force=[0,0,0];force[axis]=1;r=a.simulate(model['model_id'],{'part_id':'domain','kind':kind,'axis':axis,'force_n':force,'mesh_size_mm':4,'convergence':True,'convergence_tolerance':.15});assert r['verified'],r['convergence']
  if kind=='thermal':
   points=np.asarray(r['positions_mm']);expected=300+(points[:,axis]+10)/20*50;error=float(np.max(abs(np.asarray(r['values'])-expected)));assert error<1e-6;reference='Exact linear conduction temperature field';actual=r['metric'];target=325
  elif kind=='structural':
   target=1*.02/(70e9*.01*.01)*1000;actual=r['maximum'];error=abs(actual-target)/target;assert error<.08;reference='FL/(EA), allowing fully clamped 3D end effects'
  else:
   series=sum(math.tanh(n*math.pi/2)/n**5 for n in range(1,101,2));target=.01**4/(12*.02)*(1-192/math.pi**5*series);actual=r['outlet_flow_m3_s'];error=abs(actual-target)/target;assert error<.15;reference='Square-duct Poiseuille series'
  results.append({'axis':axis,'physics':kind,'status':'passed','reference':reference,'reference_value':target,'actual_value':actual,'error':error,'relative_residual':r['relative_residual'],'balance_error':r['relative_balance_error'],'convergence':r['convergence'],'report_id':r['report_id']});print('PASS',axis,kind,error,flush=True)
(OUT/'physics-benchmarks.json').write_text(json.dumps({'status':'passed','cases':results,'scope':'Numerical benchmark verification for these bounded formulations, not general experimental validation.'},indent=2))
