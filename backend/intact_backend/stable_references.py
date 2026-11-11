# SPDX-License-Identifier: Apache-2.0
"""Semantic geometry handles. Missing/ambiguous matches never silently pick a face."""
import json,math
from hashlib import sha256
from copy import deepcopy
from .engineering_schema import Engineering

def norm(v):return math.sqrt(sum(x*x for x in v))
def near(a,b,tolerance):return norm([x-y for x,y in zip(a,b)])<=tolerance
def parallel(a,b):
    return norm(a)>0 and norm(b)>0 and abs(abs(sum(x*y for x,y in zip(a,b))/(norm(a)*norm(b)))-1)<1e-6
def scalar(v,p):return p[v['parameter']] if isinstance(v,dict) and set(v)=={'parameter'} else v

def topology(projects,r):
    data=json.loads(projects.record_artifact(r,'topology.json').read_text());items={}
    for p in r['spec']['parts']:items[p['id']]={'ref':p['id'],'kind':'part','part_id':p['id'],'name':p['name']}
    for part in data['parts']:
        for kind in ('faces','edges','vertices'):
            for item in part[kind]:items[item['ref']]=item
    return items

def bind(projects,key,reference,label,revision,artifact_id):
    from .edit_requests import EditRequests
    from .engineering_schema import Id
    from pydantic import TypeAdapter
    TypeAdapter(Id).validate_python(label)
    EditRequests(projects).resolve(key,[reference],revision,artifact_id)
    r=projects.load(key)
    if r['spec']['revision']!=revision or r['spec']['program']['artifact_id']!=artifact_id:raise ValueError('Geometry changed while binding the reference. Reload and retry.')
    items=topology(projects,r);signature=deepcopy(items[reference]);e=Engineering.model_validate(r.get('engineering',{}));anchor=None
    if signature.get('geometry')=='cylinder' and e.attached:
        for f in e.features:
            if f.kind!='hole' or f.suppressed or f.part_id!=signature['part_id']:continue
            radius=scalar(f.params.get('diameter',6),e.parameters)/2
            if abs(signature.get('radius_mm',-1)-radius)>1e-5:continue
            axis=f.params.get('axis',[0,0,1]);n=norm(axis);axis=[x/n for x in axis]
            for i,c in enumerate(f.params.get('centers',[])):
                offset=[x-y for x,y in zip(c,signature['axis_origin'])];along=sum(x*y for x,y in zip(offset,axis));distance=norm([x-along*y for x,y in zip(offset,axis)])
                if distance<1e-5:anchor={'feature_id':f.id,'center_index':i}
    e.references[label]={'signature':signature,'origin_revision':revision,'origin_artifact':artifact_id,'anchor':anchor,'program_hash':sha256(r['spec']['program']['source'].encode()).hexdigest()}
    r['engineering']=e.model_dump(mode='json');r=projects.commit(r,revision)
    return {'stable_reference':'stable:'+label,'model_id':key,'revision':r['spec']['revision'],'anchor':anchor,'note':'Future resolution requires a unique geometric/feature match. Missing or ambiguous matches are rejected.'}

def resolve(projects,key,references):
    r=projects.ensure_ready(key);e=Engineering.model_validate(r.get('engineering',{}));items=topology(projects,r);resolved=[]
    for ref in references:
        label=ref.removeprefix('stable:');saved=e.references.get(label)
        if not saved:raise ValueError('Unknown stable reference: '+ref)
        sig=saved['signature'];candidates=[v for v in items.values() if v['kind']==sig['kind'] and v['part_id']==sig['part_id']]
        if saved.get('program_hash')!=sha256(r['spec']['program']['source'].encode()).hexdigest():raise ValueError(ref+': missing feature lineage after an unrelated Python source edit. Rebind the intended geometry.')
        if saved['origin_artifact']==r['spec']['program']['artifact_id'] and sig['ref'] in items:
            resolved.append({**items[sig['ref']],'stable_reference':ref,'matched_by':'same immutable geometry artifact'});continue
        if sig['kind']=='part':pass
        else:
            candidates=[v for v in candidates if v.get('geometry')==sig.get('geometry')]
            anchor=saved.get('anchor');feature=next((f for f in e.features if anchor and f.id==anchor['feature_id'] and not f.suppressed),None)
            if anchor and (not feature or not e.attached):raise ValueError(ref+': missing/deleted feature lineage. Select the intended current geometry and bind a new handle.')
            if feature and e.attached and feature.kind=='hole':
                center=feature.params.get('centers',[])
                if anchor['center_index']>=len(center):candidates=[]
                else:
                    c=center[anchor['center_index']];radius=scalar(feature.params.get('diameter',6),e.parameters)/2;axis=feature.params.get('axis',[0,0,1]);axis=[x/norm(axis) for x in axis];matches=[]
                    for v in candidates:
                        if abs(v.get('radius_mm',-1)-radius)>1e-5 or not parallel(v.get('axis',[0,0,0]),axis):continue
                        offset=[x-y for x,y in zip(c,v['axis_origin'])];along=sum(x*y for x,y in zip(offset,axis))
                        if norm([x-along*y for x,y in zip(offset,axis)])<1e-5:matches.append(v)
                    candidates=matches
            elif sig.get('geometry')=='plane' and sig.get('normal'):
                candidates=[v for v in candidates if v.get('normal') and near(v['normal'],sig['normal'],1e-5)]
            else:
                candidates=[v for v in candidates if near(v.get('point',v.get('center',[1e20]*3)),sig.get('point',sig.get('center',[0]*3)),e.accuracy.dimensional_tolerance_mm) and ('radius_mm' not in sig or abs(v.get('radius_mm',-1)-sig['radius_mm'])<=e.accuracy.dimensional_tolerance_mm)]
        if len(candidates)!=1:raise ValueError(ref+': '+('missing/deleted' if not candidates else 'ambiguous ('+str(len(candidates))+' matches)')+'. Select the intended current geometry and bind a new handle.')
        resolved.append({**candidates[0],'stable_reference':ref,'matched_by':'feature anchor' if saved.get('anchor') and e.attached else 'unique geometric signature'})
    return {'model_id':key,'revision':r['spec']['revision'],'artifact_id':r['spec']['program']['artifact_id'],'references':resolved,'units':'mm','coordinate_system':'cad_z_up'}
