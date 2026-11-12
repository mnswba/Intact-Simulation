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
    box('belly_frame',(0,0,244),(330,160,75),dark,14)
    box('armored_shell',(0,0,287),(352,182,47),orange,16)
    box('top_access_hatch',(-24,0,315),(187,142,12),white,5)
    for side in (-1,1):
        box('side_rail_'+str(side),(0,side*99,270),(260,12,20),silver,4)
    for i,(x,y) in enumerate(((-124,-95),(-124,95),(124,-95),(124,95))):
        side = 1 if y>0 else -1
        knee=(x-48,side*135,131)
        ankle=(x+17,side*150,36)
        cyl('hip_'+str(i),(x,y,255),35,44,dark,(90,0,0))
        cyl('hip_cap_'+str(i),(x,y+side*24,255),26,8,silver,(90,0,0))
        beam('upper_leg_'+str(i),(x,y+side*14,242),knee,38,34,orange)
        cyl('knee_drive_'+str(i),knee,25,45,dark,(90,0,0))
        beam('shin_'+str(i),knee,ankle,23,26,silver)
        box('foot_'+str(i),(ankle[0],ankle[1],17),(64,46,30),dark,9)
    box('sensor_neck',(169,0,308),(42,62,45),dark,6)
    box('stereo_head',(196,0,345),(63,135,61),white,10)
    for side in (-1,1):
        cyl('camera_bezel_'+str(side),(230,side*40,347),19,8,dark,(0,90,0))
        cyl('camera_lens_'+str(side),(235,side*40,347),12,4,blue,(0,90,0))
    cyl('lidar_pedestal',(-89,0,337),26,33,dark)
    cyl('lidar_window',(-89,0,361),32,18,blue)
    cyl('lidar_cap',(-89,0,374),34,8,dark)
    box('status_light',(-25,-94,286),(75,5,11),blue,2)
    return parts
