# SPDX-License-Identifier: Apache-2.0
"""Small provenance-bearing envelope catalog; imported supplier STEP stays separate."""
import json
from .projects import atomic_json
BOLTS={'m3':(3,5.5,3),'m4':(4,7,4),'m5':(5,8.5,5),'m6':(6,10,6),'m8':(8,13,8)}
SOURCE='https://github.com/shaise/FreeCAD_FastenersWB/blob/master/FsData/iso4762def.csv'
def catalog():
 return {'components':[{'id':'iso4762_'+key,'type':'socket_head_screw','diameter_mm':d,'head_diameter_mm':hd,'head_height_mm':hh,'source_url':SOURCE,'representation':'Nominal envelope; unthreaded shaft and simplified head, not a production fastener drawing.'} for key,(d,hd,hh) in BOLTS.items()]+[{'id':'bearing_608','type':'bearing','bore_mm':8,'outside_mm':22,'width_mm':7,'source_url':'https://docs.rs-online.com/9931/A700000008717780.pdf','representation':'SKF 608 envelope ring only; rolling elements, seals and raceway internals are not reconstructed.'}],'scope':'A small explicit catalog, not a complete supplier database. Insert other verified supplier STEP files using import_cad and retain their source/license separately.'}
def insert(projects,component_id,length_mm=12,position=(0,0,0),model_id=None,expected_revision=None,cancel=None):
 if not 1<=length_mm<=200 or len(position)!=3:raise ValueError('Invalid component length or placement.')
 import math
 if any(isinstance(v,bool) or not isinstance(v,(float,int)) or not math.isfinite(v) for v in position):raise ValueError('Position must be finite XYZ mm.')
 entry=next((p for p in catalog()['components'] if p['id']==component_id),None)
 if entry is None:raise ValueError('Unknown catalog component.')
 asset=None;prefix='    parts={}\n'
 if model_id:
  old=projects.ensure_ready(model_id)
  if old['geometry']['engine']=='implicit_mesh':raise ValueError('Native component insertion requires a native assembly.')
  if component_id in [p['id'] for p in old['spec']['parts']]:raise ValueError('A component with this ID already exists.')
  asset=projects.store_step(projects.artifact(model_id,'model.step').read_bytes(),max_bytes=32*1024**2);prefix='    parts=dict(imported_parts)\n';expected_revision=expected_revision if expected_revision is not None else old['spec']['revision']
 if component_id=='bearing_608':body='bd.Cylinder(11,7)-bd.Cylinder(4,9)'
 else:
  d,hd,hh=BOLTS[component_id.removeprefix('iso4762_')];body=f'bd.Pos(0,0,-params["length"]/2)*bd.Cylinder({d/2},params["length"])+bd.Pos(0,0,{hh/2})*bd.Cylinder({hd/2},{hh})'
 source='import build123d as bd\ndef build(params):\n'+prefix+'    parts['+repr(component_id)+']=bd.Pos('+','.join('params["'+k+'"]' for k in ('x','y','z'))+')*('+body+')\n    return parts'
 result=projects.build(source,{'length':length_mm,**dict(zip(('x','y','z'),position))},model_id=model_id,expected_revision=expected_revision,asset_id=asset,name=None if model_id else component_id,cancel_event=cancel)
 atomic_json(projects.root/'component-provenance'/(result['model_id']+'.json'),entry)
 return {'model':result,'provenance':entry,'assembly_edit_scope':'Existing parts are preserved as a native STEP snapshot. Their previous parametric source remains in revision history; insertion does not merge that source into a recovered feature tree.'}
