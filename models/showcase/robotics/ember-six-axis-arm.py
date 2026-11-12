import build123d as bd
import math

def build(params):
    parts = {}
    orange, dark, silver, blue, white = '#ed7540', '#263342', '#aabcc8', '#40bfc4', '#e4e9e6'
    def put(name, shape, color):
        shape.color = bd.Color(color)
        parts[name.replace("-", "n")] = shape
        return shape
    def box(name, xyz, size, color, radius=0):
        shape = bd.Box(*size, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.CENTER))
        if radius:
            shape = bd.fillet(shape.edges(), radius)
        return put(name, bd.Pos(*xyz) * shape, color)
    def cyl(name, xyz, radius, depth, color, rot=(0,0,0), bore=0):
        shape = bd.Cylinder(radius, depth, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.CENTER))
        if bore:
            shape = shape - bd.Cylinder(bore, depth+2, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.CENTER))
        return put(name, bd.Pos(*xyz) * bd.Rot(*rot) * shape, color)
    def beam(name, a, b, width, thickness, color):
        d = tuple(b[i]-a[i] for i in range(3))
        length = math.sqrt(sum(v*v for v in d))
        plane = bd.Plane(origin=a, z_dir=d)
        shape = bd.Box(width, thickness, length, align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN))
        return put(name, plane.location * shape, color)
    # A 620 mm reach concept, shown in a deliberate bent inspection pose.
    cyl('anchored_base', (0,0,14), 100,28,dark,bore=26)
    cyl('turntable', (0,0,40), 77,24,silver)
    cyl('yaw_drive', (0,0,77), 57,58,orange)
    box('shoulder_yoke',(0,0,131),(92,108,55),orange,8)
    cyl('axis_2_housing',(0,0,155),52,128,dark,(90,0,0))
    cyl('axis_2_front_cap',(0,-69,155),39,10,silver,(90,0,0))
    beam('upper_arm', (0,0,165),(124,0,387),68,78,orange)
    beam('upper_arm_inset',(7,-42,188),(113,-42,369),33,5,dark)
    cyl('axis_3_housing',(124,0,387),44,102,dark,(90,0,0))
    cyl('axis_3_cap',(124,-56,387),33,10,silver,(90,0,0))
    beam('forearm',(124,0,387),(336,0,301),57,65,orange)
    beam('forearm_cover',(145,-35,379),(314,-35,311),31,7,white)
    cyl('axis_4_roll',(341,0,298),35,70,dark,(0,90,0))
    cyl('axis_4_ring',(375,0,298),37,12,silver,(0,90,0))
    box('wrist_yoke',(398,0,298),(52,68,58),orange,6)
    cyl('axis_5_pitch',(414,0,298),31,86,dark,(90,0,0))
    cyl('axis_5_cap',(414,-47,298),22,8,silver,(90,0,0))
    cyl('axis_6_flange',(448,0,298),27,36,silver,(0,90,0))
    box('gripper_palm',(478,0,298),(30,76,50),dark,4)
    for side in (-1,1):
        box('jaw_carriage_'+str(side),(492,side*29,298),(22,20,45),silver,2)
        box('finger_'+str(side),(525,side*29,292),(58,14,20),orange,2)
        box('grip_pad_'+str(side),(544,side*20,292),(20,5,18),dark)
    for i, (x,y) in enumerate(((64,64),(-64,64),(64,-64),(-64,-64))):
        cyl('anchor_bolt_'+str(i),(x,y,31),7,7,silver)
    # A protected elbow cable loop modeled as a swept native torus.
    put('elbow_cable_guard',bd.Pos(119,42,387)*bd.Rot(90,0,0)*bd.Torus(55,6),blue)
    return parts
