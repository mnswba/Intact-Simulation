"""Validated MCP SDK adapter for the private Intact CAD desktop plugin."""
from __future__ import annotations
from functools import partial
import json, os, threading
from pathlib import Path
from typing import Annotated, Any, Literal
from pydantic import Field, StrictFloat, StrictBool, StrictInt
import anyio
from mcp.server import MCPServer
from mcp.server.mcpserver import Context,Image
from mcp.types import ToolAnnotations
from .projects import ProjectService, EXPORTS
from .viewer_server import viewer_url, VERSION
from .spec import from_legacy, Study, MATERIALS
from .analysis import evaluate
from .program import SandboxUnavailable
from .edit_requests import EditRequests
from .interchange import FORMATS as INTERCHANGE_FORMATS
from .engineering_schema import Requirements,Sketch,Constraint,Geometry,Feature,Accuracy
from mcp.server.mcpserver.exceptions import ToolError

Revision=Annotated[StrictInt,Field(ge=1)]
ROOT=Path(os.environ.get('INTACT_STATE_DIR',Path.home()/'.local/share/intact-studio'))

class IntactMCP:
    def authorize(self,name,args):
        """Overridden by the model-scoped Ask AI server."""
        pass
    def __init__(self,root:Path=ROOT):
        self.root=Path(root);self.projects=ProjectService(self.root);self.programs=self.projects.programs;self.models=self.projects.models
    def load(self,key):return self.projects.load(key)
    def prepare(self,record):
        return self.projects.ensure_ready(record['model_id'])
    def viewer(self,key,revision=None):
        if not self.projects.path(key).exists():
            from .feature_graph import FeatureService
            FeatureService(self.projects).load(key)
        elif revision is None:self.prepare(self.load(key))
        else:self.projects.read_revision(key,revision)
        return viewer_url(self.root,key,revision)
    def result(self,record):
        record=self.prepare(record)
        key=record['model_id'];folder=self.programs.root/record['spec']['program']['artifact_id'];url=self.viewer(key)
        formats={k:v for k,v in EXPORTS.items() if k!='step' or record['geometry'].get('engine')!='implicit_mesh'}
        return {'model_id':key,'name':record['name'],'revision':record['spec']['revision'],'geometry':record['geometry'],'viewer_url':url,'files':{n:str(self.projects.artifact(key,n)) for n in formats.values() if n!='project.json'},'downloads':{kind:url.removesuffix('view')+filename for kind,filename in formats.items()},'source_step_url':url.removesuffix('view')+'input.step' if record['spec']['program'].get('asset_id') and record['geometry'].get('asset_name','input.step')=='input.step' else None,'next':'Call validate_model with requested dimensions, inspect snapshot_model (multiple views for assemblies), then return viewer and export links. Revision clicks preview history; restore_revision is an explicit recovery operation.'}
    def call(self,name,args,cancel_event=None):
        try:return self._call(name,args,cancel_event)
        except (ValueError,OSError,SandboxUnavailable) as exc:raise ToolError(str(exc)[:4000]) from exc
    def _call(self,name,args,cancel_event=None):
        from .interactive_mcp import NAMES as INTERACTIVE,dispatch as interactive_dispatch
        if name in INTERACTIVE:return interactive_dispatch(self,name,args,cancel_event)
        from .advanced_mcp import NAMES,dispatch
        if name in NAMES:return dispatch(self,name,args,cancel_event)
        if name in ('set_design_requirements','get_design_requirements','create_sketch','set_sketch_constraints','solve_sketch','get_feature_tree','edit_feature_tree','rebuild_features'):
            from .feature_graph import FeatureService
            f=FeatureService(self.projects)
            if name=='set_design_requirements':return f.requirements(args.get('model_id'),args['requirements'],args.get('name'),args.get('expected_revision'))
            if name in ('get_design_requirements','get_feature_tree'):return f.get(args['model_id'])
            if name=='create_sketch':return f.create_sketch(args.get('model_id'),args['sketch'],args.get('expected_revision'),args.get('name'),args.get('parameters'))
            if name=='set_sketch_constraints':return f.constraints(args['model_id'],args['sketch_id'],args['constraints'],args.get('expected_revision'),args.get('geometry'))
            if name=='solve_sketch':return f.solve(args['model_id'],args.get('sketch_id'),cancel_event)
            if name=='edit_feature_tree':
                r=f.edit(args['model_id'],args['features'],args.get('parameters'),args.get('mode','replace'),args.get('expected_revision'),args.get('rebuild',True),cancel_event)
            else:r=f.rebuild(args['model_id'],expected_revision=args.get('expected_revision'),cancel_event=cancel_event)
            return self.result(r) if 'spec' in r else r
        if name=='bind_reference':
            from .stable_references import bind
            return bind(self.projects,args['model_id'],args['reference'],args['label'],args['revision'],args['artifact_id'])
        if name=='verify_design':
            from .design_checks import verify_design
            return verify_design(self.projects,args['model_id'])
        if name=='set_accuracy':
            from .accuracy import set_accuracy
            r=set_accuracy(self.projects,args['model_id'],args['settings'],args.get('expected_revision'),cancel_event)
            return self.result(r) if 'spec' in r else r
        if name=='check_accuracy':
            from .accuracy import check_accuracy
            return check_accuracy(self.projects,args['model_id'],args.get('convergence',True),cancel_event)
        if name=='status':
            from .feature_graph import FreeCADRuntime
            from .picogk import readiness
            return {'picogk':readiness(),'structured_design':FreeCADRuntime(self.projects).status(),'version':VERSION,'cad_ready':self.programs.available(),'engine':'build123d 0.13 / OpenCASCADE + distance/implicit TPMS meshes + Manifold','agent':'ChatGPT conversation tools and user-triggered, model-scoped Ask AI tasks; no external model service','analysis':['kinematic driving/walking/machine previews','3D steady conduction','3D linear elasticity','3D creeping-flow Stokes','1D rectangular beam FEM','1D single-fin thermal FVM'],'unavailable':['turbulent/inertial CFD','nonlinear/contact solid FEA and multiphysics','smooth analytic TPMS STEP fitting','general photogrammetry'],'state_directory':str(self.root),'exports':list(EXPORTS)+list(INTERCHANGE_FORMATS),'limits':{'named_parts':128,'source_bytes':120000,'numeric_parameters':150,'preview_triangles':1200000,'tpms_samples':2500000,'worker_seconds':120,'simulation_tetrahedra':18000,'engineering_jobs':3}}
        if name=='import_cad':return self.result(self.projects.import_cad(args['path'],cancel_event))
        if name=='resolve_references':
            refs=args['references']
            if refs and all(ref.startswith('stable:') for ref in refs):
                from .stable_references import resolve
                return resolve(self.projects,args['model_id'],refs)
            return EditRequests(self.projects).resolve(args['model_id'],refs,args.get('revision'),args.get('artifact_id'))
        if name=='list_edit_requests':return {'requests':EditRequests(self.projects).list(args['model_id'])}
        if name=='apply_edit_request':return self.result(EditRequests(self.projects).apply(args['model_id'],args['request_id'],args['source'],args['parameters'],cancel_event))
        if name=='list_models':return {'models':self.projects.list()}
        if name=='get_model':
            if not self.projects.path(args['model_id']).exists():
                from .feature_graph import FeatureService
                return FeatureService(self.projects).get(args['model_id'])
            return self.projects.read_revision(args['model_id'],args['revision']) if args.get('revision') is not None else self.load(args['model_id'])
        if name=='open_viewer':return {'url':self.viewer(args['model_id'],args.get('revision')),'note':'Historical views are read-only. The persistent viewer survives tool disconnection.'}
        if name=='build_model':return self.result(self.projects.build(**args,cancel_event=cancel_event))
        if name=='build_tpms':
            from .lattice_tools import build_tpms
            return self.result(build_tpms(self.projects,args,cancel_event))
        if name=='validate_model':
            from .validation import validate_model
            result=validate_model(self.projects,**args)
            if self.load(args['model_id']).get('engineering',{}).get('requirements',{}).get('checks'):
                from .design_checks import verify_design
                result['design_checks']=verify_design(self.projects,args['model_id']);result['passed']=result['passed'] and result['design_checks']['passed']
            return result
        if name=='update_parameters':return self.result(self.projects.parameters(args['model_id'],args['parameters'],cancel_event,args.get('expected_revision')))
        if name=='set_appearance':return self.projects.appearance(args['model_id'],args['part_id'],args.get('color'),args.get('material'),args.get('name'))
        if name=='revisions':return {'revisions':self.projects.revisions(args['model_id'])}
        if name=='restore_revision':return self.result(self.projects.restore(args['model_id'],args['revision']))
        if name=='import_project':return self.result(self.projects.import_project(args['path']))
        if name=='measure_model':
            r=self.load(args['model_id']);return {'units':'mm','engine':r['geometry']['engine'],'program_parameters':r['spec']['program']['parameters'],'parts':[{'id':p['id'],'name':p['name'],'bounds':{k:p['params'][k] for k in ('length','width','height')},'position':p['position'],**p['measurements']} for p in r['spec']['parts']]}
        if name=='export_model':
            key=args['model_id'];kind=args['format']
            if kind not in EXPORTS and kind not in INTERCHANGE_FORMATS:raise ValueError('Unsupported export format.')
            filename=({**EXPORTS,**INTERCHANGE_FORMATS})[kind];url=self.viewer(key).removesuffix('view')+filename
            return {'format':kind,'url':url,'path':str(self.projects.artifact(key,filename)) if kind!='project' else None,'assembled':True}
        if name=='analyze_reference':
            if args.get('approved') is not True:raise ValueError('Review and approve the analysis dimensions, material and boundary conditions first.')
            kind=args['kind']
            if kind not in ('beam','fin'):raise ValueError('Choose beam or fin; general geometry and CFD are not supported by this reference adapter.')
            study={**args['study'],'type':'mechanical' if kind=='beam' else 'thermal'}
            spec=from_legacy({**{k:args[k] for k in ('kind','length','width','height','material')},'name':'Reference study','holeDiameter':6,'finCount':9},study)
            spec.simulation.approved_fingerprint=spec.content_hash();analysis=evaluate(spec)
            source='import build123d as bd\ndef build(params):\n    return {"reference":bd.Box(params["length"],params["width"],params["height"])}'
            record=self.projects.build(source,{k:args[k] for k in ('length','width','height')},name='Cantilever reference study' if kind=='beam' else 'Cooling fin reference study',cancel_event=cancel_event)
            record['spec']['parts'][0]['material']=args['material'];record['analysis']={**analysis,'reference_spec':spec.model_dump(mode='json')}
            record=self.projects.commit(record,record['spec']['revision'])
            return {**analysis,'model_id':record['model_id'],'viewer_url':self.viewer(record['model_id'])}
        raise ValueError('Unknown tool.')

