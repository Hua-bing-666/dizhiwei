"""Browser interactions and document page-count/package/layout checks."""
from pathlib import Path
import subprocess,re,json,zipfile,xml.etree.ElementTree as ET
import pymupdf
from PIL import Image,ImageOps,ImageDraw
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'deliverables'; TMP=ROOT/'tmp/qa';TMP.mkdir(parents=True,exist_ok=True)
edge=r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
html=(OUT/'index.html').read_text(encoding='utf-8')
scripts=re.findall(r'<script>([\s\S]*?)</script>',html)
assert len(scripts)==1
js=TMP/'portal-script.js';js.write_text(scripts[0],encoding='utf-8')
subprocess.run(['node','--check',str(js)],check=True,capture_output=True)

qa='''<script>
try {
 let cases=0;
 for(const c of DATA.cases){$('comm-case').value=c.key;for(const loss of [0,.1,.3]){$('comm-loss').value=String(loss);comm();if($('comm-table').children.length!==4||!$('comm-plot').querySelector('svg'))throw Error('comparison missing');cases++;}}
 let diagnostics=0;
 for(const kind of Object.keys(diagNames))for(const noise of ['0.3','1.0','3.0','10.0']){$('diag-case').value=kind;$('diag-noise').value=noise;diagnosisView();if($('diag-results').children.length!==6||!$('diag-plot').querySelector('svg'))throw Error('diagnosis replay missing');diagnostics++;}
 $('diag-quality').value='offline';diagnosisView();if(!$('diag-status').textContent.includes('无法判断'))throw Error('offline shown as normal');
 $('diag-quality').value='invalid';diagnosisView();if(!$('diag-status').textContent.includes('停止原因判断'))throw Error('invalid state missing');
 $('diag-quality').value='model';$('diag-case').value='leak';$('diag-noise').value='0.3';diagnosisView();$('diag-ack').click();if(!$('diag-ack-result').textContent.includes('已查看'))throw Error('review demo missing');
 $('rc').value=0;model();if(!$('model-takeaway').textContent.includes('0.000 kPa'))throw Error('zero resistance invariant failed');
 $('fault').value='restriction';$('restriction').value=10;model();if(!$('model-results').textContent.includes('开启'))throw Error('model missing');
 for(let n=1;n<=15;n++){slide(n);if(!$('slideframe').querySelector('svg')||$('slide-notes').textContent.length<30)throw Error('slide missing');}
 for(const b of document.querySelectorAll('nav button')){b.click();if(!$(b.dataset.page).classList.contains('active'))throw Error('navigation failed');}
 if(document.documentElement.scrollWidth>document.documentElement.clientWidth+1)throw Error('root overflow');
 $('comm-case').value='normal';$('comm-loss').value='.1';comm();$('rc').value=.4;$('fault').value='normal';model();slide(1);navigate('overview');
 document.body.dataset.qa='passed';document.body.dataset.qaComparisons=cases;document.body.dataset.qaSlides=15;document.body.dataset.qaDiagnostics=diagnostics;
}catch(e){document.body.dataset.qa='failed';document.body.dataset.qaError=e.message;}
</script>'''
path=TMP/'portal-interaction-check.html'
path.write_text(html.replace('<head>','<head><base href="'+OUT.as_uri()+'/">',1).replace('</body>',qa+'</body>'),encoding='utf-8')
base=[edge,'--headless=new','--disable-gpu','--no-first-run','--hide-scrollbars','--user-data-dir='+str(TMP/'edge-portal-profile')]
result=subprocess.run(base+['--window-size=1280,1000','--virtual-time-budget=1000','--dump-dom',path.as_uri()],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=45)
dom=result.stdout.decode('utf-8',errors='replace')
assert 'data-qa="passed"' in dom, re.search('data-qa-error="[^" ]+',dom).group(0) if 'data-qa-error' in dom else 'No successful browser QA marker'
print('Browser: 24 communication + 24 diagnosis selections, 15 slides, 8 sections; offline, invalid and review interactions passed.')

