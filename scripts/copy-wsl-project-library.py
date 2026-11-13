"""Copy a WSL library to Windows without moving or overwriting either library."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source',type=Path,required=True)
parser.add_argument('--destination',type=Path,required=True)
parser.add_argument('--receipt',type=Path,required=True)
args=parser.parse_args();source=args.source.resolve();destination=args.destination.resolve()
assert source!=destination and source.is_dir()
excluded={'viewer-session.json','viewer.log','viewer-start.lock','ask-ai-active.json','ask-ai-runner.log','auth.json','config.toml'}
copied=0;conflicts=[];errors=[]
for path in source.rglob('*'):
    if not path.is_file() or path.is_symlink() or path.name in excluded or path.suffix in ('.lock','.log'):continue
    relative=path.relative_to(source);target=destination/relative
    if target.exists():
        if target.stat().st_size!=path.stat().st_size or sha256(target.read_bytes()).digest()!=sha256(path.read_bytes()).digest():conflicts.append(str(relative))
        continue
    try:
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target);copied+=1
    except OSError as error:errors.append({'file':str(relative),'error':str(error)})
models=[]
for path in (source/'mcp-models').glob('*.json'):
    target=destination/'mcp-models'/path.name
    original=json.loads(path.read_text());copy=json.loads(target.read_text()) if target.is_file() else None
    assert copy and copy['model_id']==original['model_id'] and copy['spec']['revision']==original['spec']['revision']
    assert sha256(path.read_bytes()).digest()==sha256(target.read_bytes()).digest()
    models.append({'model_id':original['model_id'],'revision':original['spec']['revision']})
receipt={'copied_files':copied,'models_preserved':len(models),'model_records_byte_identical':True,'source_untouched':True,'conflicts':conflicts,'errors':errors,'models':models}
args.receipt.parent.mkdir(parents=True,exist_ok=True);args.receipt.write_text(json.dumps(receipt,indent=2))
print(json.dumps({key:value for key,value in receipt.items() if key!='models'}))
if conflicts or errors:raise SystemExit('Some artifacts require review; original libraries remain intact.')
