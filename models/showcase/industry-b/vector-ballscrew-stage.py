"""Original design prompt, recorded before CAD source creation:
Design an original precision linear stage with a drilled aluminum base, two dark profiled guide rails, four blue bearing blocks, central gold screw shaft with closely spaced collar rings suggesting thread, end bearing supports, a carriage plate with a grid of mounting bores, a compact side-coupled motor and a raised cable chain represented by individual links. Expose the screw beneath the carriage and show mounting fasteners. Thread and ball circulation are visual concepts only.
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
    L=240
    base=box(L,110,12,0,0,6)
    for x in (-104,104):
        for y in (-43,43):base-=cyl(4,16,x,y,6)
    put('drilled_base',base,steel)
    for k,y in enumerate((-34,34)):
        rail=box(210,12,10,0,y,17)
        for x in (-80,-40,0,40,80):rail-=cyl(2.4,14,x,y,17)
        put('profile_rail_'+str(k),rail,dark)
        for j,x in enumerate((-24,24)):put('bearing_block_%s_%s'%(k,j),box(28,24,18,x,y,29)-box(32,12,9,x,y,21),blue)
    for k,x in enumerate((-107,107)):put('screw_end_support_'+str(k),box(18,34,32,x,0,28)-cyl(7,24,x,0,29,'x'),blue)
    put('screw_shaft',cyl(5,228,0,0,29,'x'),gold)
    for i in range(16):put('thread_indicator_%02d'%i,ring(6.8,5,2,(i-7.5)*11,0,29,'x'),steel)
    put('ball_nut_body',ring(13,5,30,0,0,29,'x'),gold)
    carriage=box(82,94,12,0,0,44)
    for x in (-28,0,28):
        for y in (-30,0,30):carriage-=cyl(3.2,16,x,y,44)
    put('carriage_mount_plate',carriage,steel)
    put('motor_body',box(42,42,46,154,0,29),dark)
    put('motor_endcap',box(8,46,46,129,0,29),blue)
    put('flex_coupling',ring(11,5,20,119,0,29,'x'),red)
    for i in range(8):put('cable_chain_link_'+str(i),box(12,18,13,-85+i*13,63,22)-box(8,20,7,-85+i*13,63,22),rubber)
    bolts('mount_fastener_',[(x,y) for x in (-104,104) for y in (-43,43)],14)

    return parts
