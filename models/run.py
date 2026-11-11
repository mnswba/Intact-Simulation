"""Build authored examples through the actual isolated Intact CAD engine."""
import argparse,json,math,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from intact_backend.projects import ProjectService

def main():
    catalog=json.loads((ROOT/'models/catalog.json').read_text())
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name',choices=sorted(catalog))
    parser.add_argument('--output',type=Path,default=ROOT/'outputs/examples')
    args=parser.parse_args();example=catalog[args.name]
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=True)
    service=ProjectService(output/'.state')
    if not service.programs.available():parser.error('Bubblewrap/user namespaces are unavailable. Complete docs/install.md first.')
    record=service.build((ROOT/'models'/example['source']).read_text(),example['parameters'],name='Example: '+args.name)
    key=record['model_id'];parts=record['spec']['parts']
    assert len(parts)==example['expected_parts'],'Unexpected assembly part count'
    assert all(p['measurements']['volume_mm3']>0 for p in parts),'Part has no solid volume'
    if args.name=='flange':
        p=example['parameters'];expected=math.pi*((p['diameter']/2)**2-(p['bore']/2)**2-6*(p['hole_diameter']/2)**2)*p['thickness']
        assert math.isclose(parts[0]['measurements']['volume_mm3'],expected,rel_tol=1e-6),'Flange volume mismatch'
    exports={}
    for kind in example['formats']:
        target=output/(args.name+'.'+kind);shutil.copy2(service.artifact(key,'model.'+kind),target);exports[kind]=str(target)
    summary={'example':args.name,'model_id':key,'engine':record['geometry']['engine'],'parts':len(parts),'volume_mm3':sum(p['measurements']['volume_mm3'] for p in parts),'exports':exports,'checks':'positive part volumes, expected part count; flange analytical volume'}
    (output/(args.name+'.json')).write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
