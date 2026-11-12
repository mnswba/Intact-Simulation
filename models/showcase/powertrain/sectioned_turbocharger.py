"""Original sectioned turbocharger teaching concept; mm, shaft axis X.
Volute-like overlapping annular cavity is illustrative: no aerodynamic/flow claims.
"""
import build123d as bd
import math

def build(params):
    parts={}; r=params['compressor_radius']
    def put(n,s,c):s.color=bd.Color(c);parts[n]=s
    def cx(rad,length,x):return bd.Pos(x,0,0)*bd.Rot(0,90,0)*bd.Cylinder(rad,length)
    # Sectioned scroll: offset inner bore, exposed quadrant, tangential discharge.
    housing=cx(r,30,40)-bd.Pos(0,5,7)*cx(r-12,38,40)
    housing+=bd.Pos(40,r-7,27)*bd.Box(30,27,54)
    housing-=bd.Pos(40,r-7,31)*bd.Cylinder(9,65)
    housing-=bd.Pos(40,-r/2,r/2)*bd.Box(50,r+5,r+5)
    put('sectioned_compressor_scroll',housing,'#97bcc6')
    lip=cx(30,12,65)-cx(24,16,65)
    lip-=bd.Pos(65,-20,25)*bd.Box(18,45,40)
    put('cutaway_inlet_lip',lip,'#d4dde1')
    put('compressor_hub',cx(12,32,47)+bd.Pos(64,0,0)*bd.Rot(0,90,0)*bd.Cone(12,4,20),'#d0b169')
    for i in range(9):
        a=i*40
        blade=bd.Pos(43,19,0)*bd.Box(16,22,2.4)
        blade=bd.Rot(a,0,0)*blade
        put('compressor_blade_'+str(i+1),blade,'#d9be80')
    put('bearing_center_housing',cx(22,37,0)-cx(8,45,0),'#4c6878')
    put('rotor_shaft',cx(6,152,0),'#b4c5d0')
    turbine=cx(46,26,-47)-cx(31,32,-47)
    turbine-=bd.Pos(-47,-26,26)*bd.Box(40,55,55)
    put('sectioned_turbine_scroll',turbine,'#9d7668')
    disk=cx(29,8,-46)
    for i in range(10):disk+=bd.Rot(i*36,0,0)*(bd.Pos(-47,30,0)*bd.Rot(0,22,0)*bd.Box(18,13,3))
    put('turbine_wheel_and_blades',disk,'#c08c64')
    flange=bd.Pos(-47,0,-49)*bd.Box(54,61,9)-bd.Pos(-47,0,-49)*bd.Cylinder(16,14)
    for x in (-66,-28):
        for y in (-22,22):flange-=bd.Pos(x,y,-49)*bd.Cylinder(3.5,15)
    put('four_bolt_exhaust_flange',flange,'#715f59')
    put('oil_feed_boss',bd.Pos(0,0,26)*bd.Cylinder(7,15)-bd.Pos(0,0,26)*bd.Cylinder(3,18),'#b5b9ba')
    for x in (-14,14):put('bearing_collar_'+('a' if x<0 else 'b'),cx(11,5,x)-cx(6.3,8,x),'#d1a956')
    return parts
