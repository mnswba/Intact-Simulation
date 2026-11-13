"""Run against a built app served at --url; artifacts stay outside source control."""
import argparse, asyncio, json, struct
from pathlib import Path
from playwright.async_api import async_playwright, expect

async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--url',default='http://127.0.0.1:8766');parser.add_argument('--out',required=True);parser.add_argument('--framed',action='store_true');args=parser.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(headless=True,args=['--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        errors=[]; requests=[]
        context=await browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
        page=await context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('request',lambda r:requests.append((r.method,r.url)))
        host=page
        await host.goto(args.url,wait_until='networkidle')
        if args.framed:page=host.frame_locator('#intact-browser-frame')
        await page.locator('#status').filter(has_text='Built and checked').wait_for()
        assert await page.locator('#dimensions').inner_text()=='80.00 × 80.00 × 8.00'
        assert await page.locator('#fit + #reset').count()==1
        await page.locator('#bottom').click();await host.wait_for_timeout(500)
        await host.screenshot(path=str(out/'desktop-bottom.png'),full_page=True)
        await page.locator('#reset').click()
        # Edit actual parametric dimensions and verify rebuild, then undo.
        radius=page.get_by_role('spinbutton',name='disk Radius · mm',exact=True)
        await radius.fill('45');await page.locator('#apply').click()
        await expect(page.locator('#dimensions')).to_have_text('90.00 × 90.00 × 8.00')
        await page.locator('#undo').click()
        await expect(page.locator('#dimensions')).to_have_text('80.00 × 80.00 × 8.00')
        # Untrusted model text cannot invoke arbitrary code or replace last good mesh.
        await page.locator('summary').filter(has_text='Design with ChatGPT').click()
        await page.locator('#recipe').fill('{"format":"intact-browser-1","url":"https://evil.invalid"}')
        await page.locator('#build').click();assert 'Recipe rejected' in await page.locator('#status').inner_text()
        assert await page.locator('#dimensions').inner_text()=='80.00 × 80.00 × 8.00'
        await page.locator('summary').filter(has_text='Save & review').click()
        async with host.expect_download() as info:await page.locator('#stl').click()
        stl=await info.value;await stl.save_as(out/'flange.stl')
        data=(out/'flange.stl').read_bytes();triangles=struct.unpack_from('<I',data,80)[0]
        assert len(data)==84+50*triangles
        assert triangles==int((await page.locator('#triangles').inner_text()).replace(',',''))
        async with host.expect_download() as info:await page.locator('#save').click()
        saved=await info.value;await saved.save_as(out/'flange.json')
        recipe=json.loads((out/'flange.json').read_text());assert recipe['name']=='Six-hole flange'
        await page.locator('#box').click()
        await expect(page.locator('#dimensions')).to_have_text('40.00 × 30.00 × 20.00')
        await page.locator('#import').set_input_files(out/'flange.json');await page.locator('#build').click()
        await expect(page.locator('#dimensions')).to_have_text('80.00 × 80.00 × 8.00')
        # Kernel failure (empty Boolean) also preserves valid output.
        empty={'format':'intact-browser-1','name':'Empty','units':'mm','nodes':[{'id':'a','type':'box','size':[5,5,5]},{'id':'b','type':'box','size':[5,5,5]},{'id':'c','type':'subtract','inputs':['a','b']}],'result':'c'}
        await page.locator('#recipe').fill(json.dumps(empty));await page.locator('#build').click()
        await page.locator('#status').filter(has_text='Build rejected').wait_for()
        assert await page.locator('#dimensions').inner_text()=='80.00 × 80.00 × 8.00'
        await page.locator('#bracket').click();await page.locator('#model-name').filter(has_text='Mounting bracket').wait_for()
        await page.locator('#status').filter(has_text='Built and checked').wait_for()
        await host.screenshot(path=str(out/'desktop-bracket.png'),full_page=True)
        # Responsive viewport and touch settings do not constitute real mobile hardware validation.
        for name,width,height in [('phone',390,844),('tablet',820,1180)]:
            mobile=await browser.new_context(viewport={'width':width,'height':height},has_touch=True,is_mobile=True,device_scale_factor=1)
            outer=await mobile.new_page();outer.on('pageerror',lambda e:errors.append(str(e)))
            await outer.goto(args.url);p=outer.frame_locator('#intact-browser-frame') if args.framed else outer
            await p.locator('#status').filter(has_text='Built and checked').wait_for()
            assert await p.locator('body').evaluate('(body)=>body.scrollWidth<=innerWidth'),name
            await p.locator('#bottom').click();await outer.wait_for_timeout(300)
            await outer.screenshot(path=str(out/f'{name}.png'),full_page=True)
            await mobile.close()
        assert not errors,errors
        assert all(method=='GET' and (args.framed or url.startswith(args.url) or url.startswith('blob:')) for method,url in requests),requests
        receipt={'chromium_desktop':True,'responsive_phone_tablet_emulation':True,'real_ios_android_tested':False,'native_mac_tested':False,'stl_triangles':triangles,'recipe_roundtrip':True,'dimension_rebuild_and_undo':True,'invalid_and_empty_preserve_previous':True,'model_upload_requests':False,'page_errors':errors}
        (out/'receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
        await browser.close()

asyncio.run(main())
