#!/usr/bin/env python3
"""Exercise real browser rendering; software GPU CI is not a hardware benchmark."""
import argparse
from datetime import datetime, timezone
from io import BytesIO
import json
from pathlib import Path
import shutil
import sys
import time
from urllib.parse import urljoin, urlparse
from PIL import Image, ImageChops, ImageStat
from playwright.sync_api import sync_playwright, TimeoutError as BrowserTimeout

# Observe real calls without mocking the GPU or suppressing validation errors.
GPU_DIAGNOSTICS = r'''(() => {
  const d = window.__blendedGpuDiagnostics = {buffers:0, submissions:0, recent:[], errors:[], lost:[], adapters:[]};
  if (!globalThis.GPUAdapter || !globalThis.GPUDevice) return;
  const requestDevice = GPUAdapter.prototype.requestDevice;
  GPUAdapter.prototype.requestDevice = async function(...args) {
    const info=this.info;
    if(info)d.adapters.push({vendor:info.vendor,architecture:info.architecture,device:info.device,description:info.description});
    const device=await requestDevice.apply(this,args);
    device.addEventListener('uncapturederror',e=>d.errors.push(String(e.error?.message ?? e.error)));
    device.lost.then(info=>d.lost.push({reason:info.reason,message:info.message}));
    return device;
  };
  const createBuffer=GPUDevice.prototype.createBuffer;
  GPUDevice.prototype.createBuffer=function(desc) {
    d.buffers++;d.recent.push({label:desc.label,size:desc.size,mapped:desc.mappedAtCreation});
    if(d.recent.length>32)d.recent.shift();
    try{return createBuffer.call(this,desc);}catch(e){d.errors.push(String(e));throw e;}
  };
  const submit=GPUQueue.prototype.submit;
  GPUQueue.prototype.submit=function(...args){const result=submit.apply(this,args);d.submissions++;return result;};
})();'''

