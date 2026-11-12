# Original Intact gallery concept. Units: millimetres; CAD Z is up.
import build123d as bd
import math

def build(params):
    parts = {}
    def add(name, shape, color):
        shape.color = bd.Color(color)
        parts[name.replace('-', 'n').replace('.', '_')] = shape
    def box(x,y,z,l,w,h):
        return bd.Pos(x,y,z)*bd.Box(l,w,h)
    def cyl(x,y,z,r,h):
        return bd.Pos(x,y,z)*bd.Cylinder(r,h)
    def ring(x,y,z,ro,ri,h):
        return cyl(x,y,z,ro,h)-cyl(x,y,z,ri,h+2)
    radius=params['rotor_radius_mm']; height=params['blade_height_mm']; twist=params['twist_deg']
    add('base',cyl(0,0,10,70,20),'#263C4C')
    add('generator',cyl(0,0,44,36,48),'#6B8793')
    add('generator_band',cyl(0,0,48,37,8),'#DBA359')
    add('shaft',cyl(0,0,80+height/2,9,height+45),'#BDCCD1')
    for i in range(3):
        sections=[]
        for j in range(9):
            frac=j/8; ang=math.radians(i*120+twist*frac)
            profile=bd.Plane.XY.offset(85+height*frac)*bd.Pos(radius*math.cos(ang),radius*math.sin(ang))*bd.Rot(0,0,i*120+twist*frac+90)*bd.Ellipse(33,5)
            sections.append(profile)
        add('twisted_blade_'+str(i),bd.loft(sections),'#35A6AE')
    for k,z in enumerate((85,85+height)):
        add('hub_'+str(k),cyl(0,0,z,19,12),'#DCA358')
        for i in range(3):
            a=i*120+(twist if k else 0)
            add('support_%d_%d'%(k,i),bd.Rot(0,0,a)*box(radius/2,0,z,radius,10,6),'#5D7F8C')
    for i in range(6):
        a=math.radians(i*60)
        add('base_bolt_'+str(i),cyl(54*math.cos(a),54*math.sin(a),22,4,5),'#D3B477')
    return parts
