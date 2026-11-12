# Original Intact concept. Units mm; Z up.
# Design prompt: Design an original display-scale electric vehicle drive axle, 660 mm across, with a deliberately opened front half housing exposing a transverse electric motor and offset differential. Use an annular motor stator with copper winding bars, steel rotor and shaft, a bored differential carrier and orange service flange, two half shafts and joint bellows represented by stepped annular ribs. Add housing mounting feet with actual through bores, eight flange bolts and external cooling ribs. Separate named metal, copper, elastomer and orange service parts. Keep all native solids; this is a simplified explanatory concept, without detailed involute gearing or performance claims.
# Simplifications: Front housing deliberately removed; windings and differential are visual abstractions, no tooth contact or electromagnetic analysis.
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
    add('opened_drive_casting',box(0,36,0,320,85,180)-box(0,10,0,290,90,150),'#547D86')
    add('motor_stator',bd.Rot(0,90,0)*ring(0,0,0,73,54,150),'#53626B')
    add('motor_rotor',bd.Rot(0,90,0)*cyl(0,0,0,45,165),'#ABB7BC')
    add('motor_shaft',rod((-130,0,0),(130,0,0),12),'#657580')
    for i in range(12):
        a=2*math.pi*i/12
        add('copper_winding_%02d'%i,box(0,62*math.cos(a),62*math.sin(a),140,8,8),'#C78445')
    add('differential_carrier',bd.Pos(80,-55,-60)*bd.Rot(0,90,0)*ring(0,0,0,48,23,75),'#DDA34A')
    for side in (-1,1):
        add('half_shaft_'+str(side),rod((side*95,-55,-60),(side*330,-55,-60),13),'#BCC4CC')
        for k in range(5): add('boot_%s_%s'%(side,k),bd.Pos(side*(170+k*10),-55,-60)*bd.Rot(0,90,0)*ring(0,0,0,26-k,14,7),'#243A46')
        foot=box(side*132,35,-108,45,65,20)-cyl(side*132,35,-108,7,24)
        add('bored_mount_'+str(side),foot,'#547D86')
    for i in range(6): add('cooling_rib_'+str(i),box(-125+i*50,80,0,6,10,155),'#6D939B')
    for i in range(8):
        a=2*math.pi*i/8
        bolt('flange_bolt_'+str(i),110*math.cos(a),-8,80*math.sin(a),4,18)
    return parts
