"""Bounded background work with persistent status, explicit errors and cancellation."""
import asyncio, json, sqlite3, threading, time, uuid
from pathlib import Path

class Jobs:
    def __init__(self,path:Path):
        self.path=path;path.parent.mkdir(parents=True,exist_ok=True);self.tasks={};self.cancels={}
        with self.db() as c:
            c.execute('CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,status TEXT,payload TEXT,updated REAL)')
            c.execute("UPDATE jobs SET status='failed',payload=?,updated=? WHERE status IN ('queued','running')",(json.dumps({'error':'The service restarted before this job finished. Please retry.'}),time.time()))
    def db(self):return sqlite3.connect(self.path,timeout=10)
    def save(self,key,status,payload):
        with self.db() as c:c.execute('INSERT OR REPLACE INTO jobs VALUES(?,?,?,?)',(key,status,json.dumps(payload,allow_nan=False),time.time()))
    def get(self,key):
        with self.db() as c:r=c.execute('SELECT status,payload,updated FROM jobs WHERE id=?',(key,)).fetchone()
        if not r:raise KeyError('Job not found.')
        return {'id':key,'status':r[0],**json.loads(r[1]),'updated_at':r[2]}
    def create(self,run):
        if sum(not task.done() for task in self.tasks.values())>=4:raise ValueError('The job queue is full. Wait for an active build to finish.')
        key=uuid.uuid4().hex;cancel=threading.Event();self.cancels[key]=cancel;self.save(key,'queued',{'progress':[]})
        async def work():
            events=[]
            def progress(event):
                events.append({**event,'at':time.time()});self.save(key,'running',{'progress':events[-40:]})
            try:
                self.save(key,'running',{'progress':[]})
                result=await asyncio.wait_for(run(progress,cancel),timeout=240)
                if cancel.is_set():self.save(key,'cancelled',{'progress':events[-40:]})
                else:self.save(key,'succeeded',{'result':result,'progress':events[-40:]})
            except asyncio.CancelledError:self.save(key,'cancelled',{'progress':events[-40:]})
            except TimeoutError:self.save(key,'failed',{'error':'The build reached its four-minute job limit. The previous model was preserved.','progress':events[-40:]})
            except Exception as exc:self.save(key,'failed',{'error':str(exc)[:2000],'progress':events[-40:]})
            finally:cancel.set();self.cancels.pop(key,None);self.tasks.pop(key,None)
        self.tasks[key]=asyncio.create_task(work());return self.get(key)
    def cancel(self,key):
        current=self.get(key)
        if current['status'] in ('succeeded','failed','cancelled'):return current
        event=self.cancels.get(key)
        if event:event.set()
        task=self.tasks.get(key)
        if task:task.cancel()
        self.save(key,'cancelled',{'progress':current.get('progress',[])})
        return self.get(key)
