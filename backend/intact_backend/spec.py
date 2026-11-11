from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
import json
import re
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

KINDS = ('beam', 'fin', 'plate', 'heatsink', 'box_shell', 'custom')
MATERIALS = {
    'aluminum': {'name': 'Aluminum 6061-T6 · representative', 'E_pa': 68.9e9, 'k_w_mk': 167., 'density_kg_m3': 2700., 'yield_pa': 276e6, 'provenance': 'Prototype representative constants; verify against the selected supplier, temper and temperature before design use.'},
    'steel': {'name': 'Steel · representative', 'E_pa': 200e9, 'k_w_mk': 50., 'density_kg_m3': 7850., 'yield_pa': 250e6, 'provenance': 'Representative material, not a certified steel grade.'},
    'copper': {'name': 'Copper · representative', 'E_pa': 117e9, 'k_w_mk': 391., 'density_kg_m3': 8960., 'yield_pa': 70e6, 'provenance': 'Representative material; properties vary with alloy and temper.'},
}
FACE_RULES = {'base': 'minimum_x', 'tip': 'maximum_x', 'top': 'maximum_z', 'bottom': 'minimum_z', 'outer_walls': 'all_external'}

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False, validate_default=True)

class Parameters(StrictModel):
    length: float = Field(gt=0, le=1e6)
    width: float = Field(gt=0, le=1e6)
    height: float = Field(gt=0, le=1e6)
    holeDiameter: float = Field(default=6, ge=.1, le=250)
    finCount: int = Field(default=9, ge=3, le=30)
    wall: float = Field(default=3, ge=.5, le=100)

class Measurements(StrictModel):
    volume_mm3:float=Field(gt=0)
    surface_area_mm2:float=Field(gt=0)
    solid_count:int=Field(ge=1,le=1000)
    face_count:int=Field(ge=1,le=1500000)
    provenance:Literal['OpenCASCADE B-rep','validated triangle mesh']='OpenCASCADE B-rep'
    watertight:bool|None=None
    relative_density:float|None=Field(default=None,gt=0,le=1)

class Part(StrictModel):
    id: str = Field(pattern=r'^[a-z][a-z0-9_]{0,47}$')
    name: str = Field(min_length=1, max_length=100)
    template: Literal['beam','fin','plate','heatsink','box_shell','custom']
    engine: Literal['build123d','implicit_mesh'] = 'build123d'
    enabled: bool = True
    material: Literal['aluminum','steel','copper'] = 'aluminum'
    color: str = Field(default='#6287bc', pattern=r'^#[0-9a-fA-F]{6}$')
    params: Parameters
    measurements:Measurements|None=None
    position: tuple[float,float,float] = (0,0,0)
    @model_validator(mode='after')
    def physical(self):
        p=self.params
        if self.template=='custom' and self.measurements is None:raise ValueError('Generated geometry requires kernel measurements.')
        if self.template!='custom' and (min(p.length,p.width,p.height)<1 or max(p.length,p.width,p.height)>1000):raise ValueError('Template dimensions must be 1–1,000 mm.')
        if self.template=='plate' and p.holeDiameter>min(p.length,p.width)/4: raise ValueError('Plate holes exceed the permitted diameter.')
        if self.template=='heatsink' and (p.height<8 or p.width<2*p.finCount): raise ValueError('Heat sink fins require height ≥8 mm and width ≥2 mm per fin.')
        if self.template=='box_shell' and (2*p.wall>=min(p.length,p.width) or p.wall>=p.height): raise ValueError('Enclosure wall must leave a positive cavity.')
        if any(abs(v)>10000 for v in self.position): raise ValueError('Part position exceeds the work envelope.')
        return self

class Study(StrictModel):
    type: Literal['mechanical','thermal'] = 'mechanical'
    force: float = Field(default=25, gt=0, le=1e6)
    heat: float = Field(default=5, gt=0, le=1e5)
    ambient: float = Field(default=25, ge=-100, le=1000)
    convection: float = Field(default=15, gt=0, le=1e5)
    nodes: int = Field(default=41, ge=11, le=101)

class Simulation(StrictModel):
    study: Study = Field(default_factory=Study)
    # Only the explicit approval endpoint can create this fingerprint; patch tools clear it.
    approved_fingerprint: str | None = Field(default=None, pattern=r'^[a-f0-9]{64}$')

class Program(StrictModel):
    meshing:dict[str,float]|None=None
    asset_id:str|None=Field(default=None,pattern=r'^[a-f0-9]{64}$')
    source:str=Field(min_length=1,max_length=120000)
    parameters:dict[str,float]=Field(default_factory=dict,max_length=150)
    artifact_id:str|None=Field(default=None,pattern=r'^[a-f0-9]{64}$')
    @model_validator(mode='after')
    def contract(self):
        from .program_policy import validate_source,validate_parameters
        validate_source(self.source);self.parameters=validate_parameters(self.parameters)
        if self.meshing is not None:
            from .engineering_schema import Accuracy
            self.meshing=Accuracy.model_validate(self.meshing).model_dump(mode='json')
        return self

