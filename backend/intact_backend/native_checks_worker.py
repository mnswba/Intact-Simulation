# SPDX-License-Identifier: Apache-2.0
"""Native design checks on an exported STEP, inside the geometry sandbox."""
import json,math,sys,traceback
from pathlib import Path
from worker_context import resource,worker_path
resource.setrlimit(resource.RLIMIT_CPU,(80,80));resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3));resource.setrlimit(resource.RLIMIT_FSIZE,(16*1024**2,16*1024**2))
import build123d as bd
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector
from OCP.gp import gp_Lin,gp_Pnt,gp_Dir
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.TopAbs import TopAbs_IN

def num(v,minimum=0):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<minimum:raise ValueError('Expected a finite nonnegative measurement.')
    return float(v)
def xyz(v):return [float(v.X),float(v.Y),float(v.Z)]
def line_distance(a,b,axis):
    d=[x-y for x,y in zip(a,b)];along=sum(x*y for x,y in zip(d,axis));return math.sqrt(sum((x-along*y)**2 for x,y in zip(d,axis)))
def intersections(shape,origin,axis,start,end):
    q=IntCurvesFace_ShapeIntersector();q.Load(shape.wrapped,1e-7);q.Perform(gp_Lin(gp_Pnt(*origin),gp_Dir(*axis)),start,end)
    return sorted({round(q.WParameter(i),10) for i in range(1,q.NbPnt()+1)})
def holes(shape,tol):
    found=[]
    for f in shape.faces():
        if f.geom_type!=bd.GeomType.CYLINDER:continue
        surface=BRepAdaptor_Surface(f.wrapped);cyl=surface.Cylinder();axis=[cyl.Axis().Direction().X(),cyl.Axis().Direction().Y(),cyl.Axis().Direction().Z()];origin=[cyl.Location().X(),cyl.Location().Y(),cyl.Location().Z()]
        p=f.position_at(.37,.53);normal=f.normal_at(.37,.53);v=[x-y for x,y in zip(xyz(p),origin)];along=sum(x*y for x,y in zip(v,axis));radial=[x-along*y for x,y in zip(v,axis)]
        if sum(x*y for x,y in zip(xyz(normal),radial))>=0:continue
        radius=cyl.Radius();lo=surface.FirstVParameter();hi=surface.LastVParameter();start=[x+lo*y for x,y in zip(origin,axis)];end=[x+hi*y for x,y in zip(origin,axis)]
        existing=next((h for h in found if abs(h['diameter_mm']-2*radius)<=tol and abs(abs(sum(x*y for x,y in zip(axis,h['axis'])))-1)<1e-6 and line_distance(origin,h['axis_origin'],axis)<=tol),None)
        if existing is not None:
            existing['segments'].extend([start,end]);continue
        extent=shape.bounding_box().size.length*3+1
        through=not intersections(shape,origin,axis,-extent,extent)
        found.append({'diameter_mm':2*radius,'axis':axis,'axis_origin':origin,'segments':[start,end],'through':through})
    for h in found:
        values=[sum(x*y for x,y in zip(p,h['axis'])) for p in h.pop('segments')];h['depth_mm']=max(values)-min(values)
    return found

def wall_samples(shape,limit=144):
    values=[];points=[];extent=shape.bounding_box().size.length*2+1
    faces=list(shape.faces());stride=max(1,math.ceil(len(faces)/16))
    for face in faces[::stride]:
        for u in (.2,.5,.8):
            for v in (.2,.5,.8):
                p=face.position_at(u,v)
                if face.distance_to(p)>1e-6:continue
                n=face.normal_at(u,v);d=[-x for x in xyz(n)];origin=xyz(p);inside=[x+1e-5*y for x,y in zip(origin,d)]
                if BRepClass3d_SolidClassifier(shape.wrapped,gp_Pnt(*inside),1e-7).State()!=TopAbs_IN:continue
                hits=intersections(shape,origin,d,1e-5,extent)
                if hits:values.append(hits[0]);points.append(origin)
                if len(values)>=limit:break
    return {'sample_count':len(values),'minimum_sampled_mm':min(values) if values else None,'maximum_sampled_mm':max(values) if values else None,'sample_locations_xyz_mm':points,'provenance':'Surface-normal ray samples, not a proof of the global minimum wall thickness.'}

