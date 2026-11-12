# Original Intact concept. Units mm; Z up.
# Design prompt: Create an original cordless drill-driver cutaway about 260 mm tall with a half-open orange grip and motor shell, visible cylindrical electric motor, copper windings, planetary-style reduction carrier with four simplified bored planet discs, coaxial chuck and jaws. Include a detachable battery pack with six visible cylindrical cells, trigger, vent slots, belt clip and housing screws. Use orange polymer, dark grip and battery, copper motor elements and steel mechanisms. Keep native positive-volume components. This is a visual concept without exact tooth profiles, electrical specifications, torque or safety claims.
# Simplifications: Half-open visual shell and simple planet discs omit gear teeth, cell wiring, threads and certified electrical or torque behavior.
import build123d as bd
import math

def build(params):
    parts={}
    def add(n,s,c='#A8B5BF'):
        s=s.scale(params.get('scale',1.0)); s.color=bd.Color(c); parts[n.replace('-', 'neg')]=s
    def box(x,y,z,l,w,h): return bd.Pos(x,y,z)*bd.Box(l,w,h)
    def cyl(x,y,z,r,h): return bd.Pos(x,y,z)*bd.Cylinder(r,h)
    def ring(x,y,z,ro,ri,h): return cyl(x,y,z,ro,h)-cyl(x,y,z,ri,h+2)
    def rod(a,b,r):
        d=bd.Vector(b)-bd.Vector(a); p=(bd.Vector(a)+bd.Vector(b))*0.5
        return bd.Plane(origin=p,z_dir=d)*bd.Cylinder(r,d.length)
    def bolt(n,x,y,z,r=3,h=12):
        add(n,cyl(x,y,z,r,h)+cyl(x,y,z+h/2,r*1.65,r*1.1),'#596674')
    shell=box(0,18,190,155,40,75)-box(0,0,190,140,48,61)
    for x in (-55,-40,-25):shell=shell-box(x,37,190,6,10,42)
    add('open_motor_shell',shell,'#DA8241')
    add('grip_half',box(-20,15,100,48,30,130)-box(-20,0,100,34,32,110),'#344B58')
    add('motor_stator',bd.Pos(-35,0,190)*bd.Rot(0,90,0)*ring(0,0,0,30,21,70),'#7C929D')
    add('rotor_shaft',rod((-76,0,190),(55,0,190),8),'#CBD3D9')
    for i in range(8):
        a=i*math.pi/4;add('copper_winding_'+str(i),box(-35,25*math.cos(a),190+25*math.sin(a),60,5,5),'#C48549')
    add('reduction_carrier',bd.Pos(27,0,190)*bd.Rot(0,90,0)*ring(0,0,0,32,8,9),'#C4A05B')
    for i in range(4):
        a=i*math.pi/2;add('planet_disc_'+str(i),bd.Pos(40,20*math.cos(a),190+20*math.sin(a))*bd.Rot(0,90,0)*ring(0,0,0,9,3,18),'#A8B8C1')
    add('chuck_body',bd.Pos(90,0,190)*bd.Rot(0,90,0)*ring(0,0,0,27,9,53),'#4A606F')
    for i in range(3):
        a=i*2*math.pi/3;add('chuck_jaw_'+str(i),rod((106,9*math.cos(a),190+9*math.sin(a)),(124,5*math.cos(a),190+5*math.sin(a)),3),'#BCC8CF')
    pack=box(-15,0,20,104,80,40)-box(-15,-10,30,92,70,34)
    add('open_battery_pack',pack,'#263E4C')
    for i in range(6):add('battery_cell_'+str(i),bd.Pos(-49+i*14,0,24)*bd.Rot(90,0,0)*cyl(0,0,0,6,60),'#5E9C93')
    add('trigger',box(3,-3,145,18,36,20),'#DA8241')
    add('belt_clip',box(-45,38,90,10,5,70)+box(-34,38,124,26,5,5),'#9CAEB9')
    for i,(x,z) in enumerate([(-68,165),(55,165),(-35,60),(-35,130)]):bolt('housing_screw_'+str(i),x,23,z,2,8)
    return parts
