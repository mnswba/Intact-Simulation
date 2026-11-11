"""Render built public examples; requires prepared runtime and Playwright Chromium."""
import asyncio,json,os,signal,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from intact_backend.viewer_server import viewer_url,live_session
from intact_backend.snapshot import snapshot
async def main():
    output=ROOT/'outputs/examples';state=output/'.state'
    existed=live_session(state)
    try:
        for name in ('flange','enclosure','gyroid'):
            record=json.loads((output/(name+'.json')).read_text())
            await snapshot(viewer_url(state,record['model_id']),ROOT/'docs/images'/(name+'.png'),'iso')
            print('Rendered example: '+name)
    finally:
        session=live_session(state)
        if session and not existed:os.kill(session['pid'],signal.SIGTERM)
if __name__=='__main__':asyncio.run(main())
