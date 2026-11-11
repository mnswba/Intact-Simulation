"""Build the pinned GNU LibreDWG command-line tools locally; no binaries in Git."""
import hashlib,json,os,shutil,subprocess,tarfile,urllib.request
from pathlib import Path
VERSION='0.14';SHA='62ebb73b984f865960f20ed26619ea5f8789d5e3fd088fa40a2598384da81275';URL=f'https://ftp.gnu.org/gnu/libredwg/libredwg-{VERSION}.tar.xz'
def main():
 base=Path.home()/'.local/share/intact-simulation';target=base/('libredwg-'+VERSION);metadata=target/'installation.json'
 if metadata.exists() and (target/'bin/dwgwrite').exists() and json.loads(metadata.read_text()).get('sha256')==SHA:print('Verified GNU LibreDWG '+VERSION+' is already installed.');return
 if not all(shutil.which(tool) for tool in ('gcc','make')):raise RuntimeError('DWG export needs gcc and make. Install build-essential, then rerun scripts/install-project-tools.py.')
 work=base/'libredwg-build';work.mkdir(parents=True,exist_ok=True);archive=work/f'libredwg-{VERSION}.tar.xz'
 if not archive.exists():
  with urllib.request.urlopen(URL,timeout=90) as response:archive.write_bytes(response.read(32*1024*1024))
 if hashlib.sha256(archive.read_bytes()).hexdigest()!=SHA:raise ValueError('LibreDWG source checksum mismatch.')
 source=work/f'libredwg-{VERSION}'
 if not (source/'configure').exists():
  with tarfile.open(archive) as stream:stream.extractall(work,filter='data')
 with (work/'build.log').open('w') as log:
  print('Building verified GNU LibreDWG '+VERSION+' for DWG export…',flush=True)
  subprocess.run(['./configure','--disable-shared','--disable-bindings','--disable-docs','--disable-python','--prefix='+str(target)],cwd=source,env={**os.environ,'CFLAGS':'-O0'},stdout=log,stderr=log,check=True)
  subprocess.run(['make','-j2'],cwd=source/'src',stdout=log,stderr=log,check=True)
  subprocess.run(['make','-j2','dwgwrite','dwgread'],cwd=source/'programs',stdout=log,stderr=log,check=True)
 (target/'bin').mkdir(parents=True,exist_ok=True)
 for name in ('dwgwrite','dwgread'):shutil.copy2(source/'programs'/name,target/'bin'/name)
 shutil.copy2(source/'COPYING',target/'COPYING')
 metadata.write_text(json.dumps({'version':VERSION,'sha256':SHA,'source':URL,'license':'GPL-3.0-or-later'},indent=2))
 print('Installed GNU LibreDWG '+VERSION+' (DWG write/read tools).')
if __name__=='__main__':main()
