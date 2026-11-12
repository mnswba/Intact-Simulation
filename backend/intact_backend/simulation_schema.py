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