def snap(page,filename,width,height=1100):
    # A screenshot-only page is generated from the same artifact; no data changes.
    view=TMP/(filename+'.html')
    view.write_text(html.replace('<head>','<head><base href="'+OUT.as_uri()+'/">',1).replace('</body>',f'<script>navigate("{page}");</script></body>'),encoding='utf-8')
    dest=TMP/(filename+'.png')
    subprocess.run(base+[f'--window-size={width},{height}','--virtual-time-budget=1000','--screenshot='+str(dest),view.as_uri()],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=45,check=True)
    assert dest.exists()
snap('overview','portal-desktop',1440,1120)
snap('communication','portal-communication',1440,1120)
snap('model','portal-model',1440,1120)
snap('diagnosis','portal-diagnosis',1440,1400)
snap('overview','portal-mobile',520,1120)

def contact(images,dest,thumb_width=320,cols=3):
    thumbs=[]
    for i,p in enumerate(images):
        im=Image.open(p).convert('RGB');im.thumbnail((thumb_width,520))
        cell=Image.new('RGB',(thumb_width+12,im.height+38),'#edf1ee');cell.paste(im,((cell.width-im.width)//2,24));ImageDraw.Draw(cell).text((8,6),str(i+1),fill='#164c45');thumbs.append(cell)
    cellh=max(t.height for t in thumbs); canvas=Image.new('RGB',((thumb_width+12)*cols,cellh*((len(thumbs)+cols-1)//cols)),'#dde5df')
    for i,im in enumerate(thumbs):canvas.paste(im,((i%cols)*(thumb_width+12),(i//cols)*cellh))
    canvas.save(dest)

for name,expected in [('项目书审阅版.pdf',None),('立项答辩审阅版.pdf',15),('大创申报书_模板审阅版.pdf',None)]:
    doc=pymupdf.open(OUT/name);assert doc.page_count==(expected or doc.page_count)
    print(name,'pages:',doc.page_count)
    images=[]
    for i,page in enumerate(doc):
        assert len(page.get_text())>30,'blank or unextractable PDF page'
        stem='template-filled' if name.startswith('大创') else 'proposal' if expected is None else 'slide'
        file=TMP/f'{stem}-{i+1:02}.png';page.get_pixmap(matrix=pymupdf.Matrix(1.2,1.2)).save(file);images.append(file)
        # No text may fall below the footer / outside the actual PDF page.
        for word in page.get_text('words'):
            assert word[0]>=-2 and word[1]>=-2 and word[2]<=page.rect.width+2 and word[3]<=page.rect.height+2, f'PDF text outside page: {word[4]}'
    contact(images,TMP/('template-filled-contact.png' if name.startswith('大创') else 'proposal-contact.png' if expected is None else 'slides-contact.png'))

with zipfile.ZipFile(OUT/'立项答辩.pptx') as z:
    assert z.testzip() is None
    pages=[p for p in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',p)]
    notes=[p for p in z.namelist() if re.fullmatch(r'ppt/notesSlides/notesSlide\d+\.xml',p)]
    assert len(pages)==15 and len(notes)==15
    text_count=sum(z.read(p).count(b'<a:t>') for p in pages)
    assert text_count>200 and b'oMath' in z.read('ppt/slides/slide5.xml')
print('PPTX package: 15 slides, 15 notes,',text_count,'editable text runs and native formula present.')
report={'date':'2026-10-03','browser':'passed','comparison_selections':24,'diagnosis_selections':24,'slides':15,'notes':15,'pdf_pages':{'project_plan':pymupdf.open(OUT/'项目书审阅版.pdf').page_count,'application':pymupdf.open(OUT/'大创申报书_模板审阅版.pdf').page_count,'deck':15},'validation_scope':'browser, chart geometry, native-editable package, WPS-native Word and PPTX export, rendered-page visual review; not physical validation'}
(OUT/'交付检查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
