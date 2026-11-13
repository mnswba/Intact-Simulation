"""Check documented directory ZIP limits before a package is recommended."""
import json
from pathlib import Path, PurePosixPath
import stat
import unicodedata
import zipfile

MIB=1024**2
MAX_ZIP=100*MIB
MAX_EXTRACTED=512*MIB
MAX_ENTRIES=5000

def check_inventory(files):
    errors=[]
    if len(files)>MAX_ENTRIES:errors.append(f'{len(files)} entries exceeds {MAX_ENTRIES}')
    size=sum(size for _,size in files)
    if size>MAX_EXTRACTED:errors.append(f'{size} extracted bytes exceeds {MAX_EXTRACTED}')
    seen=set()
    for name,size in files:
        parts=PurePosixPath(name).parts
        if not name or name.startswith('/') or '\\' in name or ':' in name or any(p in ('.','..','') for p in name.split('/')):
            errors.append('Unsafe archive path: '+name)
        if len(parts)>20:errors.append('Path deeper than 20 segments: '+name)
        normalized=unicodedata.normalize('NFC',name).casefold()
        if normalized in seen:errors.append('Normalized path collision: '+name)
        seen.add(normalized)
        if size>100*MIB:errors.append('Member exceeds 100 MiB: '+name)
    return errors

def check_stdio_command(command):
    """Match the portable host's bare-executable/contained-path requirement."""
    if not isinstance(command,str) or not command:return ['Stdio command is missing']
    if '/' not in command and '\\' not in command and ':' not in command and '$' not in command:return []
    if command.startswith('./') and not any(p in ('','..') for p in command[2:].split('/')) and not any(c in command for c in ('\\',':','$')):return []
    return ['Stdio command must be a bare executable or contained ./ path']

def validate_archive(path):
    path=Path(path);errors=[]
    if path.stat().st_size>MAX_ZIP:raise ValueError(f'{path.stat().st_size} compressed bytes exceeds {MAX_ZIP}')
    with zipfile.ZipFile(path) as archive:
        entries=archive.infolist()
        errors+=check_inventory([(i.filename.rstrip('/'),i.file_size) for i in entries])
        for item in entries:
            kind=stat.S_IFMT(item.external_attr>>16)
            if kind not in (0,stat.S_IFREG,stat.S_IFDIR):errors.append('Unsupported entry type: '+item.filename)
            if item.flag_bits&1:errors.append('Encrypted entries are unsupported: '+item.filename)
        if errors:raise ValueError('\n'.join(errors[:20]))
        names={item.filename for item in entries}
        if 'plugin.json' not in names:errors.append('Root plugin.json missing')
        else:
            record=json.loads(archive.read('plugin.json'))
            extension=record.get('extensions',{}).get('com.openai',{})
            if 'hooks' in record or 'hooks' in extension or any(n.startswith('hooks/') for n in names):errors.append('Plugin hooks are not eligible')
            interface=extension.get('interface',{})
            for key,limit in [('displayName',30),('shortDescription',30),('longDescription',4000)]:
                if not isinstance(interface.get(key),str) or not 0<len(interface[key])<=limit:errors.append(f'{key} must contain 1–{limit} characters')
        if '.app.json' in names:errors.append('App references are not eligible')
        if 'mcp.json' in names:
            for server in json.loads(archive.read('mcp.json')).get('mcpServers',{}).values():
                if server.get('type')=='stdio':
                    errors+=check_stdio_command(server.get('command'))
                    command=server.get('command','')
                    if command.startswith('./') and command[2:] not in names:errors.append('Contained stdio executable is missing: '+command)
        if errors:raise ValueError('\n'.join(errors[:20]))
        if archive.testzip() is not None:errors.append('ZIP CRC check failed')
    if errors:raise ValueError('\n'.join(errors[:20]))
    return {'compressed_bytes':path.stat().st_size,'extracted_bytes':sum(i.file_size for i in entries),'entries':len(entries),'archive_limits_passed':True,'metadata_lengths_passed':True}
