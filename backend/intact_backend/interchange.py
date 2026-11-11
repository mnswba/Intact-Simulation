"""Actual STL encodings and OpenUSD mesh scenes from saved, assembled geometry."""
import hashlib,json,os,threading,uuid
from pathlib import Path
FORMATS={'stl_ascii':'model-ascii.stl','stl_binary':'model-binary.stl','usd':'model.usd','usda':'model.usda'}
NAMES=set(FORMATS.values())
_lock=threading.RLock()
def export_record(projects,record,filename):
 if filename not in NAMES:raise ValueError('Unsupported interchange format.')
 signature={'model_id':record['model_id'],'name':record['name'],'revision':record['spec']['revision'],'artifact':record['spec']['program']['artifact_id'],'parts':[{k:p.get(k) for k in ('id','name','color','material','position')} for p in record['spec']['parts']],'format':filename,'version':1}
 digest=hashlib.sha256(json.dumps(signature,sort_keys=True).encode()).hexdigest();folder=projects.root/'interchange-cache'/digest;target=folder/filename
 with _lock:
  if target.is_file():return target
  folder.mkdir(parents=True,exist_ok=True);temporary=folder/(uuid.uuid4().hex+Path(filename).suffix)
  if filename.endswith('.stl'):
   import trimesh
   mesh=trimesh.load(projects.record_artifact(record,'model.stl'),force='mesh',process=False)
   output=mesh.export(file_type='stl_ascii' if filename=='model-ascii.stl' else 'stl')
   if isinstance(output,str):output=output.encode('ascii')
   temporary.write_bytes(output)
   if filename=='model-ascii.stl' and not output.startswith(b'solid '):raise ValueError('ASCII STL conversion failed.')
   if filename=='model-binary.stl' and len(output)!=84+int.from_bytes(output[80:84],'little')*50:raise ValueError('Binary STL conversion failed.')
  else:
   import numpy as np
   from pxr import Usd,UsdGeom,Gf,Vt
   # .usd is a genuine USDC crate; .usda is its readable text counterpart.
   temporary=temporary.with_suffix('.usdc' if filename.endswith('.usd') else '.usda')
   stage=Usd.Stage.CreateNew(str(temporary));UsdGeom.SetStageUpAxis(stage,UsdGeom.Tokens.z);UsdGeom.SetStageMetersPerUnit(stage,.001)
   root=UsdGeom.Xform.Define(stage,'/Intact');stage.SetDefaultPrim(root.GetPrim());root.GetPrim().SetDisplayName(record['name'])
   root.GetPrim().SetCustomDataByKey('intact:revision',record['spec']['revision']);root.GetPrim().SetCustomDataByKey('intact:artifact',record['spec']['program']['artifact_id'])
   mesh_data=json.loads(projects.record_artifact(record,'mesh.json').read_text())
   parts={p['id']:p for p in record['spec']['parts']}
   for item in mesh_data['parts']:
    part=parts[item['id']];prim=UsdGeom.Xform.Define(stage,'/Intact/'+part['id']);prim.GetPrim().SetDisplayName(part['name']);prim.AddTranslateOp().Set(Gf.Vec3d(*part['position']))
    shape=UsdGeom.Mesh.Define(stage,prim.GetPath().AppendChild('Geometry'))
    coords=np.asarray(item['positions'],dtype=np.float32).reshape(-1,3);coords=np.ascontiguousarray(np.column_stack((coords[:,0],-coords[:,2],coords[:,1])),dtype=np.float32)
    points=Vt.Vec3fArray.FromNumpy(coords);shape.CreatePointsAttr(points)
    indices=np.ascontiguousarray(item['indices'],dtype=np.int32);shape.CreateFaceVertexCountsAttr(Vt.IntArray.FromNumpy(np.full(len(indices)//3,3,dtype=np.int32)));shape.CreateFaceVertexIndicesAttr(Vt.IntArray.FromNumpy(indices))
    shape.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none);shape.CreateDoubleSidedAttr(True);shape.CreateExtentAttr(UsdGeom.PointBased.ComputeExtent(points))
    rgb=[int(part['color'][i:i+2],16)/255 for i in (1,3,5)];linear=[c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4 for c in rgb]
    shape.CreateDisplayColorAttr([Gf.Vec3f(*linear)]);shape.GetPrim().SetCustomDataByKey('intact:part_id',part['id'])
   stage.GetRootLayer().Save();stage=None
   check=Usd.Stage.Open(str(temporary))
   if not check or len([p for p in check.Traverse() if p.IsA(UsdGeom.Mesh)])!=len(parts):raise ValueError('OpenUSD scene validation failed.')
   check=None
  os.replace(temporary,target)
 return target
