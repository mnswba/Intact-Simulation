# SPDX-License-Identifier: Apache-2.0
"""Persistent design drafts and transactional feature rebuilds backed by FreeCAD."""
from copy import deepcopy
from hashlib import sha256
import json,os,shutil,tempfile,uuid
from pathlib import Path
from .engineering_schema import Engineering,Sketch,Constraint,Feature,Requirements,Accuracy
from .projects import atomic_json
from .isolated_worker import run_worker

class FreeCADRuntime:
    def __init__(self,projects):
        self.projects=projects
        self.root=Path(os.environ.get('INTACT_FREECAD_ROOT',str(Path.home()/'.local/share/intact-simulation/freecad-1.1.4/squashfs-root'))).resolve()
    def python(self):
        for name in ('usr/bin/python','usr/bin/python3','usr/bin/python3.11'):
            path=self.root/name
            if path.is_file():return path
        return None
    def status(self):return {'available':self.python() is not None,'engine':'FreeCAD','pinned_version':'1.1.4','isolated':self.projects.programs.available()}
    def run(self,engineering,mode='rebuild',cancel_event=None):
        python=self.python()
        if python is None:raise ValueError('FreeCAD 1.1.4 runtime is unavailable. Run the Intact FreeCAD installer.')
        worker=Path(__file__).with_name('freecad_worker.py')
        data=Engineering.model_validate(engineering).model_dump(mode='json')
        request={'mode':mode,'engineering':{k:data[k] for k in ('sketches','features','parameters')}}
        def resolved(value):
            if isinstance(value,dict):
                if set(value)=={'parameter'}:
                    if value['parameter'] not in data['parameters']:raise ValueError('Undefined feature parameter: '+value['parameter'])
                    return data['parameters'][value['parameter']]
                return {k:resolved(v) for k,v in value.items()}
            if isinstance(value,list):return [resolved(v) for v in value]
            return value
        node_keys={};sketches={s['id']:s for s in data['sketches']}
        for feature in data['features']:
            signature={'worker':sha256(worker.read_bytes()).hexdigest(),'feature':resolved(feature),'sketch':resolved(sketches.get(feature.get('sketch_id'))),'base':node_keys.get(feature.get('base')),'tool':node_keys.get(feature.get('tool'))}
            node_keys[feature['id']]=sha256(json.dumps(signature,sort_keys=True).encode()).hexdigest()
        key=sha256(worker.read_bytes()+json.dumps(request,sort_keys=True).encode()).hexdigest();cache=self.projects.root/'feature-cache'/key
        with self.projects.programs.artifact_lock('fc-'+key,cancel_event):
            report_path=cache/'report.json'
            if report_path.is_file():
                report=json.loads(report_path.read_text());files=report.get('checksums',{})
                if files and all((cache/name).is_file() and sha256((cache/name).read_bytes()).hexdigest()==value for name,value in files.items()):return report,cache
            with tempfile.TemporaryDirectory(prefix='intact-features-') as tmp:
                folder=Path(tmp);input_dir=folder/'input';output=folder/'output';input_dir.mkdir();output.mkdir();(input_dir/'nodes').mkdir();cached=[]
                if mode=='rebuild':
                    for fid,nkey in node_keys.items():
                        node=self.projects.root/'feature-node-cache'/nkey;meta=node/'sha256.json';shape=node/'shape.brep'
                        try:
                            if meta.is_file() and shape.is_file() and sha256(shape.read_bytes()).hexdigest()==json.loads(meta.read_text()).get('sha256'):
                                shutil.copyfile(shape,input_dir/'nodes'/(fid+'.brep'));cached.append(fid)
                        except (OSError,ValueError):pass
                request.update(cached_nodes=cached,export_nodes=mode=='rebuild');(input_dir/'request.json').write_text(json.dumps(request))
                env={'PYTHONHOME':str(self.root/'usr'),'PYTHONPATH':str(self.root/'usr/lib')+':'+str(self.root/'usr/Mod'),'LD_LIBRARY_PATH':str(self.root/'usr/lib')+':'+str(self.root/'usr/lib/x86_64-linux-gnu'),'FONTCONFIG_PATH':'/tmp'}
                report=run_worker(self.projects.programs,worker,input_dir,output,python=python,mounts=[self.root],env=env,cancel_event=cancel_event)
                if mode=='rebuild':
                    for fid,nkey in node_keys.items():
                        shape=output/'nodes'/(fid+'.brep')
                        if shape.is_file() and 0<shape.stat().st_size<=64*1024**2:
                            node=self.projects.root/'feature-node-cache'/nkey;node.mkdir(parents=True,exist_ok=True)
                            temporary=node/(uuid.uuid4().hex+'.tmp');shutil.copyfile(shape,temporary);temporary.replace(node/'shape.brep');atomic_json(node/'sha256.json',{'sha256':sha256(shape.read_bytes()).hexdigest()})
                expected=['result.step','design.FCStd'] if mode=='rebuild' else []
                for name in expected:
                    if not (output/name).is_file() or not 0<(output/name).stat().st_size<=64*1024**2:raise ValueError('Invalid FreeCAD output.')
                report['cache_id']=key;report['checksums']={name:sha256((output/name).read_bytes()).hexdigest() for name in expected}
                # A solve-only entry has no native files to checksum; keep a report digest.
                (output/'diagnostics.json').write_text(json.dumps(report));report['checksums']['diagnostics.json']=sha256((output/'diagnostics.json').read_bytes()).hexdigest()
                cache.mkdir(parents=True,exist_ok=True)
                for name in [*expected,'diagnostics.json']:shutil.copyfile(output/name,cache/name)
                atomic_json(report_path,report)
                return report,cache

