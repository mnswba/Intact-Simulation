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
    # Parallel jaws on twin guide shafts with compliant-looking split fingers.
    box('palm_housing',(0,0,60),(160,90,82),dark,9)
    box('faceplate',(0,-49,60),(146,10,70),silver,3)
    cyl('robot_mount',(0,0,12),47,24,silver,bore=19)
    cyl('mount_register',(0,0,28),34,10,orange,bore=19)
    box('drive_pack',(0,55,59),(75,38,64),orange,6)
    cyl('motor_rear_cap',(0,81,59),25,14,dark,(90,0,0))
    for z in (44,81):
        cyl('guide_shaft_'+str(z),(0,-59,z),7,178,silver,(0,90,0))
    cyl('drive_screw',(0,-60,63),5,156,dark,(0,90,0))
    for side in (-1,1):
        x=side*48
        box('jaw_slider_'+str(side),(x,-61,65),(31,29,61),orange,3)
        box('finger_root_'+str(side),(x,-59,111),(29,31,48),silver,3)
        # Fingers taper by a rigid linked step, leaving a useful open throat.
        beam('proximal_link_'+str(side),(x,-59,128),(side*36,-59,180),20,25,silver)
        cyl('knuckle_'+str(side),(side*36,-59,178),13,33,dark,(90,0,0))
        beam('distal_link_'+str(side),(side*36,-59,180),(side*31,-59,220),18,24,orange)
        box('tactile_pad_'+str(side),(side*22,-59,211),(7,27,36),dark,3)
        for z in (200,211,222):
            box('pad_rib_'+str(side)+'_'+str(z),(side*18,-59,z),(3,25,3),blue)
        cyl('slider_bolt_'+str(side),(x,-78,62),6,5,dark,(90,0,0))
    box('status_strip',(0,-56,91),(30,3,5),blue,1)
    return parts
