# Original Intact concept. Units mm; Z up.
# Design prompt: Create an original 3000 mm long scale pedestrian footbridge module with two open Warren side trusses, deck cross-beams, eight separate walking panels with drainage slots, end bearing pads, transverse top ties and bored end connection plates. Use tubular-looking rectangular chords, cylindrical diagonal braces, timber-colored deck panels and silver gussets. Build real holes in end plates and slots in panels. Native named components with a clear walkable central deck and approximately 1100 mm side truss height. This is a display-scale conceptual module, no structural rating or code claims.
# Simplifications: Scale demonstrator with solid chord simplifications and no structural, accessibility, connection or span certification.
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
    for s in (-1,1):
        for j,z in enumerate((90,1050)):add('chord_%s_%s'%(s,j),box(0,s*650,z,3000,65,65),'#447F91')
        for i in range(6):
            a=(-1500+i*500,s*650,90 if i%2==0 else 1050);b=(-1000+i*500,s*650,1050 if i%2==0 else 90)
            add('diagonal_%s_%s'%(s,i),rod(a,b,25),'#6799A4')
    for i,x in enumerate((-1500,-1000,-500,0,500,1000,1500)):add('deck_crossbeam_'+str(i),box(x,0,75,50,1300,65),'#8299A4')
    for i in range(8):
        x=-1312.5+i*375;panel=box(x,0,130,360,1220,45)
        for y in (-430,0,430):panel=panel-box(x,y,130,180,12,55)
        add('drained_deck_panel_'+str(i),panel,'#B69762')
    for i,x in enumerate((-1450,1450)):
        add('top_tie_'+str(i),rod((x,-650,1050),(x,650,1050),25),'#6799A4')
        for s in (-1,1):
            add('bearing_pad_%s_%s'%(i,s),box(x,s*650,25,180,180,30),'#2E424F')
            plate=box(x,s*650,520,20,145,1070)
            for z in (100,320,740,960):plate=plate-bd.Pos(x,s*650,z)*bd.Rot(0,90,0)*cyl(0,0,0,10,26)
            add('end_connection_%s_%s'%(i,s),plate,'#B9C3C8')
    return parts
