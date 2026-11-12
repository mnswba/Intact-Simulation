"""Original AI-operable design workflows; no upstream UI or code is embedded."""
from __future__ import annotations
import ast, math, operator, shutil, tempfile
from copy import deepcopy
from pathlib import Path
from .projects import ProjectService, atomic_json
from .program_policy import validate_parameters
from .view_settings import ViewSettings


def parameter_values(current, changes):
    """Bounded scalar arithmetic in CAD mm. Never evaluate Python source."""
    if not isinstance(changes,dict) or len(changes)>150:raise ValueError('Provide at most 150 parameter values.')
    if set(changes)-set(current):raise ValueError('Unknown parameter: '+', '.join(sorted(set(changes)-set(current))))
    expressions={**current,**changes}; resolved={}; visiting=set(); count=0
    ops={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv}
    def resolve(name):
        if name in resolved:return resolved[name]
        if name in visiting:raise ValueError('Cyclic parameter expression: '+name)
        if name not in expressions:raise ValueError('Unknown parameter reference: '+name)
        visiting.add(name);value=expressions[name]
        if isinstance(value,str):
            if not 1<=len(value)<=300:raise ValueError('Parameter expressions must contain 1–300 characters.')
            try:value=walk(ast.parse(value,mode='eval').body,0)
            except (SyntaxError,ZeroDivisionError,OverflowError,RecursionError) as exc:raise ValueError('Invalid parameter expression: '+name) from exc
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or abs(value)>1e9:raise ValueError('Parameter values must be finite numbers within ±1e9.')
        visiting.remove(name);resolved[name]=float(value);return resolved[name]
    def walk(node,depth):
        nonlocal count
        count+=1
        if depth>24 or count>3000:raise ValueError('Parameter expression is too complex.')
        if isinstance(node,ast.Constant) and type(node.value) in (int,float):return node.value
        if isinstance(node,ast.Name):return resolve(node.id)
        if isinstance(node,ast.BinOp) and type(node.op) in ops:return ops[type(node.op)](walk(node.left,depth+1),walk(node.right,depth+1))
        if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.UAdd,ast.USub)):return (-1 if isinstance(node.op,ast.USub) else 1)*walk(node.operand,depth+1)
        raise ValueError('Use numbers, parameter names, parentheses and + - * / only.')
    for name in expressions:resolve(name)
    return validate_parameters(resolved)


def _label(name):
    if not isinstance(name,str) or not 1<=len(name.strip())<=80:raise ValueError('Use a name containing 1–80 characters.')
    return name.strip()


def view_command(projects,key,action,settings=None,name=None,expected_view_revision=None):
    if action=='update':
        projects.save_view(key,settings or {},expected_view_revision)
    elif action in ('save','restore','delete'):
        name=_label(name)
        with projects.lock(key):
            record=projects.load(key);revision=record.get('view_revision',0)
            if expected_view_revision is not None and expected_view_revision!=revision:raise ValueError('The view changed. Read the current view and retry.')
            views=record.setdefault('named_views',{})
            if action=='save':
                if name not in views and len(views)>=30:raise ValueError('At most 30 saved views per model.')
                views[name]={'settings':deepcopy(record['view']),'artifact_id':record['spec']['program']['artifact_id']}
            elif name not in views:raise ValueError('Saved view not found.')
            elif action=='delete':del views[name]
            else:
                saved=views[name]
                # Never silently apply part/face-bound annotations to rebuilt geometry.
                if saved['artifact_id']!=record['spec']['program']['artifact_id']:raise ValueError('Saved view belongs to earlier geometry. Save a new view on the current model.')
                record['view']=ViewSettings.model_validate(saved['settings']).model_dump(mode='json')
                record['view_revision']=revision+1
            atomic_json(projects.path(key),record)
    elif action not in ('get','list'):raise ValueError('Unknown view action.')
    record=projects.load(key)
    return {'model_id':key,'cad_revision':record['spec']['revision'],'view_revision':record.get('view_revision',0),'settings':record['view'],'named_views':sorted(record.get('named_views',{}))}


def parameter_command(projects,key,action,parameters=None,name=None,expected_revision=None,cancel_event=None):
    record=projects.load(key);revision=record['spec']['revision']
    if expected_revision is not None and revision!=expected_revision:raise ValueError('The model revision changed. Reload before editing.')
    current=record['spec']['program']['parameters']
    if action=='list':return {'model_id':key,'revision':revision,'configurations':record.get('parameter_configurations',{})}
    if action in ('save','delete','apply'):name=_label(name)
    if action in ('save','preview'):values=parameter_values(current,parameters or {})
    if action in ('save','delete'):
        with projects.lock(key):
            latest=projects.load(key)
            if latest['spec']['revision']!=revision:raise ValueError('The model revision changed. Reload before editing.')
            configs=latest.setdefault('parameter_configurations',{})
            if action=='save':
                if name not in configs and len(configs)>=30:raise ValueError('At most 30 parameter configurations per model.')
                configs[name]={'parameters':values,'source_artifact':record['spec']['program']['artifact_id']}
            elif name not in configs:raise ValueError('Configuration not found.')
            else:del configs[name]
            atomic_json(projects.path(key),latest)
        return {'model_id':key,'revision':revision,'configurations':configs}
    if action=='apply':
        config=record.get('parameter_configurations',{}).get(name)
        if config is None:raise ValueError('Configuration not found.')
        return projects.parameters(key,config['parameters'],cancel_event,revision)
    if action!='preview':raise ValueError('Unknown parameter action.')
    # Scratch root includes only this validated model and its imported input asset.
    # Generated source still executes exclusively through ProgramService's sandbox.
    with tempfile.TemporaryDirectory(prefix='intact-parameter-preview-') as folder:
        scratch=ProjectService(Path(folder));atomic_json(scratch.path(key),record)
        asset=record['spec']['program'].get('asset_id')
        if asset:
            filename=projects.programs.asset_name(asset);target=scratch.programs.root/'assets'/asset/filename
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(projects.programs.root/'assets'/asset/filename,target)
        candidate=scratch.parameters(key,values,cancel_event,revision)
        parts=candidate['spec']['parts'];metrics=[{'id':p['id'],'dimensions_mm':{k:p['params'][k] for k in ('length','width','height')},'position':p['position'],'volume_mm3':p['measurements']['volume_mm3']} for p in parts]
        return {'model_id':key,'source_revision':revision,'committed':False,'parameters':values,'engine':candidate['geometry']['engine'],'parts':metrics,'volume_mm3':sum(p['measurements']['volume_mm3'] for p in parts),'note':'Sandbox rebuild only. Original geometry and revision were preserved; no preview files are retained. Use update_parameters or apply a configuration to commit.'}
