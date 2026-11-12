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
    box('lower_chassis',(0,0,151),(378,236,62),dark,12)
    box('science_deck',(0,0,194),(413,259,24),white,8)
    box('battery_enclosure',(-63,0,228),(178,151,50),orange,8)
    for side in (-1,1):
        sy=side*161
        beam('rocker_'+str(side),(-153,sy,91),(0,sy,143),22,26,silver)
        beam('bogie_'+str(side),(0,sy,143),(153,sy,91),22,26,silver)
        for j,x in enumerate((-156,0,156)):
            cyl('tire_'+str(side)+'_'+str(j),(x,side*181,76),73,47,dark,(90,0,0),bore=32)
            cyl('wheel_hub_'+str(side)+'_'+str(j),(x,side*181,76),41,49,orange,(90,0,0),bore=14)
            cyl('hub_cap_'+str(side)+'_'+str(j),(x,side*208,76),18,6,silver,(90,0,0))
    # Two raised solar wings with blue cell fields and exposed silver frames.
    for side in (-1,1):
        box('solar_frame_'+str(side),(-35,side*178,269),(270,138,12),silver,3)
        box('solar_cells_'+str(side),(-35,side*178,277),(254,122,5),'#244a70')
        for j in (-1,0,1):
            box('cell_bus_'+str(side)+'_'+str(j),(-35+j*65,side*178,280),(2,119,1),blue)
    cyl('mast_foot',(128,0,227),33,40,orange)
    cyl('sensor_mast',(128,0,337),12,190,silver)
    box('pan_tilt_head',(128,0,435),(76,122,58),dark,9)
    for side in (-1,1):
        cyl('stereo_optic_'+str(side),(169,side*35,436),18,12,blue,(0,90,0))
    box('front_instrument',(218,0,167),(22,113,56),orange,5)
    cyl('instrument_port',(233,0,169),22,8,dark,(0,90,0))
    return parts
