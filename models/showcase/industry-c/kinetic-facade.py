# Original Intact concept. Units mm; Z up.
# Design prompt: Create a 1200 by 1000 mm architectural kinetic facade mockup with an open perimeter frame, six individual vertical louver blades set at alternating angles, upper and lower pivot journals, a visible slotted actuator rail, a small actuator box, six linkage rods and corner mounting plates with real bolt bores. Louvers should have folded edge returns and a thin panel web rather than solid deep blocks. Use ivory blades, blue-grey frame and brass pivots and linkage. All components native and separately named; depict a fixed demonstration pose without wind, thermal or building-code claims.
# Simplifications: Static alternating blade pose; actuator is a visual enclosure and linkage, with no collision or wind analysis.
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
        add('vertical_frame_'+str(s),box(s*610,0,500,40,90,1040),'#547888')
        add('horizontal_frame_'+str(s),box(0,0,500+s*500,1180,90,40),'#547888')
    for i in range(6):
        x=-500+i*200;ang=25 if i%2==0 else -25
        blade=box(0,0,500,165,4,930)+box(-80,9,500,5,20,930)+box(80,9,500,5,20,930)
        add('folded_louver_'+str(i),bd.Pos(x,0,0)*bd.Rot(0,0,ang)*blade,'#D6D5C6')
        for j,z in enumerate((25,975)):add('pivot_%s_%s'%(i,j),ring(x,0,z,13,6,34),'#D4AA59')
        add('linkage_'+str(i),rod((x,0,995),(x+35,85,1030),5),'#C7A15A')
    rail=box(0,85,1030,1150,28,14)
    for x in range(-500,501,200):rail=rail-box(x,85,1030,65,10,20)
    add('slotted_actuator_rail',rail,'#8FA1AA')
    add('actuator_enclosure',box(670,45,1000,95,130,90)-box(670,5,1000,75,100,65),'#2D5368')
    for i,(x,z) in enumerate([(-610,0),(610,0),(-610,1000),(610,1000)]):
        add('bored_mount_plate_'+str(i),box(x,60,z,90,12,80)-bd.Pos(x,60,z)*bd.Rot(90,0,0)*cyl(0,0,0,8,18),'#98A9AF')
    return parts
