"""Trusted implicit lattice helpers, usable by sandboxed CAD programs and exports.

Nodal TPMS approximations, not exact minimal surfaces or constant-thickness offsets.
All sampling is bounded before allocating a grid. Coordinates and exports use mm.
"""
import math
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET
import numpy as np
import trimesh
from skimage.measure import marching_cubes

FAMILIES=('gyroid','schwarz_p','diamond','neovius','lidinoid','split_p')
MAX_VOXELS=2500000
MAX_TRIANGLES=1200000

class MeshPart:
    def __init__(self,mesh,metadata=None):
        self.mesh=mesh
        self.metadata=metadata or {}

def field(family,x,y,z):
    sx,sy,sz=np.sin(x),np.sin(y),np.sin(z)
    cx,cy,cz=np.cos(x),np.cos(y),np.cos(z)
    if family=='gyroid':return sx*cy+sy*cz+sz*cx
    if family=='schwarz_p':return cx+cy+cz
    if family=='diamond':return sx*sy*sz+sx*cy*cz+cx*sy*cz+cx*cy*sz
    if family=='neovius':return 3*(cx+cy+cz)+4*cx*cy*cz
    c2x,c2y,c2z=np.cos(2*x),np.cos(2*y),np.cos(2*z)
    wave=np.sin(2*x)*sz*cy+np.sin(2*y)*sx*cz+np.sin(2*z)*sy*cx
    if family=='lidinoid':
        wave=np.sin(2*x)*cy*sz+np.sin(2*y)*cz*sx+np.sin(2*z)*cx*sy
        return wave-(c2x*c2y+c2y*c2z+c2z*c2x)+.3
    if family=='split_p':return 1.1*wave-.2*(c2x*c2y+c2y*c2z+c2z*c2x)-.4*(c2x+c2y+c2z)
    raise ValueError('Choose a supported TPMS family: '+', '.join(FAMILIES))

