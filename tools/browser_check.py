#!/usr/bin/env python3
"""Test a real built or deployed artifact. No skipped test is a pass."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--url',required=True);p.add_argument('--expected-commit',required=True)
    p.add_argument('--output',type=Path,default=Path('evidence/browser'))
    p.add_argument('--executable');args=p.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    result={'schema':1,'url':args.url,'expected_commit':args.expected_commit,'started_utc':datetime.now(timezone.utc).isoformat(),'status':'failed','checks':[],'errors':[],'full_parity':False}
    def check(name,passed,detail=''):
        result['checks'].append({'name':name,'passed':bool(passed),'detail':detail})
        if not passed:raise AssertionError(name+': '+str(detail))
    code=1
    with sync_playwright() as pw:
        launch={'headless':True,'args':['--no-sandbox','--enable-unsafe-webgpu','--use-angle=swiftshader','--enable-features=Vulkan','--disable-vulkan-surface']}
        if args.executable:launch['executable_path']=args.executable
        browser=pw.chromium.launch(**launch)
        context=browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
        page=context.new_page()
        page.on('pageerror',lambda error:result['errors'].append(str(error)))
        try:
            response=page.goto(args.url,wait_until='networkidle',timeout=60000)
            check('dashboard_http',response is not None and response.status==200)
            page.wait_for_selector('#case-list tr',timeout=15000)
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
            page.goto(urljoin(args.url,'studio/app.html'),wait_until='domcontentloaded',timeout=60000)
            page.wait_for_selector('.app-header',timeout=90000)
            page.locator('.boot-overlay').wait_for(state='hidden',timeout=90000)
            check('webgpu_editor_boot',page.locator('canvas').count()>0)
            page.keyboard.press('Escape')
            nodes=page.locator('.react-flow__node');before=nodes.count()
            page.get_by_text('File',exact=True).first.click()
            with page.expect_file_chooser() as chooser:page.get_by_text('Import Model...',exact=True).click()
            chooser.value.set_files({'name':'compat-triangle.obj','mimeType':'text/plain','buffer':b'o CompatTriangle\nv -1 -1 0\nv 1 -1 0\nv 0 1 0\nf 1 2 3\n'})
            page.wait_for_function('(n)=>document.querySelectorAll(".react-flow__node").length>n',arg=before,timeout=30000)
            after=nodes.count();check('obj_import',after>before)
            page.keyboard.press('Control+z')
            page.wait_for_function('(n)=>document.querySelectorAll(".react-flow__node").length===n',arg=before,timeout=15000)
            check('undo_import',nodes.count()==before)
            page.keyboard.press('Control+Shift+z')
            page.wait_for_function('(n)=>document.querySelectorAll(".react-flow__node").length===n',arg=after,timeout=15000)
            check('redo_import',nodes.count()==after)
            page.screenshot(path=str(args.output/'studio.png'),full_page=True)
            check('no_uncaught_javascript_errors',not result['errors'],str(result['errors']))
            result['status']='passed';code=0
        except Exception as exc:
            result['failure']=str(exc)
            try:page.screenshot(path=str(args.output/'failure.png'),full_page=True)
            except Exception:pass
        finally:
            result['finished_utc']=datetime.now(timezone.utc).isoformat()
            (args.output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
            print(json.dumps(result,indent=2));browser.close()
    return code
if __name__=='__main__':sys.exit(main())
