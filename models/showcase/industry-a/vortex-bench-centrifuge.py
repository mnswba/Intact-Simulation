# Design prompt: Create an original benchtop laboratory centrifuge teaching cutaway. Model a pale housing with the front-right quarter removed, a stainless bowl, six-place rotor with angled-looking tube pockets represented as vertical bores, six red-capped sample tubes, exposed central spindle and motor, elevated open lid with hinge blocks, control display and keys, four rubber feet and a vent strip. Use native positive solids and label the rotor balance and containment as unverified.
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
    shell=box(0,0,45,160,150,90)-box(0,0,51,148,138,90)
    shell-=box(60,-55,60,100,110,100)
    add('sectioned_housing',shell,'#D0DEDE')
    add('chamber_bowl',ring(0,0,65,63,59,44)-box(45,-45,65,90,90,50),'#95ADB6')
    rotor=cyl(0,0,69,51,13)
    for k in range(6):
        a=k*math.pi/3;x=37*math.cos(a);y=37*math.sin(a)
        rotor-=cyl(x,y,69,7,18)
        add('sample_tube_'+str(k),ring(x,y,76,6,4.5,30),'#9BC0C4')
        add('tube_cap_'+str(k),cyl(x,y,93,7,5),'#C77972')
    add('six_place_rotor',rotor,'#547A91')
    add('spindle',cyl(0,0,47,6,52),'#C8D4D9')
    add('motor',cyl(0,0,25,25,34),'#6B8494')
    add('motor_endcap',ring(0,0,7,27,6,4),'#B1C2C8')
    lid=box(0,55,147,158,14,110)-box(0,54,147,131,18,80)
    add('open_lid_frame',lid,'#C2D5D6')
    add('lid_inner_window',box(0,56,147,130,5,78),'#7EACB8')
    for i,x in enumerate((-55,55)):add('lid_hinge_'+str(i),bd.Pos(x,67,93)*bd.Rot(0,90,0)*bd.Cylinder(7,24),'#859FA8')
    add('control_console',box(0,-79,28,90,15,35),'#B7CCCC')
    add('display',box(-15,-88,32,39,2,17),'#183E52')
    for k in range(3):add('control_key_'+str(k),box(14+k*12,-88,31,7,3,7),'#53949B')
    for k in range(5):add('vent_'+str(k),box(81,-20+k*10,28,2,5,21),'#526A76')
    for i,(x,y) in enumerate(((-62,-55),(62,-55),(-62,55),(62,55))):add('foot_'+str(i),cyl(x,y,-4,9,8),'#344653')

    return parts
