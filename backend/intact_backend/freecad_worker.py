# SPDX-License-Identifier: Apache-2.0
"""Trusted, JSON-only FreeCAD adapter. Executed exclusively in bubblewrap."""
import json,math,resource,sys,traceback
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CPU,(100,100))
resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3))
resource.setrlimit(resource.RLIMIT_FSIZE,(64*1024**2,64*1024**2))
import FreeCAD as App
import Part,Sketcher,Import

def vector(v):
    if not isinstance(v,(list,tuple)) or len(v)!=3 or any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or abs(x)>1e6 for x in v):raise ValueError('Expected a finite XYZ vector.')
    return App.Vector(*v)
def scalar(v,p):
    if isinstance(v,dict):
        if set(v)!={'parameter'} or v['parameter'] not in p:raise ValueError('Unknown parameter reference.')
        v=p[v['parameter']]
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or abs(v)>1e6:raise ValueError('Expected a finite numeric feature value.')
    return float(v)
def resolve(v,p):
    if isinstance(v,dict):return scalar(v,p)
    if isinstance(v,list):return [resolve(x,p) for x in v]
    return scalar(v,p) if isinstance(v,(int,float)) and not isinstance(v,bool) else v

def sketch(doc,spec,params):
    sk=doc.addObject('Sketcher::SketchObject',spec['id']);ids={};types={}
    for g in spec['geometry']:
        kind=g['kind'];types[g['id']]=kind
        if kind=='line':shape=Part.LineSegment(App.Vector(*g['start'],0),App.Vector(*g['end'],0))
        else:
            shape=Part.Circle(App.Vector(*g['center'],0),App.Vector(0,0,1),g['radius'])
            if kind=='arc':shape=Part.ArcOfCircle(shape,math.radians(g['start_angle_deg']),math.radians(g['end_angle_deg']))
        ids[g['id']]=sk.addGeometry(shape,g.get('construction',False))
    names={'coincident':'Coincident','horizontal':'Horizontal','vertical':'Vertical','parallel':'Parallel','perpendicular':'Perpendicular','equal':'Equal','tangent':'Tangent','length':'Distance','distance_x':'DistanceX','distance_y':'DistanceY','distance':'Distance','diameter':'Diameter','radius':'Radius','angle':'Angle','lock':'Block','point_on_object':'PointOnObject'}
    for c in spec['constraints']:
        k=c['kind'];entities=[ids[e] for e in c['entities']];points=c.get('points',[]);args=[]
        if k=='concentric':
            if len(entities)!=2 or any(types[e] not in ('circle','arc') for e in c['entities']):raise ValueError('Concentric requires two circles/arcs.')
            index=sk.addConstraint(Sketcher.Constraint('Coincident',entities[0],3,entities[1],3));sk.renameConstraint(index,c['id']);continue
        if k in ('coincident','point_on_object'):
            if len(entities)!=2:raise ValueError(k+' requires two geometry IDs.')
            args=[entities[0],points[0] if points else 1,entities[1]]
            if k=='coincident':args.append(points[1] if len(points)>1 else 1)
        elif k in ('distance_x','distance_y','distance') and points:
            for i,e in enumerate(entities):args.extend([e,points[i] if i<len(points) else 1])
        else:args=entities
        if c.get('value') is not None:
            v=scalar(c['value'],params)
            if k=='angle':v=math.radians(v)
            args.append(v)
        try:index=sk.addConstraint(Sketcher.Constraint(names[k],*args));sk.renameConstraint(index,c['id'])
        except Exception as exc:raise ValueError('Constraint '+c['id']+': '+str(exc)) from exc
    status=sk.solve();doc.recompute()
    fully=bool(sk.FullyConstrained)
    dof=getattr(sk,'DoF',getattr(sk,'SolveSpace',None))
    diagnostics={'solver_code':int(status),'fully_constrained':fully,'degrees_of_freedom':int(dof) if isinstance(dof,(int,float)) else (0 if fully else None),'constraint_ids':[c['id'] for c in spec['constraints']],'conflict':int(status)!=0,'conflicting_constraint_indices':list(sk.ConflictingConstraints),'redundant_constraint_indices':list(sk.RedundantConstraints),'geometry':[]}
    for g,geo in zip(spec['geometry'],sk.Geometry):
        item={'id':g['id'],'kind':g['kind'],'construction':g.get('construction',False)}
        if g['kind']=='line':item.update(start=[geo.StartPoint.x,geo.StartPoint.y],end=[geo.EndPoint.x,geo.EndPoint.y])
        else:item.update(center=[geo.Center.x,geo.Center.y],radius=geo.Radius,start_angle_deg=g.get('start_angle_deg',0),end_angle_deg=g.get('end_angle_deg',360))
        diagnostics['geometry'].append(item)
    rotations={'XY':App.Rotation(),'XZ':App.Rotation(App.Vector(1,0,0),90),'YZ':App.Rotation(App.Vector(0,1,0),90)}
    sk.Placement=App.Placement(vector(spec['origin']),rotations[spec['plane']]);doc.recompute()
    return sk,diagnostics

