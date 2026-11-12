"""Original design prompt, recorded before CAD source creation:
Design an original six-station rotary indexing work fixture with a drilled baseplate, ribbed blue pedestal, circular table with six evenly spaced socket nests, separate gold clamp levers, polished locator pins, a central open-bore hub and a raised inspection workpiece at one station. Expose a side drive motor with cooling ribs and coupling guard, add an annular angle scale segmented into twelve ticks and mounting bolts. The fixture should read as practical production automation without claiming positioning accuracy.
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
    base=box(190,160,12,0,0,6)
    for x in (-78,78):
        for y in (-63,63):base-=cyl(4.5,16,x,y,6)
    put('drilled_baseplate',base,dark)
    put('table_pedestal',ring(43,27,42,0,0,33),blue)
    for i in range(6):put('pedestal_rib_'+str(i),b.Rot(0,0,i*60)*box(22,7,32,45,0,29),blue)
    table=ring(76,14,12,0,0,61)
    for i in range(6):
        a=i*math.pi/3;table-=cyl(3,16,59*math.cos(a),59*math.sin(a),61)
    put('rotary_table',table,steel)
    put('center_hub',ring(23,14,15,0,0,75),gold)
    for i in range(6):
        a=i*math.pi/3;x=52*math.cos(a);y=52*math.sin(a)
        nest=box(24,24,7,x,y,71)-cyl(7,11,x,y,71)
        put('socket_nest_'+str(i),nest,blue)
        put('locator_pin_'+str(i),cyl(2.5,12,x+9,y+9,78),steel)
        put('clamp_lever_'+str(i),b.Pos(x,y,81)*b.Rot(0,0,i*60+20)*b.Pos(8,0,0)*b.Box(23,6,5),gold)
    put('inspection_workpiece',ring(7,3,23,52,0,85),red)
    put('angle_scale_ring',ring(80,76,3,0,0,56),dark)
    for i in range(12):put('angle_tick_%02d'%i,b.Rot(0,0,i*30)*box(4,1.6,1,78,0,58),gold)
    put('drive_motor',cyl(20,49,72,0,31,'x'),dark)
    for i in range(5):put('motor_cooling_rib_'+str(i),ring(23,19,2,54+i*8,0,31,'x'),steel)
    put('coupling_guard',ring(25,21,19,43,0,31,'x')-box(25,55,30,43,-25,48),blue)
    bolts('anchor_bolt_',[(x,y) for x in (-78,78) for y in (-63,63)],14)

    return parts