def centre_image(png):
    image=Image.open(BytesIO(png)).convert('RGB');w,h=image.size
    return image.crop((int(w*.25),int(h*.25),int(w*.75),int(h*.75)))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--url',required=True);p.add_argument('--expected-commit',required=True)
    p.add_argument('--output',type=Path,default=Path('evidence/browser'));p.add_argument('--executable')
    args=p.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    result={'schema':1,'url':args.url,'expected_commit':args.expected_commit,'started_utc':datetime.now(timezone.utc).isoformat(),'status':'failed','checks':[],'errors':[],'console':[],'full_parity':False,'gpu_execution':'SwiftShader software WebGPU; not a hardware performance result'}
    def check(name,passed,detail=''):
        result['checks'].append({'name':name,'passed':bool(passed),'detail':detail})
        print(name,bool(passed),flush=True)
        if not passed:raise AssertionError(name+': '+str(detail))
    code=1
    with sync_playwright() as pw:
        # This exact backend passed real texture readback and 1,000 mapped
        # buffer allocations in diagnostic run 39824082452. Do not require a
        # host Vulkan device. Software rendering needs a longer GPU watchdog
        # budget; the job/test timeouts still bound overall execution.
        launch={'headless':True,'args':['--no-sandbox','--disable-dev-shm-usage','--disable-gpu-watchdog','--enable-unsafe-webgpu','--use-angle=swiftshader']}
        executable=args.executable or shutil.which('google-chrome') or shutil.which('chromium')
        if executable:launch['executable_path']=executable
        browser=pw.chromium.launch(**launch);result['browser_version']=browser.version
        context=browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
        context.add_init_script(GPU_DIAGNOSTICS)
        if urlparse(args.url).hostname=='rawcdn.githack.com':
            context.add_cookies([{'name':'__Http-phish','value':'1','domain':'rawcdn.githack.com','path':'/','secure':True,'httpOnly':True,'sameSite':'Lax'}])
        page=context.new_page()
        page.on('pageerror',lambda error:result['errors'].append(str(error)))
        page.on('console',lambda msg:result['console'].append({'type':msg.type,'text':msg.text}) if msg.type in {'warning','error'} else None)
        try:
            response=page.goto(args.url,wait_until='networkidle',timeout=90000)
            check('dashboard_http',response is not None and response.status==200)
            page.wait_for_selector('#case-list tr',timeout=30000)
            check('traceability_rows',page.locator('#case-list tr').count()==17)
            check('parity_disclosure',page.get_by_text('Full Blender parity is not established.',exact=True).is_visible())
            manifest=page.request.get(urljoin(args.url,'build.json')).json()
            check('deployed_commit',manifest.get('source_commit')==args.expected_commit,str(manifest.get('source_commit')))
            check('studio_built',manifest.get('studio_built') is True)
            page.get_by_role('button',name='Run browser checks').click()
            page.wait_for_function('window.__blendedTestResults?.status === "passed" || window.__blendedTestResults?.status === "failed" || window.__blendedTestResults?.status === "blocked"',timeout=60000)
            wasm=page.evaluate('window.__blendedTestResults')
            check('rust_wasm_conformance',wasm['status']=='passed' and wasm['passed']==17,str(wasm))
            page.screenshot(path=str(args.output/'compatibility.png'),full_page=True)
            page.goto(urljoin(args.url,'studio/app.html'),wait_until='domcontentloaded',timeout=90000)
            page.wait_for_selector('.app-header',timeout=90000)
            page.locator('.boot-overlay').wait_for(state='hidden',timeout=90000)
            check('webgpu_editor_boot',page.locator('canvas.viewport-canvas').count()==1)
            try:
                skip=page.get_by_role('button',name='Skip',exact=True)
                skip.wait_for(state='visible',timeout=5000);skip.click()
            except BrowserTimeout:page.keyboard.press('Escape')
            page.wait_for_function('window.__blendedGpuDiagnostics.submissions > 2 || window.__blendedGpuDiagnostics.errors.length || window.__blendedGpuDiagnostics.lost.length',timeout=90000)
            gpu=page.evaluate('window.__blendedGpuDiagnostics')
            check('gpu_device_alive',not gpu['errors'] and not gpu['lost'],str(gpu))
            check('real_gpu_commands_submitted',gpu['submissions']>2,str(gpu['submissions']))
            canvas=page.locator('canvas.viewport-canvas');deadline=time.monotonic()+30
            while True:
                before_png=canvas.screenshot();before_image=centre_image(before_png)
                if sum(ImageStat.Stat(before_image).var)>1.0 or time.monotonic()>deadline:break
                page.wait_for_timeout(250)
            (args.output/'viewport-before.png').write_bytes(before_png)
            check('viewport_interior_not_blank',sum(ImageStat.Stat(before_image).var)>1.0)
            nodes=page.locator('.react-flow__node');before=nodes.count()
            page.get_by_text('File',exact=True).first.click()
            with page.expect_file_chooser() as chooser:page.get_by_text('Import Model...',exact=True).click()
            chooser.value.set_files({'name':'compat-triangle.obj','mimeType':'text/plain','buffer':b'o CompatTriangle\nv -1 -1 0\nv 1 -1 0\nv 0 1 0\nf 1 2 3\n'})
            page.wait_for_function('(n)=>document.querySelectorAll(".react-flow__node").length>n',arg=before,timeout=30000)
            after=nodes.count();check('obj_import',after>before)
            changed=False;deadline=time.monotonic()+30
            while time.monotonic()<deadline:
                after_png=canvas.screenshot();after_image=centre_image(after_png)
                if before_image.size==after_image.size and ImageChops.difference(before_image,after_image).getbbox() is not None:changed=True;break
                page.wait_for_timeout(200)
            (args.output/'viewport-after.png').write_bytes(after_png)
            check('viewport_interior_changes_after_import',changed,'Smoke check, not Cycles reference-render parity')
            page.keyboard.press('Control+z')
            page.wait_for_function('(n)=>document.querySelectorAll(".react-flow__node").length===n',arg=before,timeout=15000)
            check('undo_import',nodes.count()==before)
            page.keyboard.press('Control+Shift+z')
            page.wait_for_function('(n)=>document.querySelectorAll(".react-flow__node").length===n',arg=after,timeout=15000)
            check('redo_import',nodes.count()==after)
            page.screenshot(path=str(args.output/'studio.png'),full_page=True)
            gpu=page.evaluate('window.__blendedGpuDiagnostics')
            check('no_gpu_errors',not gpu['errors'] and not gpu['lost'],str(gpu))
            check('no_javascript_or_logged_errors',not result['errors'] and not any(c['type']=='error' for c in result['console']),str(result['errors']))
            result['status']='passed';code=0
        except Exception as exc:
            result['failure']=str(exc)
            try:
                page.screenshot(path=str(args.output/'failure.png'),full_page=True)
                (args.output/'page.txt').write_text(page.locator('body').inner_text())
            except Exception:pass
        finally:
            try:result['gpu']=page.evaluate('window.__blendedGpuDiagnostics')
            except Exception:pass
            result['finished_utc']=datetime.now(timezone.utc).isoformat()
            (args.output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
            print(json.dumps(result,indent=2));browser.close()
    return code
if __name__=='__main__':sys.exit(main())
