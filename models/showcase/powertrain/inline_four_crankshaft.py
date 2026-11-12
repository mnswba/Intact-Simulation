"""Original inline-four multi-journal crankshaft concept, mm; shaft axis X.
Separate web/pin leaves support educational inspection; no fatigue or balance claims.
"""
import build123d as bd

def build(params):
    parts={}; pitch=params['journal_pitch']; throw=params['crank_throw']
    def put(n,s,c):s.color=bd.Color(c);parts[n]=s
    def cyl(r,l,x,z=0):return bd.Pos(x,0,z)*bd.Rot(0,90,0)*bd.Cylinder(r,l)
    for i in range(5):
        x=(i-2)*pitch
        journal=cyl(23,24,x)-bd.Pos(x,0,0)*bd.Cylinder(3,70)
        put('main_journal_'+str(i+1),journal,'#c1d0d5')
    for i in range(4):
        x=(i-1.5)*pitch; z=throw if i in (0,3) else -throw
        put('crankpin_'+str(i+1),cyl(20,28,x,z),'#a7bac6')
        for j,dx in enumerate((-21,21)):
            web=cyl(30,14,x+dx,z/2)+bd.Pos(x+dx,0,z/2)*bd.Box(14,44,abs(z)+6)
            web+=cyl(37,14,x+dx,-z*.55)
            web-=cyl(9,18,x+dx,-z*.75)
            put('counterweight_web_'+str(i+1)+'_'+str(j+1),web,'#4c6575')
    flange=cyl(44,14,-2*pitch-23)-cyl(10,18,-2*pitch-23)
    for i in range(6):
        import math
        a=i*math.pi/3
        flange-=bd.Pos(-2*pitch-23,31*math.cos(a),31*math.sin(a))*bd.Rot(0,90,0)*bd.Cylinder(4,20)
    put('flywheel_bolt_flange',flange,'#7e94a1')
    put('timing_snout',cyl(16,42,2*pitch+30)-bd.Pos(2*pitch+33,0,16)*bd.Box(38,6,6),'#d5ad5e')
    return parts
