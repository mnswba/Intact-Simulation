"""Original 86 mm piston and split connecting rod. Millimeters, CAD Z up.
Concept geometry: ring gaps, grooves and pin bore are modeled; not production tooling.
"""
import build123d as bd
import math

def build(params):
    d=params['bore']; parts={}
    def put(name,shape,color):
        shape.color=bd.Color(color); parts[name]=shape
    def ring(ro,ri,h):return bd.Cylinder(ro,h)-bd.Cylinder(ri,h+2)
    # Open skirt and a full crown, with three machined circumferential grooves.
    piston=bd.Pos(0,0,158)*bd.Cylinder(d/2,60)
    piston-=bd.Pos(0,0,150)*bd.Cylinder(d/2-5,54)
    for z in (171,178,185):
        piston-=bd.Pos(0,0,z)*ring(d/2+1,d/2-3,3.2)
    piston-=bd.Pos(0,0,150)*bd.Rot(90,0,0)*bd.Cylinder(11,110)
    # Small crown bowl and two visual valve reliefs.
    piston-=bd.Pos(0,0,189)*bd.Cylinder(24,6)
    for x in (-22,22):piston-=bd.Pos(x,0,188)*bd.Cylinder(10,4)
    put('grooved_piston',piston,'#c9d6db')
    for i,z in enumerate((171,178,185)):
        r=ring(d/2-.35,d/2-2.9,2.7)-bd.Pos(d/2,0,0)*bd.Box(8,1.7,7)
        put('compression_ring_'+str(i+1),bd.Pos(0,0,z)*r,'#414d59')
    pin=ring(10.7,7,74)
    put('hollow_wrist_pin',bd.Pos(0,0,150)*bd.Rot(90,0,0)*pin,'#799aa8')
    # Rod runs from big end at z=18 to small end at z=150.
    rod=bd.Pos(0,0,93)*bd.Box(19,13,106)
    rod+=bd.Pos(0,0,150)*bd.Rot(90,0,0)*ring(18,11.2,18)
    big=bd.Pos(0,0,18)*bd.Rot(90,0,0)*ring(28,20,22)
    rod+=big & bd.Pos(0,0,57)*bd.Box(80,60,78)
    rod-=bd.Pos(0,-7,95)*bd.Box(10,5,77)
    put('forged_connecting_rod',rod,'#536d7d')
    cap=big & bd.Pos(0,0,-2)*bd.Box(80,60,40)
    put('split_big_end_cap',cap,'#78909a')
    for x in (-24,24):
        bolt=bd.Pos(x,0,19)*bd.Cylinder(3,36)+bd.Pos(x,0,39)*bd.Cylinder(5,6)
        put('rod_bolt_'+('left' if x<0 else 'right'),bolt,'#d2ae58')
    return parts