def create_server(engine:IntactMCP|None=None):
    engine=engine or IntactMCP()
    server=MCPServer('intact-simulation',version=VERSION,instructions='AI runs in this ChatGPT conversation. Create real CAD using build_model, or sampled lattices with build_tpms. Validate actual exports with validate_model using the brief dimensions, inspect snapshots from useful views, then deliver links. Preview history using revision arguments; restore only on explicit request. Mesh lattices cannot export exact STEP. Never present reduced 1D studies as general FEA or CFD.',log_level='WARNING')
    read=ToolAnnotations(read_only_hint=True,destructive_hint=False,open_world_hint=False)
    write=ToolAnnotations(read_only_hint=False,destructive_hint=False,open_world_hint=False)
    async def execute(name,args,ctx):
        cancel=threading.Event()
        try:
            await ctx.report_progress(0,100,'Running '+name.replace('_',' '))
            result=await anyio.to_thread.run_sync(partial(engine.call,name,args,cancel),abandon_on_cancel=True)
            await ctx.report_progress(100,100,'Finished '+name.replace('_',' '));return result
        except BaseException:
            cancel.set();raise
    @server.tool(annotations=write)
    def set_design_requirements(requirements:Requirements,model_id:str|None=None,name:str|None=None,expected_revision:Revision|None=None)->dict[str,Any]:
        """Save acceptance criteria and explicit assumptions. Omit model_id to create an empty design draft (no placeholder geometry). All lengths are mm. Check kinds: bounds {length,width,height}, part_count {count}, hole_pattern {count,diameter_mm,depth_mm,through,centers_mm,axis}, clearance {min_mm}, interference {max_volume_mm3}, wall_thickness {min_mm,allow_sampled}. Native through/depth checks use exported STEP. Global wall minimum is unverified unless an explicitly sampled criterion is acceptable. Returns model_id and design revision."""
        return engine.call('set_design_requirements',dict(requirements=requirements.model_dump(mode='json'),model_id=model_id,name=name,expected_revision=expected_revision))
    @server.tool(annotations=read)
    def get_design_requirements(model_id:str)->dict[str,Any]:
        """Read saved intent, acceptance checks, assumptions and accuracy settings for a model or design draft."""
        return engine.call('get_design_requirements',{'model_id':model_id})
    @server.tool(annotations=write)
    def create_sketch(sketch:Sketch,model_id:str|None=None,name:str|None=None,parameters:dict[str,StrictFloat]|None=None,expected_revision:Revision|None=None)->dict[str,Any]:
        """Create a named constrained sketch in XY/XZ/YZ, with line/circle/arc geometry and stable entity IDs. Omit model_id for a new empty draft. Constraints reference geometry IDs; points 1=start,2=end,3=circle center. Dimensional values may use {parameter:name}; angles are degrees. Provide parameters before solving. This saves a draft, not a solid. solve_sketch reports exact remaining DoF and conflicts; rebuild_features creates actual CAD."""
        return engine.call('create_sketch',dict(sketch=sketch.model_dump(mode='json'),model_id=model_id,name=name,parameters=parameters,expected_revision=expected_revision))
    @server.tool(annotations=write)
    def set_sketch_constraints(model_id:str,sketch_id:str,constraints:list[Constraint],geometry:list[Geometry]|None=None,expected_revision:Revision|None=None)->dict[str,Any]:
        """Replace a sketch's constraint list; optionally replace its geometry. Supports coincidence, horizontal/vertical, parallel/perpendicular, equal, tangent, dimensions, angle, point-on-object and explicit lock. Does not silently rebuild or change current solid geometry. Solve, then rebuild features. Conflicting drafts can be repaired without losing the last valid CAD."""
        return engine.call('set_sketch_constraints',dict(model_id=model_id,sketch_id=sketch_id,constraints=[c.model_dump(mode='json') for c in constraints],geometry=[g.model_dump(mode='json') for g in geometry] if geometry is not None else None,expected_revision=expected_revision))
    @server.tool(annotations=read)
    async def solve_sketch(model_id:str,ctx:Context,sketch_id:str|None=None)->dict[str,Any]:
        """Solve sketches in isolated FreeCAD 1.1.4 and return actual DoF, conflict/redundancy diagnostics and solved geometry. Read-only: no new revisions. A successful solve can still have remaining DoF; feature builds require fully constrained sketches unless explicitly allowed otherwise."""
        return await execute('solve_sketch',dict(model_id=model_id,sketch_id=sketch_id),ctx)
    @server.tool(annotations=read)
    def get_feature_tree(model_id:str)->dict[str,Any]:
        """Read the explicit feature dependency graph, sketch constraints, parameters, suppression, attachment state and native rebuild diagnostics. Opaque Python/STEP inputs do not acquire a recovered feature history automatically."""
        return engine.call('get_feature_tree',{'model_id':model_id})
    @server.tool(annotations=write)
    async def edit_feature_tree(model_id:str,features:list[Feature],ctx:Context,parameters:dict[str,StrictFloat]|None=None,mode:Literal['replace','upsert']='replace',rebuild:StrictBool=True,expected_revision:Revision|None=None)->dict[str,Any]:
        """Transactionally edit and optionally rebuild an ordered feature graph. Supports extrude {height,direction}, revolve {angle_deg,origin,axis}, hole {diameter,depth,through,centers,axis}, fillet {radius,edges}, chamfer {distance,edges}, boolean {operation}, pattern {count,step,fuse}, transform {translation,axis,angle_deg,origin}. Numeric params accept {parameter:name}. Assign part_id to output tips; base/tool refer to earlier feature IDs. Edge selectors use geometry, radius, at, direction, all, tolerance_mm; ambiguous picks fail. Suppression aliases a feature to its base. Failed CAD preserves the saved graph/solid; rebuild=false stages an explicitly detached draft graph."""
        return await execute('edit_feature_tree',dict(model_id=model_id,features=[f.model_dump(mode='json') for f in features],parameters=parameters,mode=mode,rebuild=rebuild,expected_revision=expected_revision),ctx)
    @server.tool(annotations=write)
    async def rebuild_features(model_id:str,ctx:Context,expected_revision:Revision|None=None)->dict[str,Any]:
        """Re-solve and rebuild the saved graph, export native STEP, validate the bridge and refresh the viewer. Returns real CAD and persistent download links. No arbitrary source/shell commands run in the FreeCAD worker."""
        return await execute('rebuild_features',dict(model_id=model_id,expected_revision=expected_revision),ctx)
    @server.tool(annotations=write)
    def bind_reference(model_id:str,reference:str,label:str,revision:Revision,artifact_id:str)->dict[str,Any]:
        """Bind an inspected native part/face/edge to a stable:label handle. Hole faces can track their feature and center index across diameter edits. Other references use unique geometric signatures. A reference may become missing or ambiguous; resolution then fails rather than selecting a different entity silently."""
        return engine.call('bind_reference',dict(model_id=model_id,reference=reference,label=label,revision=revision,artifact_id=artifact_id))
    @server.tool(annotations=read)
    async def verify_design(model_id:str,ctx:Context)->dict[str,Any]:
        """Check saved design intent against the actual exported native solid: hole count/diameter/location/depth/through state, bounds/components, clearance/interference, and sampled wall thickness. Results are pass/fail/unverified with provenance. Missing acceptance criteria never count as verified. Does not certify manufacturing or physics."""
        return await execute('verify_design',{'model_id':model_id},ctx)
    @server.tool(annotations=write)
    async def set_accuracy(model_id:str,settings:Accuracy,ctx:Context,expected_revision:Revision|None=None)->dict[str,Any]:
        """Save dimensional/meshing/convergence tolerances and rebuild with bounded linear/angular tessellation settings. Values are targets; use check_accuracy for measured results. Does not claim that tighter inputs improve the CAD kernel's physical accuracy."""
        return await execute('set_accuracy',dict(model_id=model_id,settings=settings.model_dump(mode='json'),expected_revision=expected_revision),ctx)
    @server.tool(annotations=read)
    async def check_accuracy(model_id:str,ctx:Context,convergence:StrictBool=True)->dict[str,Any]:
        """Measure native B-rep tolerances, exact-to-STL volume error and optionally two-resolution volume/area convergence in an isolated worker. Does not modify saved geometry or revisions. Unsupported/refinement-budget cases are unverified, not successful. No claim of globally bounded TPMS error or fabrication tolerance."""
        return await execute('check_accuracy',dict(model_id=model_id,convergence=convergence),ctx)
    @server.tool(annotations=read)
    def status()->dict[str,Any]:
        """Check the installed CAD runtime, available exports and analysis scope."""
        return engine.call('status',{})
    @server.tool(annotations=read)
    def list_models()->dict[str,Any]:
        """List saved local CAD models and their current revisions."""
        return engine.call('list_models',{})
    @server.tool(annotations=read)
    def get_model(model_id:str,revision:Revision|None=None)->dict[str,Any]:
        """Read saved source and facts. Optional revision previews history without creating a revision."""
        return engine.call('get_model',{'model_id':model_id,'revision':revision})
    @server.tool(annotations=write)
    async def build_model(source:str,parameters:dict[str,StrictFloat],ctx:Context,name:str|None=None,model_id:str|None=None,expected_revision:Revision|None=None)->dict[str,Any]:
        """Build real CAD using build123d 0.13 and build(params). Return Shape/BuildPart or <=128 named parts, IDs [a-z][a-z0-9_]{0,47}. Imports: build123d, math, numpy, intact_lattice. Source <=120KB, <=150 numeric parameters. intact_lattice.tpms creates implicit mesh parts (STL/GLB/3MF; no exact STEP). No file I/O. Supply model_id and expected_revision to edit. Failed builds preserve saved CAD. Verify requested dimensions with validate_model and actual snapshot_model views."""
        return await execute('build_model',{'source':source,'parameters':parameters,'name':name,'model_id':model_id,'expected_revision':expected_revision},ctx)
    @server.tool(annotations=write)
    async def build_tpms(ctx:Context,family:Literal['gyroid','schwarz_p','diamond','neovius','lidinoid','split_p']='gyroid',length:StrictFloat=30,width:StrictFloat=30,height:StrictFloat=30,cell_size:StrictFloat=10,band:StrictFloat=.3,level:StrictFloat=0,samples_per_cell:StrictInt=20,mode:Literal['sheet','solid']='sheet',envelope:Literal['box','cylinder','sphere']='box',phase_x:StrictFloat=0,phase_y:StrictFloat=0,phase_z:StrictFloat=0,gradient:StrictFloat=0,name:str|None=None,model_id:str|None=None,expected_revision:Revision|None=None)->dict[str,Any]:
        """Create an editable, capped, watertight nodal TPMS lattice in mm. Six families; box, cylinder or sphere envelopes; sheet or solid mode; phase degrees and sheet gradient. Band is a dimensionless implicit field width, NOT constant wall thickness in mm. samples_per_cell 12–64; <=2.5M grid samples. Exports STL/GLB/3MF and standalone Python; exact STEP is unavailable. Report sampled volume, area, relative density and resolution. Existing model_id edits preserve revision guards. Verify with validate_model and snapshot_model."""
        args={k:v for k,v in locals().items() if k not in ('ctx','execute')}
        return await execute('build_tpms',args,ctx)
    @server.tool(annotations=read)
    def validate_model(model_id:str,expected_bounds:dict[str,dict[str,StrictFloat]]|None=None,expected_part_ids:list[str]|None=None,tolerance_mm:StrictFloat=.01)->dict[str,Any]:
        """Independently reopen actual STEP or STL, check validity, volume/area/labels and checksums, and compare requested per-part length/width/height in CAD XYZ mm. Return actual curved face radii/centers for hole checks. Supply expected dimensions from the user's brief, not copied measurements. A false passed result needs repair or disclosure. Does not certify manufacturing or engineering safety."""
        return engine.call('validate_model',{'model_id':model_id,'expected_bounds':expected_bounds,'expected_part_ids':expected_part_ids,'tolerance_mm':tolerance_mm})
    @server.tool(annotations=write)
    async def update_parameters(model_id:str,parameters:dict[str,StrictFloat|str],ctx:Context,expected_revision:Revision|None=None)->dict[str,Any]:
        """Merge numeric or bounded arithmetic parameter changes into saved CAD source and rebuild. Expressions accept existing parameter names, parentheses and + - * / only; no functions or implicit units. Preserves model name and part colors; failed builds do not change the saved model."""
        return await execute('update_parameters',{'model_id':model_id,'parameters':parameters,'expected_revision':expected_revision},ctx)
    @server.tool(annotations=write)
    def set_appearance(model_id:str,part_id:str,color:str|None=None,material:Literal['aluminum','steel','copper']|None=None,name:str|None=None)->dict[str,Any]:
        """Save a part's hex color, material or label. Geometry remains assembled."""
        return engine.call('set_appearance',{'model_id':model_id,'part_id':part_id,'color':color,'material':material,'name':name})
    @server.tool(annotations=read)
    def revisions(model_id:str)->dict[str,Any]:
        """List saved project revisions available for recovery."""
        return engine.call('revisions',{'model_id':model_id})
    @server.tool(annotations=write)
    def restore_revision(model_id:str,revision:Revision)->dict[str,Any]:
        """Restore a saved revision as a new revision, preserving the history."""
        return engine.call('restore_revision',{'model_id':model_id,'revision':revision})
    @server.tool(annotations=write)
    def open_viewer(model_id:str,revision:Revision|None=None)->dict[str,Any]:
        """Start or reuse the persistent local viewer and return its URL. Supports cut/cap, color, visibility, explode, parameters, measurements, revisions and exports."""
        return engine.call('open_viewer',{'model_id':model_id,'revision':revision})
    @server.tool(annotations=read)
    def measure_model(model_id:str)->dict[str,Any]:
        """Read exact saved kernel volume, surface area, bounding dimensions, solid and face counts by part."""
        return engine.call('measure_model',{'model_id':model_id})
    @server.tool(annotations=write)
    async def snapshot_model(model_id:str,ctx:Context,view:Literal['current','iso','front','back','top','bottom','right','left']='current',revision:Revision|None=None)->Image:
        """Render and return an actual PNG of the CAD model for visual inspection in ChatGPT. Captures saved colors, sections and explosion without modifying the user's camera settings."""
        from .snapshot import snapshot
        import time
        try:
            engine.authorize('snapshot_model',{'model_id':model_id})
            url=await anyio.to_thread.run_sync(engine.viewer,model_id,revision)
            await ctx.report_progress(0,100,'Rendering CAD snapshot')
            output=engine.models/model_id/'snapshots'/(str(time.time_ns())+'-'+view+'.png')
            png=await snapshot(url,output,view)
            await ctx.report_progress(100,100,'CAD snapshot ready')
            return Image(data=png,format='png')
        except Exception as exc:raise ToolError('Snapshot failed: '+str(exc)[:2000]) from exc
    @server.tool(annotations=write)
    def export_model(model_id:str,format:Literal['step','stl','stl_ascii','stl_binary','glb','3mf','python','project','usd','usda'])->dict[str,Any]:
        """Return a persistent download URL and local path for the assembled model. Supports explicit ASCII/binary STL and binary USD/text USDA mesh scenes with millimeter scale. STEP is native B-rep; USD and STL are tessellated."""
        return engine.call('export_model',{'model_id':model_id,'format':format})
    @server.tool(annotations=write)
    async def import_project(path:str,ctx:Context)->dict[str,Any]:
        """Import an Intact version 2 project JSON. Rebuild and validate its Python CAD instead of trusting imported mesh or measurements."""
        return await execute('import_project',{'path':path},ctx)
    @server.tool(annotations=write)
    async def import_cad(path:str,ctx:Context)->dict[str,Any]:
        """Import a local STEP/STP assembly with native colors, named parts and face/edge topology. Accepts Linux paths and Windows drive paths such as C:\\Users\\User\\Downloads\\part.step. Editing programs can use imported_parts (dict) and input_shape without file I/O."""
        return await execute('import_cad',{'path':path},ctx)
    @server.tool(annotations=read)
    def resolve_references(model_id:str,references:list[str],revision:Revision|None=None,artifact_id:str|None=None)->dict[str,Any]:
        """Resolve selected part/face/edge/vertex IDs to exact OpenCASCADE geometry facts in CAD XYZ millimeters. Native IDs require their revision/artifact. stable:label handles are re-resolved without those arguments; ambiguous/deleted matches are rejected."""
        return engine.call('resolve_references',dict(model_id=model_id,references=references,revision=revision,artifact_id=artifact_id))
    @server.tool(annotations=read)
    def list_edit_requests(model_id:str)->dict[str,Any]:
        """Read queued geometry edits created in the viewer's Ask AI panel, including statuses and errors."""
        return engine.call('list_edit_requests',{'model_id':model_id})
    @server.tool(annotations=read)
    def read_edit_request(model_id:str,request_id:str)->list:
        """Read selected native geometry, edit instructions, current Python and attached reference/sketch images. Inspect the images before writing the edit; reject stale requests."""
        from mcp.types import TextContent
        import base64
        try:
            engine.authorize('read_edit_request',{'model_id':model_id,'request_id':request_id})
            r=EditRequests(engine.projects).read(model_id,request_id)
            images=r.pop('images');shot=r.pop('screenshot');content=[TextContent(type='text',text=json.dumps(r))]
            for item in images+([shot] if shot else []):
                header,encoded=item['data_url'].split(',',1)
                content.append(Image(data=base64.b64decode(encoded),format='png' if 'image/png' in header else 'jpeg').to_image_content())
            return content
        except (ValueError,OSError) as exc:raise ToolError(str(exc)) from exc
    @server.tool(annotations=write)
    def respond_to_edit_request(model_id:str,request_id:str,message:str,needs_reply:StrictBool=False)->dict[str,Any]:
        """Publish an answer or clarification to the Ask AI viewer. Read the request first. Set needs_reply for a clarification; after edits validate and inspect the result before reporting completion. Does not modify geometry."""
        try:
            engine.authorize('respond_to_edit_request',{'model_id':model_id,'request_id':request_id})
            return EditRequests(engine.projects).respond(model_id,request_id,message,needs_reply)
        except (ValueError,OSError) as exc:raise ToolError(str(exc)) from exc
    @server.tool(annotations=write)
    async def apply_edit_request(model_id:str,request_id:str,source:str,parameters:dict[str,StrictFloat],ctx:Context)->dict[str,Any]:
        """Apply a viewer edit request using revised build(params) Python. Preserves the previous model on failure, rejects stale selections, records completion and refreshes the open viewer. Preserve unrelated assembly parts. Inspect snapshot_model afterward."""
        return await execute('apply_edit_request',dict(model_id=model_id,request_id=request_id,source=source,parameters=parameters),ctx)
    from .advanced_mcp import register
    register(server,engine,execute,read,write)
    from .interactive_mcp import register as register_interactive
    register_interactive(server,engine,execute,read,write)
    return server

def main():create_server().run(transport='stdio')
if __name__=='__main__':main()
