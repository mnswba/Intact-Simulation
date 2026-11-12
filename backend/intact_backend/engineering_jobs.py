# SPDX-License-Identifier: Apache-2.0
"""Durable detached engineering jobs with cancellation and bounded concurrency."""
import argparse,json,os,re,signal,subprocess,sys,threading,time,uuid
from pathlib import Path
from .projects import ProjectService,atomic_json
OPS={'adaptive','simulate','optimize','convert','manufacture','drawing','freeform','sheet','lattice','hybrid','assembly','reconstruct'}
def update(projects,key,**fields):
 import fcntl
 p=path(projects,key)
 with p.with_suffix('.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);r=json.loads(p.read_text());r.update(fields);atomic_json(p,r);return r
def path(projects,key):
 if not isinstance(key,str) or not re.fullmatch('[a-f0-9]{32}',key):raise ValueError('Invalid engineering job id.')
 return projects.root/'engineering-jobs'/(key+'.json')
def status(projects,key,model_id=None):
 p=path(projects,key)
 if not p.is_file():raise ValueError('Engineering job not found.')
 r=json.loads(p.read_text())
 if model_id and r.get('model_id')!=model_id:raise ValueError('Job belongs to another model.')
 if r['status'] in ('queued','running') and r.get('pid'):
  try:
   cmd=(Path('/proc')/str(r['pid'])/'cmdline').read_bytes();alive=b'intact_backend.engineering_jobs' in cmd
  except OSError:alive=False
  if not alive:
   import fcntl
   with p.with_suffix('.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX);r=json.loads(p.read_text())
    if r['status'] in ('queued','running'):r.update(status='failed',error='The engineering worker ended before completion. Completed artifacts remain available.');atomic_json(p,r)
 return r
def submit(projects,operation,settings,model_id=None):
 if operation not in OPS:raise ValueError('Unsupported engineering job operation.')
 if not isinstance(settings,dict):raise ValueError('Settings must be an object.')
 if model_id:record=projects.load(model_id)
 jobs=projects.root/'engineering-jobs';jobs.mkdir(exist_ok=True)
 import fcntl
 with (jobs/'queue.lock').open('a') as gate:
  fcntl.flock(gate,fcntl.LOCK_EX)
  if sum(status(projects,p.stem)['status'] in ('queued','running') for p in jobs.glob('*.json'))>=3:raise ValueError('Three engineering jobs are already active.')
  key=uuid.uuid4().hex;r={'job_id':key,'operation':operation,'settings':settings,'model_id':model_id,'input_revision':record['spec']['revision'] if model_id else None,'status':'queued','progress':'Queued','cancel_requested':False,'created_at':time.time()};atomic_json(path(projects,key),r)
  with (jobs/'workers.log').open('ab') as output:process=subprocess.Popen([sys.executable,'-m','intact_backend.engineering_jobs','--state-dir',str(projects.root),'--job-id',key],stdin=subprocess.DEVNULL,stdout=output,stderr=output,start_new_session=True)
  # A fast worker can update the job before this parent returns; only add PID.
  current=update(projects,key,pid=process.pid)
 return current
def cancel(projects,key,model_id=None):
 r=status(projects,key,model_id)
 if r['status'] not in ('queued','running'):return r
 return update(projects,key,cancel_requested=True)

def run(projects,key):
 from .advanced import Advanced
 p=path(projects,key);r=json.loads(p.read_text());stop=threading.Event();cancel_event=threading.Event();deadline=time.monotonic()+900
 def watch():
  while not stop.wait(.2):
   if json.loads(p.read_text()).get('cancel_requested') or time.monotonic()>deadline:cancel_event.set();return
 threading.Thread(target=watch,daemon=True).start()
 try:
  update(projects,key,status='running',progress='Running isolated '+r['operation']);a=Advanced(projects);op=r['operation'];settings=r['settings'];model_id=r['model_id']
  if json.loads(p.read_text()).get('cancel_requested'):cancel_event.set();raise ValueError('Job cancelled before execution.')
  if op in ('simulate','optimize','hybrid','assembly','manufacture','drawing','convert') and not model_id:raise ValueError('This operation requires model_id.')
  if model_id and projects.load(model_id)['spec']['revision']!=r['input_revision']:raise ValueError('The model changed while this job was queued.')
  if op in ('hybrid','assembly'):result=getattr(a,op)(model_id,settings,expected_revision=r['input_revision'],cancel=cancel_event)
  elif op in ('simulate','optimize','manufacture'):result=getattr(a,op)(model_id,settings,cancel=cancel_event)
  elif op in ('adaptive','lattice','freeform','sheet','reconstruct'):result=getattr(a,op)(settings,cancel=cancel_event)
  elif op=='convert':result=a.convert(model_id,settings.get('maximum_faces',4000),cancel_event)
  elif op=='drawing':result=a.drawing(model_id,settings['part_id'],settings.get('title','Engineering drawing'),settings.get('tolerance_note',''),cancel_event)
  if cancel_event.is_set() or json.loads(p.read_text()).get('cancel_requested'):cancel_event.set();raise ValueError('Job cancelled or timed out; original designs and completed artifacts remain available.')
  update(projects,key,status='succeeded',progress='Completed',result=result)
 except Exception as exc:update(projects,key,status='cancelled' if cancel_event.is_set() else 'failed',error=str(exc)[:3000],progress='Stopped')
 finally:
  stop.set()

def main():
 p=argparse.ArgumentParser();p.add_argument('--state-dir',type=Path,required=True);p.add_argument('--job-id',required=True);a=p.parse_args();run(ProjectService(a.state_dir),a.job_id)
if __name__=='__main__':main()
