# Original Intact gallery concept. Units: millimetres; CAD Z is up.
import build123d as bd
import math

def build(params):
    parts = {}
    def add(name, shape, color):
        shape.color = bd.Color(color)
        parts[name.replace('-', 'n').replace('.', '_')] = shape
    def box(x,y,z,l,w,h):
        return bd.Pos(x,y,z)*bd.Box(l,w,h)
    def cyl(x,y,z,r,h):
        return bd.Pos(x,y,z)*bd.Cylinder(r,h)
    def ring(x,y,z,ro,ri,h):
        return cyl(x,y,z,ro,h)-cyl(x,y,z,ri,h+2)
    pitch=params['cell_pitch_mm']; r=params['cell_radius_mm']; h=params['cell_height_mm']
    add('cooling_plate',box(0,0,5,150,112,10),'#75B7BF')
    add('sectioned_housing',box(0,0,0,160,122,4)+box(0,59,41,160,4,80)+box(-78,0,41,4,118,80),'#243E50')
    for i in range(4):
        for j in range(3):
            x=(i-1.5)*pitch;y=(j-1)*pitch
            add('cell_%d_%d'%(i,j),cyl(x,y,14+h/2,r,h),'#B7C9CC')
            add('terminal_%d_%d'%(i,j),cyl(x,y,15+h,4,2),'#EAC16B')
    for j in range(3):
        y=(j-1)*pitch
        add('busbar_%d'%j,box(0,y,h+17,3*pitch+12,9,2),'#CF8B52')
    add('inlet_manifold',box(0,-62,6,130,12,15),'#357A8E')
    for x in (-52,52):
        add('hose_port_'+str(x),bd.Pos(x,-74,6)*bd.Rot(90,0,0)*bd.Cylinder(6,18),'#C6D3DA')
    for i in range(4):
        add('cooling_channel_rib_'+str(i),box((i-1.5)*32,0,12,7,100,4),'#357A8E')
    return parts
