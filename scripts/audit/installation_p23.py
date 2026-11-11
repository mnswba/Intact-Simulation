"""Check installed runtime and both personal plugin installations without secrets."""
import hashlib,json,tomllib
from pathlib import Path
REPO=Path(__file__).resolve().parents[2];OUT=REPO/'outputs/priority23-audit'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
runtime=Path.home()/'.local/share/intact-simulation/runtime';files=[]
assert digest(REPO/'LICENSE-PRIORITY1.txt')==digest(runtime/'LICENSE-PRIORITY1.txt')
for p in (REPO/'backend/intact_backend').iterdir():
 if p.is_file() and p.suffix in ('.py','.html','.js'):
  assert digest(p)==digest(runtime/'intact_backend'/p.name),p
  files.append(p.name)
assert not (runtime/'intact_backend/agent.py').exists()
assert not any(d['name']=='litellm' for d in tomllib.loads((runtime/'uv.lock').read_text()).get('package',[]))
installs=[]
for home in (Path.home(),Path('/mnt/c/Users/User')):
 config=tomllib.loads((home/'.codex/config.toml').read_text());assert config['plugins']['intact-simulation@intact-local']['enabled']
 for suffix in ('intact-simulation','cache/intact-local/intact-simulation/local','cache/intact-local/intact-simulation/0.12.0'):
  folder=home/'.codex/plugins'/suffix
  assert digest(REPO/'LICENSE-PRIORITY1.txt')==digest(folder/'LICENSE-PRIORITY1.txt')
  assert digest(REPO/'docs/PRIORITY1_OPEN_SOURCE.md')==digest(folder/'PRIORITY1_OPEN_SOURCE.md')
  for manifest in ('plugin.json','.codex-plugin/plugin.json'):
   assert json.loads((folder/manifest).read_text())['version']=='0.12.0'
  server=json.loads((folder/'mcp.json').read_text())['mcpServers']['intact'];expected='wsl.exe' if home==Path('/mnt/c/Users/User') else './server/launch.sh';assert server['command']==expected
  for p in (REPO/'plugin/skills/intact-cad').rglob('*'):
   if p.is_file():assert digest(p)==digest(folder/'skills/intact-cad'/p.relative_to(REPO/'plugin/skills/intact-cad'))
  installs.append(str(folder))
metadata=json.loads((Path.home()/'.local/share/intact-simulation/freecad-1.1.4/installation.json').read_text());assert metadata['version']=='1.1.4' and metadata['sha256']=='f6dc6ba676e5ac96a565ebc8d657232f94c6158e85b4352141bd1a46f6b43434'
result={'status':'passed','version':'0.12.0','runtime_files':files,'plugin_copies':installs,'freecad':metadata,'litellm_present':False,'windows_gui_tested':False}
(OUT/'installation-report.json').write_text(json.dumps(result,indent=2));print(json.dumps({'status':'passed','runtime_files':len(files),'plugin_copies':len(installs)}))
