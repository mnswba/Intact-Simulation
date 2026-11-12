# Original Intact concept. Units mm; Z up.
# Design prompt: Build a native ventilated brake assembly displayed in slight axial separation so its internal vanes are visible. Use two 280 mm outer diameter drilled friction rings with 12 radial ventilation vanes between them, a central hat with five mounting bores, a bridge caliper with disc clearance, two separate friction pads and backing plates, two cylindrical pistons with bores, two retaining pins and visible fasteners. Use steel grey friction faces, dark iron hat, copper-brown pads and a coral red caliper. Disc perforations and hat bores must be actual cuts. This is an original visual engineering study without certification, friction or thermal performance claims.
# Simplifications: Slightly separated disc faces expose ventilation; pad and caliper geometry simplified, no hydraulic seals or threads.
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
    for j,z in enumerate((-10,10)):
        disc=ring(0,0,z,140,80,7)
        for i in range(18):
            a=2*math.pi*i/18
            disc=disc-cyl(115*math.cos(a),115*math.sin(a),z,4,11)
        add('drilled_friction_ring_'+str(j),disc,'#AEBAC2')
    for i in range(12):
        a=i*30
        add('ventilation_vane_'+str(i),bd.Rot(0,0,a)*box(108,0,0,50,5,13),'#63737B')
    hat=ring(0,0,-23,83,30,18)
    for i in range(5):
        a=2*math.pi*i/5
        hat=hat-cyl(52*math.cos(a),52*math.sin(a),-23,6,24)
    add('five_bore_disc_hat',hat,'#384F5C')
    cal=box(119,0,0,66,118,68)-box(100,0,0,65,92,39)
    add('bridge_caliper',cal,'#CE614C')
    for i,z in enumerate((-21,21)):
        add('friction_pad_'+str(i),box(107,0,z,32,76,8),'#B48253')
        add('pad_backing_'+str(i),box(107,0,z*1.35,38,84,4),'#53626B')
        for k,y in enumerate((-25,25)):add('caliper_piston_%s_%s'%(i,k),ring(116,y,z*1.5,13,9,12),'#C6D0D5')
    for i,y in enumerate((-49,49)):
        add('retaining_pin_'+str(i),rod((98,y,-38),(98,y,38),3),'#D8DCE0')
        bolt('caliper_bolt_'+str(i),140,y,0,4,70)
    return parts
