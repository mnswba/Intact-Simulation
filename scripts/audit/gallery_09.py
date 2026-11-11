"""Render every audited configuration, checking framing and browser errors."""
import asyncio,html,json,os,time
from pathlib import Path
from playwright.async_api import async_playwright
from catalog_09 import CASES
from intact_backend.projects import ProjectService
from intact_backend.viewer_server import viewer_url

REPO=Path(__file__).resolve().parents[2];OUT=REPO/'outputs/0.9-audit';ROOT=Path.home()/'.local/share/intact-simulation/audit-09'

async def main():
    s=ProjectService(ROOT);saved=OUT/'renders-report.json';previous=json.loads(saved.read_text()) if saved.exists() else {};results=previous.get('cases',{});errors=previous.get('browser_errors',[])
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,env=dict(os.environ,LD_LIBRARY_PATH=str(Path.home()/'.local/share/intact-simulation/browser-libs')),args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=await browser.new_page(viewport={'width':1400,'height':950});page.on('pageerror',lambda e:errors.append(str(e)))
        for c in CASES:
            deadline=time.monotonic()+300
            while True:
                models=json.loads((OUT/'models-report.json').read_text());entry=models['cases'].get(c['id'],{})
                if entry.get('status')=='passed':
                    r=s.load(entry['model_id']);program=r['spec']['program']
                    if program['artifact_id']==s.programs.key(program['source'],program['parameters'],program.get('asset_id')):break
                if time.monotonic()>deadline:raise AssertionError('Model not ready for release rendering: '+c['id'])
                await asyncio.sleep(.5)
            prior=results.get(c['id'])
            if prior and (OUT/c['id']/'viewer.png').is_file():
                old_key=prior['viewer_url'].split('/')[-2];old=s.load(old_key)
                if old['spec']['program']['artifact_id']==program['artifact_id']:
                    print('REUSE '+c['id'],flush=True);continue
            url=viewer_url(ROOT,entry['model_id']);await page.goto(url+'?snapshot=1');await page.wait_for_selector('body[data-ready=true]',timeout=30000)
            await page.locator('[data-view=iso]').evaluate('(button)=>button.click()');await page.wait_for_timeout(100)
            result=await page.evaluate('''()=>{const state=intactInspect.project(),camera=intactInspect.camera(),canvas=document.querySelector('#cad-canvas'),bad=[];for(const p of state.spec.parts){const [cx,cy,z0]=p.position,{length:l,width:w,height:h}=p.params;for(const x of [cx-l/2,cx+l/2])for(const y of [cy-w/2,cy+w/2])for(const z of [z0,z0+h]){const a=intactInspect.screenPoint([x,y,z],p.id);if(a[0]<=0||a[0]>=canvas.clientWidth||a[1]<=0||a[1]>=canvas.clientHeight||Math.abs(a[2])>=1)bad.push(p.id);}}return {bad,direction:camera.direction};}''')
            assert not result['bad'],(c['id'],result)
            n=(2+.8**2)**.5;assert sum(a*b/n for a,b in zip(result['direction'],(1,.8,1)))>.9999
            await page.locator('#cad-canvas').screenshot(path=str(OUT/c['id']/'viewer.png'))
            results[c['id']]={'status':'passed','viewer_url':url,'framing':'all component bounds inside viewport','camera':'true isometric'}
            (OUT/'renders-report.json').write_text(json.dumps({'passed':len(results),'failed':0,'browser_errors':errors,'cases':results},indent=2));print('RENDER '+str(len(results))+'/200 '+c['id'],flush=True)
        await browser.close()
    assert not errors,errors
    cards=[]
    for c in CASES:
        e=models['cases'][c['id']];key=c['id'];exports=' · '.join(f'<a href="{key}/{filename}">{html.escape(filename.removeprefix("model."))}</a>' for filename in e['exports'])
        cards.append(f'<article data-search="{html.escape((c["name"]+" "+c["category"]).lower())}"><h2>{html.escape(c["name"])}</h2><p>{html.escape(c["category"])} · {e["parts"]} parts · {e["triangles"]:,} triangles</p><a href="{html.escape(results[key]["viewer_url"])}"><img src="{key}/viewer.png" alt="Actual audited viewer snapshot" loading="lazy"></a><p><strong>PASS</strong> · {exports}</p><a href="{key}/validation.json">Validation facts</a> · <a href="{html.escape(results[key]["viewer_url"])}">Interactive viewer</a></article>')
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Intact 0.9 · 200-model audit</title><style>*{box-sizing:border-box}body{margin:0;font:14px system-ui;color:#253343;background:#eef0f3}header{padding:24px;background:#fff;border-bottom:1px solid #bdc6d2}h1{margin:0}header p{max-width:950px;line-height:1.6}input{padding:10px;min-width:280px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px;padding:18px}article{background:white;border:1px solid #bdc6d2;border-radius:8px;padding:14px}article img{width:100%;display:block}h2{font-size:16px}p{font-size:12px}a{color:#195c94}strong{color:#207344}</style><header><h1>Intact Simulation 0.9 · 200 configurations</h1><p>50 native CAD families, 144 TPMS variants and six assemblies. Every image is an actual viewer render. Fixtures are authored regression examples; this is not model-weight training or a claim of 200 AI-generated designs. Mesh lattices export STL/GLB/3MF, with sampled measurements and no exact STEP. This gallery is private/local.</p><input id="filter" placeholder="Filter family, model or category"></header><main>'''+''.join(cards)+'''</main><script>document.querySelector('#filter').oninput=e=>{for(const card of document.querySelectorAll('article'))card.hidden=!card.dataset.search.includes(e.target.value.toLowerCase());};</script></html>'''
    (OUT/'gallery.html').write_text(page);print('Gallery complete: 200/200 actual images, no browser errors')

asyncio.run(main())
