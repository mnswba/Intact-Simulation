# SPDX-License-Identifier: Apache-2.0
"""Bounded 3D tetrahedral linear PDE solvers; no model-authored code."""
import json,resource,sys,traceback
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CPU,(160,160));resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3));resource.setrlimit(resource.RLIMIT_FSIZE,(64*1024**2,64*1024**2))
import numpy as np
import gmsh,meshio
from scipy.sparse import bmat
from skfem import MeshTet,Basis,FacetBasis,ElementTetP1,ElementTetP2,ElementVector,LinearForm,asm,condense,solve
from skfem.helpers import dot
from skfem.models.poisson import laplace,vector_laplace,mass
from skfem.models.elasticity import linear_elasticity,lame_parameters
from skfem.models.general import divergence

def calculate(spec,h):
    gmsh.initialize(['-nopopup']);gmsh.option.setNumber('General.Terminal',0);gmsh.option.setNumber('General.NumThreads',1)
    try:
        gmsh.model.occ.importShapes('/input/model.step');gmsh.model.occ.synchronize();
        volumes=gmsh.model.getEntities(3);chosen=[v for v in volumes if gmsh.model.getEntityName(*v).split('/')[-1]==spec['part_id']]
        if not chosen and len(volumes)==1:chosen=volumes
        if len(chosen)!=1:raise ValueError('Select a uniquely named single native solid for meshing: '+str([(v,gmsh.model.getEntityName(*v)) for v in volumes]))
        gmsh.model.occ.remove([v for v in volumes if v not in chosen],recursive=True);gmsh.model.occ.synchronize();gmsh.option.setNumber('Mesh.MeshSizeMin',h);gmsh.option.setNumber('Mesh.MeshSizeMax',h);gmsh.option.setNumber('Mesh.MeshSizeFromCurvature',12);gmsh.model.mesh.generate(3)
        tags,coords,_=gmsh.model.mesh.getNodes();index={int(t):i for i,t in enumerate(tags)};points=np.asarray(coords).reshape(-1,3)*.001;types,_,blocks=gmsh.model.mesh.getElements(3);cells=[]
        for kind,block in zip(types,blocks):
            if kind==4:cells.extend([[index[int(v)] for v in row] for row in np.asarray(block).reshape(-1,4)])
        if not cells or len(cells)>18000 or len(points)>6000:raise ValueError('Simulation mesh budget exceeded: <=18,000 tetrahedra and <=6,000 vertices. Increase mesh_size_mm.')
        mesh=MeshTet(points.T,np.asarray(cells).T);axis=spec['axis'];lo=points.min(0);hi=points.max(0);tol=max(hi-lo)*1e-7
        low=mesh.facets_satisfying(lambda x:np.abs(x[axis]-lo[axis])<tol,boundaries_only=True);high=mesh.facets_satisfying(lambda x:np.abs(x[axis]-hi[axis])<tol,boundaries_only=True)
        if len(low)==0 or len(high)==0:raise ValueError('The selected axis needs nonempty planar inlet/end boundary facets at both extrema.')
        if spec['kind']=='thermal':
            basis=Basis(mesh,ElementTetP1());A=spec['conductivity_w_mk']*asm(laplace,basis)
            @LinearForm
            def load(v,w):return spec['heat_source_w_m3']*v
            b=asm(load,basis);D=np.union1d(basis.get_dofs(low).all(),basis.get_dofs(high).all());x=basis.zeros();x[basis.get_dofs(low).all()]=spec['low_value'];x[basis.get_dofs(high).all()]=spec['high_value'];u=solve(*condense(A,b,x=x,D=D));scalar=u;name='temperature_K';free=np.setdiff1d(np.arange(len(u)),D);residual=np.linalg.norm((A@u-b)[free])/max(1,np.linalg.norm(b),np.linalg.norm(A@u));metric=float(u.max());vectors=None
            reaction=A@u-b;balance=abs(float(reaction[D].sum()+b.sum()))/max(1,abs(float(reaction[D].sum())),abs(float(b.sum())))
            M=asm(mass,basis);metric=float((M@u).sum()/M.sum())
        elif spec['kind']=='structural':
            basis=Basis(mesh,ElementVector(ElementTetP1()));lam,mu=lame_parameters(spec['young_modulus_pa'],spec['poisson_ratio']);A=asm(linear_elasticity(lam,mu),basis);facets=FacetBasis(mesh,ElementVector(ElementTetP1()),facets=high);area=float(np.sum(facets.dx));traction=np.asarray(spec['force_n'])/area
            @LinearForm
            def load(v,w):return dot(traction,v)
            b=asm(load,facets);D=basis.get_dofs(low).all();u=solve(*condense(A,b,D=D));vectors=np.asarray([u[ix] for ix in basis.split_indices()]).T;scalar=np.linalg.norm(vectors,axis=1)*1000;name='displacement_mm';free=np.setdiff1d(np.arange(len(u)),D);residual=np.linalg.norm((A@u-b)[free])/max(1,np.linalg.norm(b));metric=float(scalar.max());reaction=A@u-b;balance=float(np.linalg.norm(np.asarray([reaction[ix].sum() for ix in basis.split_indices()])+np.asarray(spec['force_n']))/max(1,np.linalg.norm(spec['force_n'])))
        else:
            ub=Basis(mesh,ElementVector(ElementTetP2()),intorder=4);pb=Basis(mesh,ElementTetP1(),intorder=4)
            if ub.N+pb.N>24000:raise ValueError('Stokes mixed-system DOF budget exceeded; increase mesh size.')
            A=spec['viscosity_pa_s']*asm(vector_laplace,ub);B=asm(divergence,ub,pb);K=bmat([[A,-B.T],[-B,None]],format='csr');fb=FacetBasis(mesh,ElementVector(ElementTetP2()),facets=low,intorder=4)
            @LinearForm
            def inlet(v,w):return -spec['pressure_drop_pa']*dot(w.n,v)
            b=np.concatenate([asm(inlet,fb),pb.zeros()]);walls=np.setdiff1d(mesh.boundary_facets(),np.union1d(low,high));D=ub.get_dofs(walls).all();u=solve(*condense(K,b,D=D));velocity=u[:ub.N];pressure=u[ub.N:];vectors=np.asarray([velocity[ub.nodal_dofs[i]] for i in range(3)]).T;scalar=np.linalg.norm(vectors,axis=1);name='speed_m_s';free=np.setdiff1d(np.arange(len(u)),D);residual=np.linalg.norm((K@u-b)[free])/max(1,np.linalg.norm(b));metric=float(scalar.max())
            def flux(f):
                fbase=FacetBasis(mesh,ElementVector(ElementTetP2()),facets=f,intorder=4);v=fbase.interpolate(velocity);return float(np.sum(np.sum(v*fbase.normals,axis=0)*fbase.dx))
            qi,qo=flux(low),flux(high);balance=abs(qi+qo)/max(abs(qi),abs(qo),1e-20);metric=qo
        if not np.isfinite(scalar).all() or residual>1e-6 or balance>1e-5:raise ValueError('Solver residual or conservation check failed.')
        boundary=mesh.facets[:,mesh.boundary_facets()].T
        result={'kind':spec['kind'],'field_name':name,'positions_mm':(mesh.p.T*1000).tolist(),'triangles':boundary.tolist(),'values':scalar.tolist(),'minimum':float(scalar.min()),'maximum':float(scalar.max()),'metric':metric,'tetrahedra':len(cells),'vertices':len(points),'mesh_size_mm':h,'relative_residual':float(residual),'relative_balance_error':balance,'boundary_conditions':{'axis':axis,'low_boundary_facets':len(low),'high_boundary_facets':len(high)},'scope':{'thermal':'3D steady isotropic conduction; two isothermal extrema, remaining boundaries insulated.','structural':'3D small-strain isotropic linear elasticity; clamped low end and uniform total force at high end. No contact, plasticity or buckling.','stokes':'3D incompressible creeping flow, Taylor-Hood P2/P1; pressure traction at inlet, zero outlet traction, no-slip side walls. Not turbulent or inertial CFD.'}[spec['kind']]}
        if spec['kind']=='stokes':
            reynolds=float(spec['density_kg_m3']*float(scalar.max())*min((hi-lo)[i] for i in range(3) if i!=axis)/spec['viscosity_pa_s']);result.update(inlet_flow_m3_s=-qi,outlet_flow_m3_s=qo,pressure_min_pa=float(pressure.min()),pressure_max_pa=float(pressure.max()),estimated_reynolds=reynolds,regime_valid=bool(reynolds<=.1),regime_scope='Conservative Re estimate using maximum speed and minimum transverse bounding-box span; creeping-flow acceptance requires Re <=0.1.')
        if spec['kind']=='structural':
            grad=basis.interpolate(u).grad;strain=(grad+np.swapaxes(grad,0,1))*.5;stress=2*mu*strain+lam*np.einsum('iieq->eq',strain)[None,None,:,:]*np.eye(3)[:,:,None,None];dev=stress-np.einsum('iieq->eq',stress)[None,None,:,:]*np.eye(3)[:,:,None,None]/3;vm=np.sqrt(1.5*np.einsum('ijeq,ijeq->eq',dev,dev)).mean(axis=1)
            result['maximum_von_mises_pa']=float(vm.max());result['stress_scope']='Element-average linear-elastic von Mises stress; singularities and mesh sensitivity require a separate stress convergence study.'
            result['maximum_linear_strain']=float(np.abs(strain).max());result['regime_valid']=result['maximum_linear_strain']<=.01
        vector_fields={'displacement_vector_mm':vectors*1000} if vectors is not None and spec['kind']=='structural' else {'velocity_m_s':vectors} if vectors is not None else {}
        meshio.write('/work/results.vtu',meshio.Mesh(mesh.p.T*1000,[('tetra',np.asarray(cells))],point_data={name:scalar,**vector_fields}))
        return result
    finally:gmsh.finalize()

