# SPDX-License-Identifier: Apache-2.0
"""Public MCP schemas and dispatch for priority 2/3 operations."""
from typing import Any,Literal
from pathlib import Path
from pydantic import StrictInt,StrictFloat
from mcp.server.mcpserver import Context
from .preview_schema import PreviewStudy
from .picogk import PicoGKSettings
from .p23_schema import LatticeMM,AdaptiveLattice,HybridSpec,Assembly,Freeform,Simulation,Manufacturing,SheetMetal,Reconstruction,Optimization,Comparison
NAMES={'build_lattice_mm','refine_lattice','build_hybrid','convert_mesh_to_cad','set_assembly_joints','build_freeform','compare_designs','reconstruct_geometry','component_catalog','insert_component','manufacturing_review','engineering_drawing','build_sheet_metal','run_3d_simulation','optimize_design','engineering_evidence','submit_engineering_job','get_engineering_job','cancel_engineering_job'}
NAMES.update({'build_picogk_tpms','measure_mesh_quality','configure_simulation','get_simulation_workspace','run_virtual_analysis'})
def dispatch(engine,name,args,cancel=None):
 from .advanced import Advanced
 a=Advanced(engine.projects);key=args.get('model_id');s=args.get('settings')
 if name=='build_picogk_tpms':
  from .picogk import build
  result=build(engine.projects,s,cancel);result['model']=engine.result(result['model']);return result
 if name=='configure_simulation':
  from .simulation_workspace import configure
  return configure(engine.projects,key,s,args['operation'])
 if name=='get_simulation_workspace':
  from .simulation_workspace import workspace
  return workspace(engine.projects,key)
 if name=='run_virtual_analysis':
  from .simulation_workspace import configure
  result=configure(engine.projects,key,s,'preview');return {'model_id':key,'preview':result['studies']['preview'],'mode':'kinematic-preview','viewer_url':engine.viewer(key),'scope':'Visual trajectories only. No dynamics, contact, force or walking stability prediction.'}
 if name=='build_lattice_mm':return engine.result(a.lattice(s,key,args.get('expected_revision'),cancel))
 if name=='refine_lattice':
  r=a.adaptive(s,cancel);r['model']=engine.result(r['model']);return r
 if name=='build_hybrid':return engine.result(a.hybrid(key,s,args.get('expected_revision'),cancel))
 if name=='convert_mesh_to_cad':
  r=a.convert(key,args.get('maximum_faces',4000),cancel);r['model']=engine.result(r['model']);return r
 if name=='set_assembly_joints':
  r=a.assembly(key,s,args.get('expected_revision'),cancel);r['model']=engine.result(r['model']);return r
 if name=='build_freeform':return engine.result(a.freeform(s,cancel))
 if name=='compare_designs':return a.compare(s)
 if name=='reconstruct_geometry':
  r=a.reconstruct(s,cancel)
  if 'model' in r:r['model']=engine.result(r['model'])
  return r
 if name=='component_catalog':
  from .component_library import catalog
  return catalog()
 if name=='insert_component':
  from .component_library import insert
  r=insert(engine.projects,args['component_id'],args.get('length_mm',12),args.get('position',(0,0,0)),key,args.get('expected_revision'),cancel);r['model']=engine.result(r['model']);return r
 if name=='measure_mesh_quality':r=a.mesh_quality(key,cancel)
 elif name=='manufacturing_review':r=a.manufacture(key,s,cancel)
 elif name=='engineering_drawing':r=a.drawing(key,args['part_id'],args.get('title','Reference drawing'),args.get('tolerance_note',''),cancel)
 elif name=='build_sheet_metal':
  r=a.sheet(s,cancel);r['model']=engine.result(r['model']);r['flat_model']=engine.result(r['flat_model']);return r
 elif name=='run_3d_simulation':r=a.simulate(key,s,cancel)
 elif name=='optimize_design':return a.optimize(key,s,cancel)
 elif name=='engineering_evidence':return a.evidence(key)
 elif name in ('submit_engineering_job','get_engineering_job','cancel_engineering_job'):
  from . import engineering_jobs as jobs
  if name=='submit_engineering_job':return jobs.submit(engine.projects,args['operation'],s,key)
  if name=='get_engineering_job':
   job=jobs.status(engine.projects,args['job_id'],key)
   if job.get('result',{}).get('kind') in ('thermal','structural','stokes','motion'):
    from .simulation_workspace import compact
    job={**job,'result':compact(job['result'])}
   return job
  return jobs.cancel(engine.projects,args['job_id'],key)
 else:raise ValueError('Unknown advanced tool.')
 r={k:v for k,v in r.items() if k not in ('positions_mm','triangles','values','fields','frames')};r['viewer_url']=engine.viewer(key);base=r['viewer_url'].removesuffix('view');r['report_url']=base+'engineering-file?report_id='+r['report_id']+'&file=report.json'
 if name=='engineering_drawing':r['drawing_url']=base+'engineering-file?report_id='+r['report_id']+'&file=drawing.pdf'
 if name=='run_3d_simulation':r['results_url']=base+'engineering-file?report_id='+r['report_id']+'&file=results.vtu'
 return r

