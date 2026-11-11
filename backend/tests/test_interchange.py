import numpy as np
import pytest
import trimesh
from mcp import Client
from pxr import Usd,UsdGeom
from intact_backend.projects import ProjectService
from intact_backend.mcp_server import IntactMCP,create_server
SOURCE='import build123d as bd\ndef build(params):\n return {"base":bd.Pos(7,4,3)*bd.Rot(0,0,20)*bd.Box(params["size"],10,4),"lid":bd.Pos(-5,2,17)*bd.Box(5,3,2)}'
@pytest.fixture
def model(tmp_path):
 s=ProjectService(tmp_path);r=s.build(SOURCE,{'size':20});return s,r

def test_ascii_and_binary_stl_are_different_valid_encodings(model):
 s,r=model;before=s.path(r['model_id']).read_bytes();ascii_file=s.record_artifact(r,'model-ascii.stl');binary_file=s.record_artifact(r,'model-binary.stl')
 a=ascii_file.read_bytes();b=binary_file.read_bytes();assert a.startswith(b'solid ') and b'facet normal' in a and b'endsolid' in a
 assert len(b)==84+int.from_bytes(b[80:84],'little')*50
 ma=trimesh.load(ascii_file,force='mesh',process=False);mb=trimesh.load(binary_file,force='mesh',process=False)
 assert len(ma.faces)==len(mb.faces)>0 and np.allclose(ma.bounds,mb.bounds,atol=1e-6)
 assert s.path(r['model_id']).read_bytes()==before
@pytest.mark.parametrize('filename,magic',[('model.usd',b'PXR-USDC'),('model.usda',b'#usda 1.0')])
def test_usd_scenes_preserve_parts_units_colors_and_assembled_bounds(model,filename,magic):
 s,r=model;path=s.record_artifact(r,filename);assert path.read_bytes().startswith(magic)
 stage=Usd.Stage.Open(str(path));assert UsdGeom.GetStageUpAxis(stage)=='Z' and UsdGeom.GetStageMetersPerUnit(stage)==pytest.approx(.001)
 assert stage.GetDefaultPrim().GetDisplayName()==r['name']
 meshes=[prim for prim in stage.Traverse() if prim.IsA(UsdGeom.Mesh)];assert len(meshes)==2
 for prim in meshes:
  mesh=UsdGeom.Mesh(prim);assert mesh.GetSubdivisionSchemeAttr().Get()=='none'
  assert len(mesh.GetFaceVertexIndicesAttr().Get())==3*len(mesh.GetFaceVertexCountsAttr().Get())
  assert len(mesh.GetDisplayColorAttr().Get())==1
 bounds=UsdGeom.BBoxCache(Usd.TimeCode.Default(),['default']).ComputeWorldBound(stage.GetDefaultPrim()).ComputeAlignedRange()
 actual=np.array([bounds.GetMin(),bounds.GetMax()]);reference=trimesh.load(s.record_artifact(r,'model.stl'),force='mesh',process=False).bounds
 assert np.allclose(actual,reference,atol=1e-4)
 assert s.load(r['model_id'])['spec']['revision']==1

def test_usd_cache_keeps_revision_provenance_when_geometry_returns_to_old_shape(model):
 s,r=model;key=r['model_id'];first=s.record_artifact(r,'model.usda');s.parameters(key,{'size':21});latest=s.parameters(key,{'size':20})
 assert latest['spec']['program']['artifact_id']==r['spec']['program']['artifact_id']
 last=s.record_artifact(latest,'model.usda');assert first!=last
 assert Usd.Stage.Open(str(last)).GetDefaultPrim().GetCustomDataByKey('intact:revision')==3
 assert Usd.Stage.Open(str(first)).GetDefaultPrim().GetCustomDataByKey('intact:revision')==1

async def test_ai_export_tool_accepts_all_new_formats(model):
 s,r=model
 async with Client(create_server(IntactMCP(s.root))) as client:
  status=await client.call_tool('status');assert {'usd','usda','stl_ascii','stl_binary'}<=set(status.structured_content['exports'])
  for fmt in ('usd','usda','stl_ascii','stl_binary'):
   result=await client.call_tool('export_model',{'model_id':r['model_id'],'format':fmt});assert not result.is_error,result
   assert result.structured_content['assembled']
 from test_mcp import stop_viewer
 stop_viewer(s.root)
