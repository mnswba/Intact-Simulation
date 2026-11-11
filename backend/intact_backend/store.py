"""SQLite records immutable spec versions and numerical cache keys."""
import json, sqlite3
from pathlib import Path
from .spec import DesignSpec
class Store:
    def __init__(self,path:Path):
        path.parent.mkdir(parents=True,exist_ok=True);self.path=path
        with self.connect() as c:
            c.execute('CREATE TABLE IF NOT EXISTS versions(project TEXT, hash TEXT, revision INTEGER, spec TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(project,hash))')
            c.execute('CREATE TABLE IF NOT EXISTS results(hash TEXT PRIMARY KEY, result TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)')
    def connect(self):return sqlite3.connect(self.path,timeout=10)
    def save(self,project:str,spec:DesignSpec):
        with self.connect() as c:c.execute('INSERT OR IGNORE INTO versions(project,hash,revision,spec) VALUES(?,?,?,?)',(project,spec.content_hash(),spec.revision,spec.model_dump_json()))
    def history(self,project:str):
        with self.connect() as c:return [dict(hash=r[0],revision=r[1],created_at=r[2]) for r in c.execute('SELECT hash,revision,created_at FROM versions WHERE project=? ORDER BY rowid DESC LIMIT 100',(project,))]
    def load(self,project:str,key:str):
        with self.connect() as c:r=c.execute('SELECT spec FROM versions WHERE project=? AND hash=?',(project,key)).fetchone()
        if not r:raise KeyError('Spec version not found.')
        return DesignSpec.model_validate_json(r[0])
    def result(self,key:str):
        with self.connect() as c:r=c.execute('SELECT result FROM results WHERE hash=?',(key,)).fetchone()
        return json.loads(r[0]) if r else None
    def save_result(self,key:str,result:dict):
        with self.connect() as c:c.execute('INSERT OR REPLACE INTO results(hash,result) VALUES(?,?)',(key,json.dumps(result,allow_nan=False)))
