"""Rebuild public showcase packages through Intact's Linux CAD sandbox.

Run with the installed CAD runtime Python. Native exports are deliberately ignored
by Git. Thumbnails are rendered separately from these actual GLBs, never AI images.
"""
import argparse, json, sys, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from intact_backend.projects import ProjectService


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-dir',type=Path,required=True,help='Separate disposable showcase state, never the personal CAD state')
    parser.add_argument('--output',type=Path,default=ROOT/'website/site/demo')
    args=parser.parse_args()
    if args.state_dir.resolve()==(Path.home()/'.local/share/intact-studio').resolve():raise SystemExit('Use separate showcase state.')
    projects=ProjectService(args.state_dir);args.output.mkdir(parents=True,exist_ok=True)
    items=json.loads((ROOT/'website/content/showcase.json').read_text())
    for item in items:
        sources=list((ROOT/'models/showcase').glob('*/'+item['slug']+'.py'))
        if len(sources)!=1:raise ValueError('Expected one source for '+item['slug'])
        record=projects.build(sources[0].read_text(),item['parameters'],name=item['title'],engineering={'accuracy':{'linear_deflection_mm':.15,'angular_deflection_rad':.2}})
        with zipfile.ZipFile(args.output/item['package_filename'],'w',zipfile.ZIP_DEFLATED) as package:
            for kind in item['formats']:
                path=projects.artifact(record['model_id'],'model.'+kind)
                package.write(path,'model.glb' if kind=='glb' else 'intact-'+item['slug']+'.'+kind)
            package.write(sources[0],'source.py')
            package.writestr('design-prompt.txt',item.get('design_prompt',''))
            package.writestr('geometry-audit.json',json.dumps(record['geometry']['audit'],indent=2))
            package.writestr('README.txt',item['title']+'\n'+item['summary']+'\n'+item['design_notes']+'\nOriginal showcase concept; engineering performance unverified. Apache-2.0 source. Native CAD millimeters, GLB meters/Y-up. No exact STEP for sampled TPMS.\nParameters: '+json.dumps(item['parameters']))
        print('Built',item['slug'],len(record['spec']['parts']),'parts',flush=True)

if __name__=='__main__':main()
