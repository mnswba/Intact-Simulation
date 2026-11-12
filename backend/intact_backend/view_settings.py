"""Persisted display preferences, independent of CAD revisions."""
from typing import Literal
from pydantic import Field, field_validator
from .spec import StrictModel

class ViewSettings(StrictModel):
    model_config={**StrictModel.model_config,'allow_inf_nan':False}
    cut:Literal['none','x','y','z']='none'
    slice:float=Field(default=50,ge=0,le=100)
    flip:bool=False
    cap:bool=True
    explode:float=Field(default=0,ge=0,le=100)
    wire:bool=False
    hidden:list[str]=Field(default_factory=list,max_length=128)
    camera:list[float]|None=Field(default=None,min_length=6,max_length=6)
    camera_span:float|None=Field(default=None,gt=0,lt=1e9)
    camera_zoom:float=Field(default=1,ge=.02,le=100)
    mode:Literal['solid','render','xray','hidden-line','wireframe','grid']='solid'
    theme:Literal['light','medium-light','medium','dark']='light'
    projection:Literal['perspective','orthographic']='perspective'
    surface:Literal['shaded','flat','hidden','off']='shaded'
    color_mode:Literal['original','single','part']='original'
    single_color:str='#8aa9cb'
    palette:list[str]=Field(default_factory=lambda:['#6287bc','#db9862','#68aa90','#b58cc6','#c5b85c'],min_length=1,max_length=50)
    opacity:float=Field(default=100,ge=0,le=100)
    edges:bool=True
    edge_visibility:Literal['visible','all']='visible'
    edge_color:str='#25415b'
    grid:bool=True
    grid_color:str='#344b61'
    axes:bool=False
    axes_color:str='#db9859'
    lighting:bool=True
    quality:Literal['preview','final']='preview'
    exposure:float=Field(default=0,ge=-5,le=5)
    light_rotation:float=Field(default=35,ge=0,le=360)
    softbox:float=Field(default=50,ge=1,le=200)
    fill:float=Field(default=35,ge=0,le=100)
    background:bool=True
    background_color:str='#f1f2f4'
    floor:bool=False
    floor_color:str='#293b4c'
    floor_position:Literal['origin','lowest']='lowest'
    preview:bool=False
    orbit_speed:float=Field(default=1,ge=.1,le=5)
    measurements:list[dict]=Field(default_factory=list,max_length=50)
    annotation_artifact:str|None=Field(default=None,pattern=r'^[a-f0-9]{64}$')
    component_names:bool=False
    annotations:list[dict]=Field(default_factory=list,max_length=300)
    @field_validator('theme',mode='before')
    @classmethod
    def legacy_theme(cls,v):return 'light' if v=='system' else v
    @field_validator('single_color','edge_color','grid_color','axes_color','background_color','floor_color')
    @classmethod
    def color(cls,v):
        import re
        if not re.fullmatch('#[0-9a-fA-F]{6}',v):raise ValueError('Use a six digit hex color.')
        return v
    @field_validator('palette')
    @classmethod
    def colors(cls,v):return [cls.color(c) for c in v]
    @field_validator('camera')
    @classmethod
    def camera_bounds(cls,v):
        import math
        if v and any(not math.isfinite(n) or abs(n)>1e8 for n in v):raise ValueError('Camera exceeds display limits.')
        if v and sum((v[i]-v[i+3])**2 for i in range(3))<1e-12:raise ValueError('Camera eye and target must differ.')
        return v
    @field_validator('measurements')
    @classmethod
    def dimensions(cls,items):
        for item in items:
            if not isinstance(item,dict) or not isinstance(item.get('id'),str) or not 1<=len(item['id'])<=100:raise ValueError('Each dimension needs a nonempty identifier.')
            if set(item)-{'id','a','b','artifact_id','snap_a','snap_b'}:raise ValueError('Unknown measurement field.')
            for key in ('a','b'):
                point=item.get(key)
                if not isinstance(point,list) or len(point)!=3 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not -1e7<v<1e7 for v in point):raise ValueError('Invalid measurement coordinates.')
            if any(not isinstance(item.get(k,''),str) or len(item.get(k,''))>100 for k in ('id','artifact_id','snap_a','snap_b')):raise ValueError('Invalid measurement reference.')
        return items
    @field_validator('annotations')
    @classmethod
    def drawings(cls,items):
        for item in items:
            if not isinstance(item,dict) or not isinstance(item.get('id'),str) or not 1<=len(item['id'])<=100:raise ValueError('Each annotation needs a nonempty identifier.')
            if set(item)-{'id','tool','points','color','width','text','anchor'}:raise ValueError('Unknown annotation field.')
            if item.get('tool') not in ('pen','line','arrow','rectangle','ellipse','text','fill'):raise ValueError('Invalid annotation tool.')
            cls.color(item.get('color',''))
            if not isinstance(item.get('width'),(int,float)) or not .1<=item['width']<=30:raise ValueError('Invalid stroke width.')
            pts=item.get('points')
            if not isinstance(pts,list) or not 1<=len(pts)<=2000 or any(not isinstance(p,list) or len(p)!=2 or any(not isinstance(n,(int,float)) or not 0<=n<=1 for n in p) for p in pts):raise ValueError('Invalid drawing coordinates.')
            if 'anchor' in item:
                anchor=item['anchor']
                if item['tool']!='text' or not isinstance(anchor,dict) or set(anchor)!={'part_id','point','artifact_id'}:raise ValueError('Only text annotations accept a model anchor.')
                import re,math
                if not isinstance(anchor['part_id'],str) or not re.fullmatch('[a-zA-Z0-9_-]{1,64}',anchor['part_id']):raise ValueError('Invalid anchored part.')
                if not isinstance(anchor['artifact_id'],str) or not re.fullmatch('[a-f0-9]{64}',anchor['artifact_id']):raise ValueError('Invalid annotation artifact.')
                point=anchor['point']
                if not isinstance(point,list) or len(point)!=3 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or abs(v)>1e7 for v in point):raise ValueError('Invalid model anchor coordinates.')
            if not isinstance(item.get('text',''),str) or len(item.get('text',''))>500:raise ValueError('Annotation text is too long.')
            if not isinstance(item.get('id',''),str) or len(item.get('id',''))>100:raise ValueError('Invalid annotation id.')
        return items
