"""Release only the native candidate tied to current programmatic and visual receipts.

Run AFTER individually reviewing all current rendered pages and writing manual_review.json.
This releases an internally reviewed draft, not an administrative submission.
"""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,uuid

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'simulation/application_integration'
CANDIDATE=ROOT/'tmp/application_integration/candidate'
BASE='00fd12a6cea04540e17dbc75d5627c7bea75674c'
STATUS='passed_internal_draft_checks_administrative_and_resource_confirmation_pending'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,value):p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def historical_bytes(path):return subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
def unchanged(path):
    assert (ROOT/path).read_bytes()==historical_bytes(path),('Frozen evidence changed',path)

def main():
    checks=read(DATA/'document_checks.json');manual=read(DATA/'manual_review.json')
    assert checks['native_pdf_pages']==24 and len(checks['figures'])==9
    assert len(checks['editable_tables'])==4 and len(checks['references'])==17
    assert len(checks['school_section_headings'])==9
    assert not checks['outside_page_characters']
    assert manual['status']=='passed_internal_visual_review'
    assert manual['independent_external_review'] is False and manual['physical_validation'] is False
    assert manual['reviewed_pages']==list(range(1,25))
    for path,digest in checks['source_sha256'].items():assert sha(ROOT/path)==digest,path
    for page in checks['rendered_pages']:assert sha(ROOT/page['path'])==page['sha256']
    assert manual['rendered_pages']==checks['rendered_pages']
    assert manual['programmatic_receipt_sha256']==sha(DATA/'document_checks.json')
    for name in ['大创申报书_模板填写稿.docx','大创申报书_模板审阅版.pdf']:
        assert manual['candidate_sha256'][name]==sha(CANDIDATE/name)
    for directory in ['simulation/diagnosis_review','simulation/interface_review','simulation/presentation_review','application/figures/collection_review','application/figures/diagnosis_review','application/figures/interface_review','application/figures/presentation_review','application/models/collection_review']:
        paths=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'--',directory],cwd=ROOT,text=True,encoding='utf-8').splitlines()
        for path in paths:unchanged(path.strip('"'))
    for path in ['deliverables/index.html','deliverables/立项答辩.pptx','deliverables/立项答辩审阅版.pdf','deliverables/项目书审阅版.pdf','application/references.json','附件1：塔里木大学大学生创新训练项目申报书.doc']:
        unchanged(path)
    # Keep the whole research review (including all citations) verbatim.
    def literature(text):return text.split('## 四、')[1].split('## 五、')[0]
    assert literature((ROOT/'application/正式模板正文.md').read_text(encoding='utf-8'))==literature(historical_bytes('application/正式模板正文.md').decode('utf-8'))
    frozen=ROOT/'application/application_integration';frozen.mkdir(exist_ok=True)
    for source,name in [(ROOT/'tmp/reference_review/application_payload.json','payload.json'),(CANDIDATE/'native_layout.json','native_layout.json'),(ROOT/'tmp/application_integration/artifact.md','template_contract.md')]:
        # Canonical LF avoids Git normalization invalidating public evidence hashes.
        (frozen/name).write_text(source.read_text(encoding='utf-8-sig'),encoding='utf-8',newline='\n')
    # Two separately validated native files; use in-directory atomic replacements.
    for name in ['大创申报书_模板填写稿.docx','大创申报书_模板审阅版.pdf']:
        target=ROOT/'deliverables'/name;staging=target.with_name(target.name+'.'+uuid.uuid4().hex+'.tmp')
        shutil.copyfile(CANDIDATE/name,staging);assert sha(staging)==sha(CANDIDATE/name)
        os.replace(staging,target)
    source_map={
        'tmp/reference_review/application_payload.json':'application/application_integration/payload.json',
        'tmp/application_integration/candidate/native_layout.json':'application/application_integration/native_layout.json',
        'tmp/application_integration/candidate/大创申报书_模板填写稿.docx':'deliverables/大创申报书_模板填写稿.docx',
        'tmp/application_integration/candidate/大创申报书_模板审阅版.pdf':'deliverables/大创申报书_模板审阅版.pdf'}
    sources={source_map.get(p,p):sha(ROOT/source_map.get(p,p)) for p in checks['source_sha256']}
    for path in ['simulation/application_integration/document_checks.json','simulation/application_integration/manual_review.json','scripts/finalize_application_integration.py','scripts/capture_application_panel.mjs','docs/学校模板申报书整合与分项验收.md','application/application_integration/template_contract.md']:
        sources[path]=sha(ROOT/path)
    assert all(not p.startswith('tmp/') and sha(ROOT/p)==h for p,h in sources.items())
    record={'date':'2026-10-05','scope':'A01/A03/A11 school-template draft integration','status':STATUS,'physical_validation':False,'administrative_complete':False,'independent_external_review':False,'historical_evidence_base':BASE,'pages':24,'figures':checks['figures'],'editable_tables':checks['editable_tables'],'references':{'total':17,'chinese':11,'english':6},'school_section_headings':checks['school_section_headings'],'visual_review_record':'simulation/application_integration/manual_review.json','programmatic_review_record':'simulation/application_integration/document_checks.json','rendered_pages_retention':'Local QA PNGs remain under ignored tmp; SHA receipts are packaged. Regenerate from the native PDF.','source_sha256':sources,'unresolved':['real identities and team allocation','teacher and reference instrument/water access confirmation','pressure specification quotations and actual procurement','input protection values and actual firmware','2027 batch terms and formal goals','PPT synchronization'],'planned_not_achieved':{'main_fault_operations':54,'normal_operations':18,'switching_fault_operations':12,'controlled_wireless_replay_batches':36,'continuous_recording_hours':8,'restarts':3,'correct_first_persistent_candidate_target_10_15_percent':0.9,'normal_confirmed_false_alarms_per_hour_target':1,'conditional_budget_cap_yuan':2000}}
    write(ROOT/'deliverables/申报书整合分项验收记录.json',record)
    progress_path=ROOT/'deliverables/分项验收进度.json';progress=read(progress_path)
    historical=json.loads(historical_bytes('deliverables/分项验收进度.json').decode('utf-8'))
    for task in progress['tasks']:
        if task['id'] in ['A01','A03','A11']:
            task.update(status=STATUS,record='deliverables/申报书整合分项验收记录.json')
        elif task['id']=='A10':
            original=next(t for t in historical['tasks'] if t['id']=='A10')
            assert task['record']==original['record']
            task.update(status='selected_asset_checks_passed_word_integration_checked_in_A11',previous_status=original['status'],integration_record='deliverables/申报书整合分项验收记录.json')
        elif task['id'] in ['A04','A05','A06','A07','A08','A09']:
            assert task==next(t for t in historical['tasks'] if t['id']==task['id'])
    progress.update(date='2026-10-05',scope='A01/A03/A11 internal draft accepted; formal submission and physical integration pending',this_turn='24 native school-template pages; 9 source figures; 4 editable tables; 17 references; individual visual review',next='A12 synchronize PPT with accepted Word; A13 real administrative/resource confirmation',plan_sha256=sha(ROOT/'docs/三阶段分项执行与验收标准.md'))
    write(progress_path,progress)
    delivery_path=ROOT/'deliverables/交付检查.json';delivery=read(delivery_path)
    delivery['date']='2026-10-05';delivery['pdf_pages']['application']=24
    delivery['application_integration']={'status':STATUS,'record':'申报书整合分项验收记录.json','physical_validation':False,'pages':24,'manual_pages_reviewed':24,'figures':9,'editable_tables':4,'references':17,'source_sha256':sha(ROOT/'deliverables/大创申报书_模板填写稿.docx')}
    delivery['legacy_receipts']='Older Word/PPT/research-page receipts refer to their frozen versions; current application acceptance is recorded separately.'
    write(delivery_path,delivery)
    print('Released internally reviewed 24-page Word/PDF draft; physical/administrative status remains pending.')

if __name__=='__main__':main()
