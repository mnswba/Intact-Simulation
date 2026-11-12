# Original Intact concept. Units mm; Z up.
# Design prompt: Create an original 420 mm wide open-frame desktop additive manufacturing machine with four vertical columns, upper rails, a perforated heated bed, two horizontal guide rails and a cross carriage. Include a finned print head with visible heater block and conical nozzle, two lead screws represented by plain shafts with annular collars, four corner feet, belt runs, motor boxes, a side electronics enclosure with real ventilation slots and an overhead filament spool with bore and flanges. Use charcoal frame, turquoise carriage, copper heater and gold nozzle. Native named parts and fixed pose, no firmware, printing or precision claims.
# Simplifications: Fixed printer pose; lead screws use plain shafts and collars, filament winding and complete motion hardware are simplified.
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
    add('base_frame',box(0,0,20,420,380,40)-box(0,0,20,340,300,50),'#354D5B')
    for i,(x,y) in enumerate([(-185,-165),(185,-165),(-185,165),(185,165)]):
        add('vertical_column_'+str(i),box(x,y,245,25,25,450),'#435D6B')
        add('foot_'+str(i),box(x,y,-8,45,45,16),'#263C47')
    for s in (-1,1):
        add('top_crossrail_'+str(s),box(0,s*165,470,400,25,25),'#435D6B')
        add('x_guide_'+str(s),rod((-175,s*25,300),(175,s*25,300),6),'#AFBFC8')
        add('z_lead_screw_'+str(s),rod((s*165,0,55),(s*165,0,450),5),'#C7D0D7')
        for k in range(3):add('screw_collar_%s_%s'%(s,k),ring(s*165,0,160+k*115,10,5,9),'#B89A5F')
        add('z_motor_'+str(s),box(s*165,0,60,42,42,35),'#243B49')
        add('belt_run_'+str(s),rod((-175,s*47,310),(175,s*47,310),2),'#253943')
    bed=box(0,0,145,270,265,10)
    for x in (-115,115):
        for y in (-112,112):bed=bed-cyl(x,y,145,4,15)
    add('perforated_build_bed',bed,'#9AAFB8')
    add('build_surface',box(0,0,151,250,245,2),'#3D6E79')
    add('cross_carriage',box(15,0,303,65,85,18),'#3C9CA4')
    for i in range(6):add('hotend_fin_'+str(i),box(15,0,280-i*6,35,35,2.5),'#B6C5CB')
    add('heater_block',box(15,0,238,25,23,13),'#C58D50')
    add('nozzle',bd.Pos(15,0,226)*bd.Cone(1,6,12),'#D2AA54')
    enclosure=box(240,30,115,65,190,170)-box(240,25,115,55,180,158)
    for z in range(65,171,15):enclosure=enclosure-box(272,30,z,10,135,5)
    add('vented_electronics',enclosure,'#486775')
    add('spool_support',box(0,145,540,30,25,140),'#557584')
    add('filament_spool_core',bd.Pos(0,145,610)*bd.Rot(0,90,0)*ring(0,0,0,65,15,65),'#BD995A')
    for s in (-1,1):add('spool_flange_'+str(s),bd.Pos(s*36,145,610)*bd.Rot(0,90,0)*ring(0,0,0,85,15,6),'#D7D0B8')
    return parts