def tpms(family='gyroid',size=(30,30,30),cell_size=10,band=.3,level=0,
         samples_per_cell=20,mode='sheet',envelope='box',phase=(0,0,0),gradient=0):
    """Create a capped, validated TPMS triangle solid.

    sheet: abs(F-level) <= band*(1+gradient*z/height).
    solid: F >= level. Band is dimensionless, not a wall thickness in mm.
    phase is XYZ degrees. Envelope is box, cylinder (+Z axis), or sphere.
    """
    if family not in FAMILIES:raise ValueError('Unsupported TPMS family.')
    size=np.asarray(size,dtype=float);phase=np.asarray(phase,dtype=float)
    if size.shape!=(3,) or phase.shape!=(3,) or not np.isfinite(size).all() or not np.isfinite(phase).all():raise ValueError('Size and phase must be finite XYZ triples.')
    scalars=(cell_size,band,level,samples_per_cell,gradient)
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in scalars):raise ValueError('TPMS parameters must be finite numbers.')
    if np.any(size<=0) or np.any(size>1000) or not .1<=cell_size<=1000:raise ValueError('Size must be positive and <=1000 mm; cell_size must be 0.1–1000 mm.')
    if not .03<=band<=3 or abs(level)>12 or not -.9<=gradient<=.9:raise ValueError('Band must be 0.03–3, level within ±12, gradient within ±0.9.')
    if samples_per_cell!=int(samples_per_cell) or not 12<=samples_per_cell<=64:raise ValueError('samples_per_cell must be an integer from 12 to 64.')
    if mode not in ('sheet','solid') or envelope not in ('box','cylinder','sphere'):raise ValueError('Choose sheet/solid and box/cylinder/sphere.')
    counts=np.maximum(4,np.ceil(size/cell_size*samples_per_cell).astype(np.int64))
    if int(np.prod(counts+3))>MAX_VOXELS:raise ValueError('TPMS sampling budget exceeded (2,500,000 samples). Reduce size/cell ratio or samples_per_cell; increase cell size instead of disabling isolation.')
    spacing=size/counts
    # One full sample outside every boundary closes the clipped surface.
    # Put box boundaries between samples: coincident zero-valued grid planes can
    # collapse cap triangles and open otherwise valid marching-cubes surfaces.
    axes=[(-size[i]/2-spacing[i]/2+np.arange(int(counts[i])+2)*spacing[i]).astype(np.float32) for i in range(3)]
    x,y,z=np.meshgrid(*axes,indexing='ij',sparse=True)
    p=phase*np.pi/180;k=2*np.pi/cell_size
    values=field(family,k*x+p[0],k*y+p[1],k*z+p[2])-level
    values=band*(1+gradient*z/size[2])-np.abs(values) if mode=='sheet' else values
    boundary=np.minimum(np.minimum(size[0]/2-np.abs(x),size[1]/2-np.abs(y)),size[2]/2-np.abs(z))
    if envelope=='cylinder':boundary=np.minimum(boundary,min(size[:2])/2-np.sqrt(x*x+y*y))
    if envelope=='sphere':boundary=np.minimum(boundary,min(size)/2-np.sqrt(x*x+y*y+z*z))
    values=(np.minimum(values,boundary/cell_size)-1e-7).astype(np.float32)
    # Keep contour vertices away from numerically coincident grid corners.
    # Float32 STL roundtrips can otherwise weld near-zero edges into nonmanifold
    # junctions. This field regularization is far below the sampling resolution.
    epsilon=1e-4
    values=np.where(np.abs(values)<epsilon,np.where(values>=0,epsilon,-epsilon),values).astype(np.float32)
    if not values.max()>0:raise ValueError('This TPMS level/band leaves no material inside the envelope.')
    vertices,faces,_,_=marching_cubes(values,0,spacing=tuple(spacing),allow_degenerate=False)
    if len(faces)>MAX_TRIANGLES:raise ValueError('TPMS triangle budget exceeded. Reduce sampling or cell count.')
    vertices+=np.array([a[0] for a in axes]);mesh=trimesh.Trimesh(vertices=vertices,faces=faces,process=True)
    mesh.fix_normals(multibody=True)
    if not mesh.is_watertight or not mesh.is_winding_consistent or not mesh.is_volume or mesh.volume<=0:raise ValueError('TPMS mesh failed closed-volume validation. Increase sampling or band width.')
    envelope_volume=float(np.prod(size))
    if envelope=='cylinder':envelope_volume=math.pi*(min(size[:2])/2)**2*size[2]
    elif envelope=='sphere':envelope_volume=4*math.pi/3*(min(size)/2)**3
    return MeshPart(mesh,{'family':family,'mode':mode,'envelope':envelope,'cell_size_mm':cell_size,'band':band,'level':level,'samples_per_cell':samples_per_cell,'sampling_spacing_mm':spacing.tolist(),'field_regularization':epsilon,'envelope_volume_mm3':envelope_volume,'relative_density':float(mesh.volume/envelope_volume),'gradient':gradient,'capped':True,'provenance':'Nodal TPMS approximation; dimensions, area and volume are mesh estimates. Band is not constant wall thickness.'})

