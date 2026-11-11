"""Independent artifact reopening and dimensional assertions for ChatGPT CAD reviews."""
import json,math
from .spec import DesignSpec

def validate_model(projects,model_id,expected_bounds=None,expected_part_ids=None,tolerance_mm=.01):
    if isinstance(tolerance_mm,bool) or not isinstance(tolerance_mm,(int,float)) or not math.isfinite(tolerance_mm) or not 1e-7<=tolerance_mm<=1:raise ValueError('Tolerance must be 0.0000001–1 mm.')
    r=projects.ensure_ready(model_id);parts={p['id']:p for p in r['spec']['parts']};checks=[]
    def check(name,passed,**facts):checks.append({'check':name,'passed':bool(passed),**facts})
    if expected_part_ids is not None:
        if not isinstance(expected_part_ids,list) or len(expected_part_ids)>128 or any(not isinstance(p,str) for p in expected_part_ids):raise ValueError('Expected part IDs must be a list of at most 128 strings.')
        check('part IDs match design brief',set(parts)==set(expected_part_ids),expected=expected_part_ids,actual=list(parts))
    if expected_bounds is not None:
        if not isinstance(expected_bounds,dict) or len(expected_bounds)>128:raise ValueError('Supply expected bounds by part ID.')
        for name,bounds in expected_bounds.items():
            if name not in parts:check(name+' exists',False);continue
            if not isinstance(bounds,dict) or not bounds or set(bounds)-{'length','width','height'}:raise ValueError('Bounds use length, width and height in CAD XYZ mm.')
            for axis,value in bounds.items():
                if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<=0:raise ValueError('Expected dimensions must be positive finite numbers.')
                actual=parts[name]['params'][axis];check(name+'.'+axis,abs(actual-value)<=tolerance_mm,expected_mm=value,actual_mm=actual,tolerance_mm=tolerance_mm)
    check('artifact checksums',projects.programs.cached_report(r['spec']['program']['artifact_id']) is not None)
    mesh_mode=r['geometry']['engine']=='implicit_mesh'
    if mesh_mode:
        import trimesh,numpy as np
        exported=trimesh.load(projects.artifact(model_id,'model.stl'),force='mesh',process=True)
        check('reopened STL watertight',exported.is_watertight)
        check('reopened STL positive volume',exported.is_volume and exported.volume>0,volume_mm3=float(exported.volume))
        # A mixed assembly contains native CAD parts tessellated for mesh export.
        # Compare the physical file to that actual mesh, not to exact curved CAD
        # volumes, which differ by the documented tessellation approximation.
        preview=json.loads(projects.artifact(model_id,'mesh.json').read_text());expected=0.
        for item in preview['parts']:
            p=parts[item['id']];xyz=np.asarray(item['positions']).reshape(-1,3);x,y,z=p['position']
            vertices=np.column_stack((xyz[:,0]+x,-xyz[:,2]+y,xyz[:,1]+z))
            expected+=trimesh.Trimesh(vertices,np.asarray(item['indices']).reshape(-1,3),process=False).volume
        check('mesh export volume matches sampled geometry',math.isclose(exported.volume,expected,rel_tol=1e-5,abs_tol=1e-5),sampled_volume_mm3=float(expected),export_volume_mm3=float(exported.volume))
        provenance='Triangle mesh estimates; sampled TPMS approximation, no exact native CAD faces.'
    else:
        import build123d as bd
        exported=bd.import_step(projects.artifact(model_id,'model.step'))
        check('reopened STEP valid',exported.is_valid)
        children={p.label:p for p in exported.children}
        check('STEP part labels match',set(children)==set(parts))
        for name,p in parts.items():
            shape=children.get(name)
            if shape is None:continue
            m=p['measurements'];check(name+' STEP solids',len(shape.solids())==m['solid_count'])
            check(name+' STEP volume',math.isclose(shape.volume,m['volume_mm3'],rel_tol=1e-7,abs_tol=1e-6))
            check(name+' STEP surface area',math.isclose(shape.area,m['surface_area_mm2'],rel_tol=1e-7,abs_tol=1e-6))
        provenance='OpenCASCADE B-rep; physical STEP reopened independently of preview geometry.'
    topology=json.loads(projects.artifact(model_id,'topology.json').read_text())
    features={p['id']:[{k:f[k] for k in ('ref','geometry','radius_mm','axis','axis_origin','area_mm2','center') if k in f} for f in p['faces'] if f.get('geometry') in ('cylinder','sphere','cone','torus')] for p in topology['parts']}
    return {'passed':all(c['passed'] for c in checks),'model_id':model_id,'revision':r['spec']['revision'],'provenance':provenance,'reference_mesh_volume_mm3':float(expected) if mesh_mode else None,'checks':checks,'curved_faces':features,'scope':'Checks supplied dimensions, native/mesh validity and export preservation. Does not certify design intent, fits, manufacturing safety or simulation.'}
