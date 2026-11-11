"""200 reproducible configurations: 50 CAD families, 144 lattices, six assemblies."""
from catalog import CASES as NATIVE
from itertools import product
CASES=[]
for c in NATIVE:
    CASES.append({'id':'cad_'+c['key'],'name':c['name'],'source':c['source'],'parameters':c['parameters'],'parts':c['parts'],'volume':c['volume'],'category':'native CAD'})
families=('gyroid','schwarz_p','diamond','neovius','lidinoid','split_p')
bands={'gyroid':.45,'schwarz_p':.55,'diamond':.45,'neovius':1.5,'lidinoid':.8,'split_p':.7}
for family,mode,envelope,variant in product(families,('sheet','solid'),('box','cylinder','sphere'),range(4)):
    p={'length':16+variant,'width':16+variant,'height':16+variant,'cell_size':8,'band':bands[family]*(1+variant*.05),'level':.1*variant,'samples_per_cell':16+2*(variant%2),'phase_x':variant*13,'phase_y':variant*7,'phase_z':variant*19,'gradient':.1*variant if mode=='sheet' else 0}
    CASES.append({'id':f'tpms_{family}_{mode}_{envelope}_{variant}','name':f'{family} · {mode} · {envelope} · {variant+1}','lattice':dict(family=family,mode=mode,envelope=envelope,**p),'category':'TPMS configuration'})

def assembly(key,name,source,parameters,parts):CASES.append({'id':key,'name':name,'source':source,'parameters':parameters,'parts':parts,'category':'assembly'})
assembly('assembly_128','128-component locator array','''import build123d as bd
def build(params):
    return {'locator_'+str(i+1):bd.Pos((i%16)*params['pitch'],(i//16)*params['pitch'],0)*bd.Cylinder(1.5,4) for i in range(128)}
''',{'pitch':5},128)
assembly('phone_exterior','Detailed phone exterior concept','''import build123d as bd
def build(params):
    w=params['width'];l=params['length'];h=params['thickness'];r=params['corner']
    def slab(width,length,height,z,rad):
        s=bd.Box(width,length,height)
        s=bd.fillet(s.edges().filter_by(bd.Axis.Z),rad)
        return bd.Pos(0,0,z)*s
    frame=slab(w,l,h,0,r)-slab(w-2,l-2,h+2,0,r-1)
    # Eight actual speaker bores and a transverse USB-C style slot.
    for i in range(4):
        for sign in (-1,1):frame-=bd.Pos(sign*(10+i*3),-l/2,0)*bd.Rot(90,0,0)*bd.Cylinder(params['speaker_diameter']/2,5)
    frame-=bd.Pos(0,-l/2,0)*bd.Box(9,5,3)
    parts={'frame':frame,'front_glass':slab(w-2,l-2,.6,h/2-.3,r-1),'rear_glass':slab(w-2,l-2,.6,-h/2+.3,r-1),'screen':slab(w-5,l-5,.1,h/2+.05,r-2),'camera_island':bd.Pos(-w/2+17,l/2-18,-h/2-1)*bd.Box(29,30,2),'home_indicator':bd.Pos(0,-l/2+8,h/2+.15)*bd.Box(20,.8,.1),'display_island':bd.Pos(0,l/2-10,h/2+.15)*bd.Box(17,5,.1)}
    for i,(x,y) in enumerate(((-w/2+11,l/2-10),(-w/2+24,l/2-18),(-w/2+11,l/2-26))):
        parts['lens_ring_'+str(i+1)]=bd.Pos(x,y,-h/2-2)*bd.Cylinder(5.5,2)-bd.Pos(x,y,-h/2-2)*bd.Cylinder(4.5,3)
        parts['lens_glass_'+str(i+1)]=bd.Pos(x,y,-h/2-3.05)*bd.Cylinder(4.5,.1)
    parts['flash']=bd.Pos(-w/2+24,l/2-9,-h/2-2.05)*bd.Cylinder(2,.1)
    parts['lidar']=bd.Pos(-w/2+24,l/2-27,-h/2-2.05)*bd.Cylinder(2,.1)
    parts['power_button']=bd.Pos(w/2+.3,18,0)*bd.Box(.6,15,3)
    for i,y in enumerate((20,0,-14)):parts['left_button_'+str(i+1)]=bd.Pos(-w/2-.3,y,0)*bd.Box(.6,8,3)
    for i in range(4):parts['antenna_'+str(i+1)]=bd.Pos((-1 if i%2 else 1)*(w/2+.02),(-1 if i<2 else 1)*(l/2-20),0)*bd.Box(.04,1,h)
    return parts
''',{'width':71.5,'length':147,'thickness':7.8,'corner':9,'speaker_diameter':1.2},23)
assembly('lattice_heatsink','Gyroid core with cooling base','''import build123d as bd
from intact_lattice import tpms
def build(params):
    return {'core':tpms('gyroid',size=(20,20,20),cell_size=params['cell_size'],band=.4,samples_per_cell=16),'base':bd.Pos(0,0,-11)*bd.Box(24,24,2)}
''',{'cell_size':8},2)
assembly('lattice_filter','Diamond filter with annular flange','''import build123d as bd
from intact_lattice import tpms
def build(params):
    return {'filter':tpms('diamond',size=(20,20,16),cell_size=8,band=params['band'],envelope='cylinder',samples_per_cell=16),'flange':bd.Pos(0,0,-9)* (bd.Cylinder(15,2)-bd.Cylinder(9,3))}
''',{'band':.5},2)
assembly('bolted_panel','65-component bolted inspection panel','''import build123d as bd
def build(params):
    plate=bd.Box(90,90,params['thickness']);parts={}
    for i in range(64):
        x=(i%8-3.5)*10;y=(i//8-3.5)*10
        plate-=bd.Pos(x,y,0)*bd.Cylinder(1.6,10)
        parts['fastener_'+str(i+1)]=bd.Pos(x,y,4)*bd.Cylinder(2.5,2)+bd.Pos(x,y,0)*bd.Cylinder(1.4,6)
    parts['panel']=plate
    return parts
''',{'thickness':4},65)
assembly('geartrain_concept','Seven-component indexing transmission concept','''import build123d as bd
def build(params):
    parts={'base':bd.Pos(0,0,-6)*bd.Box(100,45,4)}
    for i,x in enumerate((-32,0,32)):
        gear=bd.Cylinder(13,5)-bd.Cylinder(3,7)
        for j in range(16):gear+=bd.Rot(0,0,j*22.5)*bd.Pos(13,0,0)*bd.Box(5,2,5)
        parts['index_wheel_'+str(i+1)]=bd.Pos(x,0,1)*gear
        parts['shaft_'+str(i+1)]=bd.Pos(x,0,0)*bd.Cylinder(2.8,params['shaft_length'])
    return parts
''',{'shaft_length':16},7)
assert len(CASES)==200
