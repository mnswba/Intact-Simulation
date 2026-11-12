# Design prompt: Create a detailed original small Earth-observation satellite concept with a 120 mm cube gold thermal bus, four silver structural corner rails, two deployed dark-blue segmented solar wings on hinge barrels, visible cell interconnects, an optical payload barrel and recessed dark aperture, twin dish communication elements, a top star tracker, antenna rods and launch attachment feet. Keep each material or manufactured element named and separately selectable; simplify optical and electrical function.
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
    s=params.get('bus_size_mm',120)
    add('thermal_bus',box(0,0,0,s,s,s),'#BE9146')
    for x in (-s/2,s/2):
        for y in (-s/2,s/2):
            add('rail_'+str(int(x))+'_'+str(int(y)),box(x,y,0,7,7,s+10))
            add('launch_foot_'+str(int(x))+'_'+str(int(y)),ring(x,y,-s/2-7,8,3,6))
    for side in (-1,1):
        tag='left' if side<0 else 'right'
        add(tag+'_hinge',bd.Pos(side*(s/2+8),0,0)*bd.Rot(90,0,0)*bd.Cylinder(6,64),'#B7C4CA')
        add(tag+'_wing_frame',box(side*(s/2+87),0,0,154,104,4),'#526675')
        for col in range(3):
            for row in range(2):
                x=side*(s/2+37+col*50);y=-25+row*50
                add(tag+'_cell_'+str(col)+'_'+str(row),box(x,y,3,46,45,2),'#153F75')
        for k in range(3):add(tag+'_busbar_'+str(k),box(side*(s/2+37+k*50),0,4.5,1,94,.8),'#DFBB6C')
    add('camera_barrel',bd.Pos(0,-s/2-20,5)*bd.Rot(90,0,0)*(bd.Cylinder(24,40)-bd.Cylinder(19,44)),'#3B4C5A')
    add('camera_aperture',bd.Pos(0,-s/2-42,5)*bd.Rot(90,0,0)*bd.Cylinder(18,2),'#162B3C')
    add('star_tracker',box(-30,0,s/2+13,28,28,25),'#354B5E')
    add('tracker_lens',cyl(-30,0,s/2+27,9,3),'#133B51')
    for i,x in enumerate((-32,32)):
        add('dish_'+str(i),bd.Pos(x,0,s/2+14)*(bd.Cone(20,14,8)-bd.Pos(0,0,3)*bd.Cone(18,12,8)),'#DAE0DE')
        add('dish_feed_'+str(i),cyl(x,0,s/2+25,2,22),'#D5B56F')
    for i,x in enumerate((-42,42)):add('antenna_'+str(i),cyl(x,35,s/2+37,1.4,72),'#D2DADF')

    return parts
