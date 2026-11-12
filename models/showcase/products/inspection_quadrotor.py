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
    reach=params['arm_reach_mm']; prop=params['prop_radius_mm']
    add('lower_chassis',cyl(0,0,25,45,12),'#203744')
    sections=[bd.Plane.XY.offset(z)*bd.Ellipse(rx,ry) for z,rx,ry in [(32,43,34),(48,37,28),(63,17,18)]]
    add('canopy',bd.loft(sections),'#F2A344')
    add('top_marker',cyl(0,0,64,9,3),'#233C4E')
    for i,a in enumerate((45,135,225,315)):
        rad=math.radians(a);x=reach*math.cos(rad);y=reach*math.sin(rad)
        add('arm_'+str(i),bd.Rot(0,0,a)*box(reach/2,0,25,reach,16,10),'#536B77')
        add('motor_'+str(i),cyl(x,y,37,15,22),'#1D303B')
        add('motor_band_'+str(i),cyl(x,y,45,15.5,3),'#DC9D48')
        add('propeller_'+str(i),bd.Pos(x,y,52)*bd.Rot(0,0,a+25)*bd.extrude(bd.Ellipse(prop,7),amount=2),'#D0E4E6')
        add('guard_'+str(i),ring(x,y,54,prop+7,prop+4,8),'#357B83')
        add('guard_strut_'+str(i),bd.Pos(x,y,47)*bd.Rot(0,0,a)*bd.Box(2*(prop+4),4,3),'#357B83')
    for side in (-1,1):
        add('landing_rail_'+str(side),box(side*34,0,3,6,92,6)+box(side*34,-30,13,6,6,20)+box(side*34,30,13,6,6,20),'#263E4A')
    add('camera_yoke',box(0,-40,16,28,8,12),'#829AA3')
    add('camera_body',box(0,-47,14,23,19,18),'#223541')
    add('lens',bd.Pos(0,-60,14)*bd.Rot(90,0,0)*bd.Cylinder(8,9),'#36A4B4')
    return parts
