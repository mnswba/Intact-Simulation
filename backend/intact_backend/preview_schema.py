"""Declarative kinematic animation; never a physics result or CAD edit."""
from typing import Literal
from pydantic import Field,StrictFloat,StrictInt,model_validator
from .spec import StrictModel
from .engineering_schema import Id
Vec=tuple[StrictFloat,StrictFloat,StrictFloat]
class PreviewWheel(StrictModel):
 id:Id
 pivot_m:Vec
 part_ids:list[Id]=Field(min_length=1,max_length=32)
class PreviewJoint(StrictModel):
 part_id:Id
 parent_id:Id|None=None
 pivot_m:Vec
 axis:Vec=(0,1,0)
 amplitude_deg:StrictFloat=Field(default=25,ge=-180,le=180)
 frequency_hz:StrictFloat=Field(default=1,ge=0,le=10)
 phase_deg:StrictFloat=0
class PreviewStudy(StrictModel):
 name:str=Field(default='Kinematic preview',min_length=1,max_length=100)
 user_request:str=Field(default='',max_length=4000)
 kind:Literal['vehicle','walk','rotate','translate','joints']='vehicle'
 duration_s:StrictFloat=Field(default=8,ge=.2,le=60)
 speed_m_s:StrictFloat=Field(default=.3,ge=0,le=10)
 radius_m:StrictFloat=Field(default=.165,gt=.0001,le=100)
 direction:Vec=(1,0,0)
 moving_part_ids:list[Id]=Field(default_factory=list,max_length=128)
 wheels:list[PreviewWheel]=Field(default_factory=list,max_length=16)
 joints:list[PreviewJoint]=Field(default_factory=list,max_length=64)
 source_revision:StrictInt
 source_artifact:str
 @model_validator(mode='after')
 def valid(self):
  if sum(x*x for x in self.direction)<1e-12:raise ValueError('Motion direction cannot be zero.')
  if self.kind=='vehicle' and not self.wheels:raise ValueError('Vehicle previews need identified wheel assemblies, pivots and radius.')
  if self.kind in ('walk','joints') and not self.joints:raise ValueError('Articulated previews need separate limb/link parts and explicit pivots. A fused solid cannot articulate.')
  if self.kind=='vehicle' and self.direction!=(1,0,0):raise ValueError('Vehicle driving uses CAD +X forward.')
  if self.kind=='vehicle' and self.duration_s!=8:raise ValueError('The supplied driving timeline lasts 8 seconds.')
  ids=[];parents={}
  for wheel in self.wheels:ids.extend(wheel.part_ids)
  for joint in self.joints:
   ids.append(joint.part_id)
   if sum(v*v for v in joint.axis)<1e-12:raise ValueError('Joint axis cannot be zero.')
   if joint.parent_id:parents[joint.part_id]=joint.parent_id
  if len(ids)!=len(set(ids)):raise ValueError('A moving part belongs to one wheel or joint only.')
  if len(self.moving_part_ids)!=len(set(self.moving_part_ids)):raise ValueError('Duplicate moving part ID.')
  for child in parents:
   seen=set();node=child
   while node in parents:
    if node in seen:raise ValueError('Preview joint hierarchy contains a cycle.')
    seen.add(node);node=parents[node]
  return self
