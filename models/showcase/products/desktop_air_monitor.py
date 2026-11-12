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
    w=params['width_mm']; d=params['depth_mm']; h=params['height_mm']
    shell=box(0,0,h/2,w,d,h)-box(0,0,h/2+3,w-6,d-6,h)
    for x in range(-40,41,10):
        shell=shell-box(x,-d/2,h*0.48,4,10,28)
    add('vented_lower_shell',shell,'#D2DDDA')
    add('pcb',box(0,0,12,w-15,d-15,2),'#226B63')
    for i,(x,y,l,ww) in enumerate([(-25,0,24,22),(16,8,22,26),(28,-21,18,12),(-22,25,24,12)]):
        add('board_component_'+str(i),box(x,y,17,l,ww,8),'#293E48')
    add('sensor_chamber',box(-25,0,26,28,25,11)-box(-25,-11,26,18,8,7),'#B2C6CD')
    add('display_carrier',box(17,0,38,43,36,5),'#263D49')
    add('display_glass',box(17,0,41,37,28,2),'#134B60')
    for i,l in enumerate((25,17,22)):
        add('display_indicator_'+str(i),box(15,9-i*8,42.3,l,2,0.5),'#75DDD2')
    cover=box(0,0,0,w,d,6)-box(17,0,0,39,30,10)
    for x in range(-43,-10,8):
        cover=cover-box(x,0,0,3,48,10)
    add('lifted_vented_cover',bd.Pos(0,26,h+22)*bd.Rot(-22,0,0)*cover,'#F0B164')
    for x in (-w/2+9,w/2-9):
        for y in (-d/2+9,d/2-9):
            add('standoff_%s_%s'%(x,y),ring(x,y,8,3,1.3,10),'#D3A25B')
    add('rear_connector',box(0,d/2+1,15,16,8,8),'#526F79')
    return parts
