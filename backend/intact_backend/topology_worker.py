"""Trusted OpenCASCADE inspection; imported only inside the CAD sandbox."""
import math
from OCP.BRepAdaptor import BRepAdaptor_Surface, BRepAdaptor_Curve
import build123d as bd

def xyz(v):
    return [float(v.X()),float(v.Y()),float(v.Z())] if callable(v.X) else [float(v.X),float(v.Y),float(v.Z)]
def box(shape):
    b=shape.bounding_box()
    return {'min':xyz(b.min),'max':xyz(b.max),'size':xyz(b.size)}
def inspect_part(name,shape,linear_deflection=None,angular_deflection=.15):
    bounds=shape.bounding_box();cx=(bounds.min.X+bounds.max.X)/2;cy=(bounds.min.Y+bounds.max.Y)/2;z0=bounds.min.Z
    def local(v):return [float(v.X-cx),float(v.Z-z0),float(-(v.Y-cy))]
    positions=[];indices=[];faces=[];edges=[];vertices=[]
    tolerance=linear_deflection if linear_deflection is not None else max(.025,min(bounds.size.X,bounds.size.Y,bounds.size.Z)/1000)
    for i,f in enumerate(shape.faces()):
        ref=f'{name}.f{i+1}';verts,tris=f.tessellate(tolerance,angular_deflection);offset=len(positions)//3;start=len(indices)//3
        positions.extend(c for v in verts for c in local(v));indices.extend(offset+int(k) for tri in tris for k in tri)
        item={'ref':ref,'kind':'face','part_id':name,'index':i+1,'geometry':f.geom_type.name.lower(),'area_mm2':float(f.area),'center':xyz(f.center(bd.CenterOf.MASS)),'bounds':box(f),'triangle_start':start,'triangle_count':len(tris)}
        a=BRepAdaptor_Surface(f.wrapped)
        if item['geometry']=='plane':item['normal']=xyz(f.normal_at())
        if item['geometry'] in ('cylinder','sphere','cone','torus'):
            surface=getattr(a,item['geometry'].capitalize())()
            if item['geometry'] in ('cylinder','sphere'):item['radius_mm']=surface.Radius()
            if item['geometry']=='torus':item.update(major_radius_mm=surface.MajorRadius(),minor_radius_mm=surface.MinorRadius())
            if item['geometry']=='cone':item.update(radius_mm=surface.RefRadius(),semi_angle_rad=surface.SemiAngle())
            if item['geometry']!='sphere':item.update(axis=xyz(surface.Axis().Direction()),axis_origin=xyz(surface.Axis().Location()))
            else:item['axis_origin']=xyz(surface.Location())
        faces.append(item)
    for i,e in enumerate(shape.edges()):
        a=BRepAdaptor_Curve(e.wrapped);first=a.FirstParameter();last=a.LastParameter();kind=e.geom_type.name.lower();count=2 if kind=='line' else min(129,max(17,int(e.length/max(tolerance*20,.1))))
        samples=[xyz(a.Value(first+(last-first)*j/(count-1))) for j in range(count)]
        item={'ref':f'{name}.e{i+1}','kind':'edge','part_id':name,'index':i+1,'geometry':kind,'length_mm':float(e.length),'center':xyz(e.center(bd.CenterOf.MASS)),'bounds':box(e),'samples':samples,'start':samples[0],'end':samples[-1]}
        if kind=='circle':
            circle=a.Circle();item.update(radius_mm=circle.Radius(),axis=xyz(circle.Axis().Direction()),axis_origin=xyz(circle.Location()))
        edges.append(item)
    for i,v in enumerate(shape.vertices()):vertices.append({'ref':f'{name}.v{i+1}','kind':'vertex','part_id':name,'index':i+1,'point':xyz(v.center())})
    if len(faces)>10000 or len(edges)>30000:raise ValueError('Topology inspection limit exceeded; simplify the part.')
    return {'id':name,'positions':positions,'indices':indices,'face_groups':[{'ref':f['ref'],'start':f['triangle_start'],'count':f['triangle_count']} for f in faces]}, {'id':name,'faces':faces,'edges':edges,'vertices':vertices}

def imported_parts(shape):
    result={}
    def visit(s):
        if s.children:
            for c in s.children:visit(c)
        elif s.solids():
            import re
            key=re.sub('[^a-z0-9_]+','_',s.label.lower()).strip('_')[:40] or 'part'
            if not key[0].isalpha():key='part_'+key
            base=key;n=2
            while key in result:key=f'{base}_{n}';n+=1
            result[key]=s
    visit(shape)
    if not result and shape.solids():result['model']=shape
    return result