def main():
    request=json.loads(Path(worker_path('/input/request.json')).read_text());model=bd.import_step(worker_path('/input/model.step'));parts={p.label:p for p in model.children};tol=request['tolerance_mm'];results=[];hole_cache={}
    for check in request['checks']:
        result={'id':check['id'],'kind':check['kind'],'status':'pass','provenance':'Exported STEP / OpenCASCADE'};kind=check['kind'];part_id=check.get('part_id');p=parts.get(part_id);expected=check['expected']
        try:
            if kind=='part_count':
                count=expected.get('count');result.update(expected=count,actual=len(parts));passed=isinstance(count,int) and not isinstance(count,bool) and len(parts)==count
            elif p is None:result.update(status='fail',error='Required part is missing: '+str(part_id));results.append(result);continue
            elif kind=='bounds':
                actual=dict(zip(('length','width','height'),xyz(p.bounding_box().size)))
                if not expected or set(expected)-set(actual):raise ValueError('Bounds require length/width/height in CAD XYZ mm.')
                passed=all(abs(actual[k]-num(v))<=tol for k,v in expected.items());result.update(expected=expected,actual=actual,tolerance_mm=tol)
            elif kind=='placement':
                box=p.bounding_box();actual={'center_mm':xyz(box.center()),'min_mm':xyz(box.min),'max_mm':xyz(box.max)}
                if not expected or set(expected)-set(actual):raise ValueError('Placement uses bounding-box center_mm, min_mm or max_mm in CAD XYZ.')
                passed=True
                for name,coords in expected.items():
                    if not isinstance(coords,list) or len(coords)!=3 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in coords):raise ValueError('Supply three finite CAD XYZ coordinates.')
                    passed=passed and all(abs(a-b)<=tol for a,b in zip(actual[name],coords))
                result.update(expected=expected,actual=actual,tolerance_mm=tol,scope='Axis-aligned bounding-box placement, not a general orientation or mating constraint.')
            elif kind=='hole_pattern':
                if set(expected)-{'count','diameter_mm','depth_mm','through','centers_mm','axis'}:raise ValueError('Unknown hole requirement field.')
                if part_id not in hole_cache:hole_cache[part_id]=holes(p,tol)
                axis=expected.get('axis',[0,0,1]);a=bd.Vector(axis).normalized();axis=xyz(a)
                matches=[h for h in hole_cache[part_id] if abs(abs(sum(x*y for x,y in zip(axis,h['axis'])))-1)<1e-6]
                if 'diameter_mm' in expected:matches=[h for h in matches if abs(h['diameter_mm']-num(expected['diameter_mm']))<=tol]
                count=expected.get('count');passed=isinstance(count,int) and not isinstance(count,bool) and len(matches)==count
                if 'through' in expected:
                    if not isinstance(expected['through'],bool):raise ValueError('through must be a boolean.')
                    passed=passed and all(h['through']==expected['through'] for h in matches)
                if 'depth_mm' in expected:passed=passed and all(abs(h['depth_mm']-num(expected['depth_mm']))<=tol for h in matches)
                if 'centers_mm' in expected:
                    centers=expected['centers_mm']
                    if not isinstance(centers,list) or len(centers)!=count:raise ValueError('Supply one XYZ center for each expected hole.')
                    chosen=[]
                    for c in centers:
                        indices=[i for i,h in enumerate(matches) if line_distance(xyz(bd.Vector(c)),h['axis_origin'],axis)<=tol]
                        if len(indices)!=1 or indices[0] in chosen:passed=False
                        else:chosen.append(indices[0])
                    passed=passed and len(chosen)==count
                result.update(expected=expected,actual=matches,all_bores=hole_cache[part_id],tolerance_mm=tol)
            elif kind in ('clearance','interference'):
                other=parts.get(check.get('other_part'))
                if other is None:raise ValueError('The second part is missing.')
                if kind=='clearance':
                    distance=p.distance_to(other);minimum=num(expected.get('min_mm'));passed=distance+tol>=minimum;result.update(actual_mm=distance,minimum_mm=minimum)
                else:
                    common=p&other;volume=float(common.volume) if common is not None else 0.0;allowed=num(expected.get('max_volume_mm3',0));passed=volume<=allowed+1e-7;result.update(overlap_volume_mm3=volume,maximum_mm3=allowed)
            elif kind=='wall_thickness':
                samples=wall_samples(p);minimum=num(expected.get('min_mm'));result.update(samples,expected_minimum_mm=minimum)
                passed=samples['minimum_sampled_mm'] is not None and samples['minimum_sampled_mm']+tol>=minimum
                if passed and expected.get('allow_sampled') is not True:result.update(status='unverified',reason='Samples pass, but a global minimum thickness was not proven.')
                elif not samples['sample_count']:result.update(status='unverified',reason='No reliable wall samples were obtained.');passed=True
            else:raise ValueError('Unsupported design check.')
            if not passed:result['status']='fail'
        except Exception as exc:result.update(status='unverified',error=str(exc)[:1000])
        results.append(result)
    Path(worker_path('/work/report.json')).write_text(json.dumps({'checks':results,'all_passed':bool(results) and all(r['status']=='pass' for r in results)},allow_nan=False))

try:main()
except BaseException as exc:
    Path(worker_path('/work/error.json')).write_text(json.dumps({'error':str(exc),'traceback':traceback.format_exc()[-3000:]}));sys.exit(1)
