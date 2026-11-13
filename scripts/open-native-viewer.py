"""Open saved CAD in the installed Windows viewer without rebuilding geometry."""
import argparse
import json
import os
from pathlib import Path
from urllib.request import urlopen
import webbrowser

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-id',required=True)
    parser.add_argument('--open',action='store_true')
    args=parser.parse_args()
    base=Path(os.environ['LOCALAPPDATA'])/'IntactSimulation'
    root=base/'projects'
    from intact_backend.viewer_server import VERSION,viewer_url
    url=viewer_url(root,args.model_id)
    from urllib.parse import urlsplit
    parts=urlsplit(url)
    health=json.loads(urlopen(f'{parts.scheme}://{parts.netloc}/{parts.path.strip("/").split("/")[0]}/health',timeout=5).read())
    if health.get('version')!=VERSION:raise RuntimeError('The running viewer does not match the installed runtime')
    receipt={'url':url,'model_id':args.model_id,'viewer_version':health['version'],'state_directory':health['state_directory'],'saved_geometry_rebuilt':False}
    (base/'current-viewer.json').write_text(json.dumps(receipt,indent=2))
    if args.open:webbrowser.open(url)
    else:print('Saved model available in Windows viewer '+health['version'])

if __name__=='__main__':main()
