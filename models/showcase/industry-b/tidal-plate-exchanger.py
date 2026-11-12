"""Original design prompt, recorded before CAD source creation:
Design an original compact plate heat exchanger on a blue twin-rail skid, with a tall rectangular stack of eighteen individually spaced stainless plates, gold tie rods, drilled end frames, four annular side pipe connections, support feet, visible fasteners and a small pressure gauge. Expose the plate edges and contrasting gasket strips so the flow equipment reads clearly from a three-quarter view. Use native solids with stable component names; this is a layout concept with assumed interfaces.
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
    for y in (-53,53):put('skid_rail_'+str(y).replace('-','m'),box(190,16,12,0,y,6),blue)
    for x in (-72,72):put('skid_cross_'+str(x).replace('-','m'),box(15,122,9,x,0,14),dark)
    for i in range(18):
        x=(i-8.5)*params['detail_pitch_mm']*.65
        plate=box(2.8,80,130,x,0,89)
        for y in (-24,24):plate-=cyl(7,5,x,y,134,'x')
        put('exchange_plate_%02d'%i,plate,steel if i%2 else '#7e9ba9')
    for k,x in enumerate((-57,57)):
        end=box(12,94,148,x,0,91)
        for y in (-37,37):
            for z in (32,150):end-=cyl(3.5,16,x,y,z,'x')
        put('end_frame_'+str(k),end,blue)
        put('foot_'+str(k),box(28,112,10,x,0,22),dark)
    for k,(y,z) in enumerate([(-37,32),(37,32),(-37,150),(37,150)]):put('tie_rod_'+str(k),cyl(3,142,0,y,z,'x'),gold)
    for k,(y,z) in enumerate([(-24,56),(24,56),(-24,128),(24,128)]):
        put('pipe_nozzle_'+str(k),ring(11,7,30,-77,y,z,'x'),steel)
        put('nozzle_flange_'+str(k),ring(17,7,6,-92,y,z,'x'),blue)
    put('gauge_stem',cyl(3,20,57,0,178),gold)
    put('gauge_body',cyl(13,7,57,0,192,'y'),dark)
    put('gauge_dial',cyl(10,1,57,-4,192,'y'),'#ece9dc')
    put('gauge_needle',box(1,1,8,57,-5,195),red)

    return parts
