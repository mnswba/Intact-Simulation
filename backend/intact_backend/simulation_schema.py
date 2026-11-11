"""Simulation inputs in explicit SI/CAD units; no generated solver code."""
from typing import Literal
from pydantic import Field,StrictFloat,StrictInt,StrictBool,model_validator
from .spec import StrictModel
from .engineering_schema import Id
Vec=tuple[StrictFloat,StrictFloat,StrictFloat]
class Boundary(StrictModel):
 id:Id
 kind:Literal['temperature','heat_flux','convection','insulated','fixed','displacement','force','pressure']
 selector:Literal['extreme','faces']='extreme'
 axis:StrictInt=Field(default=0,ge=0,le=2)
 side:Literal['low','high']='low'
 references:list[str]=Field(default_factory=list,max_length=64)
 value:StrictFloat=Field(default=0,ge=-1e12,le=1e12)
 vector:Vec=(0,0,0)
 components:list[StrictInt]=Field(default_factory=lambda:[0,1,2],min_length=1,max_length=3)
 h_w_m2k:StrictFloat=Field(default=10,gt=0,le=1e8)
 ambient_k:StrictFloat=Field(default=293.15,ge=0,le=5000)
 @model_validator(mode='after')
 def valid(self):
  if self.selector=='faces' and not self.references:raise ValueError('Choose native boundary faces.')
  if any(i not in (0,1,2) for i in self.components) or len(set(self.components))!=len(self.components):raise ValueError('Choose distinct X/Y/Z constraint components.')
  if self.kind=='temperature' and not 0<=self.value<=5000:raise ValueError('Temperature must be 0–5000 K.')
  return self
class MotionBody(StrictModel):
 part_id:Id
 mass_kg:StrictFloat=Field(default=.1,ge=1e-6,le=1e8)
 fixed:StrictBool=False
 linear_velocity_mm_s:Vec=(0,0,0)
 angular_velocity_deg_s:Vec=(0,0,0)
 friction:StrictFloat=Field(default=.8,ge=0,le=3)
 restitution:StrictFloat=Field(default=0,ge=0,le=1)
 center_of_mass_mm:Vec|None=None
 inertia_kg_m2:tuple[StrictFloat,StrictFloat,StrictFloat,StrictFloat,StrictFloat,StrictFloat]|None=None
class MotionJoint(StrictModel):
 id:Id
 parent:Id
 child:Id
 kind:Literal['fixed','revolute','continuous','slider']='revolute'
 axis:Vec=(0,0,1)
 origin_mm:Vec=(0,0,0)
 minimum:StrictFloat=-180
 maximum:StrictFloat=180
 initial:StrictFloat=0
 mode:Literal['off','position','velocity','sine','torque']='position'
 target:StrictFloat=0
 amplitude:StrictFloat=30
 frequency_hz:StrictFloat=Field(default=1,ge=0,le=20)
 phase_deg:StrictFloat=0
 maximum_effort:StrictFloat=Field(default=1,gt=0,le=1e8)
 @model_validator(mode='after')
 def valid(self):
  if self.parent==self.child or sum(v*v for v in self.axis)<1e-12:raise ValueError('A joint needs distinct parts and a nonzero axis.')
  if self.minimum>self.maximum or (self.kind!='continuous' and not self.minimum<=self.initial<=self.maximum):raise ValueError('Invalid joint limits or initial value.')
  if self.kind=='fixed' and self.initial!=0:raise ValueError('A fixed joint starts at zero.')
  if self.kind in ('revolute','slider') and self.mode in ('position','sine') and (self.target-abs(self.amplitude if self.mode=='sine' else 0)<self.minimum or self.target+abs(self.amplitude if self.mode=='sine' else 0)>self.maximum):raise ValueError('Position/gait targets exceed joint limits.')
  return self
class Motion(StrictModel):
 mode:Literal['dynamics','kinematic']='dynamics'
 name:str=Field(default='Virtual analysis',min_length=1,max_length=100)
 bodies:list[MotionBody]=Field(min_length=1,max_length=128)
 joints:list[MotionJoint]=Field(default_factory=list,max_length=64)
 duration_s:StrictFloat=Field(default=2,ge=.1,le=10)
 sample_hz:StrictInt=Field(default=30,ge=1,le=60)
 gravity_m_s2:Vec=(0,0,-9.81)
 ground:StrictBool=True
 ground_z_mm:StrictFloat=Field(default=0,ge=-1e7,le=1e7)
 self_collision:StrictBool=False
 collision_model:Literal['convex_hull','box']='convex_hull'
 collision_margin_mm:StrictFloat=Field(default=.01,ge=.001,le=10)
 source_revision:StrictInt|None=None
 source_artifact:str|None=None
 @model_validator(mode='after')
 def valid(self):
  ids=[b.part_id for b in self.bodies]
  if len(set(ids))!=len(ids):raise ValueError('Duplicate motion body.')
  children={};joint_ids=set()
  for j in self.joints:
   if j.parent not in ids or j.child not in ids or j.child in children or j.id in joint_ids:raise ValueError('Joints need existing bodies, unique IDs and one parent per child.')
   children[j.child]=j.parent;joint_ids.add(j.id)
  for child in children:
   path=set();node=child
   while node in children:
    if node in path:raise ValueError('Joint graph contains a cycle.')
    path.add(node);node=children[node]
  if any(b.fixed and b.part_id in children for b in self.bodies):raise ValueError('Fixed-base applies to root bodies. Use a fixed joint for a child.')
  if len(self.bodies)*(self.duration_s*self.sample_hz+1)>30000:raise ValueError('Reduce duration, recording rate or body count: at most 30,000 recorded body poses.')
  if self.duration_s*self.sample_hz>600:raise ValueError('Motion recording is limited to 600 frames plus the initial pose.')
  return self
