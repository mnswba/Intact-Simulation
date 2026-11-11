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
        if not spec.get('boundary_conditions') and (len(low)==0 or len(high)==0):raise ValueError('The selected axis needs nonempty planar inlet/end boundary facets at both extrema.')
        extra={};scalar_fields={};boundary_evidence=[]
        conditions=spec.get('boundary_conditions',[])
        surface_facets={};face_data={}
        if any(b['selector']=='faces' for b in conditions):
            topology=json.loads(Path('/input/topology.json').read_text());part=next(p for p in topology['parts'] if p['id']==spec['part_id']);face_data={f['ref']:f for f in part['faces']}
            surfaces=[tag for dim,tag in gmsh.model.getBoundary(chosen,oriented=False) if dim==2]
            facet_lookup={tuple(sorted(mesh.facets[:,i])):i for i in mesh.boundary_facets()}
            for condition in conditions:
                for reference in condition.get('references',[]):
                    if reference in surface_facets:continue
                    if reference not in face_data:raise ValueError('A boundary face is missing or belongs to another component: '+reference)
                    face=face_data[reference];candidates=[]
                    for tag in surfaces:
                        area=gmsh.model.occ.getMass(2,tag);center=np.array(gmsh.model.occ.getCenterOfMass(2,tag));tolerance=max(1e-5,float(max(hi-lo))*1000*1e-7)
                        if abs(area-face['area_mm2'])<=max(1,abs(face['area_mm2']))*1e-5 and np.linalg.norm(center-np.array(face['center']))<=tolerance:candidates.append(tag)
                    if len(candidates)!=1:raise ValueError('Boundary face mapping is missing or ambiguous; reselect it: '+reference)
                    types2,_,blocks2=gmsh.model.mesh.getElements(2,candidates[0]);selected=[]
                    for kind2,block in zip(types2,blocks2):
                        if kind2==2:
                            for row in np.asarray(block).reshape(-1,3):
                                key=tuple(sorted(index[int(n)] for n in row))
                                if key in facet_lookup:selected.append(facet_lookup[key])
                    if not selected:raise ValueError('Selected CAD face did not produce exterior boundary facets: '+reference)
                    surface_facets[reference]=np.unique(selected)
        def select_boundary(condition):
            if condition['selector']=='faces':facets=np.unique(np.concatenate([surface_facets[ref] for ref in condition['references']]))
            else:
                a=condition['axis'];level=lo[a] if condition['side']=='low' else hi[a]
                facets=mesh.facets_satisfying(lambda x:np.abs(x[a]-level)<tol,boundaries_only=True)
            if not len(facets):raise ValueError('Boundary '+condition['id']+' has no planar exterior facets. Choose native faces instead.')
            return facets
        if spec['kind']=='thermal':
            if not conditions:conditions=[{'id':'low_temperature','kind':'temperature','selector':'extreme','axis':axis,'side':'low','value':spec['low_value']},{'id':'high_temperature','kind':'temperature','selector':'extreme','axis':axis,'side':'high','value':spec['high_value']}]
            basis=Basis(mesh,ElementTetP1());A=spec['conductivity_w_mk']*asm(laplace,basis)
            @LinearForm
            def source(v,w):return spec['heat_source_w_m3']*v
            physical=asm(source,basis);b=physical.copy();convection_matrix=None;convection_rhs=np.zeros_like(b);Dset=set();x=basis.zeros();used=set();reaction_sets={}
            for condition in conditions:
                facets=select_boundary(condition);overlap=used.intersection(map(int,facets))
                if overlap:raise ValueError('Thermal boundary faces have overlapping conditions; assign each face once.')
                used.update(map(int,facets));fb=FacetBasis(mesh,ElementTetP1(),facets=facets);area=float(np.sum(fb.dx));kind=condition['kind'];boundary_evidence.append({'id':condition['id'],'kind':kind,'facet_count':len(facets),'area_m2':area})
                if kind=='temperature':
                    dofs=basis.get_dofs(facets).all();value=condition['value']
                    if any(i in Dset and abs(x[i]-value)>1e-8 for i in dofs):raise ValueError('Temperature conditions conflict at a shared boundary node.')
                    x[dofs]=value;Dset.update(map(int,dofs));reaction_sets[condition['id']]=dofs
                elif kind=='heat_flux':
                    @LinearForm
                    def flux(v,w):return condition['value']*v
                    load=asm(flux,fb);b+=load;physical+=load
                elif kind=='convection':
                    matrix=condition['h_w_m2k']*asm(mass,fb);load=np.asarray(matrix@np.full(basis.N,condition['ambient_k']))
                    A=A+matrix;b+=load;convection_rhs+=load;convection_matrix=matrix if convection_matrix is None else convection_matrix+matrix
            if not Dset and convection_matrix is None:raise ValueError('Steady thermal analysis needs a temperature or convection boundary to define absolute temperature.')
            D=np.asarray(sorted(Dset),dtype=int);u=solve(*condense(A,b,x=x,D=D));scalar=u;name='temperature_K';vectors=None;free=np.setdiff1d(np.arange(len(u)),D);residual=np.linalg.norm((A@u-b)[free])/max(1,np.linalg.norm(b),np.linalg.norm(A@u))
            reaction=A@u-b;conv_out=float(np.sum(convection_matrix@u-convection_rhs)) if convection_matrix is not None else 0;heat_in=float(physical.sum());temp_reaction=float(reaction[D].sum());balance=abs(conv_out-heat_in-temp_reaction)/max(1,abs(conv_out),abs(heat_in),abs(temp_reaction))
            M=asm(mass,basis);metric=float((M@u).sum()/M.sum());extra.update(mean_temperature_k=metric,heat_input_w=heat_in,convection_heat_out_w=conv_out,temperature_reaction_w=temp_reaction,temperature_reactions_w={key:float(reaction[dofs].sum()) for key,dofs in reaction_sets.items()})
        elif spec['kind']=='structural':
            if not conditions:conditions=[{'id':'fixed_end','kind':'fixed','selector':'extreme','axis':axis,'side':'low','components':[0,1,2],'vector':[0,0,0]},{'id':'end_force','kind':'force','selector':'extreme','axis':axis,'side':'high','vector':spec['force_n']}]
            basis=Basis(mesh,ElementVector(ElementTetP1()));lam,mu=lame_parameters(spec['young_modulus_pa'],spec['poisson_ratio']);A=asm(linear_elasticity(lam,mu),basis);gravity=spec['density_kg_m3']*np.asarray(spec.get('gravity_m_s2',[0,0,0]))
            @LinearForm
            def body_force(v,w):return dot(gravity,v)
            b=asm(body_force,basis);Dset=set();x=basis.zeros();reaction_sets={}
            for condition in conditions:
                facets=select_boundary(condition);fb=FacetBasis(mesh,ElementVector(ElementTetP1()),facets=facets);area=float(np.sum(fb.dx));kind=condition['kind'];boundary_evidence.append({'id':condition['id'],'kind':kind,'facet_count':len(facets),'area_m2':area})
                if kind in ('fixed','displacement'):
                    nodes=np.unique(mesh.facets[:,facets]);groups={};axes=condition.get('components',[0,1,2]);values=condition.get('vector',[0,0,0])
                    for component in axes:
                        dofs=basis.nodal_dofs[component,nodes];value=values[component]*.001 if kind=='displacement' else 0
                        if any(i in Dset and abs(x[i]-value)>1e-12 for i in dofs):raise ValueError('Prescribed displacement conditions conflict at a shared node.')
                        x[dofs]=value;Dset.update(map(int,dofs));groups[component]=dofs
                    reaction_sets[condition['id']]=groups
                elif kind in ('force','pressure'):
                    @LinearForm
                    def traction_load(v,w):return dot(np.asarray(condition['vector'])/area,v) if kind=='force' else -condition['value']*dot(w.n,v)
                    b+=asm(traction_load,fb)
            D=np.asarray(sorted(Dset),dtype=int)
            if not len(D):raise ValueError('Structural analysis needs supports.')
            rigid=[];relative=(mesh.p.T-mesh.p.mean(axis=1))/max(hi-lo)
            for component in range(3):
                nodes=np.flatnonzero(np.isin(basis.nodal_dofs[component],D))
                for node in nodes:
                    px,py,pz=relative[node];rotation=np.array([[0,pz,-py],[-pz,0,px],[py,-px,0]])
                    rigid.append([*np.eye(3)[component],*rotation[component]])
            if np.linalg.matrix_rank(np.asarray(rigid))<6:raise ValueError('Supports leave rigid-body motion unconstrained. Restrain all six rigid-body modes.')
            u=solve(*condense(A,b,x=x,D=D));vectors=np.asarray([u[basis.nodal_dofs[i]] for i in range(3)]).T;scalar=np.linalg.norm(vectors,axis=1)*1000;name='displacement_mm';free=np.setdiff1d(np.arange(len(u)),D);residual=np.linalg.norm((A@u-b)[free])/max(1,np.linalg.norm(b));metric=float(scalar.max());reaction=A@u-b
            external=np.asarray([b[dofs].sum() for dofs in basis.split_indices()]);support=np.asarray([reaction[dofs].sum() for dofs in basis.split_indices()]);balance=float(np.linalg.norm(support+external)/max(1,np.linalg.norm(external)))
            extra.update(applied_force_n=external.tolist(),reaction_force_n=support.tolist(),support_reactions_n={key:[float(reaction[groups[c]].sum()) if c in groups else 0 for c in range(3)] for key,groups in reaction_sets.items()})
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
        result={'kind':spec['kind'],'field_name':name,'positions_mm':(mesh.p.T*1000).tolist(),'triangles':boundary.tolist(),'values':scalar.tolist(),'minimum':float(scalar.min()),'maximum':float(scalar.max()),'metric':metric,'tetrahedra':len(cells),'vertices':len(points),'mesh_size_mm':h,'relative_residual':float(residual),'relative_balance_error':balance,'boundary_conditions':{'axis':axis,'low_boundary_facets':len(low),'high_boundary_facets':len(high)},'scope':{'thermal':'3D steady isotropic conduction with prescribed temperatures, flux, convection and volumetric heating; unassigned faces insulated.','structural':'3D small-strain isotropic linear elasticity with supports, prescribed displacements, face forces/pressure and gravity. No contact, plasticity or buckling.','stokes':'3D incompressible creeping flow, Taylor-Hood P2/P1; pressure traction at inlet, zero outlet traction, no-slip side walls. Not turbulent or inertial CFD.'}[spec['kind']]}
        result.update(extra);result['boundary_assignments']=boundary_evidence
        if spec['kind']=='stokes':
            reynolds=float(spec['density_kg_m3']*float(scalar.max())*min((hi-lo)[i] for i in range(3) if i!=axis)/spec['viscosity_pa_s']);result.update(inlet_flow_m3_s=-qi,outlet_flow_m3_s=qo,pressure_min_pa=float(pressure.min()),pressure_max_pa=float(pressure.max()),estimated_reynolds=reynolds,regime_valid=bool(reynolds<=.1),regime_scope='Conservative Re estimate using maximum speed and minimum transverse bounding-box span; creeping-flow acceptance requires Re <=0.1.')
        if spec['kind']=='structural':
            grad=basis.interpolate(u).grad;strain=(grad+np.swapaxes(grad,0,1))*.5;stress=2*mu*strain+lam*np.einsum('iieq->eq',strain)[None,None,:,:]*np.eye(3)[:,:,None,None];dev=stress-np.einsum('iieq->eq',stress)[None,None,:,:]*np.eye(3)[:,:,None,None]/3;vm=np.sqrt(1.5*np.einsum('ijeq,ijeq->eq',dev,dev)).mean(axis=1)
            result['maximum_von_mises_pa']=float(vm.max());result['stress_scope']='Element-average linear-elastic von Mises stress; singularities and mesh sensitivity require a separate stress convergence study.'
            weights=np.abs(np.linalg.det(np.transpose(mesh.p[:,mesh.t[1:]]-mesh.p[:,mesh.t[0]][:,None,:],(2,0,1))))/6
            nodal=np.zeros(mesh.nvertices);denominator=np.zeros(mesh.nvertices)
            for row in mesh.t:np.add.at(nodal,row,vm*weights);np.add.at(denominator,row,weights)
            scalar_fields['von_mises_Pa']=(nodal/np.maximum(denominator,1e-30)).tolist()
            for component,label in enumerate(('ux_mm','uy_mm','uz_mm')):scalar_fields[label]=(vectors[:,component]*1000).tolist()
            result['maximum_linear_strain']=float(np.abs(strain).max());result['regime_valid']=result['maximum_linear_strain']<=.01
        scalar_fields[name]=scalar.tolist();result['fields']=scalar_fields
        vector_fields={'displacement_vector_mm':vectors*1000} if vectors is not None and spec['kind']=='structural' else {'velocity_m_s':vectors} if vectors is not None else {}
        meshio.write('/work/results.vtu',meshio.Mesh(mesh.p.T*1000,[('tetra',np.asarray(cells))],point_data={**{key:np.asarray(values) for key,values in scalar_fields.items()},**vector_fields},cell_data={'von_mises_Pa':[vm]} if spec['kind']=='structural' else {}))
        import csv
        with Path('/work/results.csv').open('w',newline='') as stream:
            writer=csv.writer(stream);keys=list(scalar_fields);writer.writerow(['x_mm','y_mm','z_mm',*keys])
            for i,point in enumerate(mesh.p.T*1000):writer.writerow([*point,*[scalar_fields[key][i] for key in keys]])
        return result
    finally:gmsh.finalize()

