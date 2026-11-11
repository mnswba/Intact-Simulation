"""Check portable plugin metadata, example catalog and publication exclusions."""
import argparse,ast,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--allow-workspace-metadata',action='store_true');args=parser.parse_args()
    version=(ROOT/'VERSION').read_text().strip()
    for name in ('plugin.json','.codex-plugin/plugin.json','.claude-plugin/plugin.json','plugin/plugin.json','plugin/.codex-plugin/plugin.json'):
        record=json.loads((ROOT/name).read_text());assert record['version']==version,(name,'version mismatch')
    for name in ('.mcp.json','plugin/.mcp.json','plugin/mcp.json'):
        text=(ROOT/name).read_text();json.loads(text)
        assert '/home/' not in text and '/mnt/c/' not in text,(name,'machine-specific path')
    for path in (ROOT/'models').glob('*.py'):ast.parse(path.read_text())
    catalog=json.loads((ROOT/'models/catalog.json').read_text())
    for name,item in catalog.items():
        assert (ROOT/'models'/item['source']).is_file(),name
        assert all(isinstance(v,(int,float)) and not isinstance(v,bool) for v in item['parameters'].values())
        assert not (name=='gyroid' and 'step' in item['formats'])
    assert 'Apache License' in (ROOT/'LICENSE').read_text()
    files=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode().split('\0')
    forbidden=[];secrets=[]
    sensitive=re.compile(rb'(?:ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|sk-proj-[A-Za-z0-9_-]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)')
    for name in filter(None,files):
        p=ROOT/name
        if not p.is_file():continue
        if any(x in p.relative_to(ROOT).parts for x in ('outputs','.venv','__pycache__','.openai','.state','node_modules')) or (p.name.startswith('.env') and p.name!='.env.example'):forbidden.append(name)
        if sensitive.search(p.read_bytes()):secrets.append(name)
    if not args.allow_workspace_metadata:assert not forbidden,forbidden
    else:assert all(name=='.openai/hosting.json' for name in forbidden),forbidden
    assert not secrets,('Possible credentials in files',secrets)
    print(json.dumps({'version':version,'catalog_examples':len(catalog),'portable_manifests':True,'credential_pattern_scan':'passed','excluded_workspace_files':forbidden}))
if __name__=='__main__':main()
