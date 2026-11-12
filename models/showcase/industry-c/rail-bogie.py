# Original Intact concept. Units mm; Z up.
# Design prompt: Create an original compact rail bogie demonstrator, approximately 1500 by 1100 mm, with two wheelsets and four flanged steel wheels, a blue open rectangular frame with cross-members, four axle bearing boxes, four spring stacks using spaced annular rings, a central bored bolster and four brake shoes on hangers. Add visible suspension caps and axle shafts. Keep wheel flanges and wheel treads distinct native features, accurate symmetry and plausible assembly proportions. The rail bogie is a static visual simplification without railway gauge, brake, fatigue or standards compliance claims.
# Simplifications: Four stacks use separated spring rings; simplified one-piece wheels and shoes; no gauge or service suitability asserted.
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
    for s in (-1,1):
        add('side_frame_'+str(s),box(0,s*400,350,1300,85,130)-box(0,s*400,355,1000,95,75),'#316E8F')
    for i,x in enumerate((-580,0,580)):add('frame_crossmember_'+str(i),box(x,0,350,80,880,100),'#477F99')
    add('central_bolster',box(0,0,445,340,1000,65)-cyl(0,0,445,58,70),'#8BA6AF')
    for j,x in enumerate((-480,480)):
        add('axle_'+str(j),rod((x,-590,210),(x,590,210),38),'#BCC6CE')
        for s in (-1,1):
            wheel=cyl(0,0,0,210,80)+cyl(0,0,-44*s,226,15)
            add('flanged_wheel_%s_%s'%(j,s),bd.Pos(x,s*510,210)*bd.Rot(90,0,0)*wheel,'#8E9DA7')
            add('bearing_box_%s_%s'%(j,s),box(x,s*390,220,150,150,100),'#D1A14A')
            for k in range(4):add('spring_%s_%s_%s'%(j,s,k),ring(x,s*390,290+k*18,50,39,8),'#D2D6D8')
            add('suspension_cap_%s_%s'%(j,s),box(x,s*390,365,130,130,15),'#657A87')
            add('brake_shoe_%s_%s'%(j,s),box(x+180,s*510,225,32,75,105),'#344550')
            add('brake_hanger_%s_%s'%(j,s),rod((x+180,s*510,270),(x+160,s*430,350),12),'#6D7D88')
    return parts
