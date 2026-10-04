"""Validate current school-template draft and native PDF, using bundled doc runtimes."""
from pathlib import Path
import argparse,hashlib,json,re,zipfile,xml.etree.ElementTree as ET
from pypdf import PdfReader
import pypdfium2 as pdfium

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'simulation/quality_review'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','v':'urn:schemas-microsoft-com:vml','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def norm(s):return ''.join(s.split())
def text(e):return ''.join(x.text or '' for x in e.iter() if x.tag.endswith('}t'))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--candidate-dir',default='tmp/quality_application/candidate');ap.add_argument('--render-dir',default='tmp/quality_application/render');args=ap.parse_args()
    directory=ROOT/args.candidate_dir;pdf=directory/'大创申报书_模板审阅版.pdf';docx=directory/'大创申报书_模板填写稿.docx'
    payload=read(ROOT/'tmp/quality_application/application_payload.json');native=read(directory/'native_layout.json')
    source=(ROOT/'application/正式模板正文.md').read_text(encoding='utf-8')
    refs=read(ROOT/'application/references.json')['references'];selection=read(ROOT/'simulation/presentation_review/figure_selection.json')
    assert len(payload['sections'])==len(payload['figures'])==9 and len(payload['tables'])==4
    assert len(refs)==17 and sum(r['language']=='中文' for r in refs)==11
    literature=source.split('## 四、')[1].split('参考文献')[0]
    assert {int(n) for n in re.findall(r'\[(\d+)\]',literature)}==set(range(1,18))
    assert all(r['citation'] in source for r in refs)
    assert sha(ROOT/'附件1：塔里木大学大学生创新训练项目申报书.doc')=='91a6fe38b74c804482859fc3a5e5369bac2c781069984a5a7b3baf131bf7d48d'
    with zipfile.ZipFile(docx) as z:
        xml=ET.fromstring(z.read('word/document.xml'));rels=ET.fromstring(z.read('word/_rels/document.xml.rels'))
        targets={r.get('Id'):r.get('Target') for r in rels}
        media={hashlib.sha256(z.read(n)).hexdigest():n for n in z.namelist() if n.startswith('word/media/')}
        assert not re.search(r'\[\[(FIGURE|TABLE|BIBLIOGRAPHY)',text(xml))
        figure_checks=[]
        for f in payload['figures']:
            assert sha(ROOT/f['path'])==f['sha256'] and f['sha256'] in media
            shape=next(e for e in xml.findall('.//v:shape',NS) if e.get('alt')==f['caption'])
            width=float(re.search(r'width:([\d.]+)pt',shape.get('style')).group(1))
            height=float(re.search(r'height:([\d.]+)pt',shape.get('style')).group(1))
            assert abs(width-f['width_pt'])<0.06 and abs(height-f['height_pt'])<0.06,(f['caption'],width,height)
            relative_aspect_error=abs((height/width)/(f['pixel_dimensions'][1]/f['pixel_dimensions'][0])-1)
            assert relative_aspect_error<0.0002,('Stretched figure',f['caption'])
            image=shape.find('v:imagedata',NS);target='word/'+targets[image.get('{'+NS['r']+'}id')]
            assert hashlib.sha256(z.read(target)).hexdigest()==f['sha256']
            if 'website_diagnosis_panel' in f['path']:
                capture=read(DATA/'website_capture_checks.json');minimum=capture['screenshots'][0]['minimumTextPx']*width/capture['screenshots'][0]['clip']['width']
            else:
                a=read(DATA/'figure_checks.json')
                minimum=next(c for c in a['figures'] if c['name']==Path(f['path']).stem)['minFontPt']*width/420
            assert minimum>=9.5,('Undersized figure text',f['caption'],minimum)
            n=next(c for c in native['figures'] if c['caption']==f['caption']);assert n['start_page']==n['end_page']
            figure_checks.append({'caption':f['caption'],'source':f['path'],'sha256':f['sha256'],'width_pt':width,'height_pt':height,'relative_aspect_error':relative_aspect_error,'minimum_major_font_pt':minimum,'native_page':n['start_page'],'image_and_caption_same_page':True})
        table_checks=[]
        for record in payload['tables']:
            header=''.join(record['rows'][0]);candidates=[]
            for t in xml.findall('.//w:tbl',NS):
                rows=t.findall('w:tr',NS)
                if rows and ''.join(text(c) for c in rows[0].findall('w:tc',NS))==header:candidates.append(t)
            assert len(candidates)==1,('Missing or repeated editable table',record['caption'])
            t=candidates[0];rows=t.findall('w:tr',NS)
            assert [[text(c) for c in r.findall('w:tc',NS)] for r in rows]==record['rows']
            widths=[int(c.get('{'+NS['w']+'}w'))/20 for c in t.findall('w:tblGrid/w:gridCol',NS)]
            assert widths==record['column_widths_pt']
            assert rows[0].find('w:trPr/w:tblHeader',NS) is not None
            assert all(r.find('w:trPr/w:cantSplit',NS) is not None for r in rows)
            table_checks.append({'caption':record['caption'],'rows':len(rows),'columns':len(widths),'widths_pt':widths,'editable':True,'header_repeats':True,'native_page':next(c['page'] for c in native['tables'] if c['caption']==record['caption'])})
        assert '学院意见：' in text(xml) and '学校意见：' in text(xml) and '项目组成员签字：' in text(xml)
        template=zipfile.ZipFile(ROOT/'tmp/reference_review/template.docx')
        old_media={hashlib.sha256(template.read(n)).hexdigest() for n in template.namelist() if n.startswith('word/media/')}
        assert old_media<=set(media),'Template logo missing'
    pages=PdfReader(pdf).pages;page_text=[norm(p.extract_text() or '') for p in pages]
    assert len(pages)==native['pages'] and len(pages)>=8
    section_pages=[]
    for section in payload['sections']:
        lines=section.split('\r');label=norm(lines[0]);first=norm(lines[1].split('\x0b')[-1])[:25]
        matches=[i+1 for i,p in enumerate(page_text) if label in p and first in p]
        assert len(matches)==1,('Orphaned school section heading',lines[0],matches)
        section_pages.append({'heading':lines[0],'page':matches[0],'first_body_on_same_page':True})
    entry_pages=[]
    for r in refs:
        matches=[i+1 for i,p in enumerate(page_text) if '['+str(r['number'])+']' in p and norm(r['title']) in p and r['doi'] in p]
        assert len(matches)==1,('Incomplete reference',r['number'],matches)
        entry_pages.append({'number':r['number'],'page':matches[0]})
    for f in figure_checks:assert norm(f['caption']) in page_text[f['native_page']-1]
    headings=re.findall(r'^###\s+(.+)$',source,re.M)+re.findall(r'^####\s+(.+)$',source,re.M)
    assert all(norm(h) in ''.join(page_text) for h in headings),'Missing subheading text'
    geometry=[];document=pdfium.PdfDocument(str(pdf));outside=[]
    for i in range(len(document)):
        page=document[i];width,height=page.get_size();tp=page.get_textpage();count=tp.count_chars()
        for j in range(count):
            char=tp.get_text_range(j,1)
            if not char.strip():continue
            l,b,r,t=tp.get_charbox(j)
            if l<-0.5 or b<-0.5 or r>width+0.5 or t>height+0.5:outside.append({'page':i+1,'char':char,'box':[l,b,r,t]})
        assert 594<width<597 and 840<height<843
        geometry.append({'page':i+1,'characters':count,'width_pt':width,'height_pt':height})
        tp.close();page.close()
    document.close();assert not outside,outside[:6]
    pngs=sorted((ROOT/args.render_dir).glob('page-*.png'));assert len(pngs)==len(pages)
    known=read(ROOT/'simulation/diagnosis_review/summary.json')
    assert known['trials']==480 and known['method_evaluations']==960 and known['bounded_error_cases']==288
    for kind,expected in [('leak',1),('restriction',2)]:
        group=next(g for g in known['groups'] if g['kind']==kind and g['method']=='physical' and g['pressure_sigma_kpa']==10)
        assert group['early_trials']==expected
    assert '12/20' not in source and '409/485' not in source and '396/522' not in source
    budget=payload['tables'][-1]['rows'];assert sum(int(r[1]) for r in budget[1:-1])==int(budget[-1][1])==2000
    result={'date':'2026-10-05','status':'passed_programmatic_native_draft_checks_visual_review_pending','physical_validation':False,'administrative_complete':False,'native_pdf_pages':len(pages),'figures':figure_checks,'editable_tables':table_checks,'references':entry_pages,'chinese_references':11,'english_references':6,'pdf_character_bounds':geometry,'outside_page_characters':outside,'rendered_pages':[{'page':i+1,'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for i,p in enumerate(pngs)],'source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),ROOT/'application/正式模板正文.md',ROOT/'scripts/prepare_quality_payload.py',ROOT/'scripts/fill_quality_application.ps1',ROOT/'application/references.json',pdf,docx,directory/'native_layout.json',ROOT/'tmp/quality_application/application_payload.json',DATA/'website_capture_checks.json']}}
    result['school_section_headings']=section_pages
    (DATA/'document_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    print(f'{len(pages)} native pages: 9 exact source images with preserved aspect/font >=9.5pt; 4 editable tables; 17 complete references; no out-of-page text. Visual review still required.')
if __name__=='__main__':main()
