"""Original design prompt, recorded before CAD source creation:
Design an original open cycloidal reducer concept with a blue cylindrical lower housing and sectioned upper rim, twelve separate perimeter roller pins, a silver eccentric lobed disc, three open relief bores, a gold offset input bearing, central input shaft, six output pins and a raised output carrier with six radial arms. Add a drilled mounting flange and separate gold fasteners. Use a deliberately illustrative eight-lobed rounded polygon disc and explicitly avoid claiming a conjugate cycloidal gear profile.
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
    flange=ring(73,12,10,0,0,5)
    for i in range(8):
        a=i*math.pi/4;flange-=cyl(4,14,65*math.cos(a),65*math.sin(a),5)
    put('drilled_mount_flange',flange,dark)
    put('lower_housing',ring(64,57,26,0,0,23),blue)
    rim=ring(64,58,25,0,0,48)-box(140,80,30,0,-40,48)
    put('sectioned_upper_rim',rim,blue)
    for i in range(12):
        a=i*math.pi/6;put('perimeter_roller_%02d'%i,cyl(5,30,50*math.cos(a),50*math.sin(a),33),gold)
    # A smooth lobed visual disc, not a mathematical cycloidal tooth form.
    points=[]
    for i in range(96):
        a=i*2*math.pi/96;r=41+3*math.cos(8*a);points.append((r*math.cos(a)+2,r*math.sin(a)))
    disc=b.Pos(0,0,29)*b.extrude(b.Polygon(*points),amount=9)
    disc-=cyl(11,16,2,0,33)
    for i in range(3):
        a=i*2*math.pi/3;disc-=cyl(8,16,24*math.cos(a)+2,24*math.sin(a),33)
    put('illustrative_lobed_disc',disc,steel)
    put('eccentric_bearing',ring(11,6,12,2,0,33),gold)
    put('input_shaft',cyl(5.5,72,0,0,34),steel)
    for i in range(6):
        a=i*math.pi/3;put('output_pin_'+str(i),cyl(3.5,31,31*math.cos(a),31*math.sin(a),43),gold)
    carrier=ring(13,6,8,0,0,61)
    for i in range(6):carrier+=b.Pos(0,0,61)*b.Rot(0,0,i*60)*b.Pos(19,0,0)*b.Box(34,8,8)
    put('six_arm_output_carrier',carrier,dark)
    put('output_hub',ring(16,6,15,0,0,72),blue)
    for i in range(8):
        a=i*math.pi/4;put('flange_bolt_'+str(i),cyl(3,4,65*math.cos(a),65*math.sin(a),12),gold)

    return parts
