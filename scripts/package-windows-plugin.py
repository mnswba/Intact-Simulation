"""Create and inspect a submission ZIP from a verified native Windows stage."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import zipfile
from plugin_archive_limits import check_inventory,validate_archive

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--stage',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--offline-runtime',action='store_true',help='Build a separate offline engine bundle, never a directory-upload ZIP')
args=parser.parse_args();stage=args.stage.resolve()
manifest=json.loads((stage/'plugin.json').read_text());mcp=json.loads((stage/'mcp.json').read_text())
assert manifest['version']=='0.20.0'
assert 'hooks' not in manifest and 'hooks' not in manifest['extensions']['com.openai']
assert not (stage/'hooks').exists() and not (stage/'.app.json').exists()
assert (stage/'skills/intact-cad/SKILL.md').is_file()
server=mcp['mcpServers']['intact'];assert server['type']=='stdio'
assert server['command']=='${PLUGIN_ROOT}/server/python/python.exe'
interface=manifest['extensions']['com.openai']['interface']
for name in ('websiteURL','supportURL','privacyPolicyURL','termsOfServiceURL'):
    assert interface[name].startswith('https://')
for name in ('logo','composerIcon'):
    assert (stage/interface[name]).is_file()
allow={'plugin.json','mcp.json','README.txt','LICENSE','LICENSE-PRIORITY1.txt','THIRD_PARTY_NOTICES.md','runtime-provenance.json','VERIFICATION.json','skills','assets','licenses','server'}
def included(path):
    relative=path.relative_to(stage)
    if relative.parts[0] not in allow:return False
    if '__pycache__' in relative.parts or path.suffix in ('.pyc','.log') or path.name.endswith('.verified'):return False
    if relative.as_posix().startswith(('server/dependencies/bin/','server/python/Scripts/')):return False
    if relative.as_posix()=='server/pip-install-report.json':return False
    return True
files=sorted(p for p in stage.rglob('*') if p.is_file() and included(p))
if args.offline_runtime:
    assert 'Offline-Runtime' in args.output.name,'Offline bundles must be named Offline-Runtime, not Submission.'
else:
    errors=check_inventory([(p.relative_to(stage).as_posix(),p.stat().st_size) for p in files])
    if errors:raise SystemExit('Not a valid directory upload. Use a different distribution architecture.\n'+'\n'.join(errors[:5]))
hashes={}
args.output.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(args.output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=4,allowZip64=True) as archive:
    for index,path in enumerate(files):
        if path.is_symlink():raise ValueError('No symbolic links in Windows submission: '+str(path))
        relative=path.relative_to(stage).as_posix()
        info=zipfile.ZipInfo.from_file(path,relative,strict_timestamps=False)
        info.compress_type=zipfile.ZIP_DEFLATED;info._compresslevel=4
        digest=sha256()
        with path.open('rb') as source,archive.open(info,'w',force_zip64=True) as destination:
            while block:=source.read(1024**2):
                digest.update(block);destination.write(block)
        hashes[relative]=digest.hexdigest()
        if index%5000==0:print('Packed',index+1,'of',len(files),'files',flush=True)
    archive.writestr('file-sha256.json',json.dumps(hashes,indent=2))
with zipfile.ZipFile(args.output) as archive:
    assert 'plugin.json' in archive.namelist() and 'skills/intact-cad/SKILL.md' in archive.namelist()
    assert archive.testzip() is None
if not args.offline_runtime:validate_archive(args.output)
digest=sha256()
with args.output.open('rb') as stream:
    while block:=stream.read(1024**2):digest.update(block)
receipt={'file':args.output.name,'version':manifest['version'],'bytes':args.output.stat().st_size,'files':len(files)+1,'sha256':digest.hexdigest(),'hooks':False,'skills':['intact-cad'],'local_mcp':True,'policy_status':'Support/privacy published; Terms of Service awaiting publisher review/publication.','portal_status':'Local MCP submission eligibility finding unresolved; ZIP acceptance is not review approval.'}
receipt.update(distribution_type='offline_runtime' if args.offline_runtime else 'directory_candidate',public_upload_compatible=not args.offline_runtime)
args.output.with_suffix('.sha256').write_text(digest.hexdigest()+'  '+args.output.name+'\n')
args.output.with_suffix('.verification.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps(receipt))