class FeatureService:
    def __init__(self,projects):self.projects=projects;self.runtime=FreeCADRuntime(projects)
    def draft_path(self,key):self.projects.path(key);return self.projects.root/'design-drafts'/(key+'.json')
    def load(self,key):
        if self.projects.path(key).exists():
            r=self.projects.load(key);return r,Engineering.model_validate(r.get('engineering',{})),False
        path=self.draft_path(key)
        if not path.is_file():raise ValueError('Design not found.')
        r=json.loads(path.read_text());return r,Engineering.model_validate(r['engineering']),True
    def revision(self,r,draft):return r['revision'] if draft else r['spec']['revision']
    def check_revision(self,r,draft,expected):
        if expected is not None and (isinstance(expected,bool) or not isinstance(expected,int) or expected!=self.revision(r,draft)):raise ValueError('The design changed. Read the current revision and retry.')
    def save(self,r,e,draft):
        data=e.model_dump(mode='json')
        if draft:
            r=deepcopy(r);r['revision']+=1;r['engineering']=data;atomic_json(self.draft_path(r['model_id']),r);return self.summary(r,e,True)
        r=deepcopy(r);r['engineering']=data;r=self.projects.commit(r,r['spec']['revision']);return self.summary(r,e,False)
    def summary(self,r,e,draft):return {'model_id':r['model_id'],'name':r['name'],'revision':self.revision(r,draft),'draft':draft,'geometry_available':not draft,'engineering':e.model_dump(mode='json')}
    def new(self,name='New constrained design'):
        if not isinstance(name,str) or not 1<=len(name.strip())<=100:raise ValueError('Design name must contain 1–100 characters.')
        key=uuid.uuid4().hex;r={'model_id':key,'name':name.strip(),'revision':1,'engineering':Engineering().model_dump(mode='json')};atomic_json(self.draft_path(key),r);return r,Engineering(),True
    def get(self,key):
        r,e,draft=self.load(key);result=self.summary(r,e,draft)
        for folder,field in [('sketch-solves','sketch_solve'),('verification','verification'),('accuracy-checks','accuracy_report')]:
            path=self.projects.root/folder/(key+'.json')
            if path.is_file():
                cached=json.loads(path.read_text())
                if cached.get('revision')==self.revision(r,draft):
                    result[field]=cached
                    if field=='sketch_solve':result['engineering']['diagnostics']['sketches']=cached['sketches']
        return result
    def requirements(self,key,data=None,name=None,expected_revision=None):
        requirements=Requirements.model_validate(data) if data is not None else None
        if key is None:
            r,e,draft=self.new(name or 'New constrained design')
            if requirements is not None:e.requirements=requirements;r['engineering']=e.model_dump(mode='json');atomic_json(self.draft_path(r['model_id']),r)
            return self.summary(r,e,draft)
        if requirements is None:return self.get(key)
        return self.mutate(key,lambda e:setattr(e,'requirements',requirements),expected_revision)
    def mutate(self,key,operation,expected_revision=None):
        # Serialize draft edits. Model commits have their own optimistic revision guard.
        with (self.projects.root/'engineering.lock').open('a') as lock:
            import fcntl
            fcntl.flock(lock,fcntl.LOCK_EX)
            r,e,draft=self.load(key);self.check_revision(r,draft,expected_revision);operation(e)
            e=Engineering.model_validate(e.model_dump(mode='json'));return self.save(r,e,draft)
    def create_sketch(self,key,sketch,expected_revision=None,name=None,parameters=None):
        s=Sketch.model_validate(sketch)
        if parameters is not None:Engineering(sketches=[s],parameters=parameters)
        if key is None:r,e,draft=self.new(name or 'New constrained design');key=r['model_id']
        def change(e):
            if any(old.id==s.id for old in e.sketches):raise ValueError('Sketch ID already exists. Use set_sketch_constraints or replace_sketch.')
            e.sketches.append(s);e.diagnostics.pop('sketches',None)
            if parameters is not None:e.parameters.update(parameters)
        return self.mutate(key,change,expected_revision)
    def constraints(self,key,sketch_id,constraints,expected_revision=None,geometry=None):
        cs=[Constraint.model_validate(c) for c in constraints]
        def change(e):
            s=next((s for s in e.sketches if s.id==sketch_id),None)
            if s is None:raise ValueError('Unknown sketch ID.')
            s.constraints=cs
            if geometry is not None:
                from .engineering_schema import Geometry
                s.geometry=[Geometry.model_validate(g) for g in geometry]
            e.diagnostics.pop('sketches',None)
            e.diagnostics['needs_rebuild']=True
        return self.mutate(key,change,expected_revision)
    def solve(self,key,sketch_id=None,cancel_event=None):
        r,e,draft=self.load(key)
        if sketch_id and not any(s.id==sketch_id for s in e.sketches):raise ValueError('Unknown sketch ID.')
        data=e.model_dump(mode='json')
        if sketch_id:data['sketches']=[s for s in data['sketches'] if s['id']==sketch_id];data['features']=[]
        report,_=self.runtime.run(data,'solve',cancel_event)
        # Solving is read-only: geometry, revisions and constraints remain unchanged.
        result={'model_id':key,'revision':self.revision(r,draft),'sketches':report['sketches'],'engine_version':report['version']}
        atomic_json(self.projects.root/'sketch-solves'/(key+'.json'),result)
        return result
    def edit(self,key,features,parameters=None,mode='replace',expected_revision=None,rebuild=True,cancel_event=None):
        fs=[Feature.model_validate(f) for f in features]
        r,e,draft=self.load(key);self.check_revision(r,draft,expected_revision)
        if mode=='replace':e.features=fs
        elif mode=='upsert':
            mapping={f.id:f for f in fs};e.features=[mapping.pop(f.id,f) for f in e.features]+list(mapping.values())
        else:raise ValueError('Feature edit mode must be replace or upsert.')
        if parameters is not None:e.parameters.update(parameters)
        e=Engineering.model_validate(e.model_dump(mode='json'))
        if rebuild:return self.rebuild(key,e,self.revision(r,draft),cancel_event)
        e.attached=False;e.diagnostics['needs_rebuild']=True
        def stage(current):
            current.features=e.features;current.parameters=e.parameters;current.attached=False;current.diagnostics=e.diagnostics
        return self.mutate(key,stage,self.revision(r,draft))
    def rebuild(self,key,engineering=None,expected_revision=None,cancel_event=None):
        r,e,draft=self.load(key);self.check_revision(r,draft,expected_revision)
        if engineering is not None:e=Engineering.model_validate(engineering.model_dump(mode='json') if isinstance(engineering,Engineering) else engineering)
        if not e.features:raise ValueError('The design has no feature graph to build.')
        report,cache=self.runtime.run(e.model_dump(mode='json'),'rebuild',cancel_event)
        e.diagnostics=report;e.attached=True
        asset=self.projects.store_step((cache/'result.step').read_bytes(),max_bytes=64*1024**2)
        # Exported FreeCAD labels are checked after the isolated native import.
        source="def build(params):\n    parts={}\n    wanted="+repr(report['part_ids'])+"\n    def visit(shape):\n        if shape.label in wanted:\n            parts[shape.label]=shape\n        else:\n            for child in shape.children:visit(child)\n    visit(input_shape)\n    return parts"
        native=self.projects.programs.build(source,e.parameters,asset_id=asset,meshing=e.accuracy.model_dump(mode='json'),cancel_event=cancel_event)
        if {p['part']['id'] for p in native['parts']}!=set(report['part_ids']):raise ValueError('The STEP bridge did not preserve expected part names; no design was committed.')
        with (self.projects.root/'engineering.lock').open('a') as lock:
            import fcntl
            fcntl.flock(lock,fcntl.LOCK_EX)
            latest,_,now_draft=self.load(key)
            if now_draft!=draft or self.revision(latest,now_draft)!=self.revision(r,draft):raise ValueError('The design changed during rebuild; no edit was applied.')
            result=self.projects.build(source,e.parameters,name=r['name'],model_id=None if draft else key,new_model_id=key if draft else None,initial_revision=r['revision']+1 if draft else 1,expected_revision=None if draft else r['spec']['revision'],asset_id=asset,cancel_event=cancel_event,engineering=e.model_dump(mode='json'))
            if draft:self.draft_path(key).unlink(missing_ok=True)
        return result
    def parameters(self,key,parameters,cancel_event=None,expected_revision=None):
        r,e,draft=self.load(key);self.check_revision(r,draft,expected_revision);e.parameters.update(parameters)
        return self.rebuild(key,e,self.revision(r,draft),cancel_event)
