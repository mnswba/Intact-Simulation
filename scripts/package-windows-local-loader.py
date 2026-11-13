"""Package local skills and a pinned uv runtime launcher, following uvx CAD plugins."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import zipfile
from plugin_archive_limits import validate_archive

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--uv-root',type=Path,required=True)
parser.add_argument('--wheel',type=Path,required=True)
parser.add_argument('--requirements',type=Path,required=True)
parser.add_argument('--stage',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();repo=Path(__file__).resolve().parents[1]
stage=args.stage;stage.mkdir(parents=True,exist_ok=True)
for directory in ('assets','skills'):shutil.copytree(repo/'plugin'/directory,stage/directory,dirs_exist_ok=True)
(stage/'bin').mkdir(exist_ok=True);(stage/'runtime').mkdir(exist_ok=True);(stage/'licenses').mkdir(exist_ok=True)
shutil.copy2(args.uv_root/'bin/uv.exe',stage/'bin/uv.exe')
shutil.copy2(args.wheel,stage/'runtime'/args.wheel.name)
shutil.copy2(args.requirements,stage/'runtime/requirements-windows.txt')
for path in args.uv_root.glob('uv-*.dist-info/licenses/*'):
    if path.is_file():shutil.copy2(path,stage/'licenses'/('UV-'+path.name))
shutil.copy2(repo/'LICENSE',stage/'LICENSE')
manifest=json.loads((repo/'plugin/plugin.json').read_text())
interface=manifest['extensions']['com.openai']['interface']
interface['shortDescription']='CAD modeling and verification'
interface['longDescription']='Create and verify general-purpose CAD parts and assemblies through ChatGPT on your Windows computer. Intact runs build123d/OpenCASCADE, FreeCAD, supported numerical studies and the viewer locally. On first use, the launcher installs the pinned runtime and native components into your own user profile; internet access and several GB of free disk space are required. No publisher-hosted CAD server, WSL or separate CAD computer is needed. Review generated geometry and engineering assumptions before manufacture.'
manifest['extensions']['com.openai']['onboardingSkill']='./skills/intact-cad/SKILL.md'
entry={'command':'./bin/uv.exe','args':['tool','run','--no-config','--managed-python','--python','3.12.16','--default-index','https://pypi.org/simple','--from','${PLUGIN_ROOT}/runtime/'+args.wheel.name,'--with-requirements','${PLUGIN_ROOT}/runtime/requirements-windows.txt','intact-simulation']}
(stage/'plugin.json').write_text(json.dumps(manifest,indent=2))
(stage/'mcp.json').write_text(json.dumps({'$schema':'https://agent-plugins.org/schemas/1.0.0/mcp.schema.json','mcpServers':{'intact':{'type':'stdio',**entry}}},indent=2))
# Preserve the setup timeout for hosts using the compatibility MCP format.
(stage/'.mcp.json').write_text(json.dumps({'mcpServers':{'intact':{**entry,'startup_timeout_sec':300}}},indent=2))
compat={'name':'intact-simulation','version':manifest['version'],'description':manifest['description'],'skills':'./skills/','mcpServers':'./.mcp.json','interface':interface,'requires_local_executor':True}
(stage/'.codex-plugin').mkdir(exist_ok=True)
(stage/'.codex-plugin/plugin.json').write_text(json.dumps(compat,indent=2))
skill=stage/'skills/intact-cad/SKILL.md';text=skill.read_text();end=text.index('\n---',4)+4
setup='''

## Desktop setup and execution

This is a Windows x86-64 desktop plugin. ChatGPT plans and calls tools; native
CAD generation and the viewer run on the user's own computer. No publisher
CAD server, WSL or separately provided computer is needed. The bundled launcher
uses pinned uv/Python packages. First use needs internet access and several GB
of disk space to install the local runtime, FreeCAD, browser and OpenAI client.
There are no lifecycle hooks. Do not ask users for a hosting account.

Call status first. If desktop_setup.ready is false and stage is not failed,
explain first-use setup and poll status until ready before modeling. Report a
failed setup accurately. Do not invent tool availability or geometric results.
First startup can take several minutes; after an update/restart old threads may
retain the previous connection until the desktop app is restarted.

Models are general-purpose, not limited to predefined templates. Complex
geometry needs iteration and native verification. Do not promise every possible
CAD operation or certify physical accuracy without suitable evidence. In a
standalone viewer, Ask AI may need the user's own OpenAI client sign-in; never
request passwords or API keys in CAD prompts.

'''
skill.write_text(text[:end]+setup+text[end:].lstrip())
(stage/'README.txt').write_text('''Intact Simulation 0.20.0 — Windows local execution

ChatGPT plans; this user's Windows laptop builds and stores CAD and runs the viewer.
The small ZIP contains instructions, the Intact Python wheel and a pinned uv launcher.
First use downloads the pinned Python/CAD libraries, FreeCAD, headless browser and
OpenAI local client from their distribution sources. Internet access and several
GB of local disk space are needed. Later starts reuse the cached runtime.
No publisher-operated CAD server, hosting account, WSL or external computer is needed.
The local MCP 'server' is a background process on the user's computer.
No lifecycle hooks are included. Sign in with your own ChatGPT account when the
OpenAI local client requires it. No passwords, API keys or private CAD are bundled.

This package is for Windows x86-64 desktop threads that support local MCP execution.
It is not an ordinary ChatGPT web/mobile CAD runtime. OpenAI account verification,
local-MCP submission eligibility and public review remain separate requirements.
''')
provenance={'uv_version':'0.13.8','uv_exe_sha256':sha256((stage/'bin/uv.exe').read_bytes()).hexdigest(),'wheel_sha256':sha256(args.wheel.read_bytes()).hexdigest(),'python':'3.12.16','execution':'user_windows_laptop','hosted_cad':False,'first_start_downloads':True,'hooks':False}
(stage/'runtime-provenance.json').write_text(json.dumps(provenance,indent=2))
with zipfile.ZipFile(args.output,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    for path in stage.rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts:archive.write(path,path.relative_to(stage).as_posix())
result={'file':args.output.name,**validate_archive(args.output),**provenance,'sha256':sha256(args.output.read_bytes()).hexdigest(),'public_directory_approved':False}
args.output.with_suffix('.verification.json').write_text(json.dumps(result,indent=2))
args.output.with_suffix('.sha256').write_text(result['sha256']+'  '+args.output.name+'\n')
print(json.dumps(result,indent=2))
