# SPDX-License-Identifier: Apache-2.0
"""Priority 2/3 services: isolated geometry/PDE work and revision-bound evidence."""
import json,math,shutil,tempfile,uuid
from pathlib import Path
from .projects import atomic_json,local_path
from .isolated_worker import run_worker
from .p23_schema import *

class Advanced:
 def __init__(self,projects):self.projects=projects;self.root=projects.root/'engineering';self.root.mkdir(exist_ok=True)
 def native(self,key):
  r=self.projects.ensure_ready(key)
  if r['geometry']['engine']=='implicit_mesh':raise ValueError('This operation requires native STEP geometry. Convert a bounded mesh explicitly first.')
  return r
 def worker(self,key,spec,worker='advanced_worker.py',files=None,cancel=None):
  r=self.projects.ensure_ready(key) if key else None
  if r and (spec.get('source_revision') is not None and spec['source_revision']!=r['spec']['revision'] or spec.get('source_artifact') is not None and spec['source_artifact']!=r['spec']['program']['artifact_id']):raise ValueError('Simulation geometry changed before the worker started.')
  fingerprint=uuid.uuid4().hex;target=self.root/fingerprint;target.mkdir()
  with tempfile.TemporaryDirectory(prefix='intact-engineering-') as tmp:
   i=Path(tmp)/'input';o=Path(tmp)/'output';i.mkdir();o.mkdir()
   if key:
    for name in ('model.step','model.stl','mesh.json','topology.json'):
     if name=='model.step' and r['geometry']['engine']=='implicit_mesh':continue
     shutil.copyfile(self.projects.record_artifact(r,name),i/name)
   for name,path in (files or {}).items():shutil.copyfile(path,i/name)
   if r:(i/'model.json').write_text(json.dumps({'model_id':key,'name':r['name'],'spec':{'parts':r['spec']['parts'],'revision':r['spec']['revision']}}))
   shutil.copyfile(Path(__file__).with_name('intact_lattice.py'),i/'intact_lattice.py');(i/'request.json').write_text(json.dumps(spec,allow_nan=False))
   import sys
   env={'LD_LIBRARY_PATH':str(Path(sys.prefix)/'intact-native-libs'),'PYTHONPATH':'/input'}
   result=run_worker(self.projects.programs,Path(__file__).with_name(worker),i,o,env=env,cancel_event=cancel,timeout=180)
   if cancel and cancel.is_set():raise ValueError('Cancelled; saved model preserved.')
   for p in o.iterdir():
    if p.is_file() and p.stat().st_size<=64*1024**2:shutil.copyfile(p,target/p.name)
  result.update(report_id=fingerprint,model_id=key,revision=r['spec']['revision'] if r else None,artifact_id=r['spec']['program']['artifact_id'] if r else None)
  atomic_json(target/'report.json',result)
  if key:atomic_json(self.root/(key+'-'+(spec['kind']+'-simulation' if worker=='simulation_worker.py' else spec.get('operation','motion'))+'.json'),result)
  return result,target
 def evidence(self,key):
  r=self.projects.load(key);items=[];seen=set()
  for p in self.root.glob(key+'-*.json'):
   v=json.loads(p.read_text());v={k:x for k,x in v.items() if k not in ('positions_mm','triangles','values','fields','frames')};v['stale']=v.get('artifact_id')!=r['spec']['program']['artifact_id']
   if v['report_id'] not in seen:items.append(v);seen.add(v['report_id'])
  return {'model_id':key,'reports':items}
 def lattice(self,settings,model_id=None,expected_revision=None,cancel=None):
  s=LatticeMM.model_validate(settings);p=s.model_dump(mode='json');source='from intact_lattice import tpms_mm\ndef build(params):\n    return {"lattice":tpms_mm('+repr(s.family)+',size='+repr(tuple(s.size))+',cell_size=params["cell"],thickness_mm=params["thickness"],samples_per_cell=int(params["samples"]),gradient=params["gradient"])}'
  return self.projects.build(source,{'cell':s.cell_size,'thickness':s.thickness_mm,'samples':s.samples_per_cell,'gradient':s.gradient},model_id=model_id,name=None if model_id else 'Distance-offset lattice',expected_revision=expected_revision,cancel_event=cancel)
 def adaptive(self,settings,cancel=None):
  s=AdaptiveLattice.model_validate(settings);levels=[];previous=None;last=None;n=s.samples_per_cell
  while n<=s.maximum_samples_per_cell:
   if cancel and cancel.is_set():raise ValueError('Refinement cancelled.')
   params=LatticeMM.model_validate({k:v for k,v in s.model_dump(mode='json').items() if k in LatticeMM.model_fields});params.samples_per_cell=n
   try:r=self.lattice(params.model_dump(mode='json'),cancel=cancel)
   except ValueError as e:
    if last:break
    if 'under-resolved' in str(e) and n<s.maximum_samples_per_cell:n=min(s.maximum_samples_per_cell,n*2);continue
    raise
   volume=sum(p['volume_mm3'] for p in r['geometry']['parts']);change=abs(volume-previous)/volume if previous else None;levels.append({'samples_per_cell':n,'model_id':r['model_id'],'volume_mm3':volume,'relative_change':change,'relative_density':r['geometry']['parts'][0].get('relative_density')});last=r
   if change is not None and change<=s.relative_tolerance:break
   previous=volume
   if n==s.maximum_samples_per_cell:break
   n=min(s.maximum_samples_per_cell,n*2)
  if last is None:raise ValueError('No valid refinement level.')
  return {'model':last,'levels':levels,'converged':levels[-1]['relative_change'] is not None and levels[-1]['relative_change']<=s.relative_tolerance,'scope':'Automatic global refinement selected for thin/curved lattice geometry; not local octree refinement or a global thickness proof.'}
 def hybrid(self,key,settings,expected_revision=None,cancel=None):
  s=HybridSpec.model_validate(settings);r=self.native(key);part=s.part_id
  if part not in [p['id'] for p in r['spec']['parts']]:raise ValueError('Native part not found.')
  asset=self.projects.store_step(self.projects.artifact(key,'model.step').read_bytes(),max_bytes=32*1024**2)
  source='import build123d as bd\nfrom intact_lattice import tpms_mm,hybrid\ndef build(params):\n    parts=dict(imported_parts)\n    lattice=tpms_mm('+repr(s.family)+',size='+repr(tuple(s.size))+',cell_size=params["cell"],thickness_mm=params["thickness"],samples_per_cell=int(params["samples"]),gradient=params["gradient"])\n    lattice.mesh.apply_translation('+repr(tuple(s.translation))+')\n    parts['+repr(part)+']=hybrid(parts['+repr(part)+'],lattice,'+repr(s.operation)+',tolerance='+repr(s.tessellation_mm)+')\n    return parts'
  return self.projects.build(source,{'cell':s.cell_size,'thickness':s.thickness_mm,'samples':s.samples_per_cell,'gradient':s.gradient},model_id=key,expected_revision=expected_revision if expected_revision is not None else r['spec']['revision'],asset_id=asset,cancel_event=cancel)
 def convert(self,key,maximum_faces=4000,cancel=None):
  if isinstance(maximum_faces,bool) or not 4<=maximum_faces<=8000:raise ValueError('maximum_faces must be 4–8000.')
  result,folder=self.worker(key,{'operation':'convert','maximum_faces':maximum_faces},cancel=cancel)
  r=self.projects.import_cad(folder/'result.step',cancel_event=cancel);return {'model':r,'conversion':result}
 def freeform(self,settings,cancel=None):
  s=Freeform.model_validate(settings)
  if any(not 4<=len(section)<=64 for section in s.sections):raise ValueError('Each closed section needs 4–64 interpolation points.')
  source='import build123d as bd\ndef build(params):\n    sections='+repr(s.sections)+'\n    profiles=[bd.Face(bd.Wire(bd.Spline(*points,periodic=True))) for points in sections]\n    return {"freeform":bd.loft(profiles,ruled='+repr(s.ruled)+')}'
  return self.projects.build(source,{},name='Interpolated freeform loft',cancel_event=cancel)
 def simulate(self,key,settings,cancel=None):
  record=self.native(key);s=Simulation.model_validate(settings)
  if s.part_id not in [p['id'] for p in record['spec']['parts']]:raise ValueError('Simulation part not found.')
  if s.source_revision is not None and s.source_revision!=record['spec']['revision'] or s.source_artifact is not None and s.source_artifact!=record['spec']['program']['artifact_id']:raise ValueError('Simulation definition belongs to stale geometry. Review the boundaries on the current model.')
  result,_=self.worker(key,s.model_dump(mode='json'),'simulation_worker.py',cancel=cancel);return result
 def manufacture(self,key,settings,cancel=None):
  self.native(key);s=Manufacturing.model_validate(settings)
  if sum(x*x for x in s.direction)<1e-12:raise ValueError('Tool/pull direction cannot be zero.')
  result,_=self.worker(key,{'operation':'manufacturing',**s.model_dump(mode='json')},cancel=cancel);return result
 def mesh_quality(self,key,cancel=None):
  result,_=self.worker(key,{'operation':'mesh_quality'},cancel=cancel);return result
 def drawing(self,key,part_id,title='Intact reference drawing',tolerance_note='',cancel=None):
  self.native(key)
  if len(title)>100 or len(tolerance_note)>200:raise ValueError('Drawing title/note is too long.')
  result,_=self.worker(key,{'operation':'drawing','part_id':part_id,'title':title,'tolerance_note':tolerance_note},cancel=cancel);return result
 def reconstruct(self,settings,cancel=None):
  s=Reconstruction.model_validate(settings)
  if s.mode=='orthographic_hull':
   if len(s.views)<2 or any(v<=0 or v>1000 for v in s.size_mm):raise ValueError('Supply 2–3 calibrated orthographic silhouettes and positive XYZ dimensions <=1000 mm.')
   files={}
   for view,value in s.views.items():
    path=local_path(value)
    if not path.is_file() or path.stat().st_size>16*1024**2 or path.suffix.lower() not in ('.png','.jpg','.jpeg'):raise ValueError('Each silhouette must be a PNG/JPEG <=16 MB.')
    files[view+'.png']=path
   result,folder=self.worker(None,{'operation':'reconstruct',**s.model_dump(mode='json')},files=files,cancel=cancel)
   return {'model':self.projects.import_mesh_bytes((folder/'result.stl').read_bytes(),'Orthographic visual hull',cancel),'reconstruction':result}
  path=local_path(s.path)
  if not path.is_file() or path.stat().st_size>32*1024**2:raise ValueError('Provide an existing image or scan <=32 MB.')
  if s.mode=='scan' and path.suffix.lower()!='.stl':raise ValueError('Scan input must be STL in mm.')
  if s.mode=='silhouette' and path.suffix.lower() not in ('.png','.jpg','.jpeg'):raise ValueError('Use PNG or JPEG.')
  result,folder=self.worker(None,{'operation':'reconstruct',**s.model_dump(mode='json')},files={'scan.stl' if s.mode=='scan' else 'image.png':path},cancel=cancel)
  if s.mode=='scan':
   return {'model':self.projects.import_mesh_bytes((folder/'result.stl').read_bytes(),'Imported scan',cancel),'reconstruction':result,'next':'Use bounded scan conversion for native B-rep; no invented feature tree.'}
  return {'model':self.projects.import_cad(folder/'result.step',cancel_event=cancel),'reconstruction':result}
 def sheet(self,settings,cancel=None):
  s=SheetMetal.model_validate(settings);a=math.radians(s.angle_deg);allowance=a*(s.inside_radius_mm+s.k_factor*s.thickness_mm);length=s.leg_a_mm+s.leg_b_mm+allowance
  # Neutral-axis development, a single bend with tangent leg lengths.
  source='import build123d as bd\nimport math\ndef build(params):\n    r=params["radius"];t=params["thickness"];w=params["width"];a=params["angle"];pa=params["leg_a"];pb=params["leg_b"]\n    arc=bd.CenterArc((0,0),r+t/2,0,a)\n    start=bd.Plane(origin=(r+t/2,0,0),x_dir=(1,0,0),z_dir=(0,1,0))\n    bend=bd.sweep(start*bd.Rectangle(t,w),arc)\n    first=bd.Pos(r+t/2,-pa/2,0)*bd.Box(t,pa,w)\n    end=bd.Rot(0,0,a)*(bd.Pos(r+t/2,pb/2,0)*bd.Box(t,pb,w))\n    return {"sheet":first+bend+end}'
  model=self.projects.build(source,{'radius':s.inside_radius_mm,'thickness':s.thickness_mm,'width':s.width_mm,'leg_a':s.leg_a_mm,'leg_b':s.leg_b_mm,'angle':s.angle_deg},name='Single-bend sheet metal',cancel_event=cancel)
  flat=self.projects.build('import build123d as bd\ndef build(params):\n    return {"flat":bd.Box(params["length"],params["width"],params["thickness"])}',{'length':length,'width':s.width_mm,'thickness':s.thickness_mm},name='Neutral-axis flat blank',cancel_event=cancel)
  return {'model':model,'flat_model':flat,'bend_allowance_mm':allowance,'developed_length_mm':length,'k_factor':s.k_factor,'scope':'One cylindrical bend, tangent leg lengths and user-specified K factor. No automatic arbitrary sheet unfolding or springback prediction.'}
 def compare(self,settings):
  s=Comparison.model_validate(settings);items=[]
  for key in s.model_ids:
   r=self.projects.ensure_ready(key);volume=sum(p['volume_mm3'] for p in r['geometry']['parts']);reports=self.evidence(key)['reports'];items.append({'model_id':key,'name':r['name'],'volume_mm3':volume,'mass_kg':volume*1e-9*s.density_kg_m3,'assumed_density_kg_m3':s.density_kg_m3,'part_count':len(r['spec']['parts']),'reports':[{'report_id':p['report_id'],'verified':p.get('verified',False),'stale':p['stale']} for p in reports]})
  return {'alternatives':items,'scope':'Geometry and explicitly assumed density. Performance/manufacturability only from attached non-stale reports; no AI-invented scores.'}
 def optimize(self,key,settings,cancel=None):
  s=Optimization.model_validate(settings);r=self.projects.ensure_ready(key);candidates=[]
  if s.objective!='minimum_volume' and s.simulation is None:raise ValueError('A physics objective requires a simulation definition.')
  if (s.max_displacement_mm is not None or s.max_temperature_k is not None) and s.simulation is None:raise ValueError('Physics constraints require a simulation definition.')
  if s.objective=='minimum_pressure_resistance' and s.simulation.kind!='stokes':raise ValueError('Pressure resistance needs Stokes settings.')
  if s.objective=='minimum_thermal_peak' and s.simulation.kind!='thermal' or s.objective=='minimum_displacement' and s.simulation.kind!='structural':raise ValueError('Objective and physics type do not match.')
  base=r['spec']['program']
  if s.parameter not in base['parameters']:raise ValueError('Unknown optimization parameter.')
  portable=self.projects.portable(key);file=self.root/(uuid.uuid4().hex+'.json');atomic_json(file,portable)
  try:
   for value in s.values:
    if cancel and cancel.is_set():raise ValueError('Optimization cancelled; original model preserved.')
    clone=self.projects.import_project(file)
    try:candidate=self.projects.parameters(clone['model_id'],{s.parameter:value},cancel_event=cancel)
    except ValueError as exc:
     self.projects.path(clone['model_id']).unlink(missing_ok=True);shutil.rmtree(self.projects.models/clone['model_id'],ignore_errors=True)
     if cancel and cancel.is_set():raise
     candidates.append({'model_id':None,'parameter_value':value,'volume_mm3':None,'objective_value':None,'feasible':False,'rejection':str(exc)[:2500]});continue
    volume=sum(p['volume_mm3'] for p in candidate['geometry']['parts']);entry={'model_id':candidate['model_id'],'parameter_value':value,'volume_mm3':volume,'feasible':True};score=volume
    if candidate.get('engineering',{}).get('requirements',{}).get('checks'):
     from .design_checks import verify_design
     entry['feasible']=verify_design(self.projects,candidate['model_id'])['passed']
    if s.simulation:
     result=self.simulate(candidate['model_id'],s.simulation.model_dump(mode='json'),cancel);entry['simulation']=result['report_id'];entry['feasible'] &= result['verified'];score=result['maximum'] if s.objective in ('minimum_thermal_peak','minimum_displacement') else s.simulation.pressure_drop_pa/max(result.get('outlet_flow_m3_s',0),1e-30) if s.objective=='minimum_pressure_resistance' else volume
     if s.max_displacement_mm is not None:entry['feasible'] &= result['kind']=='structural' and result['maximum']<=s.max_displacement_mm
     if s.max_temperature_k is not None:entry['feasible'] &= result['kind']=='thermal' and result['maximum']<=s.max_temperature_k
    entry['objective_value']=score;candidates.append(entry)
   feasible=[x for x in candidates if x['feasible']];return {'candidates':candidates,'best':min(feasible,key=lambda x:x['objective_value']) if feasible else None,'original_model_unchanged':self.projects.load(key)['spec']['revision']==r['spec']['revision'],'scope':'Bounded parameter sweep; only tested candidates, no claim of global optimum or topology optimization.'}
  finally:file.unlink(missing_ok=True)
 def assembly(self,key,settings,expected_revision=None,cancel=None):
  s=Assembly.model_validate(settings);r=self.native(key);ids={p['id'] for p in r['spec']['parts']};children=set();seen=set()
  if len(ids)>11:raise ValueError('Motion collision checking supports <=11 parts (55 pairs).')
  for joint in s.joints:
   if joint.parent not in ids or joint.child not in ids or joint.child in children:raise ValueError('Joints require existing parts and one parent per child.')
   children.add(joint.child)
  parents={j.child:j.parent for j in s.joints}
  for child in children:
   path=set();p=child
   while p in parents:
    if p in path:raise ValueError('Assembly joint cycle detected.')
    path.add(p);p=parents[p]
  ordered=[];pending=list(s.joints)
  while pending:
   ready=[j for j in pending if j.parent not in children or j.parent in seen]
   if not ready:raise ValueError('Joint ordering failed.')
   for j in ready:ordered.append(j);seen.add(j.child);pending.remove(j)
  old=r['spec']['program'];asset=old.get('asset_id') if old['source'].startswith('# INTACT_ASSEMBLY') else self.projects.store_step(self.projects.artifact(key,'model.step').read_bytes(),max_bytes=32*1024**2)
  if not asset:raise ValueError('The original assembly placement asset is missing.')
  source="""# INTACT_ASSEMBLY: fixed original STEP placements, editable joint values
import build123d as bd
def build(params):
    parts=dict(imported_parts)
    joints=JOINTS
    by_child={j['child']:j for j in joints}
    for name in parts:
        shape=parts[name];current=name
        while current in by_child:
            j=by_child[current];value=params[j['id']]
            if not j['minimum']<=value<=j['maximum']:raise ValueError('Joint motion limit exceeded.')
            if j['kind']=='fixed' and value!=0:raise ValueError('Fixed joint value must remain zero.')
            if j['kind']=='revolute':shape=shape.rotate(bd.Axis(j['origin'],j['axis']),value)
            elif j['kind']=='slider':shape=shape.translate(tuple(v*value/(sum(a*a for a in j['axis'])**.5) for v in j['axis']))
            current=j['parent']
        parts[name]=shape
    return parts
""".replace('JOINTS',repr([j.model_dump(mode='json') for j in ordered]))
  model=self.projects.build(source,{j.id:j.value for j in ordered},model_id=key,expected_revision=expected_revision if expected_revision is not None else r['spec']['revision'],asset_id=asset,cancel_event=cancel)
  from .feature_graph import FeatureService
  checks=[{'id':'collision_'+str(i),'kind':'interference','part_id':a,'other_part':b,'expected':{'max_volume_mm3':s.collision_tolerance_mm3}} for i,(a,b) in enumerate(( (a,b) for i,a in enumerate(sorted(ids)) for b in sorted(ids)[i+1:]))][:64]
  # Collision checks are independent evidence, not a replacement for user requirements.
  report,folder=self.worker(key,{'operation':'motion','part_id':next(iter(ids)),'checks':checks,'tolerance_mm':.001},worker='native_checks_worker.py',cancel=cancel)
  report.update(joints=[j.model_dump(mode='json') for j in ordered],scope='Acyclic fixed/revolute/slider kinematics, joint limits and discrete-pose overlap checks. No dynamics or continuous swept collision proof.')
  atomic_json(self.root/(key+'-motion.json'),report);return {'model':model,'motion':report}
