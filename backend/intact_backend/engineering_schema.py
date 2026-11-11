# SPDX-License-Identifier: Apache-2.0
"""Open JSON contracts for design intent, constrained sketches and feature edits."""
from typing import Annotated,Any,Literal
from pydantic import Field,StrictBool,StrictFloat,StrictInt,model_validator
from .spec import StrictModel

Id=Annotated[str,Field(pattern=r'^[a-z][a-z0-9_]{0,47}$')]
class Parameter(StrictModel):
    parameter:Id
Scalar=StrictFloat|Parameter

class Geometry(StrictModel):
    id:Id
    kind:Literal['line','circle','arc']
    start:tuple[StrictFloat,StrictFloat]=(0,0)
    end:tuple[StrictFloat,StrictFloat]=(1,0)
    center:tuple[StrictFloat,StrictFloat]=(0,0)
    radius:StrictFloat=Field(default=1,gt=0,le=10000)
    start_angle_deg:StrictFloat=0
    end_angle_deg:StrictFloat=90
    construction:StrictBool=False

class Constraint(StrictModel):
    id:Id
    kind:Literal['coincident','concentric','horizontal','vertical','parallel','perpendicular','equal','tangent','length','distance_x','distance_y','distance','diameter','radius','angle','lock','point_on_object']
    entities:list[Id]=Field(min_length=1,max_length=2)
    points:list[StrictInt]=Field(default_factory=list,max_length=2)
    value:Scalar|None=None
    @model_validator(mode='after')
    def valid(self):
        if any(p not in (1,2,3) for p in self.points):raise ValueError('Sketch point indices are 1=start, 2=end, 3=center where supported.')
        if self.kind in ('length','distance_x','distance_y','distance','diameter','radius','angle') and self.value is None:raise ValueError('A dimensional constraint requires value or {parameter:name}.')
        return self

class Sketch(StrictModel):
    id:Id
    plane:Literal['XY','XZ','YZ']='XY'
    origin:tuple[StrictFloat,StrictFloat,StrictFloat]=(0,0,0)
    geometry:list[Geometry]=Field(min_length=1,max_length=256)
    constraints:list[Constraint]=Field(default_factory=list,max_length=1024)
    require_fully_constrained:StrictBool=True
    @model_validator(mode='after')
    def valid(self):
        ids=[g.id for g in self.geometry]
        if len(ids)!=len(set(ids)):raise ValueError('Sketch geometry IDs must be unique.')
        if len({c.id for c in self.constraints})!=len(self.constraints):raise ValueError('Constraint IDs must be unique.')
        if any(e not in ids for c in self.constraints for e in c.entities):raise ValueError('Constraint refers to unknown sketch geometry.')
        return self

class Feature(StrictModel):
    id:Id
    kind:Literal['extrude','revolve','hole','fillet','chamfer','boolean','pattern','transform']
    part_id:Id|None=None
    sketch_id:Id|None=None
    base:Id|None=None
    tool:Id|None=None
    params:dict[str,Any]=Field(default_factory=dict,max_length=20)
    suppressed:StrictBool=False
    @model_validator(mode='after')
    def valid(self):
        keys={'extrude':{'height','direction'},'revolve':{'angle_deg','axis','origin'},'hole':{'diameter','depth','through','centers','axis'},'fillet':{'radius','edges'},'chamfer':{'distance','edges'},'boolean':{'operation'},'pattern':{'count','step','fuse'},'transform':{'translation','axis','angle_deg','origin'}}[self.kind]
        if set(self.params)-keys:raise ValueError('Unsupported '+self.kind+' parameters: '+str(sorted(set(self.params)-keys)))
        if self.kind in ('extrude','revolve') and not self.sketch_id:raise ValueError('This feature needs sketch_id.')
        if self.kind not in ('extrude','revolve') and not self.base:raise ValueError('This feature needs a base feature ID.')
        if self.kind=='boolean' and not self.tool:raise ValueError('Boolean feature needs tool feature ID.')
        return self

class Requirement(StrictModel):
    id:Id
    kind:Literal['bounds','placement','hole_pattern','part_count','clearance','interference','wall_thickness']
    part_id:Id|None=None
    other_part:Id|None=None
    expected:dict[str,Any]=Field(default_factory=dict,max_length=20)
    description:str=Field(default='',max_length=1000)

class Requirements(StrictModel):
    units:Literal['mm']='mm'
    source_text:str=Field(default='',max_length=8000)
    checks:list[Requirement]=Field(default_factory=list,max_length=64)
    assumptions:list[str]=Field(default_factory=list,max_length=30)
    components:list[Annotated[str,Field(max_length=1000)]]=Field(default_factory=list,max_length=128)
    materials:dict[Id,Annotated[str,Field(max_length=1000)]]=Field(default_factory=dict,max_length=128)
    interfaces:list[Annotated[str,Field(max_length=1000)]]=Field(default_factory=list,max_length=64)
    @model_validator(mode='after')
    def valid(self):
        if len({c.id for c in self.checks})!=len(self.checks):raise ValueError('Requirement IDs must be unique.')
        return self

class Accuracy(StrictModel):
    dimensional_tolerance_mm:StrictFloat=Field(default=.01,ge=1e-6,le=1)
    linear_deflection_mm:StrictFloat=Field(default=.025,ge=.0001,le=1)
    angular_deflection_rad:StrictFloat=Field(default=.15,ge=.01,le=.5)
    mesh_volume_relative_tolerance:StrictFloat=Field(default=.005,ge=.00001,le=.1)
    convergence_relative_tolerance:StrictFloat=Field(default=.01,ge=.0001,le=.1)

class Engineering(StrictModel):
    version:Literal[1]=1
    requirements:Requirements=Field(default_factory=Requirements)
    accuracy:Accuracy=Field(default_factory=Accuracy)
    sketches:list[Sketch]=Field(default_factory=list,max_length=64)
    features:list[Feature]=Field(default_factory=list,max_length=128)
    parameters:dict[str,StrictFloat]=Field(default_factory=dict,max_length=150)
    attached:StrictBool=False
    diagnostics:dict[str,Any]=Field(default_factory=dict)
    references:dict[str,Any]=Field(default_factory=dict,max_length=256)
    @model_validator(mode='after')
    def valid(self):
        from .program_policy import validate_parameters
        validate_parameters(self.parameters)
        if len({s.id for s in self.sketches})!=len(self.sketches):raise ValueError('Sketch IDs must be unique.')
        seen=set();sketches={s.id for s in self.sketches}
        for f in self.features:
            if f.id in seen:raise ValueError('Feature IDs must be unique.')
            if any(d not in seen for d in (f.base,f.tool) if d):raise ValueError('Features must be ordered by dependencies; missing/cyclic/forward reference.')
            if f.sketch_id and f.sketch_id not in sketches:raise ValueError('Feature refers to an unknown sketch.')
            seen.add(f.id)
        return self
