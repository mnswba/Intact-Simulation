# Design prompt: Create an original robotic surgical gripper mechanism teaching concept with a slender hollow instrument shaft, exposed proximal drive drum and bracket, distal two-jaw clevis, two tapered-looking jaws built from stepped solids with six gripping teeth each, separated pivot pins, exposed pull-rod and paired actuation links. Add colored insulating collar, cable pulleys, instrument coupling and mounting fasteners. Enlarge distal mechanism for inspection and clearly label it unsuitable for clinical use without engineering and regulatory validation.
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
    length=params.get('shaft_length_mm',180)
    add('instrument_shaft',ring(0,0,length/2,7,4,length),'#B8C8CD')
    add('pull_rod',cyl(0,0,length/2+8,2, length+28),'#708C9D')
    add('insulation_collar',ring(0,0,20,9,7,20),'#4394A2')
    add('distal_clevis',box(0,0,length+8,24,12,22)-box(0,0,length+10,15,16,23),'#8BA4B2')
    for side in (-1,1):
        tag='left' if side<0 else 'right'
        jaw=box(side*8,0,length+35,7,8,38)+box(side*5.5,0,length+55,4,6,12)
        jaw-=bd.Pos(side*8,0,length+19)*bd.Rot(90,0,0)*bd.Cylinder(2,14)
        add(tag+'_jaw',jaw,'#BCCCD2')
        for k in range(6):add(tag+'_grip_tooth_'+str(k),box(side*4,0,length+32+k*4,2,7,1.6),'#91A8B6')
        add(tag+'_pivot',bd.Pos(side*8,0,length+19)*bd.Rot(90,0,0)*bd.Cylinder(2,17),'#C8AB6D')
        add(tag+'_actuation_link',bd.Pos(side*4,0,length+12)*bd.Rot(0,side*24,0)*bd.Box(3,3,18),'#637F93')
    add('proximal_coupling',ring(0,0,-13,18,7,25),'#597C8E')
    add('drive_bracket',box(0,0,-36,68,40,10)-cyl(0,0,-36,8,14),'#98B0BD')
    for i,x in enumerate((-23,23)):
        add('cable_pulley_'+str(i),bd.Pos(x,0,-21)*bd.Rot(90,0,0)*ring(0,0,0,14,4,10),'#CC9A57')
        add('pulley_axle_'+str(i),bd.Pos(x,0,-21)*bd.Rot(90,0,0)*bd.Cylinder(4,16),'#C7D3D6')
    for i,(x,y) in enumerate(((-27,-13),(-27,13),(27,-13),(27,13))):bolt('mount_fastener_'+str(i),x,y,-29,2.5)

    return parts
