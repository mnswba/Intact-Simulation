"""Persistent loopback viewer. Survives stdio client reconnects without a console window."""
from __future__ import annotations
import argparse, fcntl, json, os, secrets, subprocess, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlsplit,parse_qs
from urllib.request import urlopen
from .projects import ProjectService, atomic_json, EXPORTS

VERSION='0.16.0'

def registry(root):return Path(root)/'viewer-session.json'

def live_session(root):
    try:
        entry=json.loads(registry(root).read_text())
        if not isinstance(entry['port'],int) or not 0<entry['port']<65536 or not isinstance(entry['token'],str) or len(entry['token'])<30:return None
        url=f"http://127.0.0.1:{entry['port']}/{entry['token']}/health"
        health=json.loads(urlopen(url,timeout=1).read())
        return entry if health.get('service')=='intact-viewer' and health.get('state_directory')==str(Path(root).resolve()) else None
    except (OSError,ValueError,KeyError,URLError):return None

def ensure_viewer(root):
    root=Path(root).resolve();root.mkdir(parents=True,exist_ok=True)
    with (root/'viewer-start.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        current=live_session(root)
        if current:return current
        with (root/'viewer.log').open('ab') as log:
            process=subprocess.Popen([sys.executable,'-m','intact_backend.viewer_server','--state-dir',str(root)],stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True,env={**os.environ,'PYTHONUNBUFFERED':'1'})
        deadline=time.monotonic()+15
        while time.monotonic()<deadline:
            current=live_session(root)
            if current:return current
            if process.poll() is not None:break
            time.sleep(.1)
        raise ValueError('The local viewer could not start. Check '+str(root/'viewer.log'))

def viewer_url(root,key,revision=None):
    service=ProjectService(Path(root))
    if service.path(key).exists():service.load(key)
    else:
        from .feature_graph import FeatureService
        FeatureService(service).load(key)
    entry=ensure_viewer(root)
    suffix='' if revision is None else '?revision='+str(revision)
    return f"http://localhost:{entry['port']}/{entry['token']}/{key}/view"+suffix

class ViewerHandler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    @property
    def projects(self):return self.server.projects
    def route(self):
        parts=urlsplit(self.path).path.strip('/').split('/')
        if len(parts)<2 or not secrets.compare_digest(parts[0],self.server.token):raise ValueError('Not found.')
        return parts
    def send(self,status,data,mime='application/json',filename=None):
        if not isinstance(data,bytes):data=json.dumps(data,allow_nan=False).encode()
        self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(data)))
        self.send_header('X-Content-Type-Options','nosniff');self.send_header('Cache-Control','no-store')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data: blob:; frame-ancestors 'none'")
        if filename:self.send_header('Content-Disposition','attachment; filename="'+filename+'"')
        self.end_headers();self.wfile.write(data)
    def do_GET(self):
        try:
            parts=self.route()
            if len(parts)==2 and parts[1]=='health':return self.send(200,{'service':'intact-viewer','version':VERSION,'state_directory':str(self.projects.root.resolve())})
            if len(parts)!=3:raise ValueError('Not found.')
            key,kind=parts[1:];value=parse_qs(urlsplit(self.path).query).get('revision',[None])[0];revision=int(value) if value is not None else None
            from .feature_graph import FeatureService
            if kind=='engineering.json':
                if revision is not None:
                    r=self.projects.read_revision(key,revision)
                    from .engineering_schema import Engineering
                    return self.send(200,{'model_id':key,'revision':revision,'draft':False,'engineering':Engineering.model_validate(r.get('engineering',{})).model_dump(mode='json')})
                return self.send(200,FeatureService(self.projects).get(key))
            if kind=='logo.svg':return self.send(200,Path(__file__).with_name('logo.svg').read_bytes(),'image/svg+xml')
            if kind=='draft-viewer.js':return self.send(200,Path(__file__).with_name('draft_viewer.js').read_bytes(),'text/javascript')
            if not self.projects.path(key).exists():
                FeatureService(self.projects).load(key)
                if kind=='view':return self.send(200,Path(__file__).with_name('draft_viewer.html').read_bytes(),'text/html; charset=utf-8')
                raise ValueError('Draft design has no solid geometry or exports.')
            record=self.projects.read_revision(key,revision) if revision is not None else self.projects.ensure_ready(key) if kind=='view' else self.projects.load(key)
            if kind in ('view','viewer.js'):
                file=Path(__file__).with_name('viewer.html' if kind=='view' else kind)
                return self.send(200,file.read_bytes(),'text/html; charset=utf-8' if kind=='view' else 'text/javascript')
            if kind=='project-file':
                from .project_exports import read_file
                query=parse_qs(urlsplit(self.path).query);filename=query.get('file',[''])[0]
                path=read_file(self.projects,key,query.get('export_id',[''])[0],filename)
                mime={'bom.csv':'text/csv; charset=utf-8','slides.pptx':'application/vnd.openxmlformats-officedocument.presentationml.presentation','drawing.dxf':'application/dxf','drawing.dwg':'application/acad'}[filename]
                return self.send(200,path.read_bytes(),mime,filename)
            if kind=='models.json':return self.send(200,{'models':self.projects.list()})
            if kind=='requests.json':
                from .edit_requests import EditRequests
                return self.send(200,{'requests':EditRequests(self.projects).list(key)})
            if kind=='bodies.json':
                from .body_selection import bodies
                try:return self.send(200,bodies(self.projects,record,parse_qs(urlsplit(self.path).query).get('part_id',[None])[0]))
                except ValueError as exc:return self.send(400,{'error':str(exc)[:1500]})
            if kind=='simulation.json':
                from .simulation_workspace import workspace
                return self.send(200,workspace(self.projects,key))
            if kind=='engineering-evidence.json':
                from .advanced import Advanced
                evidence=Advanced(self.projects).evidence(key)
                for report in evidence['reports']:report['stale']=report.get('artifact_id')!=record['spec']['program']['artifact_id']
                return self.send(200,evidence)
            if kind=='engineering-file':
                import re
                query=parse_qs(urlsplit(self.path).query);rid=query.get('report_id',[''])[0];filename=query.get('file',['report.json'])[0]
                if not re.fullmatch('[a-f0-9]{32}',rid) or filename not in ('report.json','results.vtu','results.csv','trajectory.csv','joints.csv','rig.zip','drawing.pdf','result.step','result.stl'):raise ValueError('Invalid engineering artifact.')
                folder=self.projects.root/'engineering'/rid;report=json.loads((folder/'report.json').read_text())
                if report.get('model_id')!=key:raise ValueError('Report belongs to another model.')
                return self.send(200,(folder/filename).read_bytes(),'application/pdf' if filename.endswith('.pdf') else 'application/json' if filename.endswith('.json') else 'application/octet-stream',filename if filename!='report.json' else None)
            if kind=='engineering-jobs.json':
                from .engineering_jobs import status
                return self.send(200,{'jobs':[status(self.projects,p.stem) for p in (self.projects.root/'engineering-jobs').glob('*.json') if json.loads(p.read_text()).get('model_id')==key]})
            if kind=='capabilities.json':
                from .ask_ai import capabilities
                return self.send(200,capabilities())
            if kind=='state.json':return self.send(200,record)
            if kind=='project.json':return self.send(200,self.projects.portable(key,revision=revision),filename='intact-project.json')
            if kind=='revisions.json':return self.send(200,{'revisions':self.projects.revisions(key)})
            if kind=='analysis.json':return self.send(200,record.get('analysis',{}))
            path=self.projects.record_artifact(record,kind) if revision is not None else self.projects.artifact(key,kind)
            return self.send(200,path.read_bytes(),'application/json' if kind in ('mesh.json','topology.json') else 'application/octet-stream',None if kind in ('mesh.json','topology.json') else kind)
        except (ValueError,KeyError,FileNotFoundError):self.send(404,{'error':'Model or artifact not found.'})
        except (OSError,json.JSONDecodeError):self.send(503,{'error':'The project is temporarily unavailable.'})
    def do_POST(self):
        try:
            parts=self.route()
            origin=self.headers.get('Origin')
            if origin not in (f'http://localhost:{self.server.server_port}',f'http://127.0.0.1:{self.server.server_port}'):return self.send(403,{'error':'Origin is not allowed.'})
            if len(parts)!=3:raise ValueError('Not found.')
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=24*1024*1024:return self.send(413,{'error':'Invalid request size.'})
            data=json.loads(self.rfile.read(length));key,kind=parts[1:]
            if 'revision' in parse_qs(urlsplit(self.path).query):raise ValueError('Historical revisions are read-only. Return to the current model or explicitly restore a revision.')
            if kind=='engineering':
                from .feature_graph import FeatureService
                f=FeatureService(self.projects);action=data.get('action');expected=data.get('expected_revision')
                if action=='constraints':result=f.constraints(key,data['sketch_id'],data['constraints'],expected)
                elif action=='solve':result=f.solve(key,data.get('sketch_id'))
                elif action=='features':result=f.edit(key,data['features'],data.get('parameters'),data.get('mode','upsert'),expected)
                elif action=='rebuild':result=f.rebuild(key,expected_revision=expected)
                elif action=='verify':
                    from .design_checks import verify_design
                    result=verify_design(self.projects,key)
                elif action=='parameters':
                    r,e,draft=f.load(key)
                    if not draft and e.attached:result=f.parameters(key,data['parameters'],expected_revision=expected)
                    else:result=f.mutate(key,lambda e:e.parameters.update(data['parameters']),expected)
                elif action=='accuracy':
                    from .accuracy import set_accuracy
                    result=set_accuracy(self.projects,key,data['settings'],expected)
                elif action=='check_accuracy':
                    from .accuracy import check_accuracy
                    result=check_accuracy(self.projects,key)
                else:raise ValueError('Unknown engineering operation.')
                return self.send(200,result)
            if kind=='project-export':
                from .project_exports import create
                return self.send(200,create(self.projects,key,data))
            if kind=='edit-request':
                from .edit_requests import EditRequests
                return self.send(200,EditRequests(self.projects).create(key,data))
            if kind in ('run-edit','cancel-edit'):
                from .ask_ai import start,cancel
                return self.send(200,(start if kind=='run-edit' else cancel)(self.projects,key,data['request_id']))
            if kind=='simulation-setup':
                from .simulation_workspace import configure
                return self.send(200,configure(self.projects,key,data['settings'],data['operation']))
            if kind=='engineering-job':
                from . import engineering_jobs as jobs
                if data.get('action')=='cancel':return self.send(200,jobs.cancel(self.projects,data['job_id'],key))
                return self.send(200,jobs.submit(self.projects,data['operation'],data['settings'],key))
            if kind=='import-step':
                import base64
                record=self.projects.import_step_bytes(base64.b64decode(data['base64'],validate=True),data.get('name','Imported STEP'))
                return self.send(200,{'model_id':record['model_id']})
            if kind=='appearance':record=self.projects.appearance(key,data['part_id'],data.get('color'),data.get('material'),data.get('name'));return self.send(200,record)
            if kind=='parameters':record=self.projects.parameters(key,data['parameters'],expected_revision=data.get('expected_revision'));return self.send(200,record)
            if kind=='view-settings':return self.send(200,self.projects.save_view(key,data))
            if kind=='restore':return self.send(200,self.projects.restore(key,data['revision']))
            raise ValueError('Unknown operation.')
        except (ValueError,KeyError,TypeError) as exc:self.send(400,{'error':str(exc)[:3000]})
        except Exception as exc:self.send(500,{'error':str(exc)[:1000]})

def serve(root):
    root=Path(root).resolve();projects=ProjectService(root);token=secrets.token_urlsafe(32);port=0
    try:
        previous=json.loads(registry(root).read_text());token=previous['token'];port=previous['port']
    except (OSError,ValueError,KeyError):pass
    try:server=ThreadingHTTPServer(('127.0.0.1',port),ViewerHandler)
    except OSError:server=ThreadingHTTPServer(('127.0.0.1',0),ViewerHandler)
    server.projects=projects;server.token=token
    atomic_json(registry(root),{'token':token,'port':server.server_port,'pid':os.getpid(),'version':VERSION});registry(root).chmod(0o600)
    server.serve_forever()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--state-dir',type=Path,required=True)
    serve(parser.parse_args().state_dir)
