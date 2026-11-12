"""Trusted adapter launched INSIDE the network/filesystem-isolated worker.

This module never imports the web server, provider SDK or service credentials.
It executes a CAD program only after the outer runner established isolation.
"""
import json, math, os, re, resource, sys
from copy import deepcopy
from pathlib import Path

resource.setrlimit(resource.RLIMIT_CPU,(100,100))
resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3))
resource.setrlimit(resource.RLIMIT_FSIZE,(64*1024**2,64*1024**2))
resource.setrlimit(resource.RLIMIT_NOFILE,(128,128))
resource.setrlimit(resource.RLIMIT_NPROC,(128,128))
# No application modules are imported in this process. All files below are isolated mounts.
import build123d as bd
import numpy as np
from topology_worker import inspect_part, imported_parts
from intact_lattice import MeshPart,write_mesh_exports
from geometry_audit_worker import audit_native,verify_exports,AUDIT_VERSION

_REAL_IMPORT=__import__
def cad_import(name,globals=None,locals=None,fromlist=(),level=0):
    if level or name.split('.')[0] not in ('build123d','math','numpy','intact_lattice'):raise ImportError('Unsupported CAD import.')
    return _REAL_IMPORT(name,globals,locals,fromlist,level)

SAFE_BUILTINS={name:getattr(__import__('builtins'),name) for name in ('abs','all','any','bool','dict','enumerate','Exception','float','int','isinstance','len','list','map','max','min','pow','print','range','reversed','round','set','sorted','str','sum','tuple','ValueError','zip')}
SAFE_BUILTINS['__import__']=cad_import

