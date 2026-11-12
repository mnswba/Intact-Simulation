"""Original design prompt, recorded before CAD source creation:
Design an original horizontal axial hydraulic turbine cutaway with a half-open cylindrical blue casing, inlet and outlet flange rings with bolt holes, a central gold shaft and tapered hub, six pitched broad rotor blades, six stationary guide vanes, two bearing pedestals on a ribbed foundation, fasteners and a generator coupling. Reveal the impeller through the missing front half of the casing. Native solids only, with illustrative blade pitch and no hydraulic performance claim.
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
    put('foundation',box(240,140,14,0,0,7),dark)
    for k,x in enumerate((-78,78)):
        pedestal=box(24,76,54,x,0,41)-cyl(15,30,x,0,62,'x')
        put('bearing_pedestal_'+str(k),pedestal,blue)
        put('bearing_bush_'+str(k),ring(19,10,18,x,0,67,'x'),gold)
        for j,y in enumerate((-48,48)):put('mount_bolt_%s_%s'%(k,j),cyl(4,5,x,y,17),gold)
    put('shaft',cyl(9,250,0,0,67,'x'),steel)
    shell=ring(58,53,132,0,0,67,'x')-box(150,80,140,0,-40,67)
    put('sectioned_casing',shell,blue)
    for k,x in enumerate((-66,66)):
        f=ring(65,49,8,x,0,67,'x')
        for j in range(8):
            a=j*math.pi/4; f-=cyl(3,12,x,57*math.cos(a),67+57*math.sin(a),'x')
        put('drilled_end_flange_'+str(k),f,steel)
    put('rotor_hub',cyl(19,32,0,0,67,'x'),gold)
    for i in range(6):
        blade=b.Pos(0,0,67)*b.Rot(i*60,0,0)*b.Pos(0,34,0)*b.Rot(0,22,0)*b.Box(24,35,5)
        put('pitched_rotor_blade_'+str(i),blade,steel)
        vane=b.Pos(-43,0,67)*b.Rot(i*60+25,0,0)*b.Pos(0,35,0)*b.Rot(0,-18,0)*b.Box(18,33,4)
        put('guide_vane_'+str(i),vane,dark)
    put('coupling_hub',ring(21,9,18,113,0,67,'x'),red)
    for i in range(6):
        a=i*math.pi/3;put('coupling_bolt_'+str(i),cyl(3,5,125,15*math.cos(a),67+15*math.sin(a),'x'),gold)
    for i in range(3):put('base_rib_'+str(i),box(12,126,8,(i-1)*65,0,18),blue)

    return parts
