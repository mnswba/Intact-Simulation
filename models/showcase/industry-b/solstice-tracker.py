"""Original design prompt, recorded before CAD source creation:
Design an original dual-axis solar tracker demonstrator with a perforated square ground plate, cylindrical mast, azimuth slewing rings, fork yoke, tilted rectangular solar panel frame subdivided into twelve dark photovoltaic tiles, rear support beams, elevation trunnions and a gold linear actuator. Include realistic mounting holes, separate bearing caps, a small vented control enclosure and fasteners. Keep the tilted panel visibly attached to its supporting mechanism.
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
    base=box(120,120,10,0,0,5)
    for x in (-45,45):
        for y in (-45,45):base-=cyl(5,15,x,y,5)
    put('anchor_plate',base,dark)
    put('mast',ring(21,16,110,0,0,65),steel)
    put('azimuth_lower',ring(38,19,10,0,0,123),dark)
    put('azimuth_upper',ring(34,16,9,0,0,134),gold)
    for k,x in enumerate((-43,43)):
        put('yoke_upright_'+str(k),box(12,25,53,x,0,162),blue)
        put('elevation_bearing_'+str(k),ring(15,6,8,x,0,184,'x'),steel)
    put('elevation_axle',cyl(6,108,0,0,184,'x'),gold)
    def tilt(s):return b.Pos(0,0,184)*b.Rot(25,0,0)*s
    frame=b.Box(168,118,7)-b.Box(156,106,10)
    put('solar_panel_frame',tilt(frame),steel)
    for i in range(4):
        for j in range(3):put('photovoltaic_tile_%s_%s'%(i,j),tilt(box(36,31,3,(i-1.5)*39,(j-1)*35,1)), '#244b69' if (i+j)%2 else '#315e83')
    for k,x in enumerate((-48,48)):put('rear_panel_beam_'+str(k),tilt(box(8,112,12,x,0,-10)),dark)
    put('actuator_barrel',cyl(8,48,0,-28,155),blue)
    put('actuator_rod',cyl(3,45,0,-28,186),gold)
    enclosure=box(40,22,38,38,0,62)
    for i in range(5):enclosure-=box(25,25,2,38,0,52+i*5)
    put('vented_controller',enclosure,blue)
    bolts('anchor_cap_',[(x,y) for x in (-45,45) for y in (-45,45)],12)

    return parts
