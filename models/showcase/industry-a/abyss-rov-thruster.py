# Design prompt: Create an original underwater ROV ducted thruster with a 110 mm inside-diameter annular nozzle, four hydrofoil-like flat pitched propeller blades on an orange hub, sealed central motor capsule, three radial rear stator supports, front protective grille bars, twin mounting saddles, drilled mounting feet, cable gland and end cap fasteners. Preserve an open flow path; use simplified blade sections and unverified sealing.
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
    r=params.get('duct_radius_mm',60)
    add('duct',ring(0,0,0,r,r-5,56),'#307D8E')
    add('front_lip',ring(0,0,29,r+3,r-5,5),'#90ABB2')
    add('rear_lip',ring(0,0,-29,r+3,r-5,5),'#90ABB2')
    add('motor_capsule',cyl(0,0,-17,17,60),'#718A9A')
    add('motor_rear_cap',cyl(0,0,-49,18,5),'#A8BCC5')
    add('propeller_hub',bd.Pos(0,0,18)*bd.Cone(20,9,22),'#DF964A')
    for k in range(4):
        blade=bd.Pos(34,0,12)*bd.Rot(23,0,0)*bd.Box(38,20,4)
        add('pitched_blade_'+str(k),bd.Rot(0,0,k*90)*blade,'#DF964A')
    for k in range(3):add('rear_stator_'+str(k),bd.Rot(0,0,k*120)*box(36,0,-23,40,4,10),'#698493')
    for k in range(-2,3):
        y=k*18;span=2*math.sqrt((r-4)**2-y*y)
        add('guard_bar_'+str(k+2),box(0,y,35,span,3,3),'#C0CDD1')
    for i,x in enumerate((-35,35)):
        add('mount_saddle_'+str(i),box(x,-57,0,15,24,25),'#3D5F70')
        foot=box(x,-72,0,24,6,54)
        for z in (-18,18):foot-=bd.Pos(x,-72,z)*bd.Rot(90,0,0)*bd.Cylinder(3,10)
        add('mount_foot_'+str(i),foot,'#7C96A4')
    add('cable_gland',bd.Pos(0,0,-58)*ring(0,0,0,8,4,14),'#C7AB6C')
    for k in range(6):
        a=k*math.pi/3;bolt('endcap_bolt_'+str(k),13*math.cos(a),13*math.sin(a),-52,1.8)

    return parts
