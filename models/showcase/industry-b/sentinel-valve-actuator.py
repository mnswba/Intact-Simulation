"""Original design prompt, recorded before CAD source creation:
Design an original motorized utility valve cutaway on an anchor base with a horizontal open-bore flanged valve body, a partially exposed brass valve disc and vertical stem, a ribbed actuator gearbox with its front half removed, visible worm-like shaft collars and bronze sector wheel, a side motor with cooling ribs, manual override handwheel, mounting bolts and a red position indicator. Include circular flange bolt patterns and a sectioned housing that reveals the mechanism. Gear forms are explicitly illustrative.
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
    put('anchor_base',box(160,110,12,0,0,6),dark)
    put('valve_pedestal',box(55,55,22,0,0,22),blue)
    body=ring(35,26,82,0,0,64,'x')-box(90,42,46,0,-24,88)
    put('cutaway_valve_body',body,blue)
    for k,x in enumerate((-45,45)):
        f=ring(45,26,10,x,0,64,'x')
        for i in range(8):
            a=i*math.pi/4;f-=cyl(3.4,15,x,37*math.cos(a),64+37*math.sin(a),'x')
        put('pipeline_flange_'+str(k),f,steel)
    put('valve_disc',cyl(25,5,0,0,64,'x'),gold)
    put('valve_stem',cyl(5,95,0,0,108),steel)
    put('stem_gland',ring(14,5,12,0,0,105),gold)
    housing=box(88,66,46,0,0,151)-box(78,56,48,0,0,155)-box(100,40,50,0,-24,155)
    put('sectioned_actuator_housing',housing,blue)
    wheel=ring(25,5,9,0,0,150)
    for i in range(16):wheel+=b.Pos(0,0,150)*b.Rot(0,0,i*22.5)*b.Pos(25,0,0)*b.Box(4,4,9)
    put('illustrative_sector_wheel',wheel,gold)
    put('worm_shaft',cyl(4,105,0,29,150,'x'),steel)
    for i in range(8):put('illustrative_worm_collar_'+str(i),cyl(8,2,(i-3.5)*5,29,150,'x'),gold)
    put('motor_can',cyl(19,54,74,29,150,'x'),dark)
    for i in range(7):put('motor_cooling_rib_'+str(i),ring(22,18,2,54+i*6,29,150,'x'),steel)
    put('override_handwheel',ring(24,19,5,-65,29,150,'x'),red)
    for i in range(3):put('handwheel_spoke_'+str(i),b.Pos(-65,29,150)*b.Rot(i*120,0,0)*b.Pos(0,10,0)*b.Box(5,20,4),red)
    put('position_indicator',box(28,5,5,0,0,183),red)
    bolts('base_bolt_',[(x,y) for x in (-65,65) for y in (-40,40)],15)

    return parts
