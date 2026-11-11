# SPDX-License-Identifier: Apache-2.0
"""Prepare the few Gmsh shared libraries inside the private virtual environment."""
import hashlib,json,os,shutil,subprocess,sys,tempfile,urllib.request,uuid
from pathlib import Path
root=Path.home()/'.local/share/intact-simulation';runtime=root/'runtime';target=runtime/'.venv/intact-native-libs';target.mkdir(exist_ok=True)
bundle=root/'freecad-1.1.4/squashfs-root/usr/lib'
def copy_atomic(source,destination):
 data=source.read_bytes()
 if destination.is_file() and hashlib.sha256(destination.read_bytes()).digest()==hashlib.sha256(data).digest():return
 temporary=destination.with_name(destination.name+'.'+uuid.uuid4().hex+'.tmp');temporary.write_bytes(data);temporary.replace(destination)
for name in ('libGLU.so.1','libOpenGL.so.0','libGLdispatch.so.0'):copy_atomic((bundle/name).resolve(),target/name)
sha='2f1f300e21c97023e0a8418d68e5eba095d2c5872ceab740f5d70278d94284fd';url='https://archive.ubuntu.com/ubuntu/pool/main/x/xft/libxft2_2.3.4-1_amd64.deb'
cache=root/'native-library-downloads';cache.mkdir(exist_ok=True);package=cache/'libxft2_2.3.4-1_amd64.deb'
if not package.is_file() or hashlib.sha256(package.read_bytes()).hexdigest()!=sha:
 with urllib.request.urlopen(url,timeout=60) as response:package.write_bytes(response.read(1024*1024))
if hashlib.sha256(package.read_bytes()).hexdigest()!=sha:raise RuntimeError('libXft checksum verification failed.')
with tempfile.TemporaryDirectory() as tmp:
 subprocess.run(['dpkg-deb','-x',str(package),tmp],check=True);copy_atomic((Path(tmp)/'usr/lib/x86_64-linux-gnu/libXft.so.2').resolve(),target/'libXft.so.2');copy_atomic(Path(tmp)/'usr/share/doc/libxft2/copyright',target/'libXft-copyright')
(target/'PROVENANCE.json').write_text(json.dumps({'libXft':{'url':url,'sha256':sha},'GL_libraries':'Checksum-verified installed FreeCAD 1.1.4 bundle; preserve its original notices.'},indent=2))
subprocess.run([str(runtime/'.venv/bin/python'),'-c','import gmsh,skfem,manifold3d,meshio,reportlab;print("Engineering runtime ready: Gmsh",gmsh.__version__,"scikit-fem",skfem.__version__)'],env={**os.environ,'LD_LIBRARY_PATH':str(target)},check=True)
