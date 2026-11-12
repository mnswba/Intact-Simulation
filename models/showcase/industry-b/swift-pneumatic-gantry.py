"""Original design prompt, recorded before CAD source creation:
Design an original pneumatic pick-and-place gantry with a broad mounting base, two tall columns and a blue overhead crossbeam, two polished horizontal guide rods, a gold pneumatic cylinder barrel and exposed piston rod, central sliding carriage, vertical twin-rod actuator, red two-finger gripper holding a small sample block, air fittings, limit sensors and anchor fasteners. Include bores in bearing blocks and realistic open frame space to make the mechanism readable.
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
    base=box(240,130,12,0,0,6)
    for x in (-103,103):
        for y in (-50,50):base-=cyl(4,16,x,y,6)
    put('mounting_base',base,dark)
    for k,x in enumerate((-96,96)):
        put('gantry_column_'+str(k),box(22,36,140,x,28,82),blue)
        put('column_foot_'+str(k),box(44,56,10,x,28,17),steel)
    put('overhead_crossbeam',box(222,36,22,0,28,161),blue)
    for k,z in enumerate((125,149)):put('horizontal_guide_'+str(k),cyl(5,192,0,0,z,'x'),steel)
    carriage=box(42,30,46,18,0,137)
    for z in (125,149):carriage-=cyl(5.2,48,18,0,z,'x')
    put('sliding_carriage',carriage,blue)
    put('horizontal_cylinder',ring(12,7,92,-43,31,133,'x'),gold)
    for k,x in enumerate((-92,6)):put('cylinder_end_cap_'+str(k),box(8,30,30,x,31,133),dark)
    put('horizontal_piston_rod',cyl(4,82,51,31,133,'x'),steel)
    put('carriage_drive_lug',box(12,34,12,82,15,133),gold)
    put('vertical_actuator',box(38,28,44,18,-22,111),dark)
    for k,x in enumerate((7,29)):
        put('vertical_guide_rod_'+str(k),cyl(3,60,x,-22,77),steel)
        put('gripper_finger_'+str(k),box(7,18,29,x,-22,42),red)
    put('gripper_palm',box(43,30,12,18,-22,61),blue)
    put('held_sample',box(14,14,16,18,-22,38),gold)
    for k,x in enumerate((-80,-12)):put('air_fitting_'+str(k),ring(6,2.5,13,x,31,155),steel)
    for k,x in enumerate((-77,77)):
        put('limit_sensor_'+str(k),box(18,12,9,x,-8,166),rubber)
        put('sensor_indicator_'+str(k),cyl(2,2,x,-8,172),red)
    bolts('anchor_bolt_',[(x,y) for x in (-103,103) for y in (-50,50)],14)

    return parts
