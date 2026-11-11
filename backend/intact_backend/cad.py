"""Deterministic templates only. No LLM-generated Python is accepted or executed."""
from __future__ import annotations
from itertools import combinations
import json, math, os, subprocess, sys, tempfile
from pathlib import Path
from .spec import DesignSpec

def expected_volume(part):
    p=part.params
    v=p.length*p.width*p.height
    if part.template=='plate':v-=4*math.pi*(p.holeDiameter/2)**2*p.height
    if part.template=='heatsink':v=p.length*p.width*4+p.finCount*p.length*1.5*(p.height-4)
    if part.template=='box_shell':v-=(p.length-2*p.wall)*(p.width-2*p.wall)*(p.height-p.wall)
    return v

def build_in_process(spec:DesignSpec,out:Path)->dict:
    import build123d as bd
    out.mkdir(parents=True,exist_ok=True);parts=[];reports=[]
    for part in spec.parts:
        if not part.enabled:continue
        p=part.params
        if part.template=='heatsink':
            body=bd.Box(p.length,p.width,4,align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN))
            for i in range(p.finCount):
                y=-p.width/2+.75+i*(p.width-1.5)/(p.finCount-1)
                body+=bd.Pos(0,y,4)*bd.Box(p.length,1.5,p.height-4,align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN))
        else:
            body=bd.Box(p.length,p.width,p.height,align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN))
            if part.template=='plate':
                for x in (-.32*p.length,.32*p.length):
                    for y in (-.28*p.width,.28*p.width):body-=bd.Pos(x,y,-1)*bd.Cylinder(p.holeDiameter/2,p.height+2,align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN))
            if part.template=='box_shell':body-=bd.Pos(0,0,p.wall)*bd.Box(p.length-2*p.wall,p.width-2*p.wall,p.height-p.wall+1,align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN))
        if not body.is_valid or len(body.solids())!=1 or body.volume<=0:raise ValueError(f'{part.id}: the template did not produce one valid positive-volume solid.')
        wanted=expected_volume(part)
        if abs(body.volume-wanted)/wanted>1e-6:raise ValueError(f'{part.id}: kernel volume differs from the design spec.')
        bounds=body.bounding_box();size=bounds.size
        if any(abs(a-b)>1e-5 for a,b in zip((size.X,size.Y,size.Z),(p.length,p.width,p.height))):raise ValueError(f'{part.id}: kernel bounds differ from the spec.')
        # Select groups by geometric rules on each fresh build; indices are never persisted.
        faces=list(body.faces());tol=1e-5
        groups={
            'base':[f for f in faces if abs(f.center().X+p.length/2)<tol],
            'tip':[f for f in faces if abs(f.center().X-p.length/2)<tol],
            'top':[f for f in faces if abs(f.center().Z-p.height)<tol],
            'bottom':[f for f in faces if abs(f.center().Z)<tol],
            'side_walls':[f for f in faces if abs(f.center().X+p.length/2)>tol and abs(f.center().X-p.length/2)>tol],
        }
        if part.template=='box_shell':groups['pcb_mount']=[f for f in faces if abs(f.center().Z-p.wall)<tol and f.area>(p.length-2*p.wall)*(p.width-2*p.wall)*.99]
        for name,selected in groups.items():
            if not selected:raise ValueError(f'{part.id}: named-face rule {name} did not resolve.')
        body.label=part.name;body.color=part.color;body=body.moved(bd.Pos(*part.position));parts.append((part.id,body))
        reports.append({'id':part.id,'valid':True,'solid_count':1,'volume_mm3':body.volume,'mass_g':body.volume*{'aluminum':2700,'steel':7850,'copper':8960}[part.material]/1e6,'bounds_mm':{'length':size.X,'width':size.Y,'height':size.Z},'face_count':len(faces),'named_faces':{name:{'selector':'recomputed geometric rule','count':len(fs),'area_mm2':sum(f.area for f in fs)} for name,fs in groups.items()}})
    for (aid,a),(bid,b) in combinations(parts,2):
        intersection=a.intersect(b)
        overlap=sum(s.volume for s in intersection.solids()) if intersection is not None else 0
        if overlap>1e-5:raise ValueError(f'Unintended interference between {aid} and {bid}: {overlap:.6g} mm³.')
    assembly=bd.Compound(children=[body for _,body in parts],label='Intact assembly')
    bd.export_step(assembly,out/'model.step');bd.export_stl(assembly,out/'model.stl')
    report={'engine':'build123d','geometry_hash':spec.geometry_hash(),'valid':True,'parts':reports,'interference':[],'artifacts':{'step':'model.step','stl':'model.stl'}}
    (out/'manifest.json').write_text(json.dumps(report,allow_nan=False));return report

class CadService:
    def __init__(self,root:Path):self.root=root;root.mkdir(parents=True,exist_ok=True)
    def build(self,spec:DesignSpec)->dict:
        key=spec.geometry_hash();target=self.root/key
        if (target/'manifest.json').exists():return {**json.loads((target/'manifest.json').read_text()),'cached':True}
        with tempfile.TemporaryDirectory(prefix='build-',dir=self.root) as tmp:
            path=Path(tmp);source=path/'spec.json';source.write_text(spec.model_dump_json())
            # Only trusted, fixed template code runs here. Free-form code needs a separate container runner.
            env={k:v for k,v in os.environ.items() if k in ('PATH','SYSTEMROOT','WINDIR','LD_LIBRARY_PATH','PYTHONPATH')};env['PYTHONUNBUFFERED']='1'
            try:
                run=subprocess.run([sys.executable,'-m','intact_backend.cad_worker',str(source),str(path)],env=env,capture_output=True,text=True,timeout=60,check=False)
            except subprocess.TimeoutExpired as exc:raise ValueError('CAD build exceeded its 60-second limit.') from exc
            if run.returncode:raise ValueError('CAD validation failed: '+run.stderr.strip()[-1200:])
            report=json.loads((path/'manifest.json').read_text());source.unlink()
            if not target.exists():path.rename(target)
            return {**report,'cached':False}