def main():
    spec=json.loads(Path('/input/request.json').read_text());coarse=calculate(spec,spec['mesh_size_mm']);result=coarse
    if spec['convergence']:
        try:
            fine=calculate(spec,spec['mesh_size_mm']*.7);change=abs(fine['metric']-coarse['metric'])/max(abs(fine['metric']),1e-15);fine['convergence']={'coarse_metric':coarse['metric'],'fine_metric':fine['metric'],'relative_change':change,'tolerance':spec['convergence_tolerance'],'passed':change<=spec['convergence_tolerance']};result=fine
            if spec['kind']=='thermal':
                peak_change=max(abs(fine[k]-coarse[k])/max(abs(fine[k]),1e-15) for k in ('minimum','maximum'));result['peak_temperature_convergence']={'relative_change':peak_change,'passed':peak_change<=spec['convergence_tolerance']};result['convergence']['passed']=result['convergence']['passed'] and result['peak_temperature_convergence']['passed']
            if spec['kind']=='structural':
                stress_change=abs(fine['maximum_von_mises_pa']-coarse['maximum_von_mises_pa'])/max(abs(fine['maximum_von_mises_pa']),1e-15);result['stress_convergence']={'relative_change':stress_change,'passed':stress_change<=spec['convergence_tolerance'],'scope':'Peak element-average stress refinement; local singularities may not converge.'}
        except ValueError as exc:result['convergence']={'passed':False,'reason':str(exc)}
    else:result['convergence']={'passed':False,'reason':'Mesh refinement comparison was not requested.'}
    result['solver_checks_passed']=True;result['verified']=result['convergence']['passed'] and result.get('regime_valid',True);result['verified_fields']={result['field_name']:result['verified']};
    if spec['kind']=='structural':result['verified_fields']['von_mises_Pa']=result['verified'] and result.get('stress_convergence',{}).get('passed',False)
    result['study_definition']=spec;result['unit_system']='CAD coordinates mm converted to m; force N, pressure Pa, temperature K, conductivity W/(m K), viscosity Pa s. Defaults are representative inputs, not supplier-certified properties.';Path('/work/report.json').write_text(json.dumps(result,allow_nan=False))
try:main()
except BaseException as exc:Path('/work/error.json').write_text(json.dumps({'error':str(exc),'traceback':traceback.format_exc()[-3000:]}));sys.exit(1)
