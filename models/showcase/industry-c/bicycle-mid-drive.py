# Original Intact concept. Units mm; Z up.
# Design prompt: Design a compact original electric bicycle mid-drive display cutaway. Create a 180 by 130 mm open motor cradle, transverse motor stator and rotor, exposed copper bars, a reduction pulley pair joined by a simplified belt envelope, a perforated 160 mm chainring with eight radial windows, opposed crank arms and pedal axles. Add cooling ribs and four bored mounting lugs with steel bolts. Use teal housing, copper winding bars, satin metal chainring, dark belt and ochre cranks. Separate native components with stable descriptive IDs. Omit supplier-specific interfaces and exact belt teeth and clearly document static cutaway simplifications.
# Simplifications: Belt runs and cranks simplified; no involute or sprocket tooth standard, electronics, bearings or frame fitment claim.
import build123d as bd
import math

def build(params):
    parts={}
    def add(n,s,c='#A8B5BF'):
        s=s.scale(params.get('scale',1.0)); s.color=bd.Color(c); parts[n.replace('-', 'neg')]=s
    def box(x,y,z,l,w,h): return bd.Pos(x,y,z)*bd.Box(l,w,h)
    def cyl(x,y,z,r,h): return bd.Pos(x,y,z)*bd.Cylinder(r,h)
    def ring(x,y,z,ro,ri,h): return cyl(x,y,z,ro,h)-cyl(x,y,z,ri,h+2)
    def rod(a,b,r):
        d=bd.Vector(b)-bd.Vector(a); p=(bd.Vector(a)+bd.Vector(b))*0.5
        return bd.Plane(origin=p,z_dir=d)*bd.Cylinder(r,d.length)
    def bolt(n,x,y,z,r=3,h=12):
        add(n,cyl(x,y,z,r,h)+cyl(x,y,z+h/2,r*1.65,r*1.1),'#596674')
    add('open_motor_cradle',box(0,28,0,180,55,130)-box(0,8,0,160,60,110),'#347E88')
    add('motor_stator',bd.Pos(-35,0,0)*bd.Rot(90,0,0)*ring(0,0,0,48,34,62),'#536976')
    add('motor_rotor',bd.Pos(-35,0,0)*bd.Rot(90,0,0)*cyl(0,0,0,29,66),'#BCC6CE')
    for i in range(8):
        a=2*math.pi*i/8
        add('winding_bar_'+str(i),box(-35+40*math.cos(a),0,40*math.sin(a),7,58,7),'#C7894D')
    for i,(x,r) in enumerate([(-35,21),(55,39)]):add('reduction_pulley_'+str(i),bd.Pos(x,-45,0)*bd.Rot(90,0,0)*ring(0,0,0,r,9,15),'#7F929D')
    add('upper_belt_run',rod((-35,-45,21),(55,-45,39),3),'#293C47')
    add('lower_belt_run',rod((-35,-45,-21),(55,-45,-39),3),'#293C47')
    chain=ring(0,0,0,80,12,5)
    for i in range(8):
        a=i*45;chain=chain-bd.Rot(0,0,a)*box(46,0,0,34,13,9)
    add('windowed_chainring',bd.Pos(55,-66,0)*bd.Rot(90,0,0)*chain,'#D2D8DC')
    for s in (-1,1):
        add('crank_arm_'+str(s),rod((55,s*70,0),(55+s*125,s*70,-80*s),10),'#D4A44D')
        add('pedal_axle_'+str(s),rod((55+s*125,s*68,-80*s),(55+s*125,s*110,-80*s),6),'#687984')
    for i in range(5):add('cooling_rib_'+str(i),box(-70+i*28,58,0,5,10,110),'#68949C')
    for i,(x,z) in enumerate([(-78,-72),(78,-72),(-78,72),(78,72)]):
        add('mount_lug_'+str(i),box(x,22,z,24,36,20)-cyl(x,22,z,5,24),'#347E88');bolt('mount_bolt_'+str(i),x,22,z,3,25)
    return parts
