# Design prompt: Create an original precision upright optical microscope concept with a sculptural bored arch stand, heavy foot, rectangular specimen stage with central aperture and two slide clips, vertical rack carriage, paired coaxial focus knobs, three-objective revolving nosepiece, angled binocular viewing head and two eyepieces, substage condenser and illumination base. Use contrasting ivory body, charcoal optics and teal adjustment details. Optical alignment and actual magnification remain conceptual.
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
    base=box(0,0,8,135,110,16)-box(0,-38,11,55,24,10)
    add('weighted_foot',base,'#CCD9D7')
    stand=box(0,34,95,65,35,170)-box(0,20,95,39,35,100)
    add('arch_stand',stand,'#C4D5D3')
    add('upper_arm',box(0,0,174,62,96,20),'#C4D5D3')
    add('stage_carriage',box(0,12,90,44,34,48),'#637E8E')
    add('stage',box(0,-16,106,104,83,9)-cyl(0,-16,106,15,14),'#344D5C')
    for i,x in enumerate((-26,26)):add('slide_clip_'+str(i),box(x,-16,113,5,43,3),'#C6D5D8')
    add('slide',box(0,-16,112,24,60,1.5),'#94BCC1')
    add('nose_turret',cyl(0,-18,153,29,8),'#536D80')
    for k in range(3):
        a=k*2*math.pi/3;x=19*math.cos(a);y=-18+19*math.sin(a)
        add('objective_barrel_'+str(k),ring(x,y,136,8,5,28),'#B2C5CA')
        add('objective_tip_'+str(k),ring(x,y,120,6,4,6),'#364E5B')
    add('binocular_head',bd.Pos(0,-12,193)*bd.Rot(25,0,0)*bd.Box(60,45,28),'#D0DEDA')
    for i,x in enumerate((-19,19)):
        add('eyepiece_'+str(i),bd.Pos(x,-26,216)*bd.Rot(25,0,0)*ring(0,0,0,11,7,30),'#344C5A')
        add('eyecup_'+str(i),bd.Pos(x,-33,230)*bd.Rot(25,0,0)*ring(0,0,0,14,7,7),'#263C48')
    add('condenser',ring(0,-16,85,20,11,22),'#697F8D')
    add('illumination_lens',cyl(0,-16,22,21,9),'#87B2B9')
    for i,side in enumerate((-1,1)):
        add('coarse_focus_'+str(i),bd.Pos(side*43,29,78)*bd.Rot(0,90,0)*bd.Cylinder(19,14),'#3F737E')
        add('fine_focus_'+str(i),bd.Pos(side*54,29,78)*bd.Rot(0,90,0)*bd.Cylinder(9,9),'#86B5B7')
    for k in range(6):add('rack_tooth_'+str(k),box(24,14,65+k*9,5,15,3),'#A9BAC2')

    return parts