class DesignSpec(StrictModel):
    schema_version: Literal[1] = 1
    revision: int = Field(default=1, ge=1)
    units: Literal['mm'] = 'mm'
    parts: list[Part] = Field(min_length=1,max_length=128)
    simulation: Simulation = Field(default_factory=Simulation)
    program:Program|None=None
    @model_validator(mode='after')
    def identities(self):
        if any(p.template=='custom' for p in self.parts) and self.program is None:raise ValueError('Generated parts require their CAD program.')
        if self.program is not None and any(p.template!='custom' for p in self.parts):raise ValueError('A generated CAD document must use its generated parts consistently.')
        if len({p.id for p in self.parts})!=len(self.parts): raise ValueError('Part ids must be unique.')
        if not any(p.enabled for p in self.parts): raise ValueError('At least one part must remain enabled.')
        return self
    def content_hash(self) -> str:
        data=self.model_dump(mode='json');data.pop('revision');data['simulation'].pop('approved_fingerprint')
        return sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    def geometry_hash(self) -> str:
        return sha256(json.dumps({'parts':[p.model_dump(mode='json') for p in self.parts if p.enabled],'program':self.program.model_dump(mode='json') if self.program else None},sort_keys=True,separators=(',',':')).encode()).hexdigest()

class Patch(StrictModel):
    op: Literal['set','add_part','remove_part'] = 'set'
    path: str = Field(default='',max_length=200)
    value: object

class SpecConflict(ValueError): pass

def patch_spec(spec:DesignSpec, patches:list[Patch], expected_hash:str|None=None) -> DesignSpec:
    if expected_hash and expected_hash!=spec.content_hash(): raise SpecConflict('The spec changed. Reload it before applying this edit.')
    if not 1<=len(patches)<=30: raise ValueError('Apply 1–30 edits at a time.')
    data=deepcopy(spec.model_dump(mode='json'))
    for patch in patches:
        if patch.op=='add_part':
            data['parts'].append(Part.model_validate(patch.value).model_dump(mode='json'));continue
        if patch.op=='remove_part':
            if not isinstance(patch.value,str) or not any(p['id']==patch.value for p in data['parts']):raise ValueError('Unknown part id.')
            data['parts']=[p for p in data['parts'] if p['id']!=patch.value];continue
        match=re.fullmatch(r'parts\.([a-z][a-z0-9_]{0,47})\.(name|enabled|material|color|position|params\.(length|width|height|holeDiameter|finCount|wall))',patch.path)
        if match:
            part=next((p for p in data['parts'] if p['id']==match[1]),None)
            if part is None:raise ValueError('Unknown part id.')
            if part['template']=='custom' and match[2].startswith('params.'):raise ValueError('Edit program parameters and rebuild; measured bounds are read-only.')
            keys=match[2].split('.');target=part
            for key in keys[:-1]:target=target[key]
            target[keys[-1]]=patch.value
        elif re.fullmatch(r'simulation\.study\.(type|force|heat|ambient|convection|nodes)',patch.path):
            data['simulation']['study'][patch.path.split('.')[-1]]=patch.value
        else:raise ValueError('This path is not editable by the agent.')
    data['revision']+=1;data['simulation']['approved_fingerprint']=None
    return DesignSpec.model_validate(data)

def from_legacy(design:dict, study:dict|None=None) -> DesignSpec:
    return DesignSpec(parts=[Part(id='main',name=design['name'],template=design['kind'],params=Parameters(**{k:design[k] for k in ('length','width','height','holeDiameter','finCount','wall') if k in design}),material=design['material'])],simulation=Simulation(study=Study.model_validate(study or {})))

def to_legacy(spec:DesignSpec)->dict:
    p=next(p for p in spec.parts if p.enabled)
    return dict(name=p.name,kind=p.template,material=p.material,**{k:v for k,v in p.params.model_dump().items() if k!='wall' or p.template=='box_shell'})

def boundary_table(spec:DesignSpec)->list[dict]:
    enabled=[p for p in spec.parts if p.enabled]
    if len(enabled)!=1:return [{'status':'unsupported','description':'Reduced 1D analysis requires exactly one enabled part.'}]
    p=enabled[0];s=spec.simulation.study
    if s.type=='mechanical':return [{'face':p.id+'.base','condition':'fixed','value':'All beam DOFs fixed'},{'face':p.id+'.tip','condition':'downward_force','value':s.force,'unit':'N'}]
    return [{'face':p.id+'.base','condition':'heat_power','value':s.heat,'unit':'W'},{'face':p.id+'.outer_walls','condition':'side_convection','value':s.convection,'unit':'W/m²K','ambient_c':s.ambient},{'face':p.id+'.tip','condition':'insulated','value':0,'unit':'W'}]
