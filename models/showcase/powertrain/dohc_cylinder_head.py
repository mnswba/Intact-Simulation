"""Original DOHC cutaway head/valvetrain teaching model. Millimeters, Z up.
Two cylinders shown, four valves/cylinder; cam lift, timing and ports illustrative.
"""
import build123d as bd
import math

def build(params):
    parts={}; pitch=params['cylinder_pitch']
    def put(n,s,c):s.color=bd.Color(c);parts[n]=s
    def cx(r,l,x,y,z):return bd.Pos(x,y,z)*bd.Rot(0,90,0)*bd.Cylinder(r,l)
    # An open cast head with combustion bowls, ports and gasket bolt bores.
    head=bd.Pos(0,0,20)*bd.Box(2*pitch+24,116,40)
    head-=bd.Pos(0,0,35)*bd.Box(2*pitch+12,96,32)
    for x in (-pitch/2,pitch/2):
        head-=bd.Pos(x,0,0)*bd.Cylinder(32,16)
        for y in (-36,36):head-=bd.Pos(x,y,16)*bd.Rot(90,0,0)*bd.Cylinder(13,60)
    for x in (-pitch,pitch):
        for y in (-48,48):head-=bd.Pos(x,y,20)*bd.Cylinder(4.5,50)
    put('open_cylinder_head',head,'#9fb5bd')
    # Each cam is one solid, visibly lobed and supported on pedestals.
    for row,y in enumerate((-29,29)):
        cam=cx(7,2*pitch+32,0,y,70)
        for x in (-pitch/2-13,-pitch/2+13,pitch/2-13,pitch/2+13):
            cam+=cx(10,12,x,y,70)+cx(7,12,x,y,79 if row==0 else 61)
        put('intake_camshaft' if row==0 else 'exhaust_camshaft',cam,'#5c7182')
        for j,x in enumerate((-pitch,0,pitch)):
            support=bd.Pos(x,y,48)*bd.Box(14,25,27)
            support-=cx(8,20,x,y,70)
            put('cam_pedestal_'+str(row)+'_'+str(j),support,'#b8c6ca')
        wheel=cx(26,7,pitch+25,y,70)-cx(11,12,pitch+25,y,70)
        for j in range(16):wheel+=bd.Pos(pitch+25,y,70)*bd.Rot(j*22.5,0,0)*bd.Pos(0,25,0)*bd.Box(7,5,5)
        for j in range(4):
            a=j*math.pi/2
            wheel-=cx(5,12,pitch+25,y+17*math.cos(a),70+17*math.sin(a))
        put('timing_wheel_'+str(row+1),wheel,'#c6a05d')
    for cylinder,x0 in enumerate((-pitch/2,pitch/2)):
        for row,y in enumerate((-25,25)):
            for v,dx in enumerate((-13,13)):
                x=x0+dx
                valve=bd.Pos(x,y,31)*bd.Cylinder(2.7,45)+bd.Pos(x,y,8)*bd.Cylinder(10,3)
                put('valve_'+str(cylinder)+str(row)+str(v),valve,'#ccd4da')
                # Guide and annular spring proxy, dimensionally explicit, not a helix.
                spring=bd.Pos(x,y,43)*bd.Cylinder(7.5,18)-bd.Pos(x,y,43)*bd.Cylinder(5.5,21)
                for z in (37,41,45,49):spring-=bd.Pos(x,y,z)*(bd.Cylinder(8,1)-bd.Cylinder(6.4,3))
                put('spring_guide_'+str(cylinder)+str(row)+str(v),spring,'#786850')
    return parts
