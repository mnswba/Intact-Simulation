# Design prompt: Build an original compact aircraft dual-wheel landing gear concept with a tall telescopic oleo strut, upper mounting clevis, lower fork, twin hollow rubber tires with silver drilled hubs, axle, articulated torque links, exposed brake discs, hydraulic line and securing bolts. Use a vertical strut and transverse wheel axle; show recognizable load paths and simplified mechanical joints without claiming an aircraft rating.
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
    h=params.get('strut_height_mm',180)
    add('outer_oleo',ring(0,0,h/2+45,18,12,h),'#A8B9C2')
    add('piston',cyl(0,0,52,11,94),'#D9E0E3')
    add('seal_collar',ring(0,0,48,20,11,12),'#364E60')
    add('upper_clevis',box(0,0,h+53,56,28,22)-bd.Pos(0,0,h+53)*bd.Rot(90,0,0)*bd.Cylinder(7,32),'#B5C6CF')
    add('axle',bd.Pos(0,0,0)*bd.Rot(90,0,0)*bd.Cylinder(8,126),'#CBD3D5')
    for side in (-1,1):
        tag='port' if side<0 else 'starboard'
        add(tag+'_fork',box(0,side*25,27,14,9,62),'#A8B9C2')
        tire=ring(0,0,0,45,27,24)
        add(tag+'_tire',bd.Pos(0,side*48,0)*bd.Rot(90,0,0)*tire,'#27313C')
        hub=ring(0,0,0,27,8,26)
        for k in range(6):
            a=k*math.pi/3
            hub-=cyl(17*math.cos(a),17*math.sin(a),0,4,30)
        add(tag+'_hub',bd.Pos(0,side*48,0)*bd.Rot(90,0,0)*hub)
        add(tag+'_brake',bd.Pos(0,side*31,0)*bd.Rot(90,0,0)*ring(0,0,0,31,10,4),'#8F989A')
        add(tag+'_axle_cap',bd.Pos(0,side*64,0)*bd.Rot(90,0,0)*bd.Cylinder(12,5),'#D0B16B')
        for k in range(5):
            a=k*2*math.pi/5
            add(tag+'_hub_bolt_'+str(k),bd.Pos(13*math.cos(a),side*63,13*math.sin(a))*bd.Rot(90,0,0)*bd.Cylinder(2,4))
    for i,z in enumerate((68,105)):
        add('torque_link_'+str(i),bd.Pos(22,0,z)*bd.Rot(0,35 if i==0 else -35,0)*bd.Box(9,13,46),'#657C8E')
        add('link_pin_'+str(i),bd.Pos(27,0,z)*bd.Rot(90,0,0)*bd.Cylinder(4,24),'#D1B06A')
    add('hydraulic_line',cyl(-23,6,105,2,120),'#4D6574')

    return parts