def select_edges(shape,selectors,p):
    if not isinstance(selectors,list) or not selectors:raise ValueError('Fillet/chamfer requires explicit geometric edge selectors.')
    selected=[]
    for sel in selectors:
        if not isinstance(sel,dict) or set(sel)-{'geometry','radius','at','direction','all','tolerance_mm'}:raise ValueError('Invalid edge selector.')
        found=[];tol=float(sel.get('tolerance_mm',.01))
        if not 1e-6<=tol<=1:raise ValueError('Invalid edge selection tolerance.')
        for edge in shape.Edges:
            curve=edge.Curve;name=type(curve).__name__.lower();geometry=sel.get('geometry','all')
            if geometry!='all' and geometry not in name:continue
            if 'radius' in sel and (not hasattr(curve,'Radius') or abs(curve.Radius-scalar(sel['radius'],p))>tol):continue
            if 'at' in sel and edge.distToShape(Part.Vertex(vector(sel['at'])))[0]>tol:continue
            if 'direction' in sel:
                d=vector(sel['direction']);t=edge.tangentAt((edge.FirstParameter+edge.LastParameter)/2)
                if d.Length<1e-10 or abs(abs(t.dot(d)/(t.Length*d.Length))-1)>1e-6:continue
            found.append(edge)
        if not found or len(found)>1 and not sel.get('all',False):raise ValueError('Edge selector is missing or ambiguous ('+str(len(found))+' matches); refine it or explicitly select all matches.')
        selected.extend(found)
    unique=[]
    for edge in selected:
        if not any(edge.isSame(other) for other in unique):unique.append(edge)
    return unique

