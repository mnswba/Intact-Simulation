"""Per-user runtime setup and stdio MCP; never a publisher-hosted CAD service."""
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import threading
import urllib.request
from .platform_support import background_options, file_lock

FREECAD_URL='https://github.com/FreeCAD/FreeCAD/releases/download/1.1.4/FreeCAD_1.1.4-Windows-x86_64-py311.7z'
FREECAD_SHA='4828741fc91ee37fafcdb97a1abacb18b04ba451ac4372d9ff7a7349b36f4d6d'
EXTRACTOR_URL='https://www.7-zip.org/a/7zr.exe'
EXTRACTOR_SHA='256feca8e274e5da655e2a284fabafd9f554365eb164862089dacd4e8276d282'
CLIENT_URL='https://github.com/openai/codex/releases/download/rust-v0.167.2/codex-package-x86_64-pc-windows-msvc.tar.gz'
CLIENT_SHA='20b0f94105f40b617bf209b1679b8674ab6d3d8f303e767ae43cf1860a8705da'

def digest(path):
    value=sha256()
    with Path(path).open('rb') as stream:
        while block:=stream.read(1024**2):value.update(block)
    return value.hexdigest()

def download(url,target,expected):
    target=Path(target)
    if target.is_file() and digest(target)==expected:return target
    partial=target.with_name(target.name+'.partial')
    urllib.request.urlretrieve(url,partial)
    if digest(partial)!=expected:raise ValueError('Downloaded runtime checksum mismatch: '+target.name)
    partial.replace(target);return target

def freecad(base):
    target=base/'freecad-1.1.4';metadata=target/'installation.json'
    if metadata.is_file():
        record=json.loads(metadata.read_text());root=Path(record['root'])
        if record.get('version')=='1.1.4' and record.get('sha256')==FREECAD_SHA and (root/'bin/python.exe').is_file():return root
    cache=base/'downloads';cache.mkdir(parents=True,exist_ok=True)
    archive=download(FREECAD_URL,cache/'FreeCAD_1.1.4-Windows-x86_64-py311.7z',FREECAD_SHA)
    extractor=download(EXTRACTOR_URL,cache/'7zr.exe',EXTRACTOR_SHA)
    target.mkdir(exist_ok=True)
    subprocess.run([str(extractor),'x',str(archive),'-o'+str(target),'-y'],check=True,stdout=subprocess.DEVNULL,stderr=sys.stderr,**background_options())
    python=next(target.glob('*/bin/python.exe'),None)
    if python is None:raise RuntimeError('The pinned FreeCAD Python executable is missing.')
    root=python.parent.parent
    metadata.write_text(json.dumps({'version':'1.1.4','sha256':FREECAD_SHA,'source':FREECAD_URL,'root':str(root)},indent=2))
    return root

def openai_client(base):
    from .ask_ai import client_path
    existing=client_path()
    if existing:return Path(existing)
    if os.environ.get('INTACT_CODEX_CLI'):raise ValueError('The configured INTACT_CODEX_CLI executable is unavailable.')
    target=base/'codex-0.167.2';binary=target/'bin/codex.exe';marker=target/'runtime-sha256.txt'
    if binary.is_file() and marker.is_file() and marker.read_text()==CLIENT_SHA:return binary
    cache=base/'downloads';cache.mkdir(parents=True,exist_ok=True)
    archive=download(CLIENT_URL,cache/'codex-0.167.2-windows.tar.gz',CLIENT_SHA)
    target.mkdir(exist_ok=True)
    with tarfile.open(archive,'r:gz') as bundle:bundle.extractall(target,filter='data')
    if not binary.is_file():raise RuntimeError('The pinned OpenAI client executable is missing.')
    marker.write_text(CLIENT_SHA);return binary

class DesktopSetup:
    def __init__(self,base):
        self.base=Path(base);self.finished=threading.Event();self.stage='waiting';self.error=None
    def status(self):return {'ready':self.finished.is_set() and self.error is None,'stage':self.stage,'error':self.error,'execution':'user_windows_computer','hosted_cad':False}
    def start(self):threading.Thread(target=self.prepare,daemon=True,name='intact-desktop-setup').start()
    def prepare(self):
        try:
            self.base.mkdir(parents=True,exist_ok=True)
            with (self.base/'desktop-setup.lock').open('a') as guard:
                file_lock.flock(guard,file_lock.LOCK_EX)
                self.stage='Preparing local FreeCAD 1.1.4'
                os.environ['INTACT_FREECAD_ROOT']=str(freecad(self.base))
                self.stage='Checking the local headless browser'
                from playwright.sync_api import sync_playwright
                with sync_playwright() as browser:
                    browser_exists=Path(browser.chromium.executable_path).is_file()
                if not browser_exists:
                    subprocess.run([sys.executable,'-m','playwright','install','chromium'],check=True,stdout=sys.stderr,stderr=sys.stderr,**background_options())
                self.stage='Preparing the local OpenAI client'
                os.environ['INTACT_CODEX_CLI']=str(openai_client(self.base))
                self.stage='ready'
        except BaseException as error:
            self.error=str(error);self.stage='failed'
            print('Intact desktop setup failed: '+str(error),file=sys.stderr,flush=True)
        finally:self.finished.set()
    def wait(self):
        self.finished.wait()
        if self.error:raise RuntimeError('Local Intact setup failed: '+self.error)

def main():
    if sys.platform!='win32':raise SystemExit('This Intact desktop package supports Windows x86-64.')
    base=Path(os.environ.get('INTACT_DESKTOP_HOME',str(Path(os.environ['LOCALAPPDATA'])/'IntactSimulation')))
    os.environ.setdefault('INTACT_STATE_DIR',str(base/'projects'))
    from .mcp_server import IntactMCP,create_server
    setup=DesktopSetup(base);setup.start()
    class DesktopEngine(IntactMCP):
        def _call(self,name,args,cancel_event=None):
            if name=='status':return {**super()._call(name,args,cancel_event),'desktop_setup':setup.status()}
            setup.wait();return super()._call(name,args,cancel_event)
        def viewer(self,key,revision=None):
            setup.wait();return super().viewer(key,revision)
    create_server(DesktopEngine()).run(transport='stdio')
