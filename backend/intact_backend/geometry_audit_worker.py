"""Trusted pre-display geometry/export checks, executed in the CAD sandbox.

Repair is deliberately limited to kernel healing/orientation with measured
invariants. It cannot invent missing design features or certify physical use.
"""
from copy import deepcopy
import json, math
from pathlib import Path
import build123d as bd

AUDIT_VERSION=1


def metrics(shape):
    box=shape.bounding_box();solids=list(shape.solids())
    return {'bounds_mm':[float(v) for v in (*box.min,*box.max)],'solid_count':len(solids),'face_count':len(shape.faces()),'absolute_volume_mm3':sum(abs(float(s.volume)) for s in solids),'surface_area_mm2':float(shape.area)}


def same_geometry(before,after):
    return (before['solid_count']==after['solid_count'] and before['face_count']==after['face_count']
        and all(math.isfinite(v) for v in after['bounds_mm'])
        and all(abs(a-b)<=1e-6 for a,b in zip(before['bounds_mm'],after['bounds_mm']))
        and all(math.isfinite(after[k]) and math.isclose(before[k],after[k],rel_tol=1e-8,abs_tol=1e-6) for k in ('absolute_volume_mm3','surface_area_mm2')))


def audit_native(shape,name):
    if not isinstance(shape,bd.Shape) or not shape.solids():raise ValueError(f'{name}: geometry audit rejected a surface, sketch or missing solid. Repair the CAD source before displaying it.')
    before=metrics(shape);repairs=[];candidate=shape
    if not shape.is_valid:
        candidate=deepcopy(shape).fix();repairs.append('OpenCASCADE shape healing')
    solids=list(candidate.solids())
    if any(s.volume<0 for s in solids):
        fixed=[]
        for solid in solids:
            solid=deepcopy(solid)
            if solid.volume<0:solid.wrapped.Reverse()
            fixed.append(solid)
        candidate=bd.Compound(children=fixed);candidate.color=shape.color;candidate.label=shape.label;repairs.append('Corrected reversed solid orientation')
    if not candidate.is_valid or any(not s.is_valid or not math.isfinite(s.volume) or s.volume<=1e-9 for s in candidate.solids()):raise ValueError(f'{name}: geometry audit failed. B-rep must contain valid positive-volume solids; bounded healing could not safely repair it. Fix the source; no new geometry will be published.')
    if repairs and not same_geometry(before,metrics(candidate)):raise ValueError(f'{name}: automatic repair rejected because bounds, volume, surface area or topology counts changed. Fix the source while preserving design intent.')
    after=metrics(candidate)
    if not all(math.isfinite(n) for n in after['bounds_mm']) or not all(math.isfinite(after[k]) and after[k]>0 for k in ('absolute_volume_mm3','surface_area_mm2')):raise ValueError(f'{name}: nonfinite or empty geometry rejected by the auditor.')
    return candidate,{'part_id':name,'status':'repaired' if repairs else 'passed','checks':['valid B-rep','positive finite solid volumes','finite bounds and surface area'],'repairs':repairs,'metrics':after,'repair_invariants':{'bounds_max_deviation_mm':max(abs(a-b) for a,b in zip(before['bounds_mm'],after['bounds_mm'])),'volume_delta_mm3':after['absolute_volume_mm3']-before['absolute_volume_mm3']} if repairs else None}


def verify_exports(folder,parts,mesh_mode):
    checks=[]
    def check(name,passed,**facts):
        checks.append({'check':name,'passed':bool(passed),**facts})
        if not passed:raise ValueError('Pre-display export audit failed: '+name+'. Previous model is preserved.')
    glb=(folder/'model.glb').read_bytes();check('GLB signature',glb[:4]==b'glTF')
    import struct,zipfile
    size,kind=struct.unpack_from('<II',glb,12);scene=json.loads(glb[20:20+size]);check('GLB scene structure',kind==0x4e4f534a and bool(scene.get('meshes')) and bool(scene.get('nodes')))
    with zipfile.ZipFile(folder/'model.3mf') as package:check('3MF package integrity',package.testzip() is None and any(n.endswith('.model') for n in package.namelist()))
    check('STL exported',(folder/'model.stl').stat().st_size>84)
    if not mesh_mode:
        reopened=bd.import_step(folder/'model.step');check('reopened STEP validity',reopened.is_valid)
        actual={p.label:p for p in reopened.children};expected={p['part']['id']:p for p in parts}
        check('STEP named part identities',set(actual)==set(expected))
        for name,item in expected.items():
            shape=actual[name];check(name+' STEP volume preserved',math.isclose(shape.volume,item['volume_mm3'],rel_tol=1e-7,abs_tol=1e-6))
            box=shape.bounding_box();dimensions=[box.size.X,box.size.Y,box.size.Z];target=[item['part']['params'][k] for k in ('length','width','height')]
            check(name+' STEP dimensions preserved',all(abs(a-b)<=1e-5 for a,b in zip(dimensions,target)))
    return checks
