"""Freeze and stage the installed, tested runtime dependencies for Windows."""
import argparse
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import subprocess
import sys
import tomllib
import urllib.request
import zipfile
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--stage',type=Path,required=True)
args=parser.parse_args()
repo=Path(__file__).resolve().parents[1]
project=tomllib.loads((repo/'backend/pyproject.toml').read_text())['project']
queue=[Requirement(value) for value in project['dependencies']+project['optional-dependencies']['cad']]
selected={};visited=set()
while queue:
    requirement=queue.pop()
    if requirement.marker and not requirement.marker.evaluate():continue
    name=canonicalize_name(requirement.name)
    key=(name,tuple(sorted(requirement.extras)))
    if key in visited:continue
    visited.add(key)
    dist=metadata.distribution(requirement.name)
    assert dist.version in requirement.specifier,(name,dist.version,str(requirement.specifier))
    selected[name]=dist.version
    for value in dist.requires or []:
        child=Requirement(value)
        if child.marker and not any(child.marker.evaluate({'extra':extra}) for extra in ('',*requirement.extras)):continue
        # Markers were evaluated with the requesting dependency's extras.
        child.marker=None
        queue.append(child)
server=args.stage/'server';server.mkdir(parents=True,exist_ok=True)
lock=server/'requirements-windows.txt'
lock.write_text(''.join(f'{name}=={version}\n' for name,version in sorted(selected.items())))
target=server/'dependencies'
subprocess.run([sys.executable,'-m','pip','--isolated','install','--disable-pip-version-check','--index-url','https://pypi.org/simple','--only-binary=:all:','--no-deps','--target',str(target),'--report',str(server/'pip-install-report.json'),'-r',str(lock)],check=True)
# pip --target can omit a wheel's prefix-relative data files. Gmsh's native
# library lives outside purelib in a normal installation; place its unmodified
# DLL alongside gmsh.py, one of its documented native-library search paths.
report=json.loads((server/'pip-install-report.json').read_text())
gmsh=next(item for item in report['install'] if item['metadata']['name'].lower()=='gmsh')
cache=args.stage.parent/'downloads';cache.mkdir(exist_ok=True)
wheel=cache/'gmsh-4.15.0-windows.whl'
if not wheel.is_file():urllib.request.urlretrieve(gmsh['download_info']['url'],wheel)
assert hashlib.sha256(wheel.read_bytes()).hexdigest()==gmsh['download_info']['archive_info']['hashes']['sha256']
with zipfile.ZipFile(wheel) as archive:
    member=next(name for name in archive.namelist() if name.endswith('gmsh-4.15.dll'))
    (target/'gmsh-4.15.dll').write_bytes(archive.read(member))
print(json.dumps({'runtime_distributions':len(selected),'target':str(target)}))
