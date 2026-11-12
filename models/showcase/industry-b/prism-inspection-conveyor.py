"""Original design prompt, recorded before CAD source creation:
Design an original tabletop conveyor inspection station with two blue side rails, exposed end rollers, a dark endless belt represented by a thin solid loop, four adjustable legs and leveling pads, a tall overhead camera bridge, camera lens barrel, gold illumination bars and a side sensor bracket. Show a small silver sample carrier on the belt, a finned drive motor and a vented control box. Use detailed native solids and stable named components with assumed interfaces.
Units: millimeters. Z up. Concept geometry; no engineering certification.
"""
import build123d as b
import math

def build(params):
    parts={}
    steel='#a6bac7'; dark='#334957'; blue='#297b98'; gold='#d9ae61'; red='#d35f43'; rubber='#26333a'
    def put(n,s,c=steel):
        s.color=b.Color(c); parts[n]=s
    def box(x,y,z,a,c,d): return b.Pos(a,c,d)*b.Box(x,y,z)
    def cyl(r,h,x,y,z,axis='z'):
        return b.Pos(x,y,z)*(b.Rot(0,90,0) if axis=='x' else b.Rot(90,0,0) if axis=='y' else b.Rot(0,0,0))*b.Cylinder(r,h)
    def ring(ro,ri,h,x,y,z,axis='z'):return cyl(ro,h,x,y,z,axis)-cyl(ri,h+2,x,y,z,axis)
    def bolts(prefix,xy,z,r=3):
        for i,(x,y) in enumerate(xy):put(prefix+str(i+1),cyl(r,4,x,y,z),gold)
    for k,y in enumerate((-45,45)):
        rail=box(240,10,25,0,y,64)
        for x in (-75,0,75):rail-=cyl(4,14,x,y,64,'y')
        put('side_rail_'+str(k),rail,blue)
    for k,x in enumerate((-105,105)):
        put('end_roller_'+str(k),cyl(11.5,78,x,0,65,'y'),steel)
        put('roller_axle_'+str(k),cyl(4,106,x,0,65,'y'),gold)
    belt=box(210,76,28,0,0,65)-box(214,80,23,0,0,65)
    for x in (-105,105):
        belt+=ring(14,11.5,76,x,0,65,'y')-box(40,80,40,x-(20 if x>0 else -20),0,65)
    put('endless_belt_loop',belt,rubber)
    for i,(x,y) in enumerate([(x,y) for x in (-85,85) for y in (-45,45)]):
        put('support_leg_'+str(i),box(12,12,44,x,y,30),steel)
        put('leveling_pad_'+str(i),cyl(11,6,x,y,6),dark)
    for k,y in enumerate((-61,61)):
        put('camera_bridge_upright_'+str(k),box(14,14,100,0,y,113),blue)
        put('inspection_light_'+str(k),box(70,8,8,0,y*.65,143),gold)
    put('camera_bridge_crossbar',box(22,136,14,0,0,166),blue)
    put('camera_body',box(34,30,28,0,0,145),dark)
    put('camera_lens',ring(11,7,16,0,0,124),steel)
    put('lens_glass',cyl(7,2,0,0,115),'#315b6d')
    carrier=box(44,48,6,42,0,83)-cyl(8,10,42,0,83)
    put('sample_carrier',carrier,steel)
    put('drive_motor',cyl(16,40,105,76,65,'y'),dark)
    for i in range(5):put('motor_fin_'+str(i),ring(19,15,2,105,61+i*7,65,'y'),steel)
    control=box(50,18,38,-56,62,48)
    for i in range(4):control-=box(32,22,2,-56,62,38+i*6)
    put('vented_control_box',control,blue)
    put('sensor_bracket',box(12,20,35,55,-57,91),gold)
    put('photoelectric_sensor',cyl(6,15,55,-52,107,'y'),red)

    return parts