def main():
    request=json.loads(Path('/input/request.json').read_text());e=request['engineering'];params=e['parameters'];doc=App.newDocument('Intact');objects={};sketches={};solves={}
    for s in e['sketches']:
        sk,diagnostic=sketch(doc,s,params);sketches[s['id']]=sk;solves[s['id']]=diagnostic
    report={'engine':'FreeCAD','version':'.'.join(App.Version()[:3]),'sketches':solves,'features':[]}
    if request['mode']=='solve':
        Path('/work/report.json').write_text(json.dumps(report,allow_nan=False));return
    for s in e['sketches']:
        if solves[s['id']]['conflict']:raise ValueError('Sketch '+s['id']+' has conflicting/redundant constraints: '+json.dumps(solves[s['id']]))
        if s['require_fully_constrained'] and not solves[s['id']]['fully_constrained']:raise ValueError('Sketch '+s['id']+' is under-constrained. Add constraints or explicitly allow remaining degrees of freedom.')
    outputs={}
    for f in e['features']:
        k=f['kind'];p={name:resolve(v,params) if name!='edges' else v for name,v in f['params'].items()};base=objects.get(f.get('base'));shape=None
        if f['suppressed']:
            if base is not None:objects[f['id']]=base
            if f.get('part_id') and base is not None:outputs[f['part_id']]=base
            report['features'].append({'id':f['id'],'suppressed':True});continue
        cached=f['id'] in request.get('cached_nodes',[])
        if cached:
            shape=Part.Shape();shape.read('/input/nodes/'+f['id']+'.brep')
        elif k in ('extrude','revolve'):
            sk=sketches[f['sketch_id']];wires=sk.Shape.Wires
            if not wires or not all(w.isClosed() for w in wires):raise ValueError('Feature '+f['id']+' needs closed sketch wires.')
            face=Part.makeFace(wires,'Part::FaceMakerBullseye')
            if k=='extrude':
                h=float(p.get('height',10));d=vector(p.get('direction',{'XY':[0,0,1],'XZ':[0,-1,0],'YZ':[1,0,0]}[next(s['plane'] for s in e['sketches'] if s['id']==f['sketch_id'])]))
                if h<=0 or d.Length<1e-12:raise ValueError('Extrusion height/direction must be positive/nonzero.')
                shape=face.extrude(d/d.Length*h)
            else:
                angle=float(p.get('angle_deg',360))
                if not 0<angle<=360:raise ValueError('Revolve angle must be in (0,360].')
                shape=face.revolve(vector(p.get('origin',[0,0,0])),vector(p.get('axis',[0,0,1])),angle)
        elif base is None:raise ValueError('Base feature is unavailable or suppressed.')
        elif k=='hole':
            axis=vector(p.get('axis',[0,0,1]));axis.normalize();diameter=float(p.get('diameter',6));depth=float(p.get('depth',10));centers=p.get('centers')
            if diameter<=0 or depth<=0 or not isinstance(centers,list) or not 1<=len(centers)<=256:raise ValueError('Hole needs positive diameter/depth and 1–256 XYZ centers.')
            shape=base.Shape.copy();extent=max(base.Shape.BoundBox.DiagonalLength*2,1)
            for center in centers:
                c=vector(center);through=p.get('through',True)
                cutter=Part.makeCylinder(diameter/2,extent*2 if through else depth,c-axis*extent if through else c,axis)
                shape=shape.cut(cutter)
        elif k in ('fillet','chamfer'):
            amount=float(p.get('radius' if k=='fillet' else 'distance',1))
            if amount<=0:raise ValueError('Fillet/chamfer size must be positive.')
            edges=select_edges(base.Shape,p.get('edges'),params);shape=base.Shape.makeFillet(amount,edges) if k=='fillet' else base.Shape.makeChamfer(amount,edges)
        elif k=='boolean':
            other=objects.get(f['tool'])
            if other is None:raise ValueError('Boolean tool is unavailable.')
            op=p.get('operation','cut')
            if op not in ('cut','fuse','common'):raise ValueError('Boolean operation must be cut, fuse or common.')
            shape=getattr(base.Shape,op)(other.Shape)
        elif k=='pattern':
            count=p.get('count',2)
            if isinstance(count,bool) or count!=int(count) or not 1<=count<=128:raise ValueError('Pattern count must be an integer 1–128.')
            step=vector(p.get('step',[10,0,0]));copies=[]
            for i in range(int(count)):
                copy=base.Shape.copy();copy.translate(step*i);copies.append(copy)
            shape=copies[0].multiFuse(copies[1:]) if p.get('fuse',False) and len(copies)>1 else Part.makeCompound(copies)
        elif k=='transform':
            shape=base.Shape.copy();shape.rotate(vector(p.get('origin',[0,0,0])),vector(p.get('axis',[0,0,1])),float(p.get('angle_deg',0)));shape.translate(vector(p.get('translation',[0,0,0])))
        if shape is None or shape.isNull() or not shape.isValid() or not shape.Solids or any(s.Volume<=1e-9 for s in shape.Solids):raise ValueError('Feature '+f['id']+' did not produce valid positive-volume solids.')
        obj=doc.addObject('PartDesign::Feature',f['id']);obj.Label=f['id'];obj.Shape=shape
        obj.addProperty('App::PropertyString','IntactParameters');obj.IntactParameters=json.dumps(f['params'],sort_keys=True)
        if base is not None:obj.addProperty('App::PropertyLink','InputFeature');obj.InputFeature=base
        if f.get('sketch_id'):obj.addProperty('App::PropertyLink','Profile');obj.Profile=sketches[f['sketch_id']]
        objects[f['id']]=obj
        if request.get('export_nodes'):
            Path('/work/nodes').mkdir(exist_ok=True);shape.exportBrep('/work/nodes/'+f['id']+'.brep')
        if f.get('part_id'):outputs[f['part_id']]=obj
        report['features'].append({'id':f['id'],'kind':k,'part_id':f.get('part_id'),'volume_mm3':shape.Volume,'faces':len(shape.Faces),'suppressed':False,'reused_cached_geometry':cached})
    if not outputs:raise ValueError('Assign part_id to at least one output feature.')
    tips=[]
    for name,obj in outputs.items():
        out=doc.addObject('PartDesign::Feature','Output_'+name);out.Label=name;out.Shape=obj.Shape.copy();tips.append(out)
    doc.recompute();Import.export(tips,'/work/result.step');doc.saveAs('/work/design.FCStd')
    report['part_ids']=list(outputs);Path('/work/report.json').write_text(json.dumps(report,allow_nan=False))

try:main()
except BaseException as exc:
    Path('/work/error.json').write_text(json.dumps({'error':str(exc),'traceback':traceback.format_exc()[-4000:]}));sys.exit(1)
