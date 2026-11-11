"""Check revision browsing, ChatGPT request handoff and TPMS viewer behavior."""
import asyncio,json,os
from pathlib import Path
from urllib.request import Request,urlopen
from playwright.async_api import async_playwright
from intact_backend.projects import ProjectService
from intact_backend.edit_requests import EditRequests
from intact_backend.lattice_tools import build_tpms
from intact_backend.viewer_server import viewer_url

REPO=Path(__file__).resolve().parents[2];OUT=REPO/'outputs/0.9-audit';OUT.mkdir(parents=True,exist_ok=True)
ROOT=Path.home()/'.local/share/intact-simulation/audit-09-ui'
SOURCE="import build123d as bd\ndef build(params):\n    return {'plate':bd.Box(params['length'],20,5)}"

async def main():
    s=ProjectService(ROOT);r=s.build(SOURCE,{'length':30},name='History and ChatGPT workflow');key=r['model_id'];s.parameters(key,{'length':40});url=viewer_url(ROOT,key);base=url.removesuffix('view');checks=[];errors=[]
    async with async_playwright() as p:
        env=dict(os.environ,LD_LIBRARY_PATH=str(Path.home()/'.local/share/intact-simulation/browser-libs'))
        browser=await p.chromium.launch(headless=True,env=env,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        context=await browser.new_context(viewport={'width':1500,'height':1000},permissions=['clipboard-read','clipboard-write']);page=await context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
        await page.goto(url);await page.wait_for_selector('body[data-ready=true]');before=s.revisions(key)
        await page.locator('details').filter(has=page.locator('#revisions')).locator('summary').click()
        await page.locator('[data-revision="1"]').click();await page.wait_for_selector('body[data-ready=true][data-historical=true]')
        assert s.revisions(key)==before and (await page.evaluate('window.intactInspect.project().spec.program.parameters.length'))==30
        assert await page.locator('#rebuild').is_disabled() and await page.locator('#toggle-edit').is_disabled()
        old=await page.request.get(base+'project.json?revision=1');assert (await old.json())['spec']['program']['parameters']['length']==30
        forbidden=await page.request.post(base+'parameters?revision=1',data={'parameters':{'length':99}},headers={'Origin':base.split('/')[0]+'//'+base.split('/')[2]});assert forbidden.status==400
        await page.locator('#cad-canvas').screenshot(path=str(OUT/'history-preview.png'))
        checks.append('history clicks read-only; no new revision; old geometry/exports; mutation rejected')
        await page.locator('details').filter(has=page.locator('#revisions')).locator('summary').click()
        await page.locator('[data-revision="2"]').click();await page.wait_for_selector('body[data-ready=true][data-historical=false]')
        assert s.revisions(key)==before
        await page.locator('details').filter(has=page.locator('#revisions')).locator('summary').click();await page.locator('[data-restore="1"]').click();await page.wait_for_selector('body[data-revision="3"]')
        await page.locator('[data-restore="1"]').click();await page.wait_for_timeout(500);assert s.load(key)['spec']['revision']==3
        checks.append('explicit restore works; duplicate restore does not create history')
        assert await page.locator('#connect-ai').count()==0 and await page.locator('#cancel-ai').count()==0
        await page.locator('#toggle-edit').click();await page.locator('#edit-prompt').fill('Make the plate length 45 mm and preserve its width and thickness.');await page.locator('#run-ai').click()
        await page.wait_for_selector('#chatgpt-handoff:not([hidden])');prompt=await page.locator('#chatgpt-prompt').input_value();requests=EditRequests(s);request=requests.list(key)[0];data=requests.read(key,request['request_id'])
        assert request['request_id'] in prompt and data['status']=='pending' and data['screenshot'] and data['screenshot']['data_url'].startswith('data:image/png;base64,')
        assert s.load(key)['spec']['revision']==3
        caps=json.loads(urlopen(base+'capabilities.json').read());assert caps['agent']=='chatgpt' and not caps['external_model_service']
        # Model the exact tools that the ChatGPT conversation invokes, with no inference server.
        result=requests.apply(key,request['request_id'],SOURCE,{'length':45});assert result['spec']['revision']==4
        await page.wait_for_selector('body[data-revision="4"]');await page.wait_for_function("document.querySelector('#ai-progress').textContent.includes('ChatGPT applied')")
        await page.locator('#cad-canvas').screenshot(path=str(OUT/'chatgpt-edit-result.png'))
        checks.append('ChatGPT-only request contains image and revision; no autonomous inference; tool application refreshes viewer')
        lattice=build_tpms(s,{'family':'gyroid','length':20,'width':20,'height':20,'cell_size':8,'samples_per_cell':16});await page.goto(viewer_url(ROOT,lattice['model_id']));await page.wait_for_selector('body[data-ready=true]')
        assert 'Implicit mesh' in await page.locator('#stage-status').text_content()
        assert await page.locator('a[href="model.step"]').is_hidden()
        await page.locator('#toggle-grid').click();await page.locator('#cut').select_option('x');await page.locator('#slice').fill('50');await page.locator('#slice').dispatch_event('input')
        await page.locator('#cad-canvas').screenshot(path=str(OUT/'tpms-section.png'));assert not errors,errors
        checks.append('TPMS renders with honest mesh labels, hidden STEP export, grid and section controls')
        await browser.close()
    report={'status':'passed','checks':checks,'browser_errors':errors};(OUT/'viewer-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
asyncio.run(main())
