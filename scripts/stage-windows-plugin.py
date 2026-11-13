"""Assemble the native Windows distribution; never copy user state or profiles."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import urllib.request

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--stage',type=Path,required=True)
args=parser.parse_args()
repo=Path(__file__).resolve().parents[1];stage=args.stage.resolve()
server=stage/'server';server.mkdir(parents=True,exist_ok=True)
assert (server/'python/python.exe').is_file(),'Prepare the verified portable Python first.'
assert (server/'dependencies/build123d').is_dir(),'Prepare the pinned dependencies first.'
ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.log','.git')
def copy_updated(source,target):
    source=Path(source);target=Path(target)
    if target.is_file() and source.stat().st_size==target.stat().st_size and source.stat().st_mtime_ns==target.stat().st_mtime_ns:return str(target)
    return shutil.copy2(source,target)
for name in ('skills','assets'):
    shutil.copytree(repo/'plugin'/name,stage/name,dirs_exist_ok=True,ignore=ignore,copy_function=copy_updated)
shutil.copytree(repo/'backend/intact_backend',server/'runtime/intact_backend',dirs_exist_ok=True,ignore=ignore,copy_function=copy_updated)
managed=Path(os.environ['LOCALAPPDATA'])/'IntactSimulation'
freecad=Path(json.loads((managed/'freecad-1.1.4/installation.json').read_text())['root'])
shutil.copytree(freecad,server/'freecad',dirs_exist_ok=True,ignore=ignore,copy_function=copy_updated)
browser=Path(os.environ['LOCALAPPDATA'])/'ms-playwright/chromium_headless_shell-1254'
shutil.copytree(browser,server/'browsers'/browser.name,dirs_exist_ok=True,ignore=ignore,copy_function=copy_updated)
site=server/'python/Lib/site-packages';site.mkdir(parents=True,exist_ok=True)
shutil.copy2(repo/'scripts/windows-sitecustomize.py',site/'sitecustomize.py')
shutil.copy2(repo/'scripts/windows-launch.py',server/'launch.py')
manifest=json.loads((repo/'plugin/plugin.json').read_text())
manifest['extensions']['com.openai']['onboardingSkill']='./skills/intact-cad/SKILL.md'
(stage/'plugin.json').write_text(json.dumps(manifest,indent=2)+'\n')
mcp={'$schema':'https://agent-plugins.org/schemas/1.0.0/mcp.schema.json','mcpServers':{'intact':{'type':'stdio','command':'${PLUGIN_ROOT}/server/python/python.exe','args':['-X','utf8','${PLUGIN_ROOT}/server/launch.py'],'cwd':'${PLUGIN_ROOT}'}}}
(stage/'mcp.json').write_text(json.dumps(mcp,indent=2)+'\n')
for name in ('LICENSE','LICENSE-PRIORITY1.txt','THIRD_PARTY_NOTICES.md'):
    shutil.copy2(repo/name,stage/name)
licenses=stage/'licenses';licenses.mkdir(exist_ok=True)
for name in ('PRIORITY1_OPEN_SOURCE.md','PRIORITY23_OPEN_SOURCE.md'):
    shutil.copy2(repo/'docs'/name,licenses/name)
for name in ('LICENSE','NOTICE'):
    url='https://raw.githubusercontent.com/openai/codex/rust-v0.167.2/'+name
    try:(licenses/('CODEX-'+name)).write_bytes(urllib.request.urlopen(url,timeout=30).read())
    except urllib.error.HTTPError as error:
        if error.code!=404:raise
report=json.loads((server/'pip-install-report.json').read_text())
bom=[{'name':item['metadata']['name'],'version':item['metadata']['version'],'url':item['download_info']['url'],'hashes':item['download_info']['archive_info'].get('hashes',{})} for item in report['install']]
(licenses/'python-distributions.json').write_text(json.dumps(bom,indent=2))
shutil.copy2(managed/'freecad-1.1.4/installation.json',licenses/'freecad-upstream.json')
data=json.loads((licenses/'freecad-upstream.json').read_text());data.pop('root',None)
(licenses/'freecad-upstream.json').write_text(json.dumps(data,indent=2))
(stage/'README.txt').write_text('''Intact Simulation 0.20.0 — Windows x86-64 desktop

This package includes Python, native CAD/numerical libraries, FreeCAD,
Chromium headless rendering and the official OpenAI local client.
No WSL, Linux, system Python, developer checkout or API key is required.

Install as a desktop plugin. The MCP entry point is mcp.json.
Your projects are stored separately in %LOCALAPPDATA%/IntactSimulation/projects.
An existing WSL project library is not moved or deleted by this installation.
Use project JSON export/import when moving designs between installations.

ChatGPT conversation tools work through the host. In a standalone local viewer,
Ask AI starts a separate scoped OpenAI local task. If sign-in is required, run
server/client/bin/codex.exe login, then sign in using your own ChatGPT account.
Never place login profiles, passwords or private models inside this package.

Optional PicoGK and GNU LibreDWG are not bundled in this Windows distribution.
The built-in TPMS engine and DXF exports remain available.

SUBMISSION CANDIDATE: the Terms of Service page requires publisher approval
and publication. The portal's local-MCP eligibility finding must be resolved
with OpenAI; accepting a ZIP draft does not itself establish that eligibility.
This package is not a claim of public-directory approval.
''',encoding='utf-8')
(licenses/'DISTRIBUTION-NOTICES.txt').write_text('''This binary distribution retains each dependency's own license and notices.
Python distribution licenses accompany server/python. Python wheel licenses
and metadata accompany server/dependencies. FreeCAD and its bundled components
retain notices in server/freecad. The OpenAI client is unmodified; its source
license and NOTICE are supplied here. See python-distributions.json for exact
wheel provenance. Intact's Apache-2.0 license does not replace these licenses.
Upstream source locations:
https://github.com/FreeCAD/FreeCAD/tree/1.1.4
https://gmsh.info/src/gmsh-4.15.0-source.tgz
https://github.com/CadQuery/OCP
https://github.com/Open-Cascade-SAS/OCCT
https://github.com/astral-sh/python-build-standalone/releases/tag/20261110
https://github.com/openai/codex/tree/rust-v0.167.2
''')
print(json.dumps({'stage':str(stage),'version':manifest['version'],'python_distributions':len(bom),'skills':[str(p.relative_to(stage)) for p in (stage/'skills').glob('*/SKILL.md')]}))
