# SPDX-License-Identifier: Apache-2.0
"""Typed contracts for bounded priority 2/3 engineering operations."""
from typing import Literal,Annotated,Any
from pydantic import Field,StrictBool,StrictFloat,StrictInt,model_validator
from .spec import StrictModel
from .engineering_schema import Id
Vec=tuple[StrictFloat,StrictFloat,StrictFloat]
class LatticeMM(StrictModel):
    family:Literal['gyroid','schwarz_p','diamond','neovius','lidinoid','split_p']='gyroid'
    size:Vec=(16,16,16)
    cell_size:StrictFloat=Field(default=8,ge=.1,le=1000)
    thickness_mm:StrictFloat=Field(default=1.2,ge=.05,le=100)
    samples_per_cell:StrictInt=Field(default=24,ge=12,le=64)
    gradient:StrictFloat=Field(default=0,ge=-.8,le=.8)
class AdaptiveLattice(LatticeMM):
    maximum_samples_per_cell:StrictInt=Field(default=48,ge=12,le=64)
    relative_tolerance:StrictFloat=Field(default=.03,ge=.001,le=.3)
class HybridSpec(LatticeMM):
    part_id:Id
    operation:Literal['union','difference','intersection']='union'
    translation:Vec=(0,0,0)
    tessellation_mm:StrictFloat=Field(default=.05,ge=.005,le=.5)
class Joint(StrictModel):
    id:Id
    kind:Literal['fixed','revolute','slider']
    parent:Id
    child:Id
    axis:Vec=(0,0,1)
    origin:Vec=(0,0,0)
    minimum:StrictFloat=-180
    maximum:StrictFloat=180
    value:StrictFloat=0
    @model_validator(mode='after')
    def valid(self):
        if self.child==self.parent or not self.minimum<=self.value<=self.maximum:raise ValueError('Invalid joint parts or motion limits.')
        if self.kind=='fixed' and self.value!=0:raise ValueError('Fixed joints require value=0.')
        if sum(v*v for v in self.axis)<1e-12:raise ValueError('Joint axis cannot be zero.')
        return self
class Assembly(StrictModel):
    joints:list[Joint]=Field(min_length=1,max_length=64)
    collision_tolerance_mm3:StrictFloat=Field(default=.001,ge=0,le=10)
class Freeform(StrictModel):
    sections:list[list[Vec]]=Field(min_length=2,max_length=12)
    ruled:StrictBool=False
class Simulation(StrictModel):
    kind:Literal['thermal','structural','stokes']
    part_id:Id
    axis:StrictInt=Field(default=0,ge=0,le=2)
    mesh_size_mm:StrictFloat=Field(default=4,ge=.1,le=1000)
    conductivity_w_mk:StrictFloat=Field(default=200,gt=0,le=10000)
    heat_source_w_m3:StrictFloat=Field(default=0,ge=0,le=1e12)
    low_value:StrictFloat=Field(default=300,ge=0,le=5000)
    high_value:StrictFloat=Field(default=350,ge=0,le=5000)
    young_modulus_pa:StrictFloat=Field(default=70e9,gt=0,le=1e13)
    poisson_ratio:StrictFloat=Field(default=.3,ge=0,lt=.49)
    force_n:Vec=(1,0,0)
    viscosity_pa_s:StrictFloat=Field(default=1,gt=0,le=1e6)
    density_kg_m3:StrictFloat=Field(default=1000,gt=0,le=25000)
    pressure_drop_pa:StrictFloat=Field(default=1,gt=0,le=1e8)
    convergence:StrictBool=True
    convergence_tolerance:StrictFloat=Field(default=.1,ge=.001,le=.5)
class Manufacturing(StrictModel):
    part_id:Id
    process:Literal['cnc','molding','additive']
    direction:Vec=(0,0,1)
    minimum_wall_mm:StrictFloat=Field(default=1,gt=0,le=100)
    minimum_draft_deg:StrictFloat=Field(default=1,ge=0,le=20)
class SheetMetal(StrictModel):
    width_mm:StrictFloat=Field(default=30,gt=0,le=1000)
    leg_a_mm:StrictFloat=Field(default=30,gt=0,le=1000)
    leg_b_mm:StrictFloat=Field(default=20,gt=0,le=1000)
    thickness_mm:StrictFloat=Field(default=2,gt=0,le=20)
    inside_radius_mm:StrictFloat=Field(default=3,gt=0,le=100)
    angle_deg:StrictFloat=Field(default=90,gt=0,lt=170)
    k_factor:StrictFloat=Field(default=.4,gt=0,lt=1)
class Reconstruction(StrictModel):
    mode:Literal['silhouette','scan','orthographic_hull']
    path:str=Field(default='',max_length=1000)
    width_mm:StrictFloat=Field(default=40,gt=0,le=1000)
    depth_mm:StrictFloat=Field(default=5,gt=0,le=1000)
    threshold:StrictFloat=Field(default=.5,ge=.01,le=.99)
    simplify_px:StrictFloat=Field(default=1,ge=0,le=10)
    invert:StrictBool=False
    source_note:str=Field(default='',max_length=2000)
    views:dict[Literal['front','top','right'],str]=Field(default_factory=dict,max_length=3)
    size_mm:Vec=(40,30,20)
    voxel_resolution:StrictInt=Field(default=48,ge=16,le=128)
class Optimization(StrictModel):
    parameter:Id
    values:list[StrictFloat]=Field(min_length=2,max_length=12)
    objective:Literal['minimum_volume','minimum_thermal_peak','minimum_displacement','minimum_pressure_resistance']='minimum_volume'
    simulation:Simulation|None=None
    max_displacement_mm:StrictFloat|None=Field(default=None,gt=0)
    max_temperature_k:StrictFloat|None=Field(default=None,gt=0)
class Comparison(StrictModel):
    model_ids:list[str]=Field(min_length=2,max_length=12)
    density_kg_m3:StrictFloat=Field(default=2700,gt=0,le=25000)
