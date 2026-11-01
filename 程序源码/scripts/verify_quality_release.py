"""Read-only release audit; append --bundle to verify packaged evidence hashes."""
from pathlib import Path
import argparse,hashlib,json,subprocess,zipfile
from html.parser import HTMLParser
from urllib.parse import unquote,urlsplit

ROOT=Path(__file__).resolve().parents[1]
BASELINE='d8b22f0cbb0c1d795e57b087864ffbd5fa4609f4'
DATA=ROOT/'simulation/quality_review'
sha=lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p: json.loads(Path(p).read_text(encoding='utf-8'))

class Links(HTMLParser):
    def __init__(self):
        super().__init__();self.links=[]
    def handle_starttag(self, tag, attrs):
        for key,value in attrs:
            if value and ((tag=='a' and key=='href') or (tag in ['img','script','iframe'] and key=='src') or (tag=='link' and key=='href')):
                self.links.append(value)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--bundle',action='store_true');ap.add_argument('--staged',action='store_true');args=ap.parse_args()
    r=read(ROOT/'deliverables/格式优化与实施项目书验收记录.json')
    assert r['status']=='passed_internal_material_and_scoped_software_review'
    assert not r['physical_validation'] and not r['administrative_complete'] and not r['official_taskbook_template_obtained']
    for entry in r['artifacts_and_frozen_inputs']+r['receipts']:
        assert sha(ROOT/entry['path'])==entry['sha256'],('Published hash drift',entry['path'])
    for item in r['artifacts_and_frozen_inputs']:
        origin=ROOT/item['origin']
        if origin.exists():assert sha(origin)==item['sha256']
    provenance=read(ROOT/'application/school_templates/provenance.json')
    assert all(a['status']=='not_document' for n in provenance['notices'] for a in n['attachments'])
    assert [p.name for p in (ROOT/'application/school_templates').iterdir()]==['provenance.json']
    original=ROOT/'附件1：塔里木大学大学生创新训练项目申报书.doc'
    assert sha(original)=='91a6fe38b74c804482859fc3a5e5369bac2c781069984a5a7b3baf131bf7d48d'
    protected=[
        'simulation/diagnosis_review/','simulation/interface_review/','simulation/presentation_review/',
        'simulation/diagnosis_results/','simulation/communication_results/',
        'application/models/','application/figures/collection_review/','application/figures/diagnosis_review/',
        'application/figures/interface_review/','application/figures/presentation_review/',
        'application/application_integration/','simulation/application_integration/',
        'deliverables/大创申报书_模板填写稿.docx','deliverables/大创申报书_模板审阅版.pdf',
        'deliverables/立项答辩.pptx','deliverables/立项答辩审阅版.pdf',
        'deliverables/申报书整合分项验收记录.json',
    ]
    # Git may quote non-ASCII paths; request literal paths rather than parsing quotes.
    tracked=subprocess.check_output(['git','-c','core.quotepath=false','ls-tree','-r','--name-only',BASELINE],cwd=ROOT).decode('utf-8').splitlines()
    protected_files=[]
    for name in tracked:
        if not any(name.startswith(prefix) for prefix in protected):continue
        old=subprocess.check_output(['git','show',BASELINE+':'+name],cwd=ROOT)
        assert (ROOT/name).read_bytes()==old,('Historical evidence overwritten',name)
        protected_files.append(name)
    app=read(DATA/'document_checks.json');book=read(DATA/'execution_book_checks.json')
    assert app['native_pdf_pages']==25 and book['native_pdf_pages']==13
    assert len(app['figures'])==9 and len(app['editable_tables'])==4 and len(app['references'])==17
    assert app['chinese_references']==11 and app['english_references']==6
    assert len(book['figures'])==5 and len(book['editable_tables'])==6 and len(book['headings'])==9
    assert all(x['minimum_major_font_pt']>=9.5 and x['image_and_caption_same_page'] for x in app['figures']+book['figures'])
    assert not app['outside_page_characters'] and not book['outside_page_characters']
    sample=read(DATA/'sampling_checks.json')
    assert sample['phase_checks_total']==20000 and sample['recommended_provisional_sample_s']==20
    assert sample['required_calibrated_usable_capacity_ml_min']==440
    site=read(DATA/'site_checks.json');capture=read(DATA/'website_capture_checks.json')
    assert len(site['navigation_checks'])==30 and len(site['replay_checks'])==24 and len(site['workflow_checks'])==20 and len(site['export_checks'])==3
    assert not site['console_errors'] and not site['external_requests']
    assert site['source_sha256']==sha(ROOT/'deliverables/index.html')
    assert capture['source_sha256']['site']==sha(ROOT/'deliverables/index.html')
    assert capture['source_sha256']['research']==sha(ROOT/'deliverables/研究与答辩资料.html')
    viewer=read(DATA/'model_viewer_checks.json')
    assert viewer['status'].startswith('passed_programmatic') and len(viewer['views'])==20
    assert not viewer['console_errors'] and not viewer['external_requests']
    assert all(not v['outside'] and not v['overlap'] for v in viewer['views'])
    for name,digest in viewer['source_sha256'].items():assert sha(ROOT/name)==digest
    link_checks=[]
    for name in ['deliverables/index.html','deliverables/研究与答辩资料.html','deliverables/台架三维结构交互模型_收集优化候选版.html']:
        p=ROOT/name;parser=Links();parser.feed(p.read_text(encoding='utf-8'))
        checked=0
        for link in parser.links:
            u=urlsplit(link)
            if u.scheme or u.netloc or not u.path:continue
            target=(p.parent/unquote(u.path)).resolve()
            assert target.is_relative_to(ROOT.resolve()) and target.exists(),('Broken local link',name,link)
            checked+=1
        link_checks.append({'path':name,'existing_local_links':checked})
    result={'date':'2026-10-05','status':'passed_release_consistency_checks','physical_validation':False,'official_taskbook_template_obtained':False,'published_hash_checks':len(r['artifacts_and_frozen_inputs'])+len(r['receipts']),'historical_files_unchanged':len(protected_files),'local_links':link_checks,'native_document_pages':38,'current_concept_model_views_and_widths_checked':20,'source_sha256':sha(Path(__file__)),'package_verification':'Run package_submission.py then this checker --bundle; checks archive entries against embedded evidence manifest without modifying the archive.'}
    if args.bundle:
        manifest=read(ROOT/'deliverables/证据清单.json')
        for e in manifest['entries']:assert sha(ROOT/e['path'])==e['sha256'],('Manifest drift',e['path'])
        with zipfile.ZipFile(ROOT/'deliverables/申报材料与证据包.zip') as z:
            assert z.testzip() is None
            assert not any(n.startswith(('tmp/','output/')) or Path(n).name.startswith('~$') or Path(n).name=='.env' for n in z.namelist())
            embedded=json.loads(z.read('deliverables/证据清单.json'))
            assert embedded==manifest
            for e in embedded['entries']:assert hashlib.sha256(z.read(e['path'])).hexdigest()==e['sha256']
            print(f'Final archive verified: {len(z.namelist())} files, {len(embedded["entries"])} manifest hashes; release and local links pass.')
    else:
        (DATA/'release_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
        print(f'Release hashes pass; {len(protected_files)} historical files unchanged; all {sum(x["existing_local_links"] for x in link_checks)} local links exist.')
    if args.staged:
        manifest=read(ROOT/'deliverables/证据清单.json')
        for e in manifest['entries']:
            blob=subprocess.check_output(['git','show',':'+e['path']],cwd=ROOT)
            assert hashlib.sha256(blob).hexdigest()==e['sha256'],('Git index changes delivered bytes',e['path'])
        for name in ['deliverables/证据清单.json','deliverables/申报材料与证据包.zip']:
            blob=subprocess.check_output(['git','show',':'+name],cwd=ROOT)
            assert hashlib.sha256(blob).hexdigest()==sha(ROOT/name)
        print(f'Git index preserves all {len(manifest["entries"])} evidence hashes and exact final archive bytes.')

if __name__=='__main__':
    main()
