"""Shared local project operations used by MCP and the persistent viewer."""
from __future__ import annotations
from contextlib import contextmanager
from copy import deepcopy
import base64
from hashlib import sha256
import fcntl, json, re, shutil, threading, uuid
from pathlib import Path, PureWindowsPath
from .generated import generated_spec
from .program import ProgramService
from .program_policy import validate_parameters
from .spec import DesignSpec, from_legacy

MODEL_ID = re.compile(r'^[a-f0-9]{32}$')
EXPORTS={'step':'model.step','stl':'model.stl','glb':'model.glb','3mf':'model.3mf','python':'program.py','project':'project.json'}

def local_path(value):
    """Accept the desktop client's Windows paths on the WSL CAD host."""
    text=str(value)
    if text.startswith('\\\\?\\'):text=text[4:]
    if re.match(r'^[A-Za-z]:[\\/]',text):
        windows=PureWindowsPath(text)
        return Path('/mnt')/windows.drive[0].lower()/Path(*windows.parts[1:])
    return Path(text).expanduser()

def atomic_json(path:Path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    temporary.write_text(json.dumps(value,allow_nan=False),encoding='utf-8');temporary.replace(path)

class ProjectService:
    def __init__(self,root:Path):
        self.root=Path(root);self.models=self.root/'mcp-models';self.models.mkdir(parents=True,exist_ok=True)
        self.programs=ProgramService(self.root/'programs')
    def path(self,key):
        if not isinstance(key,str) or not MODEL_ID.fullmatch(key):raise ValueError('Invalid model id.')
        return self.models/(key+'.json')
    @contextmanager
    def lock(self,key):
        path=self.path(key).with_suffix('.lock')
        with path.open('a') as stream:
            fcntl.flock(stream,fcntl.LOCK_EX)
            try:yield
            finally:fcntl.flock(stream,fcntl.LOCK_UN)
    def load(self,key):
        path=self.path(key)
        if not path.is_file():raise ValueError('Model not found.')
        record=json.loads(path.read_text(encoding='utf-8'));DesignSpec.model_validate(record['spec'])
        record.setdefault('view',{});return record
    def list(self):
        models=[]
        for path in self.models.glob('*.json'):
            try:
                r=self.load(path.stem);models.append({'model_id':r['model_id'],'name':r['name'],'revision':r['spec']['revision'],'part_count':len(r['spec']['parts']),'updated_at':path.stat().st_mtime})
            except (ValueError,KeyError,OSError):continue
        for path in (self.root/'design-drafts').glob('*.json'):
            try:
                r=json.loads(path.read_text())
                if not self.path(r['model_id']).exists():models.append({'model_id':r['model_id'],'name':r['name'],'revision':r['revision'],'part_count':0,'draft':True,'updated_at':path.stat().st_mtime})
            except (ValueError,KeyError,OSError):continue
        return sorted(models,key=lambda r:r['name'].lower())
    def commit(self,record,expected=None):
        key=record['model_id']
        with self.lock(key):
            old=self.load(key) if self.path(key).exists() else None
            if expected is not None and old and old['spec']['revision']!=expected:raise ValueError('The project changed during this operation. Read the latest revision and retry; no edit was applied.')
            if old:
                history=self.models/key/'revisions'
                atomic_json(history/(str(old['spec']['revision'])+'.json'),old)
                record['spec']['revision']=old['spec']['revision']+1
                record['view']=deepcopy(old.get('view',{}))
            else:record['spec']['revision']=record.pop('initial_revision',1)
            DesignSpec.model_validate(record['spec'])
            atomic_json(self.path(key),record)
        return record
    def build(self,source,parameters,name=None,model_id=None,cancel_event=None,expected_revision=None,asset_id=None,engineering=None,new_model_id=None,initial_revision=1):
        if expected_revision is not None and (not isinstance(expected_revision,int) or isinstance(expected_revision,bool) or expected_revision<1):raise ValueError('Expected revision must be a positive integer.')
        old=self.load(model_id) if model_id else None;key=model_id or new_model_id or uuid.uuid4().hex
        if new_model_id and self.path(new_model_id).exists():raise ValueError('Design ID is already in use.')
        expected=old['spec']['revision'] if old else None
        if expected_revision is not None and expected_revision!=expected:raise ValueError('The model revision changed. Reload before editing.')
        if name is not None and (not isinstance(name,str) or not name.strip() or len(name)>100):raise ValueError('Model names must contain 1–100 characters.')
        previous=DesignSpec.model_validate(old['spec']) if old else from_legacy({'name':'New CAD','kind':'beam','length':100,'width':20,'height':5,'holeDiameter':6,'finCount':9,'material':'aluminum'})
        asset_id=asset_id or (old['spec']['program'].get('asset_id') if old else None)
        meshing=engineering.get('accuracy') if engineering is not None else old.get('engineering',{}).get('accuracy') if old else None
        report=self.programs.build(source,parameters,cancel_event,asset_id=asset_id,meshing=meshing)
        if cancel_event and cancel_event.is_set():raise ValueError('CAD build cancelled; the previous revision was preserved.')
        spec=generated_spec(source,parameters,report,previous)
        record={'model_id':key,'name':name.strip() if name else old['name'] if old else 'Generated CAD','spec':spec.model_dump(mode='json'),'geometry':report,'view':deepcopy(old.get('view',{})) if old else {}}
        if engineering is not None:
            from .engineering_schema import Engineering
            record['engineering']=Engineering.model_validate(engineering).model_dump(mode='json')
        elif old and old.get('engineering'):
            record['engineering']=deepcopy(old['engineering'])
            if old['spec']['program']['source']!=source or old['spec']['program'].get('asset_id')!=asset_id:
                record['engineering']['attached']=False
                record['engineering']['diagnostics']['detached_reason']='The Python program or imported geometry changed outside the feature graph. Rebuild features explicitly to replace it.'
        if not old:record['initial_revision']=initial_revision
        return self.commit(record,expected)
    def ensure_ready(self,key):
        """Upgrade cached exports without discarding a matching saved reference study."""
        old=self.load(key);program=old['spec']['program'];folder=self.programs.root/program['artifact_id']
        if program['artifact_id']==self.programs.key(program['source'],program['parameters'],program.get('asset_id'),program.get('meshing')) and self.programs.cached_report(program['artifact_id']):return old
        report=self.programs.build(program['source'],program['parameters'],asset_id=program.get('asset_id'),meshing=program.get('meshing'))
        spec=generated_spec(program['source'],program['parameters'],report,DesignSpec.model_validate(old['spec']))
        record=deepcopy(old);record.update(spec=spec.model_dump(mode='json'),geometry=report)
        # Cache repair/migration is not a user edit and must not add history.
        with self.lock(key):
            latest=self.load(key)
            if latest['spec']['revision']!=old['spec']['revision']:return latest
            record['spec']['revision']=old['spec']['revision'];record['view']=latest.get('view',{})
            atomic_json(self.path(key),record)
        return record
    def parameters(self,key,parameters,cancel_event=None,expected_revision=None):
        old=self.load(key)
        if old.get('engineering',{}).get('attached'):
            from .feature_graph import FeatureService
            return FeatureService(self).parameters(key,parameters,cancel_event,expected_revision)
        program=old['spec']['program']
        merged=validate_parameters({**program['parameters'],**parameters})
        return self.build(program['source'],merged,model_id=key,cancel_event=cancel_event,expected_revision=old['spec']['revision'] if expected_revision is None else expected_revision)
    def appearance(self,key,part_id,color=None,material=None,name=None):
        old=self.load(key);expected=old['spec']['revision'];record=deepcopy(old)
        part=next((p for p in record['spec']['parts'] if p['id']==part_id),None)
        if part is None:raise ValueError('Unknown part id.')
        if material is not None and material!=part['material']:record.pop('analysis',None)
        for field,value in [('color',color),('material',material),('name',name)]:
            if value is not None:part[field]=value
        record['spec']['simulation']['approved_fingerprint']=None
        DesignSpec.model_validate(record['spec']);return self.commit(record,expected)
    def save_view(self,key,view):
        from .view_settings import ViewSettings
        view=ViewSettings.model_validate(view).model_dump(mode='json',exclude_unset=True)
        with self.lock(key):
            record=self.load(key);record['view'].update(view);atomic_json(self.path(key),record)
        return record['view']
    def revisions(self,key):
        current=self.load(key);items=[{'revision':current['spec']['revision'],'name':current['name'],'current':True}]
        for p in sorted((self.models/key/'revisions').glob('*.json'),key=lambda p:int(p.stem),reverse=True):
            r=json.loads(p.read_text());items.append({'revision':r['spec']['revision'],'name':r['name'],'current':False})
        return items
    def read_revision(self,key,revision=None):
        """Read and repair an immutable historical view without committing a revision."""
        current=self.load(key)
        if revision is None:return self.ensure_ready(key)
        if not isinstance(revision,int) or isinstance(revision,bool) or revision<1:raise ValueError('Revision must be a positive integer.')
        if revision==current['spec']['revision']:record=deepcopy(current)
        else:
            path=self.models/key/'revisions'/(str(revision)+'.json')
            if not path.is_file():raise ValueError('Saved revision not found.')
            record=json.loads(path.read_text())
        program=record['spec']['program']
        if not self.programs.cached_report(program['artifact_id']):
            report=self.programs.build(program['source'],program['parameters'],asset_id=program.get('asset_id'),meshing=program.get('meshing'))
            spec=generated_spec(program['source'],program['parameters'],report,DesignSpec.model_validate(record['spec']))
            spec.revision=revision;record.update(geometry=report,spec=spec.model_dump(mode='json'))
        record['historical']=True;record['current_revision']=current['spec']['revision']
        return record
    def restore(self,key,revision):
        if not isinstance(revision,int) or isinstance(revision,bool) or revision<1:raise ValueError('Revision must be a positive integer.')
        current=self.load(key)
        if revision==current['spec']['revision']:return current
        path=self.models/key/'revisions'/(str(int(revision))+'.json')
        if not path.is_file():raise ValueError('Saved revision not found.')
        record=json.loads(path.read_text());program=record['spec']['program']
        if record['name']==current['name'] and DesignSpec.model_validate(record['spec']).content_hash()==DesignSpec.model_validate(current['spec']).content_hash():return current
        if program['artifact_id']!=self.programs.key(program['source'],program['parameters'],program.get('asset_id'),program.get('meshing')) or not self.programs.cached_report(program['artifact_id']):
            report=self.programs.build(program['source'],program['parameters'],asset_id=program.get('asset_id'),meshing=program.get('meshing'))
            record['geometry']=report;record['spec']=generated_spec(program['source'],program['parameters'],report,DesignSpec.model_validate(record['spec'])).model_dump(mode='json')
        return self.commit(record,current['spec']['revision'])
    def artifact(self,key,filename):
        return self.record_artifact(self.ensure_ready(key),filename)
    def record_artifact(self,record,filename):
        if filename=='design.FCStd':
            key=record.get('engineering',{}).get('diagnostics',{}).get('cache_id','')
            if not re.fullmatch('[a-f0-9]{64}',key):raise ValueError('No native feature document is available.')
            path=self.root/'feature-cache'/key/'design.FCStd'
            if not path.is_file():raise ValueError('Rebuild features to recreate the native document.')
            return path
        if filename not in (*EXPORTS.values(),'mesh.json','manifest.json','topology.json','input.step','input.stl'):raise ValueError('Unknown export format.')
        artifact_id=record['spec']['program']['artifact_id']
        if filename=='model.step' and record['geometry'].get('engine')=='implicit_mesh':raise ValueError('This model contains implicit triangle geometry. Export STL, GLB or 3MF; exact STEP is unavailable for mesh models.')
        if filename in ('model.step','model.glb','model.3mf'):return self.appearance_export(record,filename)
        if filename=='program.py':return self.source_export(record)
        path=self.programs.root/artifact_id/filename
        if not path.is_file():raise ValueError('Artifact is unavailable. Rebuild the model to recreate exports.')
        return path
    def appearance_export(self,record,filename):
        program=record['spec']['program'];native=self.programs.root/program['artifact_id']
        colors={p['id']:p['color'].lower() for p in record['spec']['parts']}
        originals={p['part']['id']:p['part']['color'].lower() for p in record['geometry']['parts']}
        if colors==originals:return native/filename
        if record['geometry'].get('engine')=='implicit_mesh':
            from .intact_lattice import write_mesh_exports
            import numpy as np,trimesh
            fingerprint=sha256(json.dumps({'artifact':program['artifact_id'],'colors':colors},sort_keys=True).encode()).hexdigest()
            folder=self.root/'mesh-colors'/fingerprint
            with self.programs.artifact_lock('colors-'+fingerprint):
                if not (folder/filename).is_file():
                    items=[]
                    for item in json.loads((native/'mesh.json').read_text())['parts']:
                        p=next(p for p in record['spec']['parts'] if p['id']==item['id']);points=np.asarray(item['positions']).reshape(-1,3);x,y,z=p['position']
                        vertices=np.column_stack((points[:,0]+x,-points[:,2]+y,points[:,1]+z))
                        items.append((p['id'],trimesh.Trimesh(vertices,np.asarray(item['indices']).reshape(-1,3),process=False),colors[p['id']]))
                    write_mesh_exports(items,folder)
            return folder/filename
        # Recolor the saved STEP inside the existing isolated importer; do not
        # re-run model-authored CAD or change its geometry artifact/references.
        asset=self.store_step((native/'model.step').read_bytes(),max_bytes=32*1024*1024)
        source="import build123d as bd\ndef build(params):\n    parts={}\n    colors="+repr(colors)+"\n    def visit(shape):\n        if shape.label in colors:\n            shape.color=bd.Color(colors[shape.label])\n            parts[shape.label]=shape\n        else:\n            for child in shape.children:visit(child)\n    visit(input_shape)\n    return parts\n"
        report=self.programs.build(source,{},asset_id=asset,meshing=program.get('meshing'))
        return self.programs.root/report['artifact_id']/filename
    def source_export(self,record):
        from .program_export import executable_source
        program=record['spec']['program'];colors={p['id']:p['color'] for p in record['spec']['parts']}
        fingerprint=sha256(json.dumps({'artifact':program['artifact_id'],'colors':colors,'engineering':record.get('engineering')},sort_keys=True).encode()).hexdigest()
        folder=self.root/'export-sources'/fingerprint;folder.mkdir(parents=True,exist_ok=True);path=folder/'program.py'
        asset_name=self.programs.asset_name(program['asset_id']) if program.get('asset_id') else None
        source=executable_source(program['source'],program['parameters'],'stl' if asset_name=='input.stl' else bool(program.get('asset_id')),colors,program.get('meshing'))
        if record.get('engineering',{}).get('attached'):
            from .feature_source import executable_feature_source
            source=executable_feature_source(record['engineering'])
        if not path.is_file() or path.read_text()!=source:
            temporary=folder/(uuid.uuid4().hex+'.tmp');temporary.write_text(source);temporary.replace(path)
        if asset_name and (not (folder/asset_name).exists() or sha256((folder/asset_name).read_bytes()).hexdigest()!=program['asset_id']):shutil.copyfile(self.programs.root/'assets'/program['asset_id']/asset_name,folder/asset_name)
        return path
    def portable(self,key,revision=None):
        record=self.read_revision(key,revision) if revision is not None else self.ensure_ready(key);mesh=json.loads(self.record_artifact(record,'mesh.json').read_text())
        asset_id=record['spec']['program'].get('asset_id')
        asset_name=self.programs.asset_name(asset_id) if asset_id else None
        asset={'format':'stl' if asset_name=='input.stl' else 'step','base64':base64.b64encode((self.programs.root/'assets'/asset_id/asset_name).read_bytes()).decode()} if asset_id else None
        return {'asset':asset,'topology':json.loads(self.record_artifact(record,'topology.json').read_text()),'model_id':key,'format':'intact-project','version':3 if record.get('engineering') else 2,'name':record['name'],'spec':record['spec'],'mesh':mesh,'view':record['view'],**({'engineering':record['engineering']} if record.get('engineering') else {})}
    def import_project(self,path):
        path=local_path(path)
        if not path.is_file() or path.stat().st_size>32*1024*1024:raise ValueError('Choose an Intact project JSON file smaller than 32 MB.')
        data=json.loads(path.read_text(encoding='utf-8'))
        if data.get('format')!='intact-project' or data.get('version') not in (2,3):raise ValueError('Choose an Intact version 2 or 3 project file.')
        spec=DesignSpec.model_validate(data['spec']);program=spec.program
        if not program:raise ValueError('This import tool requires a project containing a CAD program.')
        asset_id=None
        if program.asset_id:
            asset=data.get('asset')
            if not isinstance(asset,dict) or asset.get('format') not in ('step','stl'):raise ValueError('Imported project is missing its geometry source asset.')
            raw=base64.b64decode(asset.get('base64',''),validate=True);asset_id=self.store_mesh(raw) if asset['format']=='stl' else self.store_step(raw)
            if asset_id!=program.asset_id:raise ValueError('STEP asset checksum does not match the project.')
        from .view_settings import ViewSettings
        view=ViewSettings.model_validate(data.get('view',{})).model_dump(mode='json',exclude_unset=True)
        name=data.get('name','Imported CAD')
        if not isinstance(name,str) or not 1<=len(name.strip())<=100:raise ValueError('Imported model name must contain 1–100 characters.')
        report=self.programs.build(program.source,program.parameters,asset_id=asset_id,meshing=program.meshing)
        if {p['part']['id'] for p in report['parts']}!={p.id for p in spec.parts}:raise ValueError('The rebuilt program part IDs do not match the saved project.')
        # Validate everything before the first project commit. Appearances and
        # disabled flags come from the saved spec; measurements come from CAD.
        imported=generated_spec(program.source,program.parameters,report,spec)
        record={'model_id':uuid.uuid4().hex,'name':name.strip(),'spec':imported.model_dump(mode='json'),'geometry':report,'view':view}
        if data.get('version')==3:
            from .engineering_schema import Engineering
            record['engineering']=Engineering.model_validate(data.get('engineering',{})).model_dump(mode='json')
            record['engineering']['diagnostics'].pop('cache_id',None)
        return self.commit(record)

    def store_mesh(self,data):
        if not isinstance(data,bytes) or not 84<=len(data)<=32*1024**2:raise ValueError('Supply an STL asset from 84 bytes to 32 MB.')
        key=sha256(data).hexdigest();folder=self.programs.root/'assets'/key;folder.mkdir(parents=True,exist_ok=True);path=folder/'input.stl'
        if not path.exists() or sha256(path.read_bytes()).hexdigest()!=key:
            temporary=folder/(uuid.uuid4().hex+'.tmp');temporary.write_bytes(data);temporary.replace(path)
        return key
    def import_mesh_bytes(self,data,name='Imported scan',cancel_event=None):
        asset=self.store_mesh(data)
        return self.build('from intact_lattice import MeshPart\ndef build(params):\n    return {"scan":input_mesh}',{},name=name[:100],asset_id=asset,cancel_event=cancel_event)
    def store_step(self,data,max_bytes=16*1024*1024):
        if not isinstance(data,bytes) or not 0<len(data)<=max_bytes or b'ISO-10303-21;' not in data[:1000]:raise ValueError('Choose an ISO STEP file smaller than 16 MB.')
        key=sha256(data).hexdigest();folder=self.programs.root/'assets'/key;folder.mkdir(parents=True,exist_ok=True)
        path=folder/'input.step'
        if not path.exists() or sha256(path.read_bytes()).hexdigest()!=key:
            temporary=folder/(uuid.uuid4().hex+'.tmp');temporary.write_bytes(data);temporary.replace(path)
        return key
    def import_cad(self,path,cancel_event=None):
        path=local_path(path)
        if not path.is_file() or path.stat().st_size>16*1024*1024:raise ValueError('Choose a STEP file smaller than 16 MB.')
        return self.import_step_bytes(path.read_bytes(),path.stem,cancel_event)
    def import_step_bytes(self,data,name,cancel_event=None):
        asset_id=self.store_step(data)
        return self.build('def build(params):\n    return dict(imported_parts)',{},name=name[:100] or 'Imported STEP',cancel_event=cancel_event,asset_id=asset_id)