def main():
    data=json.loads(Path('/input/request.json').read_text());parameters=data['parameters'];accuracy=data.get('meshing') or {};linear=accuracy.get('linear_deflection_mm');angular=accuracy.get('angular_deflection_rad',.15)
    scope={'__builtins__':SAFE_BUILTINS,'bd':bd,'math':math,'np':np}
    if data.get('asset_id'):
        if data.get('asset_name')=='input.stl':
            import trimesh
            m=trimesh.load('/input/input.stl',force='mesh',process=True)
            if len(m.faces)>250000 or not m.is_volume:raise ValueError('Imported STL must be a closed positive volume with <=250,000 triangles.')
            scope['input_mesh']=MeshPart(m,{'provenance':'Supplied STL in millimeters; no automatic feature reconstruction.'})
        else:
            input_shape=bd.import_step('/input/input.step');scope.update(input_shape=input_shape,imported_parts=imported_parts(input_shape))
    exec(compile(data['source'],'design.py','exec'),scope,scope)
    output=scope['build'](dict(parameters))
    if isinstance(output,bd.BuildPart):output=output.part
    if isinstance(output,(bd.Shape,MeshPart)):output={'model':output}
    if isinstance(output,(list,tuple)):output={f'part_{i+1}':shape for i,shape in enumerate(output)}
    if not isinstance(output,dict) or not 1<=len(output)<=128:raise ValueError('build(params) must return a shape or a dictionary of 1–128 named shapes.')
    audit_parts=[];parts=[];meshes=[];topology=[];assembly=[];mesh_exports=[];total_vertices=0;total_triangles=0
    mesh_mode=any(isinstance(s,MeshPart) for s in output.values())
    for name,shape in output.items():
        if not isinstance(name,str) or not re.fullmatch('[a-z][a-z0-9_]{0,47}',name):raise ValueError('Part IDs must start with a lowercase letter, contain only lowercase letters, numbers or underscores, and be at most 48 characters; for example mounting_flange.')
        if isinstance(shape,bd.BuildPart):shape=shape.part
        if isinstance(shape,MeshPart):
            m=shape.mesh
            if not m.is_volume or not m.is_watertight or not m.is_winding_consistent or not np.isfinite(m.vertices).all():raise ValueError(f'{name}: mesh must enclose a valid watertight positive volume.')
            lo,hi=m.bounds;size=hi-lo;origin=np.array([(lo[0]+hi[0])/2,(lo[1]+hi[1])/2,lo[2]])
            if min(size)<=1e-6 or max(size)>1e6:raise ValueError('Invalid mesh dimensions.')
            local=m.vertices-origin;positions=np.column_stack((local[:,0],local[:,2],-local[:,1])).ravel().tolist()
            count=int(m.body_count)
            if count>1000:raise ValueError('The lattice contains more than 1000 disconnected components. Adjust the band/level or sampling.')
            part={'id':name,'name':name.replace('_',' ').capitalize(),'template':'custom','engine':'implicit_mesh','enabled':True,'material':'aluminum','color':'#6287bc','params':dict(length=float(size[0]),width=float(size[1]),height=float(size[2])),'position':origin.tolist()}
            entry={'part':part,'valid':True,'solid_count':count,'volume_mm3':float(m.volume),'surface_area_mm2':float(m.area),'face_count':len(m.faces),'provenance':'validated triangle mesh','watertight':True,'lattice':shape.metadata}
            if 'relative_density' in shape.metadata:entry['relative_density']=shape.metadata['relative_density']
            audit_parts.append({'part_id':name,'status':'passed','checks':['finite mesh coordinates','watertight','consistent winding','positive volume'],'repairs':[]})
            parts.append(entry);meshes.append({'id':name,'positions':positions,'indices':m.faces.ravel().tolist(),'face_groups':[]})
            topology.append({'id':name,'faces':[],'edges':[],'vertices':[],'provenance':'Mesh approximation; no native CAD faces or edges.'})
            mesh_exports.append((name,m,part['color']));total_vertices+=len(m.vertices);total_triangles+=len(m.faces)
            if total_vertices>750000 or total_triangles>1200000:raise ValueError('The combined preview mesh budget was exceeded.')
            continue
        shape,part_audit=audit_native(shape,name);audit_parts.append(part_audit)
        # Located copies may share a TopoDS TShape. Give STEP/XCAF independent
        # shape identities so naming/recoloring one occurrence cannot rename another.
        shape=deepcopy(shape)
        solids=list(shape.solids())
        if any(not s.is_valid or s.volume<=1e-9 for s in solids):raise ValueError(f'{name}: every solid must have positive volume and valid topology.')
        bounds=shape.bounding_box();size=bounds.size
        if min(size.X,size.Y,size.Z)<=1e-6 or max(size.X,size.Y,size.Z)>1e6:raise ValueError(f'{name}: dimensions must be positive and at most 1,000,000 mm.')
        cx=(bounds.min.X+bounds.max.X)/2;cy=(bounds.min.Y+bounds.max.Y)/2;z0=bounds.min.Z
        mesh,inspection=inspect_part(name,shape,linear,angular)
        total_vertices+=len(mesh['positions'])//3;total_triangles+=len(mesh['indices'])//3
        if total_vertices>750000 or total_triangles>1200000:raise ValueError('The preview exceeds its mesh budget. Simplify the model.')
        if any(not math.isfinite(v) for v in mesh['positions']):raise ValueError('Non-finite tessellation.')
        topology.append(inspection)
        if shape.color is None:shape.color=bd.Color('#6287bc')
        shape.label=name;assembly.append(shape)
        part={'id':name,'name':name.replace('_',' ').capitalize(),'template':'custom','engine':'build123d','enabled':True,'material':'aluminum','color':('#'+''.join(f'{round(max(0,min(1,c))*255):02x}' for c in tuple(shape.color)[:3])) if shape.color else '#6287bc','params':{'length':float(size.X),'width':float(size.Y),'height':float(size.Z),'holeDiameter':6,'finCount':9,'wall':3},'position':[float(cx),float(cy),float(z0)]}
        parts.append({'part':part,'valid':True,'solid_count':len(solids),'volume_mm3':float(shape.volume),'surface_area_mm2':float(shape.area),'face_count':len(shape.faces())})
        meshes.append(mesh)
        if mesh_mode:
            import trimesh
            points=np.asarray(mesh['positions']).reshape(-1,3);points=np.column_stack((points[:,0]+cx,-points[:,2]+cy,points[:,1]+z0))
            mesh_exports.append((name,trimesh.Trimesh(points,np.asarray(mesh['indices']).reshape(-1,3),process=False),part['color']))
    out=Path('/work')
    if mesh_mode:write_mesh_exports(mesh_exports,out)
    else:
        combined=bd.Compound(children=assembly,label='Intact generated model')
        bd.export_step(combined,out/'model.step');bd.export_stl(combined,out/'model.stl',**({'tolerance':linear,'angular_tolerance':angular} if linear is not None else {}))
        bd.export_gltf(combined,out/'model.glb',binary=True,linear_deflection=linear if linear is not None else .1,angular_deflection=angular)
        mesher=bd.Mesher();mesher.add_shape(assembly,linear_deflection=linear if linear is not None else .1,angular_deflection=angular);mesher.write(out/'model.3mf')
    (out/'topology.json').write_text(json.dumps({'version':1,'units':'mm','coordinate_system':'cad_z_up','provenance':'OpenCASCADE B-rep; references valid for this artifact only','parts':topology},separators=(',',':'),allow_nan=False))
    (out/'mesh.json').write_text(json.dumps({'version':1,'units':'mm','coordinate_system':'viewer_y_up','parts':meshes},separators=(',',':'),allow_nan=False))
    export_checks=verify_exports(out,parts,mesh_mode)
    audit={'version':AUDIT_VERSION,'status':'passed','stage':'before CAD revision commit and viewer display','parts':audit_parts,'export_checks':export_checks,'repairs_count':sum(len(p['repairs']) for p in audit_parts),'design_verification':'Not evaluated by geometry audit. Saved requirements are checked separately when present.','scope':'Geometry/topology and exported-file preservation only; not manufacturing or physical performance certification.'}
    (out/'audit.json').write_text(json.dumps(audit,allow_nan=False))
    artifacts={'audit':'audit.json','stl':'model.stl','glb':'model.glb','3mf':'model.3mf','mesh':'mesh.json','source':'program.py','topology':'topology.json'}
    if not mesh_mode:artifacts['step']='model.step'
    (out/'manifest.json').write_text(json.dumps({'engine':'implicit_mesh' if mesh_mode else 'build123d','valid':True,'audit':audit,'mode':'program','meshing':data.get('meshing'),'parts':parts,'vertices':total_vertices,'triangles':total_triangles,'artifacts':artifacts},allow_nan=False))

if __name__=='__main__':
    try:main()
    except Exception as exc:
        import traceback
        Path('/work/error.json').write_text(json.dumps({'error':type(exc).__name__,'detail':str(exc)[:2000],'traceback':traceback.format_exc()[-4000:]}));sys.exit(1)
