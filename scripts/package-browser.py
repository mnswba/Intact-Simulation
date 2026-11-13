"""Package the built static website; this is NOT a ChatGPT submission ZIP."""
import argparse, hashlib, json, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    source=ROOT/'browser-cad/dist'
    names=['index.html','app.css','app.js','worker.js','manifold.wasm','HOSTING.md','THIRD_PARTY_NOTICES.txt','LICENSE.txt','wordpress-page.json','wordpress-preview.html','wordpress-host-preview.html']
    for name in names:
        if not (source/name).is_file():raise SystemExit('Missing build output: '+name)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(args.out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name in names:
            info=zipfile.ZipInfo(name,date_time=(2026,11,13,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,(source/name).read_bytes(),compresslevel=9)
    checksum=hashlib.sha256(args.out.read_bytes()).hexdigest()
    args.out.with_suffix('.zip.sha256').write_text(f'{checksum}  {args.out.name}\n')
    record={'edition':'Intact Browser CAD','version':'0.1.0','kind':'website deployment, not ChatGPT plugin submission','filename':args.out.name,'size_bytes':args.out.stat().st_size,'sha256':checksum,'entries':len(names),'uncompressed_bytes':sum((source/n).stat().st_size for n in names)}
    args.out.with_suffix('.zip.verification.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))

if __name__=='__main__':main()
