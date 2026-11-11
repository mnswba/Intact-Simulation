"""Independent reduced analytical and numerical tiers. No 3D FEA is claimed."""
from __future__ import annotations
import math
import numpy as np
from .spec import DesignSpec, MATERIALS

def evaluate(spec:DesignSpec,require_approval:bool=True)->dict:
    if require_approval and spec.simulation.approved_fingerprint!=spec.content_hash():raise ValueError('Review and approve the current boundary conditions before solving.')
    enabled=[p for p in spec.parts if p.enabled]
    if len(enabled)!=1:raise ValueError('Reduced 1D studies require one enabled part.')
    p=enabled[0];s=spec.simulation.study;dims=p.params;L=dims.length/1000;b=dims.width/1000;t=dims.height/1000;mat=MATERIALS[p.material]
    checks=[];warnings=['Representative material constants have not been verified against a supplier datasheet.']
    if s.type=='mechanical':
        if p.template!='beam':raise ValueError('This mechanical adapter requires the beam template.')
        I=b*t**3/12;analytical=s.force*L**3/(3*mat['E_pa']*I)*1000
        def numerical(n):
            le=L/(n-1);K=np.zeros((2*n,2*n));f=np.zeros(2*n)
            local=mat['E_pa']*I/le**3*np.array([[12,6*le,-12,6*le],[6*le,4*le**2,-6*le,2*le**2],[-12,-6*le,12,-6*le],[6*le,2*le**2,-6*le,4*le**2]])
            for e in range(n-1):K[2*e:2*e+4,2*e:2*e+4]+=local
            f[-2]=-s.force;u=np.r_[0.,0.,np.linalg.solve(K[2:,2:],f[2:])];reaction=(K@u-f)[0]
            return u[::2]*1000,abs(reaction-s.force)/s.force
        field,balance=numerical(s.nodes);fine,_=numerical(2*s.nodes-1);value=abs(float(field[-1]));refine=abs(value-abs(float(fine[-1])))/max(abs(float(fine[-1])),1e-12)
        stress=s.force*L*t/(2*I)/1e6
        if L/t<10:warnings.append('Beam length/thickness is below 10; shear deformation is neglected.')
        if value/1000/L>.05:warnings.append('Deflection exceeds the small-deflection regime.')
        if stress*1e6>mat['yield_pa']:warnings.append('The elastic stress exceeds representative yield strength.')
        points=[{'x_mm':float(x),'displacement_mm':float(u),'section_max_stress_mpa':stress*(1-x/L/1000)} for x,u in zip(np.linspace(0,L*1000,s.nodes),field)]
        quantity='tip_displacement';unit='mm';spread=abs(value-analytical)/max(analytical,1e-12)
    else:
        if p.template!='fin':raise ValueError('This thermal adapter requires the single-fin template.')
        A=b*t;P=2*(b+t);k=mat['k_w_mk'];m=math.sqrt(s.convection*P/(k*A))
        rise=s.heat/(k*A*m*math.tanh(m*L));analytical=s.ambient+rise
        def numerical(n):
            dx=L/(n-1);g=k*A/dx;K=np.zeros((n,n));rhs=np.zeros(n);conv=np.full(n,s.convection*P*dx);conv[[0,-1]]*=.5
            for i in range(n):
                K[i,i]=conv[i];rhs[i]=conv[i]*s.ambient
                if i>0:K[i,i]+=g;K[i,i-1]=-g
                if i<n-1:K[i,i]+=g;K[i,i+1]=-g
            rhs[0]+=s.heat;temp=np.linalg.solve(K,rhs)
            return temp,abs(float(conv@(temp-s.ambient))-s.heat)/s.heat
        field,balance=numerical(s.nodes);fine,_=numerical(2*s.nodes-1);value=float(field[0]);refine=abs(value-float(fine[0]))/max(abs(float(fine[0])-s.ambient),1e-12);spread=abs(value-analytical)/max(abs(analytical-s.ambient),1e-12)
        points=[{'x_mm':float(x),'temperature_c':float(v)} for x,v in zip(np.linspace(0,L*1000,s.nodes),field)]
        if s.convection*(A/P)/k>.1:warnings.append('Cross-section temperature uniformity is not justified by Biot number.')
        if value>150:warnings.append('High temperature: constant properties may be unsuitable.')
        quantity='base_temperature';unit='°C'
    balance=float(balance);refine=float(refine);spread=float(spread)
    checks=[{'name':'energy_balance' if s.type=='thermal' else 'force_balance','relative_error':balance,'limit':.01,'passed':balance<.01},{'name':'mesh_sensitivity','relative_error':refine,'limit':.05,'passed':refine<.05},{'name':'analytical_agreement','relative_error':spread,'limit':.1,'passed':spread<.1}]
    confidence='high' if all(c['passed'] for c in checks) else 'medium' if spread<=.25 and balance<.01 else 'low'
    # Material provenance is a real limitation, so implementation agreement never upgrades screening confidence to high.
    confidence='low' if len(warnings)>1 else 'medium' if confidence=='high' else confidence
    return {'spec_hash':spec.content_hash(),'scope':'reduced_1d','quantity':quantity,'unit':unit,'headline':value,'tiers':{'A':{'method':'closed-form analytical','value':analytical},'B':{'method':'1D beam finite elements' if s.type=='mechanical' else '1D fin finite volumes','value':value,'nodes':s.nodes},'C':{'status':'unavailable','reason':'No trained and validated surrogate exists.'}},'relative_spread':spread,'confidence':confidence,'checks':checks,'warnings':warnings,'fields':points,'assumptions':['Single solid with uniform rectangular section.','No 3D stress concentration, radiation, contact, CFD or temperature-dependent material properties.']}
