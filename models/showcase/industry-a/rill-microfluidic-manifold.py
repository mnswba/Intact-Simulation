# Design prompt: Create an original inspectable microfluidic laboratory manifold concept: a machined aluminum rectangular base with eight top fluid ports, a turquoise channel layer showing an orthogonal branched flow network milled into the top, an offset lifted lid with matching port bores, eight gold hollow threaded-style fittings, four steel lid screws, locating dowels, dual valve blocks and a mounting flange. Deliberately enlarge channels for teaching visibility and report no validated seal, sterility or flow behavior.
# Units: mm. Original unverified concept; Z up.
import build123d as bd
import math

def build(params):
    parts = {}
    def add(name, shape, color='#AABAC5'):
        shape.color=bd.Color(color)
        parts[name.replace('-', 'n').replace('.', '_')]=shape
    def box(x,y,z,a,b,c):return bd.Pos(x,y,z)*bd.Box(a,b,c)
    def cyl(x,y,z,r,h):return bd.Pos(x,y,z)*bd.Cylinder(r,h)
    def ring(x,y,z,r,ri,h):return cyl(x,y,z,r,h)-cyl(x,y,z,ri,h+2)
    def bolt(name,x,y,z,r=2.5):
        add(name,cyl(x,y,z,r,4)-box(x,y,z+1,2*r,.8,2),'#C9D2D7')
    l=params.get('manifold_length_mm',130)
    base=box(0,0,0,l,80,12)
    for x in (-l/2+8,l/2-8):
        for y in (-31,31):base-=cyl(x,y,0,3,16)
    add('machined_base',base,'#98AFBB')
    layer=box(0,0,10,l-12,65,8)
    layer-=box(0,0,13,l-30,4,5)
    for x in (-42,-14,14,42):
        layer-=box(x,0,13,4,50,5)
        for y in (-24,24):layer-=cyl(x,y,10,3,14)
    add('channel_layer',layer,'#4F9FA6')
    lid=box(0,0,47,l-12,65,6)
    for i,x in enumerate((-42,-14,14,42)):
        for j,y in enumerate((-24,24)):
            lid-=cyl(x,y,47,3,10)
            add('hollow_port_'+str(i)+'_'+str(j),ring(x,y,57,5.5,2.5,16),'#D0AC68')
    add('lifted_lid',lid,'#AEC6CE')
    for i,(x,y) in enumerate(((-51,-24),(-51,24),(51,-24),(51,24))):
        add('lid_screw_'+str(i),cyl(x,y,51,2,13),'#C3D0D5')
        bolt('screw_head_'+str(i),x,y,59,3.5)
    for i,x in enumerate((-50,50)):add('locating_dowel_'+str(i),cyl(x,0,24,2,30),'#DBE2E4')
    for i,x in enumerate((-24,24)):
        add('valve_body_'+str(i),box(x,0,23,18,18,17)-cyl(x,0,23,3,22),'#5B7B8B')
        add('valve_actuator_'+str(i),cyl(x,0,37,6,12),'#BF7C60')
    add('mounting_flange',box(0,0,-9,l+14,95,6)-box(0,0,-9,l-25,60,10),'#536E80')

    return parts
