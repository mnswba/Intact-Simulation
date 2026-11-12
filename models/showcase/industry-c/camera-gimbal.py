# Original Intact concept. Units mm; Z up.
# Design prompt: Create an original three-axis tabletop camera gimbal with a bored mounting base, vertical yaw motor, offset roll motor and U-shaped tilt cradle carrying a compact camera. Include separate concentric motor caps, mounting holes, exposed mounting bolts, lens barrel with three rings and blue lens glass, camera shell with a rear screen, and vent cuts. Use black camera, teal motor housings, gold caps and silver cradle. Native solids and distinct descriptive part IDs; fixed pose only without motion range, balancing, optics or payload claims.
# Simplifications: Static pose, generic motors and solid optical glass; no cables, optical prescription, balancing or motion envelope analysis.
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
    base=box(0,0,8,150,125,16)
    for x in (-55,55):
        for y in (-42,42):base=base-cyl(x,y,8,5,22)
    add('bored_base',base,'#8095A0')
    add('yaw_motor',ring(0,0,44,40,10,55),'#23788A')
    add('yaw_cap',ring(0,0,74,34,10,6),'#D1A154')
    add('yaw_arm',box(-48,0,130,24,40,112)+box(-22,0,83,75,40,18),'#A6B7BE')
    add('roll_motor',bd.Pos(-48,0,180)*bd.Rot(0,90,0)*ring(0,0,0,35,8,32),'#23788A')
    add('roll_cap',bd.Pos(-68,0,180)*bd.Rot(0,90,0)*ring(0,0,0,30,8,6),'#D1A154')
    cradle=box(14,0,150,100,24,14)+box(60,0,194,14,24,90)+box(-28,0,170,14,24,42)
    add('tilt_cradle',cradle,'#A6B7BE')
    add('tilt_motor',bd.Pos(63,0,218)*bd.Rot(0,90,0)*ring(0,0,0,28,7,28),'#23788A')
    shell=box(10,0,218,80,60,53)-box(10,-3,218,72,54,45)
    for x in (-15,-5,5,15,25):shell=shell-box(x,30,218,3,8,25)
    add('vented_camera_body',shell,'#293C49')
    add('camera_back_screen',box(10,32,218,65,3,37),'#26607A')
    for i,(y,r,h) in enumerate([(-38,25,16),(-50,23,8),(-59,25,10)]):add('lens_barrel_'+str(i),bd.Pos(10,y,218)*bd.Rot(90,0,0)*ring(0,0,0,r,19,h),'#4E606B')
    add('lens_glass',bd.Pos(10,-65,218)*bd.Rot(90,0,0)*cyl(0,0,0,18,2),'#28788B')
    for i in range(6):
        a=2*math.pi*i/6;bolt('base_motor_bolt_'+str(i),29*math.cos(a),29*math.sin(a),76,2,8)
    for i,x in enumerate((-18,38)):bolt('camera_mount_bolt_'+str(i),x,0,156,2,12)
    return parts
