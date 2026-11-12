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
    l=params['board_length_mm']; w=params['board_width_mm']
    add('carrier',box(0,0,4,l+20,w+20,8),'#263E50')
    add('mainboard',box(0,0,12,l,w,3),'#28746F')
    add('processor_socket',box(-30,0,17,42,42,6),'#243845')
    add('waterblock_copper',box(-30,0,23,40,40,6),'#CF965E')
    add('waterblock_lid',box(-30,0,29,44,44,7),'#92BCC6')
    for i in range(4):
        add('memory_'+str(i),box(-40+i*22,47,25,13,38,20),'#344C59')
    for i in range(3):
        add('power_stage_'+str(i),box(-58+i*24,-47,19,17,17,10),'#C5CCCD')
    add('rear_io',box(-l/2+5,0,25,16,65,24),'#A9BFC5')
    add('radiator_tank',box(l/2+26,0,30,27,110,45),'#34596B')
    for i in range(10):
        add('radiator_fin_'+str(i),box(l/2+27,-46+i*10,34,47,2.5,40),'#7FA5B2')
    for i,y in enumerate((-14,14)):
        add('block_fitting_'+str(i),ring(-30,y,38,6,3,12),'#D8AB63')
        add('radiator_fitting_'+str(i),ring(l/2+18,y*2,59,6,3,12),'#D8AB63')
        start=(-30,y,44);end=(l/2+18,y*2,65)
        path=bd.Spline(start,(-10,y*2,75),(45,y*3,83),end)
        profile=bd.Plane(origin=start,z_dir=(20,y,31))*bd.Circle(4)
        add('coolant_tube_'+str(i),bd.sweep(profile,path),'#37B4C2')
    for x in (-l/2+10,l/2-10):
        for y in (-w/2+10,w/2-10):
            add('mount_%s_%s'%(x,y),cyl(x,y,10,4,9),'#DAAF68')
    return parts
