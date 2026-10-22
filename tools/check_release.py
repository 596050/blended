#!/usr/bin/env python3
"""Real artifact checks: execute WASM, import/render a cube, undo and redo.

An empty scene may legitimately render a solid background. Visual assertions
therefore apply AFTER importing known geometry. Browser contexts are isolated
so GPU diagnostic hooks never cross a document navigation.
"""
import argparse
from datetime import datetime,timezone
from io import BytesIO
import json
from pathlib import Path
import shutil
import sys
import time
from urllib.parse import urljoin,urlparse
from PIL import Image,ImageChops,ImageStat
from playwright.sync_api import sync_playwright,TimeoutError as BrowserTimeout
from browser_check import GPU_DIAGNOSTICS

CUBE=b'''o CompatibilityCube
v -1 -1 -1
v 1 -1 -1
v 1 1 -1
v -1 1 -1
v -1 -1 1
v 1 -1 1
v 1 1 1
v -1 1 1
f 1 4 3 2
f 5 6 7 8
f 1 2 6 5
f 2 3 7 6
f 3 4 8 7
f 4 1 5 8
'''
def interior(png):
    im=Image.open(BytesIO(png)).convert('RGB');w,h=im.size
    return im.crop((w//4,h//4,w*3//4,h*3//4))
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--url',required=True);p.add_argument('--expected-commit',required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--executable')
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    r={'schema':2,'url':a.url,'expected_commit':a.expected_commit,'started_utc':datetime.now(timezone.utc).isoformat(),'status':'failed','checks':[],'errors':[],'console':[],'full_parity':False,'gpu_execution':'Software GPU, not a performance benchmark'}
    def check(name,value,detail=None):
        r['checks'].append({'name':name,'passed':bool(value),'detail':detail});print(name,bool(value),flush=True)
        if not value:raise AssertionError(name+': '+str(detail))
    def events(page):
        page.on('pageerror',lambda e:r['errors'].append(str(e)))
        page.on('console',lambda m:r['console'].append({'type':m.type,'text':m.text}) if m.type in ['error','warning'] else None)
    def context(browser,gpu=False):
        c=browser.new_context(viewport={'width':1200,'height':850},accept_downloads=True)
        if gpu:c.add_init_script(GPU_DIAGNOSTICS)
        if urlparse(a.url).hostname=='rawcdn.githack.com':
            c.add_cookies([{'name':'__Http-phish','value':'1','domain':'rawcdn.githack.com','path':'/','secure':True,'httpOnly':True,'sameSite':'Lax'}])
        return c
    with sync_playwright() as pw:
        exe=a.executable or shutil.which('google-chrome') or shutil.which('chromium')
        b=pw.chromium.launch(executable_path=exe,headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu-watchdog','--enable-unsafe-webgpu','--use-angle=swiftshader'])
        r['browser_version']=b.version;c=context(b);page=c.new_page();events(page)
        try:
            res=page.goto(a.url,wait_until='networkidle',timeout=90000)
            check('dashboard_http',res is not None and res.status==200)
            page.wait_for_selector('#case-list tr',timeout=30000)
            check('traceability_rows',page.locator('#case-list tr').count()==17)
            check('parity_disclosure',page.get_by_text('Full Blender parity is not established.',exact=True).is_visible())
            build=page.request.get(urljoin(a.url,'build.json')).json()
            check('exact_deployed_commit',build.get('source_commit')==a.expected_commit,build.get('source_commit'))
            check('studio_built',build.get('studio_built') is True)
            page.get_by_role('button',name='Run browser checks').click()
            page.wait_for_function('! ["not_run","running"].includes(window.__blendedTestResults?.status)',timeout=60000)
            wasm=page.evaluate('window.__blendedTestResults');r['wasm']=wasm
            check('rust_wasm_conformance',wasm.get('status')=='passed' and wasm.get('passed')==17)
            page.screenshot(path=str(a.output/'compatibility.png'),full_page=True)
            c.close();c=context(b,gpu=True);page=c.new_page();events(page)
            page.goto(urljoin(a.url,'studio/app.html'),wait_until='domcontentloaded',timeout=90000)
            page.wait_for_selector('.app-header',timeout=90000)
            page.locator('.boot-overlay').wait_for(state='hidden',timeout=90000)
            try:
                skip=page.get_by_role('button',name='Skip',exact=True)
                skip.wait_for(state='visible',timeout=4000);skip.click()
            except BrowserTimeout:page.keyboard.press('Escape')
            canvas=page.locator('canvas.viewport-canvas')
            check('editor_canvas',canvas.count()==1)
            page.wait_for_function('window.__blendedGpuDiagnostics.submissions>2',timeout=60000)
            before_png=canvas.screenshot();before_im=interior(before_png)
            (a.output/'before-import.png').write_bytes(before_png)
            nodes=page.locator('.react-flow__node');n=nodes.count()
            page.get_by_text('File',exact=True).first.click()
            with page.expect_file_chooser() as fc:page.get_by_text('Import Model...',exact=True).click()
            fc.value.set_files({'name':'compatibility-cube.obj','mimeType':'text/plain','buffer':CUBE})
            page.wait_for_function('(n)=>document.querySelectorAll(".react-flow__node").length>n',arg=n,timeout=60000)
            count=nodes.count();check('obj_cube_import',count>n)
            deadline=time.monotonic()+45;changed=False
            while time.monotonic()<deadline:
                png=canvas.screenshot();im=interior(png)
                changed=im.size==before_im.size and ImageChops.difference(im,before_im).getbbox() is not None
                if changed and sum(ImageStat.Stat(im).var)>1.0:break
                page.wait_for_timeout(250)
            (a.output/'after-import.png').write_bytes(png)
            r['interior_variance']=ImageStat.Stat(im).var
            check('rendered_geometry_not_blank',sum(r['interior_variance'])>1.0,r['interior_variance'])
            check('rendered_geometry_changes_pixels',changed)
            page.keyboard.press('Control+z')
            page.wait_for_function('(n)=>document.querySelectorAll(".react-flow__node").length===n',arg=n,timeout=15000)
            check('undo_import',nodes.count()==n)
            page.keyboard.press('Control+Shift+z')
            page.wait_for_function('(n)=>document.querySelectorAll(".react-flow__node").length===n',arg=count,timeout=15000)
            check('redo_import',nodes.count()==count)
            gpu=page.evaluate('window.__blendedGpuDiagnostics');r['gpu']=gpu
            check('real_gpu_submission',gpu['submissions']>3,gpu['submissions'])
            check('gpu_not_lost',not gpu['lost'] and not gpu['errors'],{'lost':gpu['lost'],'errors':gpu['errors']})
            check('no_browser_errors',not r['errors'] and not any(x['type']=='error' for x in r['console']),r['errors'])
            page.screenshot(path=str(a.output/'studio.png'),full_page=True)
            r['status']='passed'
        except Exception as e:
            r['failure']=str(e)
            try:page.screenshot(path=str(a.output/'failure.png'),full_page=True);r['gpu']=page.evaluate('window.__blendedGpuDiagnostics ?? null')
            except Exception:pass
        finally:
            r['finished_utc']=datetime.now(timezone.utc).isoformat()
            (a.output/'result.json').write_text(json.dumps(r,indent=2)+'\n')
            print(json.dumps(r,indent=2));b.close()
    return 0 if r['status']=='passed' else 1
if __name__=='__main__':sys.exit(main())
