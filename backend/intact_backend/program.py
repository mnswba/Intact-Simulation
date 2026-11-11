"""Execute model-authored CAD Python in an actual rootless Linux sandbox.

Filesystem mounts contain only Python/runtime libraries, one request and an output folder.
No model/service credentials, home files, host /proc or network are accessible.
AST checks are a usability layer; they are NOT used as a substitute for OS isolation.
"""
from __future__ import annotations
from hashlib import sha256
import re,math
import json, os, shutil, subprocess, sys, tempfile, threading, time, signal
from pathlib import Path
from contextlib import contextmanager
import fcntl
from .program_policy import validate_source,validate_parameters
from .program_export import executable_source

class SandboxUnavailable(RuntimeError):pass
class ProgramBuildError(ValueError):pass

class ProgramService:
    def __init__(self,root:Path,binary:str|None=None,timeout:float=120):
        self.root=root;root.mkdir(parents=True,exist_ok=True);self.binary=binary or os.environ.get('INTACT_BWRAP_BIN') or shutil.which('bwrap') or str(Path.home()/'.local/bin/bwrap');self.timeout=timeout;self._lock=threading.Lock();self._ready=None
    def available(self)->bool:
        if self._ready is None:
            try:
                result=subprocess.run([self.binary,'--unshare-all','--die-with-parent','--new-session','--ro-bind','/usr','/usr','--ro-bind','/lib','/lib','--ro-bind','/lib64','/lib64','--proc','/proc','--dev','/dev','--clearenv','/usr/bin/true'],capture_output=True,timeout=5,env={'PATH':'/usr/bin:/bin'})
                self._ready=result.returncode==0
            except (OSError,subprocess.SubprocessError):self._ready=False
        return self._ready
    def cached_report(self,key):
        target=self.root/key
        try:
            report=json.loads((target/'manifest.json').read_text())
            if not isinstance(report,dict) or not isinstance(report.get('sha256'),dict):return None
            if not isinstance(report.get('parts'),list) or not 1<=len(report['parts'])<=128:return None
            for part in report['parts']:
                if not isinstance(part,dict):return None
                for field in ('volume_mm3','surface_area_mm2'):
                    n=part.get(field)
                    if isinstance(n,bool) or not isinstance(n,(int,float)) or not math.isfinite(n) or n<=0:return None
            names=('model.stl','mesh.json','topology.json','model.glb','model.3mf','program.py')
            if report.get('engine')!='implicit_mesh':names+=('model.step',)
            if report.get('asset_id'):names+=(report.get('asset_name','input.step'),)
            if report.get('valid') is not True or report.get('artifact_id')!=key:return None
            checksums=report.get('sha256',{})
            for name in names:
                path=target/name
                if not path.is_file() or path.is_symlink() or not 0<path.stat().st_size<=64*1024*1024:return None
                if checksums.get(name)!=sha256(path.read_bytes()).hexdigest():return None
            return report
        except (OSError,ValueError,TypeError):return None
    def key(self,source:str,parameters:dict,asset_id=None,meshing=None)->str:
        worker_signature=sha256(b''.join(Path(__file__).with_name(name).read_bytes() for name in ('program_worker.py','topology_worker.py','intact_lattice.py'))).hexdigest()
        data={'worker':5,'worker_signature':worker_signature,'asset_id':asset_id,'build123d':'0.13.0','source':source,'parameters':parameters}
        if meshing:data['meshing']=meshing
        return sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    def asset_name(self,asset_id):
        if not re.fullmatch('[a-f0-9]{64}',asset_id):raise ValueError('Invalid geometry asset id.')
        return 'input.stl' if (self.root/'assets'/asset_id/'input.stl').is_file() else 'input.step'
    @contextmanager
    def artifact_lock(self,key,cancel_event=None):
        with (self.root/(key+'.lock')).open('a') as stream:
            deadline=time.monotonic()+self.timeout+5
            while True:
                if cancel_event and cancel_event.is_set():raise ProgramBuildError('CAD build cancelled.')
                try:fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB);break
                except BlockingIOError:
                    if time.monotonic()>deadline:raise ProgramBuildError('The CAD worker is busy. Retry after the active build finishes.')
                    time.sleep(.05)
            try:yield
            finally:fcntl.flock(stream,fcntl.LOCK_UN)
    def build(self,source:str,parameters:dict,cancel_event:threading.Event|None=None,asset_id:str|None=None,meshing=None)->dict:
        source=validate_source(source);parameters=validate_parameters(parameters)
        if meshing is not None:
            from .engineering_schema import Accuracy
            meshing=Accuracy.model_validate(meshing).model_dump(mode='json')
        if not self.available():raise SandboxUnavailable('Free-form CAD needs bubblewrap with working user/network namespaces on the Python host. Execution is disabled until isolation is available.')
        asset_name=self.asset_name(asset_id) if asset_id else 'input.step'
        if asset_id is not None and not (self.root/'assets'/asset_id/asset_name).is_file():raise ValueError('Imported geometry asset is missing.')
        if asset_id and sha256((self.root/'assets'/asset_id/asset_name).read_bytes()).hexdigest()!=asset_id:raise ValueError('Imported geometry source is damaged. Reimport the original source or portable project.')
        key=self.key(source,parameters,asset_id,meshing);target=self.root/key
        with self._lock,self.artifact_lock(key,cancel_event):
            report=self.cached_report(key)
            if report:return {**report,'cached':True}
            with tempfile.TemporaryDirectory(prefix='program-',dir=self.root) as temporary:
                folder=Path(temporary);input_dir=folder/'input';output_dir=folder/'output';input_dir.mkdir();output_dir.mkdir()
                (input_dir/'request.json').write_text(json.dumps({'source':source,'parameters':parameters,'asset_id':asset_id,'asset_name':asset_name,'meshing':meshing},allow_nan=False))
                if asset_id:shutil.copyfile(self.root/'assets'/asset_id/asset_name,input_dir/asset_name)
                worker=Path(__file__).with_name('program_worker.py').resolve();runtime=Path(sys.base_prefix).resolve();venv=Path(sys.prefix).resolve()
                command=[self.binary,'--unshare-all','--die-with-parent','--new-session','--cap-drop','ALL','--clearenv']
                for path in dict.fromkeys(['/usr','/lib','/lib64',str(runtime),str(Path(sys.base_prefix)),str(Path(os.readlink(venv/'bin/python')).parent.parent),str(venv)]):command+=['--ro-bind',path,path]
                if Path('/etc/ld.so.cache').exists():command+=['--ro-bind','/etc/ld.so.cache','/etc/ld.so.cache']
                command+=['--proc','/proc','--dev','/dev','--tmpfs','/tmp','--dir','/home/cad','--ro-bind',str(input_dir),'/input','--ro-bind',str(worker),'/worker.py','--ro-bind',str(worker.with_name('topology_worker.py')),'/topology_worker.py','--bind',str(output_dir),'/work','--chdir','/work']
                command+=['--ro-bind',str(worker.with_name('intact_lattice.py')),'/intact_lattice.py']
                for name,value in {'PATH':'/usr/bin:/bin','HOME':'/home/cad','PYTHONNOUSERSITE':'1','PYTHONDONTWRITEBYTECODE':'1','OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','PYTHONUNBUFFERED':'1'}.items():command+=['--setenv',name,value]
                command += [str(venv/'bin/python'),'/worker.py']
                log=folder/'worker.log'
                try:
                    with log.open('wb') as output:
                        process=subprocess.Popen(command,stdout=output,stderr=subprocess.STDOUT,start_new_session=True,env={'PATH':'/usr/bin:/bin'})
                        deadline=time.monotonic()+self.timeout
                        while process.poll() is None:
                            if cancel_event and cancel_event.is_set() or time.monotonic()>deadline:
                                os.killpg(process.pid,signal.SIGKILL);process.wait()
                                raise ProgramBuildError('CAD build cancelled.' if cancel_event and cancel_event.is_set() else 'CAD program exceeded its wall-clock limit. Simplify the operation; the previous model was preserved.')
                            time.sleep(.05)
                except OSError as exc:raise ProgramBuildError('The isolated CAD worker could not start.') from exc
                if process.returncode:
                    if (output_dir/'error.json').exists():error=json.loads((output_dir/'error.json').read_text());detail=error['detail']+'\n'+error.get('traceback','')
                    else:detail=log.read_text(errors='replace')[-2500:]
                    raise ProgramBuildError('CAD program failed validation: '+detail[-3500:])
                if not (output_dir/'manifest.json').is_file():raise ProgramBuildError('Worker output manifest is missing.')
                report=json.loads((output_dir/'manifest.json').read_text())
                expected=('manifest.json','model.stl','mesh.json','topology.json','model.glb','model.3mf')
                if report.get('engine')!='implicit_mesh':expected+=('model.step',)
                for filename in expected:
                    path=output_dir/filename
                    if not path.is_file() or path.is_symlink() or path.stat().st_size>64*1024*1024:raise ProgramBuildError('Worker output is missing or exceeds its artifact limit.')
                report=json.loads((output_dir/'manifest.json').read_text());(output_dir/'program.py').write_text(executable_source(source,parameters,'stl' if asset_id and asset_name=='input.stl' else asset_id is not None))
                report['artifact_id']=key;report['asset_id']=asset_id;
                if asset_id:shutil.copyfile(input_dir/asset_name,output_dir/asset_name);report['asset_name']=asset_name
                report['sha256']={p.name:sha256(p.read_bytes()).hexdigest() for p in output_dir.iterdir() if p.is_file() and p.name!='manifest.json'}
                (output_dir/'manifest.json').write_text(json.dumps(report,allow_nan=False))
                if target.exists():target.rename(self.root/('stale-'+key+'-'+str(time.monotonic_ns())))
                output_dir.rename(target)
                return {**report,'cached':False}
