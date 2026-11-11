# SPDX-License-Identifier: Apache-2.0
"""Install the official, SHA256-pinned open-source FreeCAD runtime without root."""
import concurrent.futures,hashlib,json,subprocess,time,urllib.request
from pathlib import Path
VERSION='1.1.4';SIZE=820812280;SHA='f6dc6ba676e5ac96a565ebc8d657232f94c6158e85b4352141bd1a46f6b43434'
URL='https://github.com/FreeCAD/FreeCAD/releases/download/1.1.4/FreeCAD_1.1.4-Linux-x86_64-py311.AppImage'
BASE=Path.home()/'.local/share/intact-simulation';ROOT=BASE/('freecad-'+VERSION);DOWNLOAD=BASE/'freecad-download';APP=DOWNLOAD/('FreeCAD_'+VERSION+'.AppImage');CHUNK=8*1024**2

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        while block:=stream.read(1024**2):h.update(block)
    return h.hexdigest()
def fetch(i):
    start=i*CHUNK;end=min(SIZE,start+CHUNK)-1;p=DOWNLOAD/('chunk-'+str(i))
    if p.exists() and p.stat().st_size==end-start+1:return
    for attempt in range(4):
        try:
            request=urllib.request.Request(URL,headers={'Range':f'bytes={start}-{end}','User-Agent':'Intact-Development'})
            with urllib.request.urlopen(request,timeout=90) as r:
                if r.status!=206 or r.headers.get('Content-Range')!=f'bytes {start}-{end}/{SIZE}':raise ValueError('Release server did not return the requested range.')
                with p.open('wb') as stream:
                    while block:=r.read(262144):stream.write(block)
            if p.stat().st_size!=end-start+1:raise ValueError('Incomplete download.')
            return
        except Exception:
            if attempt==3:raise
            time.sleep(1)
def main():
    metadata=ROOT/'installation.json'
    if metadata.is_file() and (ROOT/'squashfs-root/usr/lib/FreeCAD.so').exists() and json.loads(metadata.read_text()).get('sha256')==SHA:
        print('Verified FreeCAD '+VERSION+' runtime is already installed.');return
    ROOT.mkdir(parents=True,exist_ok=True);DOWNLOAD.mkdir(parents=True,exist_ok=True)
    if not APP.exists() or APP.stat().st_size!=SIZE or digest(APP)!=SHA:
        count=(SIZE+CHUNK-1)//CHUNK
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
            for n,_ in enumerate(pool.map(fetch,range(count)),1):print(f'FreeCAD download {n}/{count}',flush=True)
        with APP.open('wb') as stream:
            for i in range(count):stream.write((DOWNLOAD/('chunk-'+str(i))).read_bytes())
        if digest(APP)!=SHA:raise ValueError('FreeCAD SHA256 verification failed. The runtime was not installed.')
    APP.chmod(0o755)
    if not (ROOT/'squashfs-root/usr/lib/FreeCAD.so').exists():
        with (ROOT/'extraction.log').open('w') as log:subprocess.run([str(APP),'--appimage-extract'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    metadata.write_text(json.dumps({'version':VERSION,'sha256':SHA,'source':URL,'license':'FreeCAD LGPL; see the bundled license/third-party notices','isolated_worker':True},indent=2))
    for p in DOWNLOAD.glob('chunk-*'):p.unlink()
    print('Installed FreeCAD '+VERSION+' from the verified official release.')
if __name__=='__main__':main()