def register(server,engine,execute,read,write):
 @server.tool(annotations=write)
 async def build_picogk_tpms(settings:PicoGKSettings,ctx:Context)->dict[str,Any]:
  """Generate a real PicoGK voxel TPMS mesh through the pinned optional Linux bridge (2.4.0-alpha04 prerelease). Six families; <=4 million bounding voxels, >=3 voxels across nominal minimum wall. Local-gradient distance approximation, not certified uniform thickness. Creates a new mesh model; STL/GLB/3MF, no smooth STEP. No silent fallback. Readiness appears in status."""
  return await execute('build_picogk_tpms',{'settings':settings.model_dump(mode='json')},ctx)

 @server.tool(annotations=write)
 def configure_simulation(model_id:str,operation:Literal['simulate','preview'],settings:dict[str,Any])->dict[str,Any]:
  """Save a validated mechanical or virtual study without changing CAD. Read get_simulation_workspace first; use Simulation/PreviewStudy schema and revision/artifact guards."""
  return engine.call('configure_simulation',dict(model_id=model_id,operation=operation,settings=settings))
 @server.tool(annotations=read)
 def get_simulation_workspace(model_id:str)->dict[str,Any]:
  """Read saved simulation definitions, available parts, revision identity and compact job/results summaries."""
  return engine.call('get_simulation_workspace',dict(model_id=model_id))
 @server.tool(annotations=read)
 async def run_virtual_analysis(model_id:str,settings:PreviewStudy,ctx:Context)->dict[str,Any]:
  """Configure a viewer-only kinematic driving, walking or machine preview using stable CAD part IDs. All pivots are assembled CAD XYZ in METRES; directions are CAD +Z up, +X forward. Supply explicit wheel groups or limb/link joints from inspected geometry. No physical simulation, balance, contact or force predictions. Preserves CAD and exports."""
  return await execute('run_virtual_analysis',dict(model_id=model_id,settings=settings.model_dump(mode='json')),ctx)

 @server.tool(annotations=read)
 async def measure_mesh_quality(model_id:str,ctx:Context)->dict[str,Any]:
  """Measure exported mesh volume, bounds, watertightness and finite surface-normal wall chords. Returns minimum/maximum sampled thickness, not a certified global minimum. Useful for distance-offset TPMS and scan quality."""
  return await execute('measure_mesh_quality',{'model_id':model_id},ctx)
 @server.tool(annotations=write)
 async def build_lattice_mm(settings:LatticeMM,ctx:Context,model_id:str|None=None,expected_revision:StrictInt|None=None)->dict[str,Any]:
  """Generate TPMS using sampled Euclidean distance offsets targeting wall thickness in mm. Requires >=3 samples across thinnest wall. Returns validated meshes, grid spacing and distance uncertainty; no exact constant-thickness or smooth STEP claim."""
  return await execute('build_lattice_mm',dict(settings=settings.model_dump(mode='json'),model_id=model_id,expected_revision=expected_revision),ctx)
 @server.tool(annotations=write)
 async def refine_lattice(settings:AdaptiveLattice,ctx:Context)->dict[str,Any]:
  """Automatically select/refine global TPMS resolution and compare actual volume/density. Returns converged false on budget limits. This is global resolution adaptation, not spatial octree sampling."""
  return await execute('refine_lattice',{'settings':settings.model_dump(mode='json')},ctx)
 @server.tool(annotations=write)
 async def build_hybrid(model_id:str,settings:HybridSpec,ctx:Context,expected_revision:StrictInt|None=None)->dict[str,Any]:
  """Boolean union/intersection/difference of a distance-offset lattice with a named native part, preserving other parts. Native geometry is tessellated and result is mesh-only. No exact B-rep or smooth transition claim; trim inside imported STEP with intersection."""
  return await execute('build_hybrid',dict(model_id=model_id,settings=settings.model_dump(mode='json'),expected_revision=expected_revision),ctx)
 @server.tool(annotations=write)
 async def convert_mesh_to_cad(model_id:str,ctx:Context,maximum_faces:StrictInt=4000)->dict[str,Any]:
  """Explicit bounded conversion of a watertight mesh into sewn planar triangular B-rep solids and real STEP. <=8000 faces; no silent simplification or analytic TPMS fitting. Reopens STEP and checks volume. Creates a separate native model."""
  return await execute('convert_mesh_to_cad',dict(model_id=model_id,maximum_faces=maximum_faces),ctx)
 @server.tool(annotations=write)
 async def set_assembly_joints(model_id:str,settings:Assembly,ctx:Context,expected_revision:StrictInt|None=None)->dict[str,Any]:
  """Pose <=11 native parts using acyclic fixed/revolute/slider joints, mm/degrees and motion limits. Preserve original rest geometry for subsequent parameter changes. Checks every part-pair for overlap at this pose. No dynamics or continuous swept collision proof."""
  return await execute('set_assembly_joints',dict(model_id=model_id,settings=settings.model_dump(mode='json'),expected_revision=expected_revision),ctx)
 @server.tool(annotations=write)
 async def build_freeform(settings:Freeform,ctx:Context)->dict[str,Any]:
  """Create native CAD by lofting closed periodic interpolating B-spline sections with 4–64 points each. Supports ruled/smooth OCCT lofts. No general G2 patch continuity solver or sculpting claim."""
  return await execute('build_freeform',{'settings':settings.model_dump(mode='json')},ctx)
 @server.tool(annotations=read)
 def compare_designs(settings:Comparison)->dict[str,Any]:
  """Compare saved alternatives by actual volume, components, explicitly assumed mass density and available revision-bound verification reports. Never invent performance or manufacturability scores."""
  return engine.call('compare_designs',{'settings':settings.model_dump(mode='json')})
 @server.tool(annotations=write)
 async def reconstruct_geometry(settings:Reconstruction,ctx:Context)->dict[str,Any]:
  """Calibrate a PNG/JPEG silhouette and supplied depth, intersect 2–3 calibrated orthographic silhouette views into a visual hull, or import a closed STL scan in mm. Reports measured versus inferred data. No hidden geometry, perspective photogrammetry or automatic feature recovery."""
  return await execute('reconstruct_geometry',{'settings':settings.model_dump(mode='json')},ctx)
 @server.tool(annotations=read)
 def component_catalog()->dict[str,Any]:
  """List provenance-bearing nominal ISO4762 screw envelopes and a SKF608 bearing envelope. Simplified internals/threads are declared. Other supplier STEP parts can be imported; this is not a complete supplier database."""
  return engine.call('component_catalog',{})
 @server.tool(annotations=write)
 async def insert_component(component_id:str,ctx:Context,length_mm:StrictFloat=12,position:tuple[StrictFloat,StrictFloat,StrictFloat]=(0,0,0),model_id:str|None=None,expected_revision:StrictInt|None=None)->dict[str,Any]:
  """Create or insert a catalog component into a native assembly with nominal dimensions and source provenance. Does not model threads, bearing internals or certify fits."""
  return await execute('insert_component',dict(component_id=component_id,length_mm=length_mm,position=position,model_id=model_id,expected_revision=expected_revision),ctx)
 @server.tool(annotations=read)
 async def manufacturing_review(model_id:str,settings:Manufacturing,ctx:Context)->dict[str,Any]:
  """Native-part geometric screening for CNC directional visibility, mold draft or additive walls. Uses finite surface and wall samples, flags findings and does not certify cutter access, mold release, printability or production readiness."""
  return await execute('manufacturing_review',dict(model_id=model_id,settings=settings.model_dump(mode='json')),ctx)
 @server.tool(annotations=read)
 async def engineering_drawing(model_id:str,part_id:str,ctx:Context,title:str='Reference drawing',tolerance_note:str='')->dict[str,Any]:
  """Export an orthographic PDF from actual CAD with native overall dimensions and user tolerance note. Projection includes tessellated edges, not classified hidden lines or a complete GD&T production drawing."""
  return await execute('engineering_drawing',dict(model_id=model_id,part_id=part_id,title=title,tolerance_note=tolerance_note),ctx)
 @server.tool(annotations=write)
 async def build_sheet_metal(settings:SheetMetal,ctx:Context)->dict[str,Any]:
  """Build a real single cylindrical bend and a separate neutral-axis flat blank using explicit tangent leg lengths, bend radius/angle and K factor. No arbitrary imported-sheet unfolding or springback simulation."""
  return await execute('build_sheet_metal',{'settings':settings.model_dump(mode='json')},ctx)
 @server.tool(annotations=read)
 async def run_3d_simulation(model_id:str,settings:Simulation,ctx:Context)->dict[str,Any]:
  """Gmsh tetrahedra + scikit-fem: 3D steady conduction, small-strain linear elasticity, or incompressible creeping-flow Stokes P2/P1. Select one native solid; Axis extrema or revision-bound native faces define temperature, heat flux, convection, supports, displacement, force and pressure conditions. Explicit SI material/load inputs; CAD mm converted to m. Checks residual/conservation and optional mesh convergence; verified only when convergence passes. No turbulent/inertial CFD, contact, nonlinear mechanics or multiphysics. Returns VTU and viewer scalar overlay."""
  return await execute('run_3d_simulation',dict(model_id=model_id,settings=settings.model_dump(mode='json')),ctx)
 @server.tool(annotations=write)
 async def optimize_design(model_id:str,settings:Optimization,ctx:Context)->dict[str,Any]:
  """Evaluate 2–12 parameter candidates on separate models, preserving the original. Minimize volume or verified thermal/displacement/creeping-flow objectives, with optional constraints. Only converged physics candidates are feasible. No global optimum or topology-optimization claim. Prefer background jobs for many solves."""
  return await execute('optimize_design',dict(model_id=model_id,settings=settings.model_dump(mode='json')),ctx)
 @server.tool(annotations=read)
 def engineering_evidence(model_id:str)->dict[str,Any]:
  """Read revision/artifact-bound engineering reports and mark stale results. Does not validate stale physics against changed geometry."""
  return engine.call('engineering_evidence',{'model_id':model_id})
 @server.tool(annotations=write)
 def submit_engineering_job(operation:Literal['adaptive','simulate','optimize','convert','manufacture','drawing','freeform','sheet','lattice','hybrid','assembly','reconstruct'],settings:dict[str,Any],model_id:str|None=None)->dict[str,Any]:
  """Start a durable detached engineering job (<=3 active, <=15 minutes, each worker separately bounded). Use the corresponding tool's settings schema. Status/progress survive tool disconnects; stale queued edits are rejected. Cancellation preserves prior valid designs and completed artifacts."""
  return engine.call('submit_engineering_job',dict(operation=operation,settings=settings,model_id=model_id))
 @server.tool(annotations=read)
 def get_engineering_job(job_id:str,model_id:str|None=None)->dict[str,Any]:
  """Read persistent engineering job status, progress and results. Supplying model_id enforces ownership."""
  return engine.call('get_engineering_job',dict(job_id=job_id,model_id=model_id))
 @server.tool(annotations=write)
 def cancel_engineering_job(job_id:str,model_id:str|None=None)->dict[str,Any]:
  """Request cancellation of a bounded engineering job. A completed atomic edit remains in revision history."""
  return engine.call('cancel_engineering_job',dict(job_id=job_id,model_id=model_id))
