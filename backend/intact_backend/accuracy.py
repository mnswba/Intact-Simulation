# SPDX-License-Identifier: Apache-2.0
"""Requested accuracy, native tolerances and measured mesh convergence."""
from copy import deepcopy
import math
from .engineering_schema import Accuracy,Engineering
from .feature_graph import FeatureService

def set_accuracy(projects,key,settings,expected_revision=None,cancel_event=None):
    service=FeatureService(projects);r,e,draft=service.load(key);service.check_revision(r,draft,expected_revision);e.accuracy=Accuracy.model_validate(settings)
    if draft:return service.mutate(key,lambda data:setattr(data,'accuracy',e.accuracy),expected_revision)
    if e.attached:return service.rebuild(key,e,r['spec']['revision'],cancel_event)
    p=r['spec']['program']
    return projects.build(p['source'],p['parameters'],model_id=key,expected_revision=r['spec']['revision'],asset_id=p.get('asset_id'),engineering=e.model_dump(mode='json'),cancel_event=cancel_event)

def check_accuracy(projects,key,convergence=True,cancel_event=None):
    import trimesh
    r=projects.ensure_ready(key);e=Engineering.model_validate(r.get('engineering',{}));p=r['spec']['program'];settings=e.accuracy.model_dump(mode='json');checks=[]
    def add(name,passed,**facts):checks.append({'check':name,'status':'pass' if passed else 'fail',**facts})
    coarse=trimesh.load(projects.artifact(key,'model.stl'),force='mesh',process=True);mesh_mode=r['geometry']['engine']=='implicit_mesh'
    if not mesh_mode:
        import build123d as bd
        from OCP.BRep import BRep_Tool
        shape=bd.import_step(projects.artifact(key,'model.step'));tolerances=[BRep_Tool.Tolerance_s(f.wrapped) for f in shape.faces()]+[BRep_Tool.Tolerance_s(edge.wrapped) for edge in shape.edges()]+[BRep_Tool.Tolerance_s(v.wrapped) for v in shape.vertices()]
        native=max(tolerances,default=0);add('native B-rep tolerances',native<=e.accuracy.dimensional_tolerance_mm,maximum_native_tolerance_mm=native,requested_mm=e.accuracy.dimensional_tolerance_mm,scope='Kernel-stored tolerances, not a guarantee of intended dimensions or manufacturing accuracy.')
        exact=sum(x['volume_mm3'] for x in r['geometry']['parts']);error=abs(coarse.volume-exact)/exact
        add('STL volume approximation',error<=e.accuracy.mesh_volume_relative_tolerance,relative_error=float(error),allowed=e.accuracy.mesh_volume_relative_tolerance)
    if convergence:
        fine_params=deepcopy(p['parameters']);meshing=p.get('meshing') or {**settings,'linear_deflection_mm':.001,'angular_deflection_rad':.1}
        if mesh_mode:
            if 'samples_per_cell' not in fine_params or fine_params['samples_per_cell']>=64:
                checks.append({'check':'mesh convergence','status':'unverified','reason':'Expose a samples_per_cell parameter below 64 to compare resolutions.'});fine=None
            else:fine_params['samples_per_cell']=min(64,fine_params['samples_per_cell']*2);fine=True
        else:
            refined={**meshing,'linear_deflection_mm':max(.0001,meshing['linear_deflection_mm']/2),'angular_deflection_rad':max(.01,meshing['angular_deflection_rad']/2)}
            fine=any(refined[k]<meshing[k] for k in ('linear_deflection_mm','angular_deflection_rad'))
            if not fine:checks.append({'check':'mesh convergence','status':'unverified','reason':'Meshing is already at the supported refinement floor; a second resolution is unavailable.'})
            meshing=refined
        if fine:
            try:
                report=projects.programs.build(p['source'],fine_params,asset_id=p.get('asset_id'),meshing=meshing,cancel_event=cancel_event)
                finer=trimesh.load(projects.programs.root/report['artifact_id']/'model.stl',force='mesh',process=True)
                volume_change=abs(finer.volume-coarse.volume)/abs(finer.volume);area_change=abs(finer.area-coarse.area)/finer.area
                add('mesh convergence',max(volume_change,area_change)<=e.accuracy.convergence_relative_tolerance,relative_volume_change=float(volume_change),relative_area_change=float(area_change),allowed=e.accuracy.convergence_relative_tolerance,scope='Two-resolution comparison; not proof of a global surface-deviation bound.')
            except ValueError as exc:checks.append({'check':'mesh convergence','status':'unverified','reason':str(exc)[:2000]})
    result={'model_id':key,'revision':r['spec']['revision'],'requested':settings,'checks':checks,'passed':bool(checks) and all(c['status']=='pass' for c in checks),'scope':'Reports measured geometry/export approximations. It does not certify fabrication tolerances or exact TPMS wall thickness.','geometry_revision_unchanged':projects.load(key)['spec']['revision']==r['spec']['revision']}
    from .projects import atomic_json
    atomic_json(projects.root/'accuracy-checks'/(key+'.json'),result)
    return result
