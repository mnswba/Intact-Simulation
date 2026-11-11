"""Render our own local viewer for agent visual inspection, without changing saved views."""
import os
from pathlib import Path
from playwright.async_api import async_playwright

async def snapshot(url:str,output:Path,view='current'):
    browser_libs=Path.home()/'.local/share/intact-simulation/browser-libs'
    env=dict(os.environ)
    if browser_libs.is_dir():env['LD_LIBRARY_PATH']=str(browser_libs)+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,env=env,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        try:
            page=await browser.new_page(viewport={'width':1280,'height':900},device_scale_factor=1)
            await page.goto(url+('&' if '?' in url else '?')+'snapshot=1',wait_until='networkidle',timeout=30000)
            await page.wait_for_selector('body[data-ready="true"]',timeout=15000)
            detail=await page.locator('#error').text_content()
            if detail:raise ValueError('The viewer failed to render: '+detail)
            if view!='current':
                # These keyboard-accessible buttons share space with the cube.
                # A forced pointer click can hit the cube instead of the button.
                await page.locator('[data-view="'+view+'"]').evaluate('(button)=>button.click()')
                directions={'iso':[1,.8,1],'front':[0,0,1],'back':[0,0,-1],'right':[1,0,0],'left':[-1,0,0],'top':[0,1,0],'bottom':[0,-1,0]}
                await page.wait_for_timeout(400)
                actual=await page.evaluate('window.intactInspect.camera().direction')
                expected=directions[view];length=sum(n*n for n in expected)**.5
                if sum(a*b/length for a,b in zip(actual,expected))<.9999:raise ValueError('The viewer did not reach the requested snapshot direction.')
            await page.wait_for_timeout(400)
            output.parent.mkdir(parents=True,exist_ok=True)
            await page.locator('#cad-canvas').screenshot(path=str(output))
            return output.read_bytes()
        finally:await browser.close()
