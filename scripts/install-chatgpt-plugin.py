"""Install/update this private plugin from WSL/Linux, without model credentials.

Example: python3 scripts/install-chatgpt-plugin.py --windows-home /mnt/c/Users/User
Requires uv and a working bubblewrap installation on the Linux host.
"""
import argparse, json, os, re, shutil, subprocess,sys
from pathlib import Path

repo=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--with-picogk',action='store_true',help='Install the optional pinned PicoGK Linux TPMS bridge')
parser.add_argument('--windows-home',type=Path)
parser.add_argument('--distro',default=os.environ.get('WSL_DISTRO_NAME','Ubuntu-22.04'))
args=parser.parse_args()
subprocess.run([sys.executable,str(repo/'scripts/install-freecad.py')],check=True)
uv=shutil.which('uv') or str(Path.home()/'.local/bin/uv')
runtime=Path.home()/'.local/share/intact-simulation/runtime'
runtime.mkdir(parents=True,exist_ok=True)
shutil.copy2(repo/'LICENSE-PRIORITY1.txt',runtime/'LICENSE-PRIORITY1.txt')
shutil.copy2(repo/'docs/PRIORITY1_OPEN_SOURCE.md',runtime/'PRIORITY1_OPEN_SOURCE.md')
shutil.copy2(repo/'docs/PRIORITY23_OPEN_SOURCE.md',runtime/'PRIORITY23_OPEN_SOURCE.md')
shutil.copy2(repo/'plugin/skills/intact-cad/references/structured-modeling.md',runtime/'structured-modeling.md')
shutil.copy2(repo/'plugin/skills/intact-cad/references/priority23.md',runtime/'priority23.md')
shutil.copy2(repo/'plugin/skills/intact-cad/references/simulation.md',runtime/'simulation.md')
for filename in ('pyproject.toml','uv.lock'):shutil.copy2(repo/'backend'/filename,runtime/filename)
shutil.copytree(repo/'backend/intact_backend',runtime/'intact_backend',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
for obsolete in ('agent.py','codex_transport.py','model_connection.py','edit_jobs.py','motion_worker.py'):
    (runtime/'intact_backend'/obsolete).unlink(missing_ok=True)
    for cached in (runtime/'intact_backend/__pycache__').glob(obsolete[:-3]+'.*.pyc'):cached.unlink()
subprocess.run([uv,'sync','--project',str(runtime),'--extra','cad','--frozen'],check=True)
runtime_python=str(runtime/'.venv/bin/python')
if args.with_picogk:subprocess.run([sys.executable,str(repo/'scripts/install-picogk.py')],check=True)
subprocess.run([sys.executable,str(repo/'scripts/install-engineering-runtime.py')],check=True)
subprocess.run([runtime_python,str(repo/'scripts/install-project-tools.py')],check=True)
subprocess.run([runtime_python,'-m','playwright','install','chromium'],check=True)

def backup(path):
    target=path.with_name(path.name+'.intact-backup')
    if path.exists() and not target.exists():shutil.copy2(path,target)

def install(home,windows=False):
    folder=home/'.codex/plugins/intact-simulation'
    shutil.copytree(repo/'plugin',folder,dirs_exist_ok=True)
    shutil.copy2(repo/'LICENSE-PRIORITY1.txt',folder/'LICENSE-PRIORITY1.txt')
    shutil.copy2(repo/'docs/PRIORITY1_OPEN_SOURCE.md',folder/'PRIORITY1_OPEN_SOURCE.md')
    shutil.copy2(repo/'docs/PRIORITY23_OPEN_SOURCE.md',folder/'PRIORITY23_OPEN_SOURCE.md')
    server={'command':runtime_python,'args':['-m','intact_backend.mcp_server']}
    if windows:server={'command':'wsl.exe','args':['--distribution',args.distro,'--user',Path.home().name,'--exec',server['command'],*server['args']]}
    portable=server if windows else {'command':'./server/launch.sh','args':[]}
    (folder/'mcp.json').write_text(json.dumps({'$schema':'https://agent-plugins.org/schemas/1.0.0/mcp.schema.json','mcpServers':{'intact':{'type':'stdio',**portable}}},indent=2))
    (folder/'.mcp.json').write_text(json.dumps({'mcpServers':{'intact':{**server,'startup_timeout_sec':300}}},indent=2))
    catalog=home/'.agents/plugins/marketplace.json';catalog.parent.mkdir(parents=True,exist_ok=True)
    backup(catalog)
    market=json.loads(catalog.read_text()) if catalog.exists() else {'name':'intact-local','interface':{'displayName':'Intact Simulation · Local'},'plugins':[]}
    market['plugins']=[p for p in market['plugins'] if p['name']!='intact-simulation']
    market['plugins'].append({'name':'intact-simulation','source':{'source':'local','path':'./.codex/plugins/intact-simulation'},'policy':{'installation':'AVAILABLE','authentication':'ON_INSTALL'},'category':'Productivity'})
    catalog.write_text(json.dumps(market,indent=2))
    version=json.loads((folder/'plugin.json').read_text())['version']
    for suffix in ('local',version):shutil.copytree(folder,home/'.codex/plugins/cache'/market['name']/'intact-simulation'/suffix,dirs_exist_ok=True)
    config=home/'.codex/config.toml';config.parent.mkdir(parents=True,exist_ok=True);backup(config)
    text=config.read_text() if config.exists() else ''
    section='[plugins."intact-simulation@'+market['name']+'"]'
    match=re.search(re.escape(section)+r'([^\[]*)',text)
    if match:
        body=match[1]
        body=re.sub(r'(?m)^enabled\s*=.*$', 'enabled = true',body) if re.search(r'(?m)^enabled\s*=',body) else '\nenabled = true\n'+body
        text=text[:match.start(1)]+body+text[match.end(1):]
    else:text+='\n'+section+'\nenabled = true\n'
    config.write_text(text)
    print('Installed private plugin in '+str(folder))

install(Path.home())
if args.windows_home:install(args.windows_home,True)
# Refresh only our own background viewer after updating its Python modules. Its
# persisted token/port let existing browser tabs reconnect at the same URL.
subprocess.run([runtime_python,'-c','''
import os,signal,time
from pathlib import Path
from intact_backend.viewer_server import live_session,ensure_viewer
root=Path.home()/'.local/share/intact-studio'
entry=live_session(root)
if entry:
    command=Path('/proc')/str(entry['pid'])/'cmdline'
    args=command.read_bytes().split(b'\\0') if command.exists() else []
    if b'intact_backend.viewer_server' in args and str(root).encode() in args:
        os.kill(entry['pid'],signal.SIGTERM)
        for _ in range(50):
            if not live_session(root):break
            time.sleep(.1)
        ensure_viewer(root)
'''],check=True)
print('Restart ChatGPT desktop and select Intact Simulation from the personal plugin marketplace.')
