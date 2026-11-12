# Original Intact concept. Units mm; Z up.
# Design prompt: Create an original exposed double wishbone suspension corner with a 360 mm tall outboard upright, two triangular tubular wishbones, bored inboard pivots and a tilted coil-over damper. Include upper and lower ball joint housings, an annular wheel hub with five genuine bolt bores, separate wheel studs, damper body and piston rod, and eight spaced coil-like spring rings. Show blue links, silver hub, dark pivots and a red spring. The spring uses individual annular rings as an explicit static simplification. Use native parts and realistic component proportions; no vehicle fitment or load claims.
# Simplifications: Static spring rings approximate a helical spring; no steering sweep or chassis fitment verification.
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
    add('upright',box(160,0,155,28,42,220)-bd.Pos(160,0,110)*bd.Rot(90,0,0)*cyl(0,0,0,16,60),'#718A97')
    for level,z,w in [('lower',50,115),('upper',255,85)]:
        for s in (-1,1):
            add(level+'_arm_'+str(s),rod((-100,s*w,z),(155,0,z),13),'#2C83A6')
            add(level+'_pivot_'+str(s),bd.Pos(-100,s*w,z)*bd.Rot(90,0,0)*ring(0,0,0,22,10,45),'#344653')
            bolt(level+'_pivot_bolt_'+str(s),-100,s*w,z,5,42)
        add(level+'_ball_joint',cyl(155,0,z,25,25),'#ABB7C1')
    hub=ring(0,0,0,78,20,22)
    for i in range(5):
        a=i*2*math.pi/5;hub=hub-cyl(52*math.cos(a),52*math.sin(a),0,6,26)
    add('five_bore_hub',bd.Pos(183,0,110)*bd.Rot(0,90,0)*hub,'#C2CBD0')
    for i in range(5):
        a=i*2*math.pi/5
        add('wheel_stud_'+str(i),rod((180,52*math.cos(a),110+52*math.sin(a)),(218,52*math.cos(a),110+52*math.sin(a)),4),'#535F6C')
    add('damper_body',rod((30,0,55),(-45,0,255),19),'#DCA543')
    add('damper_piston',rod((-45,0,255),(-68,0,320),9),'#CAD2DA')
    for i in range(8):
        add('spring_turn_'+str(i),bd.Plane(origin=(20-i*8,0,85+i*22),z_dir=(-75,0,200))*ring(0,0,0,36,30,8),'#DC674B')
    for i,(x,z) in enumerate([(30,55),(-68,320)]):add('damper_eye_'+str(i),bd.Pos(x,0,z)*bd.Rot(90,0,0)*ring(0,0,0,20,9,22),'#506976')
    return parts
