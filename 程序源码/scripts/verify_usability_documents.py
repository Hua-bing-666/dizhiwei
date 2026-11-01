"""Verify the final proposal and execution book, without changing either document."""
from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
from PIL import Image
import hashlib, io, json, re

R=Path(__file__).resolve().parents[1]
OUT=R/'application/usability_revision'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','m':'http://schemas.openxmlformats.org/officeDocument/2006/math','v':'urn:schemas-microsoft-com:vml','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships','a':'http://schemas.openxmlformats.org/drawingml/2006/main','wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'}
W='{'+NS['w']+'}'
tx=lambda p:''.join(p.xpath('.//w:t/text()',namespaces=NS))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
# WPS reports DrawingML inline-object placeholders as "/"; VML as U+0001.
clean=lambda s:s.replace('\x01','').replace('\x0b','').strip().lstrip('/').strip()
results={}
for kind,expected_pages,expected_figures,expected_tables in [('submission',18,10,3),('execution',12,5,6)]:
    record_file=OUT/(kind+'_edit.json')
    record=json.loads(record_file.read_text(encoding='utf-8'))
    source=R/record['source'];output=R/record['output']
    assert sha(source)==record['source_sha256']
    assert sha(output)==record['output_sha256']
    with ZipFile(source) as a,ZipFile(output) as b:
        assert a.namelist()==b.namelist()
        assert [n for n in a.namelist() if a.read(n)!=b.read(n)]==record['changed_parts']
        old=E.fromstring(a.read('word/document.xml'));root=E.fromstring(b.read('word/document.xml'))
        tables=root.xpath('.//w:tbl',namespaces=NS)
        references=[];citations=0
        if kind=='submission':
            rows=tables[0].findall(W+'tr');oldrows=old.find(W+'body/'+W+'tbl').findall(W+'tr')
            assert len(rows)==31
            for i in record['protected_rows']:assert E.tostring(rows[i])==E.tostring(oldrows[i]),i
            native=root.xpath('.//m:oMath',namespaces=NS);prior=old.xpath('.//m:oMath',namespaces=NS)
            assert len(native)==len(prior)==11
            assert [E.tostring(x) for x in native]==[E.tostring(x) for x in prior]
            references=[tx(p) for p in rows[19].xpath('.//w:p',namespaces=NS) if re.match(r'^\[[1-8]\]',tx(p))]
            assert len(references)==8
            assert references==[tx(p) for p in oldrows[19].xpath('.//w:p',namespaces=NS) if re.match(r'^\[[1-8]\]',tx(p))]
            assert all(re.search('[\u4e00-\u9fff]',s) for s in references[:5])
            assert all(not re.search('[\u4e00-\u9fff]',s) for s in references[5:])
            for row in rows[16:24]:
                for p in row.xpath('.//w:p',namespaces=NS):
                    if re.match(r'^\[[1-8]\]',tx(p)):continue
                    for run in p.findall(W+'r'):
                        if re.search(r'\[[1-8](?:[,，][1-8])*\]',tx(run)):
                            va=run.find(W+'rPr/'+W+'vertAlign')
                            assert va is not None and va.get(W+'val')=='superscript'
                            citations+=1
            assert citations>=8
            data_tables=[t for t in tables[1:] if len(t.find(W+'tr').findall(W+'tc'))>=3]
        else:
            data_tables=tables
            text=tx(root)
            for stale in ['本地六模块','199个','中文11篇','3 科研积分','44B事件','24B ACK','V≥']:
                assert stale not in text,stale
            budget=next(t for t in tables if tx(t).startswith('用途金额'))
            assert len(budget.findall(W+'tr'))==5
            assert all(not tx(row).strip() for row in budget.findall(W+'tr')[1:])
        assert len(data_tables)==expected_tables
        for table in data_tables:
            assert table.find(W+'tblPr/'+W+'jc').get(W+'val')=='center'
            assert table.find(W+'tr/'+W+'trPr/'+W+'tblHeader') is not None
            for p in table.find(W+'tr').xpath('.//w:p',namespaces=NS):
                assert p.find(W+'pPr/'+W+'jc').get(W+'val')=='center'
        rel={e.get('Id'):e.get('Target') for e in E.fromstring(b.read('word/_rels/document.xml.rels'))}
        figures=[]
        for p in root.xpath('.//w:p',namespaces=NS):
            caption=tx(p)
            if not re.match(r'^(图\d+|表\d+)\s',caption):continue
            assert p.find(W+'pPr/'+W+'jc').get(W+'val')=='center',caption
            if caption.startswith('表'):continue
            if kind=='submission':
                shape=p.xpath('.//v:shape[.//v:imagedata]',namespaces=NS)[0]
                rid=shape.xpath('.//v:imagedata/@r:id',namespaces=NS)[0]
                dims={k:float(v) for k,v in re.findall(r'(width|height):([\d.]+)pt',shape.get('style'))}
                width,height=dims['width'],dims['height']
            else:
                rid=p.xpath('.//a:blip/@r:embed',namespaces=NS)[0]
                extent=p.xpath('.//wp:extent',namespaces=NS)[0]
                width,height=int(extent.get('cx'))/12700,int(extent.get('cy'))/12700
            part='word/'+rel[rid];iw,ih=Image.open(io.BytesIO(b.read(part))).size
            assert abs(width*ih/iw-height)<.13,caption
            assert iw/width*72>=300,caption
            figures.append({'caption':caption,'part':part,'dpi':round(iw/width*72,1),'preserved_bytes':a.read(part)==b.read(part)})
        assert len(figures)==expected_figures
        if kind=='submission':assert sum(f['preserved_bytes'] for f in figures)==2
    tmp=R/'tmp/usability_submission'/kind
    layout=json.loads((tmp/'native_layout.json').read_text(encoding='utf-8-sig'))
    assert layout['pages']==expected_pages
    assert layout['source']==output.name
    assert layout['math_count']==(11 if kind=='submission' else 0)
    captions=[p for p in layout['paragraphs'] if re.match(r'^(图\d+|表\d+)\s',clean(p['text']))]
    assert len(captions)==expected_figures+expected_tables
    assert all(p['start_page']==p['end_page'] for p in captions)
    for f in layout['figures']:
        if clean(f['caption']).startswith('图'):assert f['start_page']==f['end_page']
    if kind=='submission':
        for table in data_tables:
            texts=[tx(p) for p in table.xpath('.//w:p',namespaces=NS) if tx(p).strip()]
            first=[p for p in layout['paragraphs'] if clean(p['text'])==texts[0]]
            last=[p for p in layout['paragraphs'] if clean(p['text'])==texts[-1]]
            assert first and last and any(a['start_page']==b['end_page'] for a in first for b in last),'Data table split across pages'
        p=next(p for p in layout['paragraphs'] if clean(p['text']).startswith('前期还构造了未知正常负载'))
        assert p['start_page']==p['end_page'],'Model limitation paragraph split across pages'
    pages=json.loads((tmp/'pages/pages.json').read_text(encoding='utf-8'))
    assert len(pages)==expected_pages
    for page in pages:assert sha(R/page['file'])==page['sha256']
    results[kind]={'output':record['output'],'output_sha256':sha(output),'source_sha256':sha(source),'pages':expected_pages,'figures':figures,'centered_tables':expected_tables,'native_math':layout['math_count'],'superscript_citations':citations,'reference_count':len(references),'pdf_sha256':sha(tmp/'document.pdf'),'page_images':pages}

# Recount the model comparison cited in the proposal instead of trusting prose.
trials=json.loads((R/'simulation/platform_upgrade/scheduling_trials.json').read_text(encoding='utf-8'))
assert len(trials)==432
for scene,early in [('leak',[9,17,39]),('restriction',[9,17,42])]:
    for period,count,success in zip([1,2,5],[9,18,45],early):
        selected=[t for t in trials if t['scene']==scene and t['period']==period]
        assert len(selected)==count and sum(t['early_valid'] for t in selected)==success
cross=json.loads((R/'simulation/platform_upgrade/cross_operating_points.json').read_text(encoding='utf-8'))
assert len(cross['trials'])==72
scene=json.loads((R/'application/models/system_upgrade/bench_scene.json').read_text(encoding='utf-8'))
assert len(scene['meshes'])==207
report={'result':'passed','documents':results,'sampling_model_trials':432,'unseen_model_trials':72,'concept_mesh_entities':207,'physical_data':False,'renderer':'Read-only WPS PDF export and bundled PDFium; packaged render_docx unavailable because soffice.exe is absent.'}
(OUT/'acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Document checks passed: proposal 18 pages / 10 figures / 11 equations / 5+3 references; execution 12 pages / 5 figures / 6 tables. Sources unchanged.')
