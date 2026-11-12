# Design prompt: Create a sectioned marine centrifugal pump concept on a rectangular mounting skid, with a blue annular casing opened over one quadrant, visible brass impeller plate and eight radial vanes, inlet flange with bolt holes, tangential outlet and flange, rear bearing cartridge, drive shaft and coaxial finned electric motor. Use through bores and distinguish fluid hardware from rotating hardware. The volute and impeller hydraulics are deliberately simplified.
# Units: mm. Original unverified concept; Z up.
import build123d as bd
import math

def build(params):
    parts = {}
    def add(name, shape, color='#AABAC5'):
        shape.color=bd.Color(color)
        parts[name.replace('-', 'n').replace('.', '_')]=shape
    def box(x,y,z,a,b,c):return bd.Pos(x,y,z)*bd.Box(a,b,c)
    def cyl(x,y,z,r,h):return bd.Pos(x,y,z)*bd.Cylinder(r,h)
    def ring(x,y,z,r,ri,h):return cyl(x,y,z,r,h)-cyl(x,y,z,ri,h+2)
    def bolt(name,x,y,z,r=2.5):
        add(name,cyl(x,y,z,r,4)-box(x,y,z+1,2*r,.8,2),'#C9D2D7')
    add('skid',box(0,0,-163,140,125,10),'#354B5B')
    casing=ring(0,0,0,56,47,35)-box(35,-35,10,70,70,60)
    add('sectioned_casing',casing,'#22788C')
    add('backplate',ring(0,0,-20,56,10,6),'#22788C')
    add('impeller_shroud',ring(0,0,-12,44,10,5),'#C9A455')
    add('impeller_hub',ring(0,0,-2,16,8,23),'#D7B56A')
    for k in range(8):add('impeller_vane_'+str(k),bd.Rot(0,0,k*45)*box(29,0,-3,28,3,14),'#C9A455')
    flange=ring(0,0,24,30,19,7)
    for k in range(6):
        a=k*math.pi/3;flange-=cyl(25*math.cos(a),25*math.sin(a),24,2.5,10)
    add('suction_flange',flange,'#92B9C1')
    add('suction_neck',ring(0,0,16,23,19,12),'#22788C')
    add('outlet_neck',bd.Pos(-48,34,0)*bd.Rot(0,90,0)*ring(0,0,0,16,11,44),'#22788C')
    add('outlet_flange',bd.Pos(-73,34,0)*bd.Rot(0,90,0)*ring(0,0,0,25,11,7),'#92B9C1')
    add('drive_shaft',bd.Pos(0,0,-44)*bd.Cylinder(8,60),'#CAD4D8')
    add('bearing_cartridge',ring(0,0,-40,22,8,26),'#60798B')
    add('motor_stand',box(0,0,-148,70,65,22),'#3A5A68')
    add('motor_body',cyl(0,0,-111,30,68),'#527D85')
    for k in range(10):
        a=k*2*math.pi/10
        add('motor_fin_'+str(k),bd.Pos(30*math.cos(a),30*math.sin(a),-111)*bd.Rot(0,0,a*180/math.pi)*bd.Box(8,3,62),'#829D9F')
    add('terminal_box',box(42,0,-111,20,29,30),'#3B596A')
    for i,a in enumerate((30,90,150,210)):
        bolt('case_bolt_'+str(i),51*math.cos(math.radians(a)),51*math.sin(math.radians(a)),21)

    return parts
