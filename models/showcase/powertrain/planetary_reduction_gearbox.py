"""Original planetary reduction concept in millimeters, Z up.
Radial block teeth illustrate arrangement only; NOT manufacturing-grade involute
or certified gearing. No ratio, contact, torque or efficiency certification.
"""
import build123d as bd
import math

def build(params):
    parts={}; ring_r=params['ring_outer_radius']
    def put(n,s,c):s.color=bd.Color(c);parts[n]=s
    def ann(ro,ri,h):return bd.Cylinder(ro,h)-bd.Cylinder(ri,h+2)
    def gear(r,n,h):
        s=bd.Cylinder(r,h)
        for i in range(n):s+=bd.Rot(0,0,i*360/n)*bd.Pos(r+.9,0,0)*bd.Box(4,3,h)
        return s
    # Expose the tooth train from above with a partial protective rim.
    ring=ann(ring_r,59,17)
    for i in range(60):ring+=bd.Rot(0,0,i*6)*bd.Pos(58,0,0)*bd.Box(4,3,17)
    put('internal_ring_illustrative_teeth',bd.Pos(0,0,22)*ring,'#527783')
    sun=gear(18,20,14)-bd.Cylinder(6,20)
    put('sun_gear_illustrative_teeth',bd.Pos(0,0,22)*sun,'#d2aa5a')
    for i in range(3):
        a=i*2*math.pi/3;x=38*math.cos(a);y=38*math.sin(a)
        planet=gear(17,18,14)-bd.Cylinder(5.2,20)
        put('planet_gear_'+str(i+1),bd.Pos(x,y,22)*planet,'#b7c5d0')
        put('planet_pin_'+str(i+1),bd.Pos(x,y,19)*bd.Cylinder(5,37),'#d4ac65')
    carrier=bd.Pos(0,0,6)*ann(48,10,7)
    for i in range(3):
        a=i*2*math.pi/3
        carrier-=bd.Pos(27*math.cos(a+.5),27*math.sin(a+.5),6)*bd.Cylinder(11,12)
    put('lower_carrier_plate',carrier,'#657c8c')
    upper=bd.Pos(0,0,42)*ann(13,6,6)
    for i in range(3):upper+=bd.Pos(0,0,42)*bd.Rot(0,0,i*120)*bd.Pos(23,0,0)*bd.Box(40,11,6)
    put('upper_three_arm_carrier',upper,'#819aab')
    put('output_shaft',bd.Pos(0,0,-14)*bd.Cylinder(10,40),'#9fb3bf')
    put('input_shaft',bd.Pos(0,0,48)*bd.Cylinder(5.8,60),'#c3a060')
    base=bd.Pos(0,0,-3)*ann(ring_r+7,15,9)
    for i in range(6):
        a=i*math.pi/3
        base-=bd.Pos((ring_r+1)*math.cos(a),(ring_r+1)*math.sin(a),-3)*bd.Cylinder(3.3,15)
    put('six_bolt_mounting_flange',base,'#415a68')
    cover=bd.Pos(0,0,28)*ann(ring_r+5,ring_r+1,53)
    cover-=bd.Pos(0,-55,28)*bd.Box(180,110,70)
    put('half_section_housing',cover,'#9bb5bc')
    return parts