def write_mesh_exports(items,folder):
    """items: named (name, trimesh, hex_color) in assembled CAD coordinates."""
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);scene=trimesh.Scene()
    for name,mesh,color in items:
        mesh=mesh.copy();rgba=[int(color[i:i+2],16) for i in (1,3,5)]+[255]
        # glTF is meters and +Y up; STL/3MF below remain CAD XYZ millimeters.
        points=mesh.vertices
        mesh.vertices=np.column_stack((points[:,0],points[:,2],-points[:,1]))*.001
        mesh.visual=trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(baseColorFactor=rgba,metallicFactor=.1,roughnessFactor=.55))
        scene.add_geometry(mesh,node_name=name,geom_name=name)
    (folder/'model.glb').write_bytes(scene.export(file_type='glb'))
    (folder/'model.stl').write_bytes(trimesh.util.concatenate([m for _,m,_ in items]).export(file_type='stl'))
    ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';ET.register_namespace('',ns)
    node=lambda tag: '{'+ns+'}'+tag
    root=ET.Element(node('model'),unit='millimeter');resources=ET.SubElement(root,node('resources'));build=ET.SubElement(root,node('build'))
    palette=ET.SubElement(resources,node('basematerials'),id='1')
    for index,(name,mesh,color) in enumerate(items):
        ET.SubElement(palette,node('base'),name=name,displaycolor=color.upper()+'FF')
        obj=ET.SubElement(resources,node('object'),id=str(index+2),type='model',name=name,pid='1',pindex=str(index));m=ET.SubElement(obj,node('mesh'));v=ET.SubElement(m,node('vertices'));t=ET.SubElement(m,node('triangles'))
        for x,y,z in mesh.vertices:ET.SubElement(v,node('vertex'),x=format(x,'.12g'),y=format(y,'.12g'),z=format(z,'.12g'))
        for a,b,c in mesh.faces:ET.SubElement(t,node('triangle'),v1=str(a),v2=str(b),v3=str(c))
        ET.SubElement(build,node('item'),objectid=str(index+2))
    with zipfile.ZipFile(folder/'model.3mf','w',zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('3D/3dmodel.model',ET.tostring(root,encoding='utf-8',xml_declaration=True))
        archive.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        archive.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')

# Priority 2 helpers: original Apache-2.0 adapters.
def as_mesh(shape,tolerance=.05):
    if isinstance(shape,MeshPart):return shape.mesh.copy()
    import build123d as bd
    if not isinstance(shape,bd.Shape):raise ValueError('Supply native CAD or a MeshPart.')
    vertices,faces=shape.tessellate(tolerance,.15)
    mesh=trimesh.Trimesh([tuple(v) for v in vertices],faces,process=True);mesh.fix_normals(multibody=True)
    if not mesh.is_volume:raise ValueError('Native tessellation is not a closed positive volume.')
    return mesh

def hybrid(base,tool,operation='union',tolerance=.05):
    """Mesh boolean on native and/or implicit solids; result remains a mesh."""
    import manifold3d as mf
    if operation not in ('union','difference','intersection'):raise ValueError('Choose union, difference or intersection.')
    import io
    def convert(s,offset=None):
        m=as_mesh(s,tolerance)
        if offset is not None:m.vertices+=offset
        if len(m.faces)>250000:raise ValueError('Boolean input exceeds 250,000 triangles.')
        result=mf.Manifold(mf.Mesh64(np.asarray(m.vertices,dtype=np.float64),np.asarray(m.faces,dtype=np.uint64)))
        if result.status()!=mf.Error.NoError:raise ValueError('Manifold rejected the input solid.')
        return result
    a=convert(base);epsilon=tolerance*.002
    for offset in (np.zeros(3),np.array([1,1.3,1.7])*epsilon,np.array([1,1.3,1.7])*epsilon*3):
        b=convert(tool,offset);result=a+b if operation=='union' else a-b if operation=='difference' else a^b
        result=result.simplify(1e-5);out=result.to_mesh64();m=trimesh.Trimesh(np.asarray(out.vert_properties)[:,:3],out.tri_verts,process=True)
        if not m.is_volume:continue
        reopened=trimesh.load(io.BytesIO(m.export(file_type='stl')),file_type='stl',process=True)
        glb_points=(m.vertices*.001).astype(np.float32).astype(np.float64)*1000;glb_test=trimesh.Trimesh(glb_points,m.faces,process=True)
        if reopened.is_volume and glb_test.is_volume:
            return MeshPart(m,{'operation':operation,'engine':'Manifold double precision','native_tessellation_mm':tolerance,'alignment_perturbation_mm':offset.tolist(),'simplification_tolerance_mm':1e-5,'connected_components':int(m.body_count),'provenance':'Mesh boolean; STL and float32 preview precision checked before commit. Tiny declared alignment perturbations are tried only to avoid export-degenerate coincidences. Not an exact B-rep or smooth blend.'})
    raise ValueError('Boolean is empty or cannot preserve a closed volume at export precision. Move geometry nearer the origin or change coincident feature alignment.')

def sampled_thickness(mesh,samples=48):
    """Finite inward normal ray measurements; never a global minimum proof."""
    tris=mesh.triangles;a=tris[:,0];e1=tris[:,1]-a;e2=tris[:,2]-a;values=[]
    ids=np.linspace(0,len(tris)-1,min(samples,len(tris)),dtype=int)
    for i in ids:
        direction=-mesh.face_normals[i];origin=mesh.triangles_center[i]+direction*1e-5
        h=np.cross(np.broadcast_to(direction,e2.shape),e2);det=np.einsum('ij,ij->i',e1,h);good=np.abs(det)>1e-12;inv=np.divide(1,det,out=np.zeros_like(det),where=good);s=origin-a;u=inv*np.einsum('ij,ij->i',s,h);q=np.cross(s,e1);v=inv*np.einsum('ij,j->i',q,direction);t=inv*np.einsum('ij,ij->i',e2,q);hits=t[good&(u>=-1e-9)&(v>=-1e-9)&(u+v<=1+1e-9)&(t>1e-4)]
        if len(hits):values.append(float(hits.min()+1e-5))
    return {'samples':len(values),'minimum_sampled_mm':min(values) if values else None,'maximum_sampled_mm':max(values) if values else None,'scope':'Finite surface-normal chords, including envelope caps; not global minimum thickness.'}

def tpms_mm(family='gyroid',size=(20,20,20),cell_size=8,thickness_mm=.8,samples_per_cell=24,gradient=0):
    """Distance-transform offsets in mm, with explicit grid uncertainty."""
    from scipy.ndimage import distance_transform_edt
    size=np.asarray(size,float)
    if size.shape!=(3,) or not np.isfinite(size).all() or np.any(size<=0) or max(size)>1000:raise ValueError('Invalid size.')
    if not .05<=thickness_mm<=cell_size/2 or not .1<=cell_size<=1000 or not 12<=samples_per_cell<=64 or not -.8<=gradient<=.8:raise ValueError('Invalid thickness, cell size, resolution or gradient.')
    counts=np.maximum(4,np.ceil(size/cell_size*samples_per_cell).astype(int));spacing=size/counts
    if np.prod(counts+3)>MAX_VOXELS:raise ValueError('Distance-field grid budget exceeded.')
    if thickness_mm*(1-abs(gradient))<3*max(spacing):raise ValueError('Thin wall is under-resolved: use at least three samples across the thinnest wall.')
    axes=[-size[i]/2-spacing[i]+np.arange(counts[i]+3)*spacing[i] for i in range(3)];x,y,z=np.meshgrid(*axes,indexing='ij',sparse=True);k=2*np.pi/cell_size;f=field(family,k*x,k*y,k*z);positive=f>=0
    signed=distance_transform_edt(positive,sampling=spacing)-distance_transform_edt(~positive,sampling=spacing);signed-=np.sign(signed)*min(spacing)/2
    material=thickness_mm*(1+gradient*z/size[2])/2-np.abs(signed);boundary=np.minimum(np.minimum(size[0]/2-np.abs(x),size[1]/2-np.abs(y)),size[2]/2-np.abs(z));values=np.minimum(material,boundary)-1e-6
    points,faces,_,_=marching_cubes(values.astype(np.float32),0,spacing=tuple(spacing),allow_degenerate=False);points+=np.array([a[0] for a in axes]);mesh=trimesh.Trimesh(points,faces,process=True);mesh.fix_normals(multibody=True)
    if not mesh.is_volume:raise ValueError('Distance-offset lattice did not form a valid solid.')
    return MeshPart(mesh,{'family':family,'target_thickness_mm':thickness_mm,'gradient':gradient,'sampling_spacing_mm':spacing.tolist(),'distance_uncertainty_mm':float(np.linalg.norm(spacing)),'relative_density':float(mesh.volume/np.prod(size)),'provenance':'Sampled Euclidean distance-transform offset; not an exact constant-thickness surface.'})
