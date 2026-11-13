"""Update the local ChatGPT plugin to an already verified Windows engine."""
import datetime
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile
from plugin_archive_limits import validate_archive

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--package',type=Path,help='Install a validated local-runtime loader ZIP instead of the offline engine launcher')
parser.add_argument('--local-revision',help='Semver build suffix to force a new host cache, e.g. local.1; runtime version is unchanged')
args=parser.parse_args()

if os.name!='nt':raise SystemExit('This installer is for native Windows.')
repo=Path(__file__).resolve().parents[1]
home=Path.home();managed=Path(os.environ['LOCALAPPDATA'])/'IntactSimulation'
engine=managed/'Desktop/0.20.0'
receipt=json.loads((engine/'engine-installation.json').read_text())
if receipt.get('version')!='0.20.0':raise SystemExit('Install the verified Windows engine first.')
python=engine/'server/python/python.exe'
folder=home/'.codex/plugins/intact-simulation'
backup=managed/'install-backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
backup.mkdir(parents=True)
if folder.exists():shutil.copytree(folder,backup/'intact-simulation',ignore=shutil.ignore_patterns('__pycache__'))
if args.package:
    validate_archive(args.package)
    with zipfile.ZipFile(args.package) as archive:archive.extractall(folder)
    # Portable commands must be contained ./ paths, not absolute paths. The
    # host expands PLUGIN_ROOT in arguments when it loads the installed copy.
else:
    shutil.copytree(repo/'plugin',folder,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
    entry={'command':str(python),'args':['-B',str(engine/'server/launch.py')]}
    (folder/'mcp.json').write_text(json.dumps({'$schema':'https://agent-plugins.org/schemas/1.0.0/mcp.schema.json','mcpServers':{'intact':{'type':'stdio',**entry}}},indent=2))
    (folder/'.mcp.json').write_text(json.dumps({'mcpServers':{'intact':{**entry,'startup_timeout_sec':300}}},indent=2))
if args.local_revision:
    import re
    if not re.fullmatch(r'[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*',args.local_revision):raise SystemExit('Invalid semver build suffix')
    for name in ('plugin.json','.codex-plugin/plugin.json'):
        path=folder/name;record=json.loads(path.read_text())
        record['version']=record['version'].split('+')[0]+'+'+args.local_revision
        path.write_text(json.dumps(record,indent=2))
version=json.loads((folder/'plugin.json').read_text())['version']
print(json.dumps({'local_source':str(folder),'version':version,'runtime':'native Windows','backup':str(backup)}),flush=True)
result=subprocess.run([str(engine/'server/client/bin/codex.exe'),'plugin','add','intact-simulation@intact-local','--json'])
if result.returncode:
    raise SystemExit('Host registration failed; source and backup are preserved. Retry with a new --local-revision to avoid a loaded cache directory.')
