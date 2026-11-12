# Design prompt: Create an original laboratory peristaltic pump concept with a blue instrument chassis, open circular pump head, three bearing-mounted rollers on an orange rotor, a teal flexible tube following a 240-degree planar arc plus inlet and outlet tails, tube retaining clamps, rear stepper motor, control display and adjustment knob. Include bores, hub fasteners, chassis vents and feet. The tubing arc is illustrative and occlusion and flow calibration are unverified.
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
    add('instrument_base',box(0,0,-40,150,120,45),'#376D81')
    head=ring(0,0,0,55,46,22)-box(0,-52,0,110,28,28)
    add('open_pump_race',head,'#B4C9CF')
    add('rotor_plate',ring(0,0,-3,31,6,7),'#D9984D')
    add('rotor_hub',ring(0,0,5,12,5,16),'#D9984D')
    for k in range(3):
        a=k*2*math.pi/3;x=30*math.cos(a);y=30*math.sin(a)
        add('roller_'+str(k),ring(x,y,5,9,3,18),'#D1DCE0')
        add('roller_pin_'+str(k),cyl(x,y,6,3,23),'#6B8796')
        bolt('hub_fastener_'+str(k),7*math.cos(a),7*math.sin(a),15,1.6)
    path=bd.CenterArc((0,0,5),42,-30,240)
    start=(42*math.cos(-math.pi/6),42*math.sin(-math.pi/6),5)
    profile=bd.Plane(origin=start,z_dir=(.5,.866,0))*(bd.Circle(3)-bd.Circle(1.6))
    add('curved_tube',bd.sweep(profile,path),'#55AFB2')
    for i,side in enumerate((-1,1)):
        add('tube_tail_'+str(i),bd.Pos(side*36.4,-42,5)*bd.Rot(90,0,0)*ring(0,0,0,3,1.6,43),'#55AFB2')
        add('tube_clamp_'+str(i),box(side*37,-36,0,17,12,16)-bd.Pos(side*36.4,-36,5)*bd.Rot(90,0,0)*bd.Cylinder(3.3,16),'#647F8F')
    add('stepper_motor',box(0,0,-32,44,44,36),'#526575')
    add('control_display',box(-38,-61,-39,44,3,19),'#162F42')
    add('speed_knob',bd.Pos(37,-65,-39)*bd.Rot(90,0,0)*bd.Cylinder(11,9),'#9BC8C9')
    for k in range(5):add('case_vent_'+str(k),box(76,-25+k*11,-41,2,5,22),'#253F52')
    for i,(x,y) in enumerate(((-57,-43),(57,-43),(-57,43),(57,43))):add('rubber_foot_'+str(i),cyl(x,y,-66,7,7),'#283F4D')

    return parts
