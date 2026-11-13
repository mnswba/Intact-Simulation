"""Install the checksum-pinned official portable FreeCAD Windows runtime."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.request

VERSION='1.1.4'
SHA='4828741fc91ee37fafcdb97a1abacb18b04ba451ac4372d9ff7a7349b36f4d6d'
URL='https://github.com/FreeCAD/FreeCAD/releases/download/1.1.4/FreeCAD_1.1.4-Windows-x86_64-py311.7z'


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        while block:=stream.read(1024**2):h.update(block)
    return h.hexdigest()


def main():
    if os.name!='nt':raise RuntimeError('Use the Linux FreeCAD installer on Linux.')
    base=Path(os.environ['LOCALAPPDATA'])/'IntactSimulation'
    cache=base/'downloads';cache.mkdir(parents=True,exist_ok=True)
    archive=cache/'FreeCAD_1.1.4-Windows-x86_64-py311.7z'
    if not archive.is_file() or digest(archive)!=SHA:
        print('Downloading official Windows FreeCAD 1.1.4 portable runtime…',flush=True)
        temporary=archive.with_suffix('.partial')
        urllib.request.urlretrieve(URL,temporary)
        if digest(temporary)!=SHA:raise RuntimeError('FreeCAD SHA256 verification failed.')
        temporary.replace(archive)
    target=base/'freecad-1.1.4';target.mkdir(exist_ok=True)
    metadata=target/'installation.json'
    if not metadata.is_file():
        extractor=cache/'7zr.exe'
        extractor_sha='256feca8e274e5da655e2a284fabafd9f554365eb164862089dacd4e8276d282'
        if not extractor.is_file():urllib.request.urlretrieve('https://www.7-zip.org/a/7zr.exe',extractor)
        if digest(extractor)!=extractor_sha:raise RuntimeError('7-Zip extractor checksum mismatch; update its verified pin before continuing.')
        subprocess.run([str(extractor),'x',str(archive),'-o'+str(target),'-y'],check=True,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
        python=next(target.glob('*/bin/python.exe'),None)
        if python is None and (target/'bin/python.exe').is_file():python=target/'bin/python.exe'
        if python is None:raise RuntimeError('Portable FreeCAD Python executable is missing.')
        metadata.write_text(json.dumps({'version':VERSION,'sha256':SHA,'source':URL,'root':str(python.parent.parent)},indent=2),encoding='utf-8')
    print('Verified Windows FreeCAD runtime: '+json.loads(metadata.read_text())['root'],flush=True)


if __name__=='__main__':main()
