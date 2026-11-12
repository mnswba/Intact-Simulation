# Design prompt: Build a detailed original small turbofan teaching cutaway along the Z axis. Include a silver nacelle with a broad section removed, open inlet lip, twelve pitched fan blades around a nose cone, three staged compressor discs with repeated blades, amber combustor liner with perforations, red turbine disc and blades, exhaust annulus, central shaft, rear nozzle and two mounting pylons. Distinguish functional stages with color; straight pitched blades and annular flow paths are simplified and no aerodynamic performance is implied.
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
    length=params.get('engine_length_mm',240)
    cut=box(60,-60,0,120,120,length+40)
    add('sectioned_nacelle',ring(0,0,0,72,65,length)-cut,'#AABBC5')
    add('inlet_lip',ring(0,0,-length/2,74,63,10),'#CCD7DB')
    add('shaft',cyl(0,0,0,7,length+10),'#C3CCD0')
    add('spinner',bd.Pos(0,0,-length/2-8)*bd.Cone(5,20,30),'#6C8294')
    add('fan_hub',cyl(0,0,-96,20,18),'#63889B')
    for k in range(12):add('fan_blade_'+str(k),bd.Rot(0,0,k*30)*bd.Pos(42,0,-98)*bd.Rot(18,0,0)*bd.Box(42,13,3),'#7FA5B4')
    for stage,z in enumerate((-53,-22,9)):
        add('compressor_disc_'+str(stage),ring(0,0,z,29-stage*2,7,6),'#8C9FA9')
        for k in range(5):add('compressor_blade_'+str(stage)+'_'+str(k),bd.Rot(0,0,k*72+stage*15)*bd.Pos(37,0,z)*bd.Rot(25,0,0)*bd.Box(23,12,3),'#8C9FA9')
    liner=ring(0,0,47,46,39,40)-box(36,-36,47,72,72,48)
    for k in range(8):
        a=(k+0.5)*math.pi/4
        liner-=bd.Pos(43*math.cos(a),43*math.sin(a),47)*bd.Rot(0,90,a*180/math.pi)*bd.Cylinder(3,16)
    add('perforated_combustor',liner,'#CE9C56')
    add('turbine_disc',ring(0,0,84,26,7,8),'#AF6952')
    for k in range(6):add('turbine_blade_'+str(k),bd.Rot(0,0,k*60)*bd.Pos(36,0,84)*bd.Rot(-22,0,0)*bd.Box(23,13,3),'#AF6952')
    add('exhaust_nozzle',ring(0,0,115,48,42,25)-box(40,-40,115,80,80,30),'#536778')
    for i,z in enumerate((-40,65)):add('mounting_pylon_'+str(i),box(0,76,z,24,30,22),'#526C7D')

    return parts
