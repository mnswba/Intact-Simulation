"""Six-hole flange. Dimensions in millimeters; build(params) runs in the CAD sandbox."""
import math
import build123d as bd

def build(params):
    radius=params['diameter']/2
    thickness=params['thickness']
    body=bd.Cylinder(radius,thickness)-bd.Cylinder(params['bore']/2,thickness+2)
    for index in range(6):
        angle=math.radians(index*60)
        body-=bd.Pos(params['bolt_circle']/2*math.cos(angle),params['bolt_circle']/2*math.sin(angle),0)*bd.Cylinder(params['hole_diameter']/2,thickness+2)
    return {'flange':body}
