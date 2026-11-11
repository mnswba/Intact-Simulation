"""Fifty engineering CAD regression briefs. Sources are test fixtures, not a model whitelist."""
from textwrap import indent,dedent
import math
CASES=[]
def case(key,name,category,body,params,edit,expected,volume=None,parts=None):
    source='import build123d as bd\nimport math\ndef build(params):\n'+indent(dedent(body).strip(),'    ')+'\n'
    CASES.append(dict(key=key,name=name,category=category,source=source,parameters=params,edit=edit,expected_parameters=expected,volume=volume,parts=parts))

case('mounting_plate','Four-hole mounting plate','extrusion / booleans', '''
    body=bd.Box(params['length'],params['width'],params['thickness'])
    for x in (-20,20):
        for y in (-10,10):body-=bd.Pos(x,y,0)*bd.Cylinder(params['hole']/2,params['thickness']+2)
    return {'plate':body}
''',{'length':60,'width':35,'thickness':6,'hole':4},'Increase the four mounting holes from diameter 4 to 5 mm; preserve the plate and hole centers.',{'hole':5},(60*35-4*math.pi*2**2)*6,1)
case('pipe_flange','Six-bolt pipe flange','polar patterns', '''
    body=bd.Cylinder(params['outer']/2,params['thickness'])-bd.Cylinder(params['bore']/2,params['thickness']+2)
    for i in range(6):
        a=math.radians(i*60);body-=bd.Pos(30*math.cos(a),30*math.sin(a),0)*bd.Cylinder(3,params['thickness']+2)
    return {'flange':body}
''',{'outer':80,'thickness':8,'bore':24},'Increase the central bore from 24 to 28 mm diameter. Keep the outer diameter and six bolt holes.',{'bore':28},(math.pi*(40**2-12**2)-6*math.pi*3**2)*8,1)
case('l_bracket','Filleted L bracket','fillets / transverse holes', '''
    a=(bd.Align.MIN,bd.Align.MIN,bd.Align.MIN);t=params['wall']
    body=bd.Box(60,35,t,align=a)+bd.Box(t,35,40,align=a)
    body=bd.fillet(body.edges().filter_by(bd.Axis.Y),params['fillet'])
    body-=bd.Pos(40,17.5,-1)*bd.Cylinder(3,t+2,align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN))
    return {'bracket':body}
''',{'wall':5,'fillet':1},'Change the bracket fillet radius from 1 to 1.5 mm; preserve wall thickness and mounting hole.',{'fillet':1.5},parts=1)
case('u_bracket','Clevis U bracket','three-wall union', '''
    t=params['wall'];w=params['width']
    body=bd.Box(50,w,t)+bd.Pos(-25+t/2,0,12)*bd.Box(t,w,24)+bd.Pos(25-t/2,0,12)*bd.Box(t,w,24)
    body-=bd.Pos(0,0,16)*bd.Rot(0,90,0)*bd.Cylinder(params['pin']/2,60)
    return {'clevis':body}
''',{'wall':5,'width':30,'pin':6},'Increase the transverse clevis pin hole from 6 to 8 mm diameter, keeping both arms.',{'pin':8},parts=1)
case('gusset_bracket','Triangular gusset bracket','polygon extrusion', '''
    body=bd.Box(50,30,4)+bd.Pos(-23,0,18)*bd.Box(4,30,40)
    profile=bd.Plane.XZ*bd.Polygon((-23,0),(20,0),(-23,35),align=None)
    body+=bd.extrude(profile,amount=params['rib'],both=True)
    return {'gusset':body}
''',{'rib':2},'Increase the central gusset rib half-thickness from 2 to 3 mm. Preserve the bracket plates.',{'rib':3},parts=1)
case('angle_rail','Long angle rail','constant section extrusion', '''
    t=params['wall'];a=(bd.Align.MIN,bd.Align.MIN,bd.Align.MIN)
    return {'rail':bd.Box(params['length'],25,t,align=a)+bd.Box(params['length'],t,25,align=a)}
''',{'length':100,'wall':3},'Lengthen the angle rail from 100 to 120 mm while preserving its cross section.',{'length':120},100*(25*3+25*3-3*3),1)
case('t_rail','T-section rail','section union', '''
    t=params['web'];l=params['length']
    return {'rail':bd.Box(l,30,t)+bd.Pos(0,0,12)*bd.Box(l,t,24)}
''',{'web':3,'length':80},'Increase the T rail length from 80 to 100 mm. Keep its T section unchanged.',{'length':100},parts=1)
case('i_beam','I-section beam','section modeling', '''
    l=params['length'];t=params['wall']
    return {'beam':bd.Pos(0,0,-13.5)*bd.Box(l,25,t)+bd.Pos(0,0,13.5)*bd.Box(l,25,t)+bd.Box(l,t,27)}
''',{'length':100,'wall':3},'Make the I beam 140 mm long instead of 100, retaining the section.',{'length':140},parts=1)
case('rectangular_tube','Rectangular hollow tube','hollow section', '''
    l=params['length'];w=params['wall']
    return {'tube':bd.Box(l,30,20)-bd.Box(l+2,30-2*w,20-2*w)}
''',{'length':80,'wall':2},'Increase the rectangular tube wall from 2 to 3 mm, preserving its 30 by 20 mm outside section.',{'wall':3},80*(30*20-26*16),1)
case('round_tube','Round hollow tube','cylindrical surfaces', '''
    return {'tube':bd.Cylinder(params['outer']/2,params['length'])-bd.Cylinder((params['outer']-2*params['wall'])/2,params['length']+2)}
''',{'outer':30,'length':60,'wall':2},'Increase the tube length from 60 to 75 mm. Keep the outside diameter and wall thickness.',{'length':75},math.pi*(15**2-13**2)*60,1)
case('stepped_shaft','Revolved stepped shaft','revolve', '''
    profile=bd.Plane.XZ*bd.Polygon((0,0),(8,0),(8,10),(params['radius'],10),(params['radius'],40),(8,40),(8,50),(0,50),align=None)
    return {'shaft':bd.revolve(profile,axis=bd.Axis.Z)}
''',{'radius':12},'Increase the middle shaft radius from 12 to 14 mm while preserving both 8 mm end radii and axial lengths.',{'radius':14},math.pi*(8**2*20+12**2*30),1)
case('keyed_shaft','Shaft with keyway','slot boolean', '''
    body=bd.Cylinder(params['radius'],50)
    body-=bd.Pos(params['radius']-1,0,0)*bd.Box(4,params['key_width'],32)
    return {'shaft':body}
''',{'radius':10,'key_width':4},'Widen the keyway from 4 to 5 mm without changing its depth, length or shaft diameter.',{'key_width':5},parts=1)
case('v_pulley','V-groove pulley','profile revolve', '''
    r=params['radius'];h=params['height']
    profile=bd.Plane.XZ*bd.Polygon((5,0),(r,0),(r,3),(r-4,6),(r-4,h-6),(r,h-3),(r,h),(5,h),align=None)
    return {'pulley':bd.revolve(profile,axis=bd.Axis.Z)}
''',{'radius':22,'height':20},'Increase the pulley outer radius from 22 to 26 mm. Keep its V groove, height and 10 mm center bore.',{'radius':26},parts=1)
case('double_groove_pulley','Two-groove pulley','multiple revolved grooves', '''
    r=params['radius'];profile=bd.Plane.XZ*bd.Polygon((5,0),(r,0),(r,3),(r-3,5),(r-3,9),(r,11),(r,14),(r-3,16),(r-3,20),(r,22),(r,25),(5,25),align=None)
    return {'pulley':bd.revolve(profile,axis=bd.Axis.Z)}
''',{'radius':20},'Increase the outer pulley radius from 20 to 23 mm while keeping both groove profiles and axial dimensions.',{'radius':23},parts=1)
case('spool','Flanged cable spool','coaxial unions', '''
    body=bd.Cylinder(12,params['length'])+bd.Pos(0,0,-params['length']/2)*bd.Cylinder(22,3)+bd.Pos(0,0,params['length']/2)*bd.Cylinder(22,3)
    return {'spool':body-bd.Cylinder(5,params['length']+10)}
''',{'length':32},'Extend the spool barrel from 32 to 40 mm and move the end flanges accordingly; preserve all radii.',{'length':40},parts=1)
case('toothed_wheel','Radial-tooth indexing wheel','polygon tooth pattern', '''
    body=bd.Cylinder(18,params['thickness'])
    for i in range(16):body+=bd.Rot(0,0,i*22.5)*bd.Pos(18,0,0)*bd.Box(7,3,params['thickness'])
    return {'wheel':body-bd.Cylinder(params['bore']/2,params['thickness']+2)}
''',{'thickness':6,'bore':8},'Increase the indexing wheel bore from 8 to 10 mm. Keep all sixteen straight-sided teeth. This is an indexing-wheel concept, not a rated involute gear.',{'bore':10},parts=1)
case('conical_knob','Conical control knob','cone / blind bore', '''
    body=bd.Cone(14,params['top_radius'],18)
    body-=bd.Pos(0,0,-5)*bd.Cylinder(3,14)
    return {'knob':body}
''',{'top_radius':10},'Increase the knob top radius from 10 to 12 mm; preserve the lower radius, height and blind shaft socket.',{'top_radius':12},parts=1)
case('fluted_knob','Twelve-flute hand knob','radial cuts', '''
    body=bd.Cylinder(18,14)-bd.Cylinder(params['bore']/2,16)
    for i in range(12):
        a=math.radians(i*30);body-=bd.Pos(19*math.cos(a),19*math.sin(a),0)*bd.Cylinder(3,16)
    return {'knob':body}
''',{'bore':6},'Increase the hand knob shaft bore from 6 to 8 mm while preserving all twelve flutes.',{'bore':8},parts=1)
case('hex_nut','Unthreaded hex nut blank','polygon prism', '''
    body=bd.extrude(bd.RegularPolygon(params['radius'],6),amount=8)
    return {'nut':body-bd.Cylinder(params['bore']/2,20)}
''',{'radius':10,'bore':8},'Increase the nut blank bore from 8 to 10 mm; keep the hexagon and height. Do not add cosmetic threads.',{'bore':10},parts=1)
case('hex_bolt','Unthreaded hex-head bolt blank','fastener solids', '''
    head=bd.extrude(bd.RegularPolygon(8,6),amount=5)
    shank=bd.Pos(0,0,-params['length']/2)*bd.Cylinder(4,params['length'])
    return {'bolt':head+shank}
''',{'length':30},'Increase the bolt shank length from 30 to 40 mm, keeping the head and 8 mm unthreaded shank diameter.',{'length':40},parts=1)
case('socket_screw','Socket-head screw blank','hexagonal recess', '''
    body=bd.Pos(0,0,params['length']/2)*bd.Cylinder(3,params['length'])+bd.Pos(0,0,-3)*bd.Cylinder(5,6)
    socket=bd.Pos(0,0,-6)*bd.extrude(bd.RegularPolygon(params['socket_radius'],6),amount=3)
    return {'screw':body-socket}
''',{'length':25,'socket_radius':2.5},'Increase the unthreaded screw shank from 25 to 32 mm while preserving the socket head.',{'length':32},parts=1)
case('washer','Annular washer','annulus extrusion', '''
    return {'washer':bd.Cylinder(params['outer']/2,params['thickness'])-bd.Cylinder(params['bore']/2,params['thickness']+2)}
''',{'outer':24,'bore':10,'thickness':2},'Increase washer thickness from 2 to 3 mm. Preserve the 24 mm outer diameter and 10 mm bore.',{'thickness':3},math.pi*(12**2-5**2)*2,1)
case('split_collar','Split shaft collar','radial slit / transverse drilling', '''
    body=bd.Cylinder(16,12)-bd.Cylinder(params['bore']/2,14)
    body-=bd.Pos(13,0,0)*bd.Box(15,params['slit'],16)
    body-=bd.Pos(11,0,0)*bd.Rot(90,0,0)*bd.Cylinder(2,40)
    return {'collar':body}
''',{'bore':18,'slit':1},'Widen the collar radial slit from 1 to 1.5 mm; preserve its shaft bore and clamp hole.',{'slit':1.5},parts=1)
case('bearing','Ten-part ball bearing concept','spheres / cylindrical races / assembly', '''
    parts={'inner_race':bd.Cylinder(10,8)-bd.Cylinder(6,10),'outer_race':bd.Cylinder(18,8)-bd.Cylinder(14,10)}
    for i in range(8):
        a=math.radians(i*45);parts['ball_'+str(i+1)]=bd.Pos(12*math.cos(a),12*math.sin(a),0)*bd.Sphere(params['ball_radius'])
    return parts
''',{'ball_radius':2},'Change all eight bearing ball radii from 2 to 1.8 mm; preserve both races and the ball centers.',{'ball_radius':1.8},parts=10)
case('hinge','Three-part hinge','coaxial knuckles / assembly', '''
    a=bd.Pos(-11,0,0)*bd.Box(18,30,3);b=bd.Pos(11,0,0)*bd.Box(18,30,3)
    for y in (-10,10):a+=bd.Pos(0,y,0)*bd.Rot(90,0,0)*(bd.Cylinder(3,8)-bd.Cylinder(params['bore']/2,10))
    b+=bd.Rot(90,0,0)*(bd.Cylinder(3,8)-bd.Cylinder(params['bore']/2,10))
    return {'left_leaf':a,'right_leaf':b,'pin':bd.Rot(90,0,0)*bd.Cylinder(1.2,34)}
''',{'bore':3},'Increase the hinge knuckle bore from 3 to 3.4 mm. Preserve the pin and both leaf shapes outside the bores.',{'bore':3.4},parts=3)
case('enclosure','Two-part electronics enclosure','hollow box / assembly', '''
    l=params['length'];w=params['width'];h=params['height'];t=params['wall']
    base=bd.Box(l,w,h)-bd.Pos(0,0,t)*bd.Box(l-2*t,w-2*t,h)
    lid=bd.Pos(0,0,h/2+2)*bd.Box(l,w,3)
    return {'base':base,'lid':lid}
''',{'length':70,'width':45,'height':25,'wall':2},'Increase enclosure wall thickness from 2 to 3 mm. Keep the outside dimensions and lid unchanged.',{'wall':3},parts=2)
case('straight_heatsink','Parallel-fin heat sink','repeated thin solids', '''
    count=int(params['fins']);parts=bd.Box(60,40,4)
    for i in range(count):parts+=bd.Pos(-27+i*54/(count-1),0,10)*bd.Box(2,40,20)
    return {'heatsink':parts}
''',{'fins':10},'Change the heat sink to 12 evenly spaced fins over the same span. Preserve base size and fin thickness/height.',{'fins':12},parts=1)
case('radial_heatsink','Radial-fin heat sink','rotated thin unions', '''
    body=bd.Cylinder(24,3)+bd.Pos(0,0,6)*bd.Cylinder(7,15)
    for i in range(int(params['fins'])):body+=bd.Rot(0,0,i*360/params['fins'])*bd.Pos(14,0,6)*bd.Box(20,1.5,15)
    return {'heatsink':body}
''',{'fins':12},'Increase the radial heat sink from 12 to 16 fins while preserving all other dimensions.',{'fins':16},parts=1)
case('vent_panel','Slotted ventilation panel','rounded slot array', '''
    body=bd.Box(70,45,params['thickness'])
    for y in (-14,-7,0,7,14):body-=bd.extrude(bd.Pos(0,y,-5)*bd.SlotOverall(50,3),amount=12)
    return {'panel':body}
''',{'thickness':3},'Increase the vent panel thickness from 3 to 4 mm while preserving all five rounded slots.',{'thickness':4},parts=1)
case('perforated_disk','Twelve-hole filter disk','radial hole pattern', '''
    body=bd.Cylinder(28,params['thickness'])
    for i in range(12):
        a=math.radians(i*30);body-=bd.Pos(20*math.cos(a),20*math.sin(a),0)*bd.Cylinder(params['hole']/2,10)
    return {'disk':body}
''',{'thickness':4,'hole':4},'Increase the twelve filter holes from diameter 4 to 5 mm, retaining the bolt circle and disk.',{'hole':5},math.pi*(28**2-12*2**2)*4,1)
case('swept_elbow','Hollow 90-degree pipe elbow','curved sweep', '''
    r=params['bend_radius'];path=bd.Plane.XZ*bd.CenterArc((0,0),r,0,90);start=bd.Plane(origin=(r,0,0),z_dir=(0,0,1))
    return {'elbow':bd.sweep(start*bd.Circle(5),path)-bd.sweep(start*bd.Circle(3.5),path)}
''',{'bend_radius':40},'Increase the elbow centerline bend radius from 40 to 50 mm. Keep the 90-degree angle and tube radii.',{'bend_radius':50},math.pi*(5**2-3.5**2)*math.pi/2*40,1)
case('pipe_tee','Hollow pipe tee','intersecting cylindrical booleans', '''
    outer=bd.Cylinder(8,50)+bd.Pos(15,0,0)*bd.Rot(0,90,0)*bd.Cylinder(8,30)
    inner=bd.Cylinder(params['bore']/2,54)+bd.Pos(16,0,0)*bd.Rot(0,90,0)*bd.Cylinder(params['bore']/2,36)
    return {'tee':outer-inner}
''',{'bore':10},'Increase both connected tee flow bores from 10 to 11 mm diameter while keeping the outside geometry.',{'bore':11},parts=1)
case('conical_reducer','Conical pipe reducer','loft / inner loft', '''
    h=params['height'];w=2
    outer=bd.loft([bd.Circle(25),bd.Plane.XY.offset(h)*bd.Circle(14)])
    inner=bd.loft([bd.Circle(25-w),bd.Plane.XY.offset(h)*bd.Circle(14-w)])
    return {'reducer':outer-inner}
''',{'height':45},'Increase reducer axial height from 45 to 55 mm while preserving the end radii and 2 mm wall.',{'height':55},parts=1)
case('rect_round_transition','Rectangular-to-round transition','mixed-profile loft', '''
    h=params['height']
    outer=bd.loft([bd.Rectangle(40,30),bd.Plane.XY.offset(h)*bd.Circle(12)])
    inner=bd.loft([bd.Rectangle(36,26),bd.Plane.XY.offset(h)*bd.Circle(10)])
    return {'duct':outer-inner}
''',{'height':40},'Increase the transition duct height from 40 to 50 mm; preserve both opening profiles and wall offsets.',{'height':50},parts=1)
case('offset_duct','Offset tapered duct','translated loft sections', '''
    h=params['height'];x=params['offset']
    outer=bd.loft([bd.Circle(20),bd.Plane(origin=(x,0,h))*bd.Circle(12)])
    inner=bd.loft([bd.Circle(18),bd.Plane(origin=(x,0,h))*bd.Circle(10)])
    return {'duct':outer-inner}
''',{'height':45,'offset':15},'Increase the duct top opening offset from 15 to 20 mm in X. Keep all radii and height.',{'offset':20},parts=1)
case('helical_spring','Helical compression spring','3D path sweep', '''
    path=bd.Helix(params['pitch'],36,10)
    start=bd.Plane(origin=path.position_at(0),z_dir=path.tangent_at(0))
    return {'spring':bd.sweep(start*bd.Circle(params['wire']/2),path,is_frenet=True)}
''',{'pitch':6,'wire':2},'Increase the spring wire diameter from 2 to 2.4 mm. Preserve the 10 mm centerline radius, pitch and height.',{'wire':2.4},parts=1)
case('helical_tube','Coiled hollow tube','hollow helical sweep', '''
    path=bd.Helix(12,36,15);start=bd.Plane(origin=path.position_at(0),z_dir=path.tangent_at(0))
    return {'coil':bd.sweep(start*bd.Circle(params['outer']/2),path,is_frenet=True)-bd.sweep(start*bd.Circle(1),path,is_frenet=True)}
''',{'outer':4},'Increase the coiled tube outside diameter from 4 to 4.5 mm while retaining its 2 mm bore and centerline path.',{'outer':4.5},parts=1)
case('toroidal_ring','Toroidal sealing ring','toroidal surface', '''
    return {'ring':bd.Torus(params['major'],params['minor'])}
''',{'major':18,'minor':3},'Increase the torus minor radius from 3 to 3.5 mm; retain the 18 mm major radius.',{'minor':3.5},2*math.pi**2*18*3**2,1)
case('spherical_knob','Ball-ended control handle','sphere / cylinder union', '''
    return {'handle':bd.Sphere(params['ball'])+bd.Pos(0,0,-10)*bd.Cylinder(3,18)}
''',{'ball':9},'Increase the spherical handle radius from 9 to 11 mm while keeping the stem.',{'ball':11},parts=1)
case('hemisphere_shell','Hemispherical cover','sphere intersection / shell', '''
    outer=bd.Sphere(params['radius']);inner=bd.Sphere(params['radius']-params['wall'])
    upper=bd.Pos(0,0,25)*bd.Box(100,100,50)
    return {'cover':(outer-inner)&upper}
''',{'radius':20,'wall':2},'Increase the hemispherical cover wall from 2 to 3 mm; keep the outside radius and open equator.',{'wall':3},2*math.pi/3*(20**3-18**3),1)
case('funnel','Funnel with outlet stem','cone / cylindrical stem', '''
    a=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN)
    body=bd.Cone(5,20,30,align=a)+bd.Pos(0,0,-12)*bd.Cylinder(5,12,align=a)
    void=bd.Cone(3,18,30,align=a)+bd.Pos(0,0,-13)*bd.Cylinder(params['outlet']/2,14,align=a)
    return {'funnel':body-void}
''',{'outlet':6},'Increase the funnel outlet bore from 6 to 6.5 mm while keeping the exterior and conical bowl.',{'outlet':6.5},parts=1)
case('dovetail_slide','Two-part dovetail slide','profile extrusion / assembly', '''
    male=bd.Plane.YZ*bd.Polygon((-8,0),(8,0),(12,6),(-12,6),align=None)
    slider=bd.extrude(male,amount=params['length'])
    channel=bd.extrude(bd.Plane.YZ*bd.Polygon((-8.3,-.3),(8.3,-.3),(12.5,6.3),(-12.5,6.3),align=None),amount=params['length']+2,both=True)
    base=bd.Pos(params['length']/2,0,0)*bd.Box(params['length'],34,18)-channel
    return {'slider':slider,'base':base}
''',{'length':60},'Lengthen both dovetail members from 60 to 75 mm. Preserve their cross sections and clearance.',{'length':75},parts=2)
case('snap_tab','Cantilever snap-fit tab','small wedge / fusion', '''
    body=bd.Pos(0,0,params['thickness']/2)*bd.Box(35,10,params['thickness'])
    hook=bd.Plane.XZ*bd.Polygon((12,0),(17.5,0),(17.5,params['thickness']+3),(12,params['thickness']),align=None)
    return {'tab':body+bd.extrude(hook,amount=5,both=True)}
''',{'thickness':2},'Increase the tab beam thickness from 2 to 2.5 mm and keep its hook above the beam.',{'thickness':2.5},parts=1)
case('cable_clip','C-shaped cable clip','open ring / base union', '''
    body=bd.Cylinder(10,10)-bd.Cylinder(params['bore']/2,12)
    body-=bd.Pos(10,0,0)*bd.Box(20,10,14)
    body+=bd.Pos(-10,0,0)*bd.Box(5,24,10)
    return {'clip':body}
''',{'bore':14},'Increase the cable clip opening bore from 14 to 15 mm, retaining the base and side gap.',{'bore':15},parts=1)
case('hose_barb','Hollow hose barb','sawtooth profile revolve', '''
    r=params['radius'];profile=bd.Plane.XZ*bd.Polygon((3,0),(7,0),(7,4),(r,4),(r,8),(r+1,8),(r,12),(r,16),(r+1,16),(r,20),(r,24),(3,24),align=None)
    return {'barb':bd.revolve(profile,axis=bd.Axis.Z)}
''',{'radius':5},'Increase the hose barb nominal outside radius from 5 to 5.5 mm. Preserve the barb ramps, mounting shoulder and 6 mm flow bore.',{'radius':5.5},parts=1)
case('piston_assembly','Three-part piston concept','moving-part static assembly', '''
    piston=bd.Cylinder(12,8);rod=bd.Pos(0,0,4+params['rod_length']/2)*bd.Cylinder(4,params['rod_length'])
    housing=bd.Pos(0,0,-7)*bd.Cylinder(16,30)-bd.Cylinder(12.3,60)
    return {'piston':piston,'rod':rod,'housing':housing}
''',{'rod_length':40},'Increase the piston rod length from 40 to 50 mm, keeping its lower mating face at Z=4 and leaving piston/housing unchanged.',{'rod_length':50},parts=3)
case('two_link_arm','Pinned two-link arm concept','rotated assembly', '''
    profile=bd.Pos(20,0)*bd.Rectangle(40,12)+bd.Circle(6)+bd.Pos(40,0)*bd.Circle(6)
    link=bd.extrude(profile,amount=4)-bd.Cylinder(2,10)-bd.Pos(40,0,0)*bd.Cylinder(2,10)
    second=bd.Pos(40,0,5)*bd.Rot(0,0,params['angle'])*link
    return {'first_link':link,'second_link':second,'pin':bd.Pos(40,0,4)*bd.Cylinder(1.8,14)}
''',{'angle':45},'Rotate only the second arm link to 60 degrees instead of 45 about its pivot at (40,0,5). Keep the first link and pin fixed.',{'angle':60},parts=3)
case('impeller','Six-blade lofted impeller concept','twisted loft / fusion', '''
    body=bd.Cylinder(28,3)+bd.Pos(0,0,5)*bd.Cylinder(8,12)
    for i in range(6):
        sections=[bd.Plane.XY.offset(z)*bd.Rot(0,0,i*60+z)*bd.Pos(15,0)*bd.Rectangle(20,params['blade']) for z in (0,5,10)]
        body+=bd.loft(sections)
    return {'impeller':body-bd.Cylinder(3,30)}
''',{'blade':2},'Increase impeller blade profile thickness from 2 to 2.5 mm; preserve all six blade positions and twist, base, hub and bore.',{'blade':2.5},parts=1)
case('manifold','Cross-drilled manifold block','intersecting passages', '''
    body=bd.Box(60,40,25)-bd.Rot(0,90,0)*bd.Cylinder(4,70)
    for x in (-20,0,20):
        for y in (-10,10):
            body-=bd.Pos(x,y,5)*bd.Cylinder(params['port']/2,20)
            body-=bd.Pos(x,0,0)*bd.Rot(90,0,0)*bd.Cylinder(3,50)
    return {'manifold':body}
''',{'port':6},'Increase all six top port bores from 6 to 7 mm; preserve the block and cross-drilled galleries.',{'port':7},parts=1)
case('engraved_plate','Engraved identification plate','font outlines / engraving', '''
    body=bd.Box(60,22,3)
    text=bd.Pos(0,0,1)*bd.extrude(bd.Text('INTACT',font_size=8,font='DejaVu Sans'),amount=params['depth'])
    return {'plate':body-text}
''',{'depth':1},'Change the engraved plate text from INTACT to CAD LAB. Keep the plate size and engraving depth.',{},parts=1)
assert len(CASES)==50,len(CASES)
assert len({c['key'] for c in CASES})==50
