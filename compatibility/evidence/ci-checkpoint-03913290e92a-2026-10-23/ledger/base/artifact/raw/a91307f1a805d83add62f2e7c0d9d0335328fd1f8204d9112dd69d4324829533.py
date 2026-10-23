#!/usr/bin/env python3
"""End-to-end tests against the actual deployed/built Rust + Three.js modeller."""
import argparse,json,shutil,sys
from datetime import datetime,timezone
from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin,urlparse
from PIL import Image,ImageChops,ImageStat
from playwright.sync_api import sync_playwright
CUBE=b'o ImportedCube\nv -1 -1 -1\nv 1 -1 -1\nv 1 1 -1\nv -1 1 -1\nv -1 -1 1\nv 1 -1 1\nv 1 1 1\nv -1 1 1\nf 1 4 3 2\nf 5 6 7 8\nf 1 2 6 5\nf 2 3 7 6\nf 3 4 8 7\nf 4 1 5 8\n'
def main():
 p=argparse.ArgumentParser();p.add_argument('--url',required=True);p.add_argument('--commit',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 result={'schema':1,'url':a.url,'commit':a.commit,'status':'failed','checks':[],'errors':[],'console_errors':[],'started_utc':datetime.now(timezone.utc).isoformat(),'scope':'limited object modeller, not Blender parity'}
 def check(name,value,detail=None):
  result['checks'].append({'name':name,'passed':bool(value),'detail':detail});print(name,bool(value),flush=True)
  if not value:raise AssertionError(name+': '+str(detail))
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=shutil.which('google-chrome'),headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  ctx=browser.new_context(viewport={'width':1400,'height':950},accept_downloads=True)
  if urlparse(a.url).hostname=='rawcdn.githack.com':ctx.add_cookies([{'name':'__Http-phish','value':'1','domain':'rawcdn.githack.com','path':'/','secure':True,'httpOnly':True,'sameSite':'Lax'}])
  page=ctx.new_page();page.on('pageerror',lambda e:result['errors'].append(str(e)));page.on('console',lambda m:result['console_errors'].append(m.text) if m.type=='error' else None)
  try:
   response=page.goto(a.url,wait_until='domcontentloaded',timeout=90000);check('http_200',response is not None and response.status==200)
   page.wait_for_function('window.__blended?.ready === true || window.__blended?.error',timeout=90000)
   check('application_ready',page.evaluate('window.__blended.ready'),page.evaluate('window.__blended.error ?? null'))
   manifest=page.request.get(urljoin(a.url,'build.json')).json();check('source_commit',manifest['source_commit']==a.commit,manifest['source_commit']);check('honest_scope',manifest['blender_parity'] is False)
   getdoc=lambda:page.evaluate('window.__blended.getDocument()')
   check('rust_default_cube',len(getdoc()['objects'])==1 and len(getdoc()['objects'][0]['indices'])==36)
   check('wasm_geometry_bounds',page.evaluate('window.__blended.getPrimitiveBounds()')==[-1,1])
   page.wait_for_function('window.__blended.getRenderStats().calls>0')
   page.wait_for_timeout(500);canvas=page.locator('#viewport');png=canvas.screenshot();im=Image.open(BytesIO(png)).convert('RGB');w,h=im.size;centre=im.crop((w//4,h//4,w*3//4,h*3//4))
   warm=sum(1 for r,g,b in centre.getdata() if r-g>12 and g-b>6 and r>80)
   check('rendered_cube_pixels',warm>500,{'warm_pixels':warm,'centre_variance':ImageStat.Stat(centre).var})
   (a.output/'cube.png').write_bytes(png)
   page.locator('#delete').click();check('delete_object',len(getdoc()['objects'])==0)
   page.wait_for_timeout(150);empty=Image.open(BytesIO(canvas.screenshot())).convert('RGB');check('geometry_changes_render',ImageChops.difference(im,empty).getbbox() is not None)
   page.locator('#undo').click();check('undo_delete',len(getdoc()['objects'])==1)
   page.locator('#add-cube').click();check('add_rust_cube',len(getdoc()['objects'])==2)
   page.locator('#position-0').fill('3');page.locator('#position-0').press('Tab');check('numeric_transform',getdoc()['objects'][-1]['position'][0]==3)
   page.locator('#undo').click();check('undo_transform',getdoc()['objects'][-1]['position'][0]==0)
   page.locator('#redo').click();check('redo_transform',getdoc()['objects'][-1]['position'][0]==3)
   page.locator('#duplicate').click();check('duplicate',len(getdoc()['objects'])==3);page.locator('#delete').click();check('delete_duplicate',len(getdoc()['objects'])==2)
   page.locator('#add-sphere').click();check('sphere',len(getdoc()['objects'])==3 and len(getdoc()['objects'][-1]['positions'])>100)
   page.locator('#undo').click();check('undo_add',len(getdoc()['objects'])==2)
   with page.expect_download() as dl:page.locator('#save').click()
   saved=dl.value;saved.save_as(str(a.output/'scene.blended.json'));saved_doc=json.loads((a.output/'scene.blended.json').read_text());check('scene_save',saved_doc==getdoc())
   page.locator('#add-plane').click();check('add_rust_plane',len(getdoc()['objects'])==3 and len(getdoc()['objects'][-1]['indices'])==6)
   with page.expect_file_chooser() as fc:page.locator('#open').click()
   fc.value.set_files(str(a.output/'scene.blended.json'));page.wait_for_function('window.__blended.getDocument().objects.length===2');check('scene_round_trip',getdoc()==saved_doc)
   with page.expect_file_chooser() as fc:page.locator('#import').click()
   fc.value.set_files({'name':'cube.obj','mimeType':'text/plain','buffer':CUBE});page.wait_for_function('window.__blended.getDocument().objects.length===3');check('obj_import',getdoc()['objects'][-1]['name']=='ImportedCube')
   with page.expect_download() as dl:page.locator('#export-obj').click()
   dl.value.save_as(str(a.output/'scene.obj'));text=(a.output/'scene.obj').read_text();check('obj_export','\nv ' in text and '\nf ' in text and 'ImportedCube' in text)
   with page.expect_download() as dl:page.locator('#export-stl').click()
   dl.value.save_as(str(a.output/'scene.stl'));check('stl_export',(a.output/'scene.stl').stat().st_size>84)
   before=len(getdoc()['objects'])
   with page.expect_file_chooser() as fc:page.locator('#import').click()
   fc.value.set_files(str(a.output/'scene.stl'));page.wait_for_function('(n)=>window.__blended.getDocument().objects.length===n',arg=before+1);check('stl_import',len(getdoc()['objects'])==before+1)
   page.locator('#tests').click();page.wait_for_selector('#test-dialog[open]');compat=page.evaluate('window.__blendedCompatibility');check('rust_compatibility_17',compat['passed']==17 and compat['status']=='passed',compat);page.locator('#close-tests').click()
   with page.expect_download() as dl:page.locator('#image').click()
   dl.value.save_as(str(a.output/'render.png'));render=Image.open(a.output/'render.png').convert('RGB');check('png_render',render.width>200 and sum(ImageStat.Stat(render).var)>10)
   page.locator('#frame').click();page.wait_for_timeout(200);page.screenshot(path=str(a.output/'application.png'),full_page=True)
   check('no_browser_errors',not result['errors'] and not result['console_errors'],{'errors':result['errors'],'console':result['console_errors']})
   result['status']='passed'
  except Exception as e:
   result['failure']=str(e)
   try:page.screenshot(path=str(a.output/'failure.png'),full_page=True)
   except Exception:pass
  finally:
   result['finished_utc']=datetime.now(timezone.utc).isoformat();(a.output/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));browser.close()
 return 0 if result['status']=='passed' else 1
if __name__=='__main__':sys.exit(main())