def main():
    spec=json.loads(Path('/input/request.json').read_text());coarse=calculate(spec,spec['mesh_size_mm']);result=coarse
    if spec['convergence']:
        try:
            fine=calculate(spec,spec['mesh_size_mm']*.7);change=abs(fine['metric']-coarse['metric'])/max(abs(fine['metric']),1e-15);fine['convergence']={'coarse_metric':coarse['metric'],'fine_metric':fine['metric'],'relative_change':change,'tolerance':spec['convergence_tolerance'],'passed':change<=spec['convergence_tolerance']};result=fine
        except ValueError as exc:result['convergence']={'passed':False,'reason':str(exc)}
    else:result['convergence']={'passed':False,'reason':'Mesh refinement comparison was not requested.'}
    result['solver_checks_passed']=True;result['verified']=result['convergence']['passed'] and result.get('regime_valid',True);result['study_definition']=spec;result['unit_system']='CAD coordinates mm converted to m; force N, pressure Pa, temperature K, conductivity W/(m K), viscosity Pa s. Defaults are representative inputs, not supplier-certified properties.';Path('/work/report.json').write_text(json.dumps(result,allow_nan=False))
try:main()
except BaseException as exc:Path('/work/error.json').write_text(json.dumps({'error':str(exc),'traceback':traceback.format_exc()[-3000:]}));sys.exit(1)
