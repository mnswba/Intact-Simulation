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
                await page.locator('#view-cube [data-view="'+view+'"]').evaluate('(button)=>button.click()')
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

async def presentation_images(url:str):
    """Render a pinned revision without changing the user's live camera or view."""
    import base64
    browser_libs=Path.home()/'.local/share/intact-simulation/browser-libs';env=dict(os.environ)
    if browser_libs.is_dir():env['LD_LIBRARY_PATH']=str(browser_libs)
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,env=env,args=['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        try:
            page=await browser.new_page(viewport={'width':2240,'height':1260},device_scale_factor=1)
            await page.goto(url+('&' if '?' in url else '?')+'snapshot=1',wait_until='networkidle',timeout=45000)
            await page.wait_for_selector('body[data-ready="true"]',timeout=30000)
            error=await page.locator('#error').text_content()
            if error:raise ValueError('Presentation render failed: '+error)
            await page.evaluate("document.body.dataset.viewportOnly='true'")
            await page.wait_for_timeout(200)
            # These are ordinary display controls. snapshot=1 and the pinned
            # historical URL prevent any preference/revision writes.
            if await page.evaluate('window.intactInspect.view().grid'):await page.locator('#toggle-grid').evaluate('(button)=>button.click()')
            await page.locator('#setting-quality').evaluate("el=>{el.value='final';el.dispatchEvent(new Event('change'));el.dispatchEvent(new Event('input'));}")
            images=[]
            for orientation,title in [('current','Current design review'),('iso','Assembly overview'),('front','Front elevation'),('top','Plan view'),('right','Right elevation')]:
                if orientation!='current':
                    await page.locator('#drawing-clear').evaluate('(button)=>button.click()')
                    await page.locator('#clear-measurements').evaluate('(button)=>button.click()')
                    if await page.evaluate('window.intactInspect.view().component_names'):await page.locator('#add-names').evaluate('(button)=>button.click()')
                    await page.locator('#reset').evaluate('(button)=>button.click()')
                    await page.locator('#view-cube [data-view="'+orientation+'"]').evaluate('(button)=>button.click()')
                await page.wait_for_timeout(250)
                data_url=await page.evaluate('window.intactInspect.captureImage()')
                if len(data_url)>4*1024*1024:raise ValueError('Presentation image exceeds the supported image size; reduce display detail.')
                images.append({'name':title,'data_url':data_url})
            return images
        finally:await browser.close()
