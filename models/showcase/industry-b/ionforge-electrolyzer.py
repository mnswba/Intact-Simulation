"""Original design prompt, recorded before CAD source creation:
Design an original electrolyzer module on a dark support tray, with sixteen closely spaced square cell plates alternating teal and silver, gold compression rods through four corners, thick drilled endplates, two colored header manifolds, four open-bore service fittings, insulated terminal blocks and raised copper busbars. Add distinct feet, tie-rod nuts and a safety terminal shield arranged to leave the layered stack visible. Assume concept dimensions without pressure or electrochemical certification.
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
    put('support_tray',box(190,116,8,0,0,4),dark)
    for k,x in enumerate((-61,61)):put('support_foot_'+str(k),box(25,100,15,x,0,15),blue)
    for i in range(16):
        x=(i-7.5)*params['detail_pitch_mm']*.7
        plate=box(4,90,100,x,0,77)
        for y in (-35,35):
            for z in (39,115):plate-=cyl(3.5,7,x,y,z,'x')
        put('cell_layer_%02d'%i,plate,steel if i%2 else '#3a8e94')
    for k,x in enumerate((-54,54)):
        frame=box(12,104,115,x,0,77)
        for y in (-35,35):
            for z in (39,115):frame-=cyl(3.5,16,x,y,z,'x')
        put('compression_endplate_'+str(k),frame,blue)
    for k,(y,z) in enumerate([(-35,39),(35,39),(-35,115),(35,115)]):
        put('compression_rod_'+str(k),cyl(3,132,0,y,z,'x'),gold)
        put('rod_nut_'+str(k),ring(6,3,6,-65,y,z,'x'),gold)
    for k,y in enumerate((-31,31)):
        put('fluid_header_'+str(k),ring(9,5,126,0,y,143,'x'),red if k else blue)
        for j,x in enumerate((-70,70)):put('service_union_%s_%s'%(k,j),ring(13,5,12,x,y,143,'x'),steel)
    for k,x in enumerate((-60,60)):
        put('terminal_insulator_'+str(k),box(18,24,12,x,0,145),rubber)
        put('copper_busbar_'+str(k),box(8,50,6,x,0,154),'#c98955')
    put('terminal_shield',box(28,60,3,60,0,164),'#dabb71')

    return parts
