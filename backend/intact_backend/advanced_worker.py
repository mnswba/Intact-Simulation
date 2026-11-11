# SPDX-License-Identifier: Apache-2.0
"""Trusted geometry analysis, reconstruction, drawings and mesh-to-B-rep adapter."""
import json,math,resource,sys,traceback
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CPU,(150,150));resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3));resource.setrlimit(resource.RLIMIT_FSIZE,(64*1024**2,64*1024**2))
import numpy as np,trimesh,build123d as bd

def main():
 r=json.loads(Path('/input/request.json').read_text());op=r.pop('operation');report={}
 if op=='mesh_quality':
  from intact_lattice import sampled_thickness
  mesh=trimesh.load('/input/model.stl',force='mesh',process=True)
  report={'watertight':bool(mesh.is_watertight),'positive_volume':bool(mesh.is_volume),'volume_mm3':float(mesh.volume),'bounds_mm':mesh.bounds.tolist(),'triangles':len(mesh.faces),'thickness':sampled_thickness(mesh,96),'scope':'Measured exported mesh. Thickness uses finite inward surface-normal chords, not a global minimum or an exact implicit-surface thickness proof.'}
 elif op=='convert':
  mesh=trimesh.load('/input/model.stl',force='mesh',process=True)
  if not mesh.is_volume:raise ValueError('Only closed, consistently oriented positive-volume meshes can become solids.')
  if len(mesh.faces)>r['maximum_faces']:raise ValueError('Faceted STEP face budget exceeded. Supply a genuinely coarser mesh; no silent decimation is performed.')
  solids=[]
  for component in mesh.split(only_watertight=True):
   faces=[bd.Face(bd.Wire.make_polygon([bd.Vector(*p) for p in tri],close=True)) for tri in component.triangles]
   solid=bd.Solid(bd.Shell(faces))
   if not solid.is_valid or solid.volume<=0:raise ValueError('Faceted B-rep sewing failed.')
   solid.label='converted_'+str(len(solids));solids.append(solid)
  combined=bd.Compound(children=solids);bd.export_step(combined,'/work/result.step');reopened=bd.import_step('/work/result.step');err=abs(reopened.volume-mesh.volume)/mesh.volume
  if err>1e-4:raise ValueError('STEP reopening changed the converted volume.')
  report={'representation':'sewn planar triangular B-rep','faces':len(mesh.faces),'source_volume_mm3':float(mesh.volume),'step_volume_mm3':float(reopened.volume),'relative_volume_error':err,'fitting_error_to_source_triangles_mm':0,'scope':'Planar facets reproduce the input triangles; no smooth analytic TPMS or recovered parametric feature tree. Sampling error relative to the intended implicit surface remains.'}
 elif op=='reconstruct':
  if r['mode']=='orthographic_hull':
   from PIL import Image
   from skimage.measure import marching_cubes
   n=r['voxel_resolution'];solid=np.ones((n,n,n),dtype=bool)
   for view in r['views']:
    image=Image.open('/input/'+view+'.png')
    if image.width*image.height>16000000:raise ValueError('Image pixel budget exceeded.')
    values=np.asarray(image.convert('L'))/255;mask=values<r['threshold'];mask=~mask if r['invert'] else mask;ys,xs=np.where(mask)
    if len(xs)<4:raise ValueError('Silhouette is empty.')
    mask=mask[ys.min():ys.max()+1,xs.min():xs.max()+1];mask=np.asarray(Image.fromarray(mask).resize((n,n),Image.Resampling.NEAREST),dtype=bool)[::-1].T
    solid &= mask[:,:,None] if view=='top' else mask[:,None,:] if view=='front' else mask[None,:,:]
   spacing=np.asarray(r['size_mm'])/n;vertices,faces,_,_=marching_cubes(np.pad(solid,1).astype(np.float32),.5,spacing=spacing);vertices-=np.asarray(r['size_mm'])/2+spacing/2;mesh=trimesh.Trimesh(vertices,faces,process=True);mesh.fix_normals(multibody=True)
   if not mesh.is_volume:raise ValueError('Visual hull did not form a valid closed solid.')
   mesh.export('/work/result.stl');report={'mode':'orthographic_hull','views':list(r['views']),'measured':['User-supplied XYZ dimensions'],'inferred':['Visual hull from aligned orthographic silhouettes; concavities invisible in supplied views are not recovered.'],'voxel_spacing_mm':spacing.tolist(),'scope':'Calibrated orthographic visual hull, not perspective photogrammetry or internal-feature reconstruction.'}
  elif r['mode']=='scan':
   mesh=trimesh.load('/input/scan.stl',force='mesh',process=True)
   if len(mesh.faces)>250000 or not mesh.is_volume:raise ValueError('Scan must be a closed positive-volume STL with <=250,000 triangles; repair is not inferred silently.')
   mesh.export('/work/result.stl');report={'mode':'scan','units':'mm','measured':['Provided scan vertices'],'inferred':[],'scope':'Preserves the supplied watertight scan; no feature recovery or hidden-surface inference.'}
  else:
   from skimage.io import imread
   from skimage.color import rgb2gray
   from skimage.measure import find_contours,approximate_polygon
   image=imread('/input/image.png')
   if image.shape[0]*image.shape[1]>16000000:raise ValueError('Image exceeds 16 million pixels.')
   gray=rgb2gray(image[:,:,:3]) if image.ndim==3 else image.astype(float)/(255 if image.max()>1 else 1)
   mask=gray<r['threshold'];mask=~mask if r['invert'] else mask
   contours=find_contours(np.pad(mask,1),.5)
   if not contours:raise ValueError('No closed silhouette was found.')
   contour=max(contours,key=len);contour=approximate_polygon(contour,tolerance=r['simplify_px']);contour=contour[:-1] if np.allclose(contour[0],contour[-1]) else contour
   if not 3<=len(contour)<=512:raise ValueError('Silhouette complexity exceeds 512 points; increase simplify_px.')
   span=np.ptp(contour[:,1]);scale=r['width_mm']/span;points=[((float(p[1])-contour[:,1].mean())*scale,(-float(p[0])+contour[:,0].mean())*scale,0) for p in contour]
   face=bd.Face(bd.Wire.make_polygon(points,close=True));solid=bd.extrude(face,amount=r['depth_mm']);solid.label='reconstruction';bd.export_step(bd.Compound(children=[solid]),'/work/result.step');report={'mode':'silhouette','calibration_mm_per_pixel':scale,'measured':['User-supplied width_mm'],'inferred':['Largest closed silhouette contour','Constant depth supplied by user; not inferred from a single photo'],'source_note':r['source_note'],'scope':'Calibrated single-view outline extrusion. Does not recover internal holes, multiple photo geometry, perspective correction or hidden surfaces.'}
 else:
  shape=bd.import_step('/input/model.step');parts={p.label:p for p in shape.children};p=parts.get(r.get('part_id'))
  if p is None:raise ValueError('Part not found.')
  if op=='manufacturing':
   direction=np.asarray(r['direction'],float);direction/=np.linalg.norm(direction);findings=[];draft=[];blocked=0;tested=0
   for face in p.faces():
    for u,v in ((.3,.3),(.5,.5),(.7,.7)):
     point=face.position_at(u,v);normal=face.normal_at(u,v);n=np.asarray(tuple(normal));cos=float(np.dot(n,direction));angle=math.degrees(math.asin(min(1,abs(cos))))
     if abs(cos)<.99:draft.append(angle)
     if r['process']=='cnc' and cos>.05:
      # A line from a surface point along the tool approach must not cross other material.
      from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector
      from OCP.gp import gp_Lin,gp_Pnt,gp_Dir
      inter=IntCurvesFace_ShapeIntersector();inter.Load(p.wrapped,1e-7);inter.Perform(gp_Lin(gp_Pnt(*tuple(point)),gp_Dir(*direction)),1e-4,p.bounding_box().size.length*2);blocked+=inter.NbPnt()>0;tested+=1
   if r['process']=='molding':findings.append({'check':'sampled draft','status':'pass' if draft and min(draft)>=r['minimum_draft_deg'] else 'needs_review','minimum_sampled_deg':min(draft) if draft else None})
   if r['process']=='cnc':findings.append({'check':'sampled tool-direction visibility','status':'needs_review' if blocked or not tested else 'sampled_pass','blocked_samples':blocked,'samples':tested})
   # A surface-normal chord sampler in this trusted file avoids importing application code.
   mesh_vertices,mesh_faces=p.tessellate(.1,.15);mesh=trimesh.Trimesh([tuple(v) for v in mesh_vertices],mesh_faces,process=True)
   from intact_lattice import sampled_thickness
   thickness=sampled_thickness(mesh);findings.append({'check':'sampled wall thickness','status':'fail' if thickness['minimum_sampled_mm'] is not None and thickness['minimum_sampled_mm']<r['minimum_wall_mm'] else 'unverified','measurement':thickness})
   report={'process':r['process'],'findings':findings,'face_count':len(p.faces()),'minimum_wall_target_mm':r['minimum_wall_mm'],'certified':False,'scope':'Geometric screening only. Visibility samples do not prove cutter accessibility; draft samples exclude caps and do not prove mold release. Wall target requires separate sampled/native wall analysis; no CAM, tooling or manufacturing certification.'}
  elif op=='drawing':
   from reportlab.pdfgen.canvas import Canvas
   from reportlab.lib.pagesizes import A4,landscape
   c=Canvas('/work/drawing.pdf',pagesize=landscape(A4));c.setTitle(r['title']);c.setFont('Helvetica',14);c.drawString(30,560,r['title'][:80]);c.setFont('Helvetica',8);c.drawString(30,545,'Units: mm | Orthographic mesh-edge projections from exported CAD | Hidden lines not classified | '+r.get('tolerance_note',''))
   verts,tri=p.tessellate(.05,.1);verts=np.asarray([tuple(v) for v in verts]);box=p.bounding_box();dims=tuple(box.size)
   for index,(axes,label) in enumerate([((0,1),'Top XY'),((0,2),'Front XZ'),((1,2),'Right YZ')]):
    x0=45+index*260;y0=180;v=verts[:,axes];lo=v.min(0);span=np.ptp(v,axis=0);scale=min(210/max(span[0],.01),280/max(span[1],.01));v=(v-lo)*scale+np.array([x0,y0]);edges=set()
    for t in tri:
     for a,b in ((t[0],t[1]),(t[1],t[2]),(t[2],t[0])):edges.add(tuple(sorted((int(a),int(b)))))
    if len(edges)>30000:raise ValueError('Drawing complexity budget exceeded.')
    c.setLineWidth(.2)
    for a,b in edges:c.line(*v[a],*v[b])
    c.setFont('Helvetica',10);c.drawString(x0,y0-25,label);c.drawString(x0,y0-42,f'{span[0]:.3f} × {span[1]:.3f} mm');c.line(x0,y0-8,x0+span[0]*scale,y0-8)
   c.setFont('Helvetica',9);c.drawString(30,55,'Overall native CAD bounds: '+ ' × '.join(f'{x:.3f}' for x in dims)+' mm');c.drawString(30,40,'Reference drawing: add datum scheme, feature dimensions and manufacturing tolerances before production.');c.save();report={'dimensions_mm':list(dims),'views':['XY','XZ','YZ'],'scope':'Reference orthographic PDF with measured overall dimensions; not a complete GD&T or hidden-line manufacturing drawing.'}
 Path('/work/report.json').write_text(json.dumps(report,allow_nan=False))
try:main()
except BaseException as exc:Path('/work/error.json').write_text(json.dumps({'error':str(exc),'traceback':traceback.format_exc()[-3000:]}));sys.exit(1)
