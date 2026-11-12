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
            shape = bd.fillet(shape.edges(), min(radius, min(size) * 0.4))
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
    # Compact 1.37 m service-robot concept with approachable rounded armor.
    box('pelvis',(0,0,668),(222,145,104),dark,18)
    box('chest',(0,0,892),(290,168,285),white,28)
    box('breastplate',(0,-91,913),(220,24,183),orange,18)
    box('chest_display',(0,-107,943),(126,12,72),dark,10)
    box('display_bar',(0,-115,943),(76,4,9),blue,3)
    cyl('waist',(0,0,741),74,68,silver)
    cyl('neck',(0,0,1063),39,63,dark)
    box('head_shell',(0,-3,1170),(168,145,165),white,28)
    box('visor',(0,-79,1181),(139,18,68),dark,14)
    for side in (-1,1):
        box('eye_'+str(side),(side*35,-91,1188),(24,5,10),blue,3)
        cyl('ear_'+str(side),(side*88,0,1174),29,17,orange,(0,90,0))
        cyl('shoulder_'+str(side),(side*179,0,988),48,74,dark,(0,90,0))
        beam('upper_arm_'+str(side),(side*191,0,969),(side*243,-8,807),62,69,white)
        cyl('elbow_'+str(side),(side*243,-8,792),36,78,dark,(90,0,0))
        beam('forearm_'+str(side),(side*243,-8,777),(side*252,-54,637),54,61,orange)
        cyl('wrist_'+str(side),(side*252,-54,625),27,28,silver)
        box('hand_'+str(side),(side*252,-57,578),(61,44,73),white,13)
        box('thumb_'+str(side),(side*217,-64,587),(19,31,49),dark,7)
        cyl('hip_joint_'+str(side),(side*68,0,637),43,68,orange,(0,90,0))
        beam('thigh_'+str(side),(side*70,0,615),(side*74,-5,389),74,87,white)
        cyl('knee_'+str(side),(side*74,-6,365),43,94,dark,(90,0,0))
        beam('shin_'+str(side),(side*74,-2,338),(side*77,9,107),66,79,white)
        box('shin_inset_'+str(side),(side*77,-44,236),(35,9,151),orange,7)
        cyl('ankle_'+str(side),(side*77,0,93),33,65,dark,(0,90,0))
        box('foot_'+str(side),(side*77,-44,42),(101,206,77),dark,18)
        box('toe_armor_'+str(side),(side*77,-101,62),(91,83,32),orange,10)
    return parts
