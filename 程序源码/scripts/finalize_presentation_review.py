"""Freeze A09/A10 software and selected assets, without releasing Word or hardware."""
from pathlib import Path
import hashlib,json,re,subprocess
from urllib.parse import unquote
from html.parser import HTMLParser

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'simulation/presentation_review'
FIG=ROOT/'application/figures/presentation_review'
BASE='43411a5'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
def check_sources(d):
    for p,h in d['source_sha256'].items():assert sha(ROOT/p)==h,('Stale source',p)

def main():
    site=read(DATA/'site_checks.json');capture=read(DATA/'capture_checks.json')
    assets=read(DATA/'asset_checks.json');selection=read(DATA/'figure_selection.json')
    layout=read(DATA/'diagram_layout_checks.json');provenance=read(FIG/'figure_provenance.json')
    stats=read(FIG/'statistics_provenance.json');manual=read(DATA/'manual_review.json')
    replay=read(DATA/'web_replay.json');scientific=read(ROOT/'simulation/diagnosis_review/summary.json')
    assert site['status']==assets['status']==layout['status']=='passed'
    assert capture['status']=='captured' and not any(capture[k] for k in ['physical_data','dom_replaced','css_overridden','pixels_postprocessed'])
    assert len(site['navigation_checks'])==24 and all(not c['overflow'] for c in site['navigation_checks'])
    assert len(site['replay_checks'])==24 and len(site['workflow_checks'])==19 and len(site['export_checks'])==3
    assert not site['console_errors'] and not site['external_requests'] and not assets['console_errors']
    assert sha(ROOT/'deliverables/index.html')==site['source_sha256']==capture['source_sha256']['site']
    for record in [selection,provenance,stats]:check_sources(record)
    for k,p in {'script':'scripts/capture_presentation_evidence.mjs','site':'deliverables/index.html','research':'deliverables/研究与答辩资料.html','replay':'simulation/presentation_review/web_replay.json'}.items():assert sha(ROOT/p)==capture['source_sha256'][k]
    for k,p in {'script':'scripts/verify_presentation_assets.mjs','selection':'simulation/presentation_review/figure_selection.json','review_html':'deliverables/申报图文取舍与呈现审阅.html','capture_checks':'simulation/presentation_review/capture_checks.json'}.items():assert sha(ROOT/p)==assets['source_sha256'][k]
    for k,p in {'script':'scripts/verify_presentation_diagrams.mjs','provenance':'application/figures/presentation_review/figure_provenance.json'}.items():assert sha(ROOT/p)==layout['source_sha256'][k]
    assert len(selection['main_figures'])==len(assets['figures'])==9 and len(selection['supplemental'])==8
    assert len(selection['tables_for_A11'])==4 and len(assets['proofs'])==len(manual['proofs'])==12
    assert not manual['independent_external_review'] and not manual['physical_validation']
    for f in assets['figures']:
        assert not f['outside'] and not f['overlaps'] and f['minimum_font_pt_at_425pt']>=9
    for f in selection['main_figures']:
        for ext,digest in f['sha256'].items():assert sha(ROOT/f[ext])==digest
    for f in layout['figures']:
        assert not f['outside'] and not f['overlaps'] and not f['boxErrors']
        for ext,digest in f['sha256'].items():assert sha(FIG/(f['name']+'.'+ext))==digest
    for f,m in zip(assets['proofs'],manual['proofs']):
        assert f['file']==m['file'] and sha(ROOT/f['file'])==f['sha256']==m['sha256'] and m['viewed']
        if f['mode']=='color':assert abs(f['image_width_pt']-425)<0.05 and f['caption_after_image'] and f['notes_after_caption'] and f['caption_font_pt']>=9
    for f in capture['screenshots']:assert sha(FIG/(f['name']+'.png'))==f['sha256'] and not f['overlaps']
    assert len(capture['research_notice_checks'])==4 and all(c['notice_present'] and not c['root_overflow'] for c in capture['research_notice_checks'])
    assert replay['source_summary_sha256']==sha(ROOT/replay['source_summary'])
    assert replay['adapter_sha256']==sha(ROOT/'scripts/prepare_presentation_review.py')
    assert replay['protocol_version']==scientific['protocol_version']=='20261004-A06A07-v1'
    assert not replay['physical_data'] and not replay['operation_state_gating_implemented']
    comparisons=0
    for t in scientific['traces'].values():
        a=replay['traces'][t['kind']+'_'+format(t['pressure_sigma_kpa'],'.1f')]
        assert len(a['p0'])==601
        for i,row in enumerate(t['observed']):
            assert [a[k][i] for k in ('p0','p1','q')]==row
            for k in ('k','r','state'):assert a[k][i]==t[k][i]
            comparisons+=6
    old=read(ROOT/'application/figures/diagnosis_review/figure_provenance.json')
    original=next(f for f in old['figures'] if f['name']=='noise_outcomes')
    assert stats['figures'][0]['series']==original['series']
    for ext,digest in stats['figures'][0]['sha256'].items():assert sha(FIG/('noise_outcomes_print.'+ext))==digest
    tracked=subprocess.run(['git','ls-tree','-r','--name-only','-z',BASE],cwd=ROOT,capture_output=True,check=True).stdout.decode('utf-8').split('\0')
    prefixes=['application/models/','application/figures/collection_review/','application/figures/diagnosis_review/','application/figures/interface_review/','simulation/diagnosis_review/','simulation/interface_review/','simulation/diagnosis_results/','simulation/hardware_results/','simulation/communication_results/']
    preserve=['application/references.json','deliverables/大创申报书_模板填写稿.docx','deliverables/大创申报书_模板审阅版.pdf','deliverables/项目书审阅版.pdf','deliverables/立项答辩.pptx','deliverables/立项答辩审阅版.pdf','deliverables/三维分项验收记录.json','deliverables/仿真分项验收记录.json','deliverables/接口与通信分项验收记录.json','docs/三维台架建模论证与本轮验收.md','docs/仿真建模与诊断证据分项验收.md','docs/硬件接口与LoRa通信论证分项验收.md']
    preserved=[]
    for p in sorted(set(preserve+[p for p in tracked if any(p.startswith(x) for x in prefixes)])):
        prior=subprocess.run(['git','show',BASE+':'+p],cwd=ROOT,capture_output=True,check=True).stdout
        assert (ROOT/p).read_bytes()==prior,('Out of scope modification',p)
        preserved.append({'path':p,'sha256':sha(ROOT/p)})
    # Check all review/report local paths; future report self-link is allowed.
    report_path=ROOT/'deliverables/网站与图文分项验收记录.json'
    links=0
    doc=ROOT/'docs/网站佐证与申报图表分项验收.md'
    for target in re.findall(r'\]\(([^)]+)\)',doc.read_text(encoding='utf-8')):
        if '://' in target or re.match(r'^[A-Za-z]:',target) or target.startswith('#'):continue
        path=(doc.parent/unquote(target.split('#')[0])).resolve()
        assert path==report_path or path.is_file(),('Missing Markdown link',target);links+=1
    class Links(HTMLParser):
        def handle_starttag(self,tag,attrs):
            nonlocal links
            for k,v in attrs:
                if k not in ('href','src') or not v or v.startswith(('#','data:','http:','https:','mailto:')):continue
                path=(self.base/unquote(v.split('#')[0])).resolve()
                assert path==report_path or path.is_file(),('Missing HTML link',str(self.base),v);links+=1
    for name in ['index.html','研究与答辩资料.html','申报图文取舍与呈现审阅.html']:
        parser=Links();parser.base=ROOT/'deliverables';parser.feed((parser.base/name).read_text(encoding='utf-8'))
    progress=read(ROOT/'deliverables/分项验收进度.json')
    prior_progress=json.loads(subprocess.run(['git','show',BASE+':deliverables/分项验收进度.json'],cwd=ROOT,capture_output=True,check=True).stdout)
    for ident in ['A04','A05','A06','A07','A08']:
        assert next(t for t in progress['tasks'] if t['id']==ident)==next(t for t in prior_progress['tasks'] if t['id']==ident)
    statuses={'A09':'candidate_internal_checks_passed_physical_unverified','A10':'selected_asset_checks_passed_word_integration_pending'}
    for t in progress['tasks']:
        if t['id'] in statuses:t.update(status=statuses[t['id']],record='deliverables/网站与图文分项验收记录.json')
    progress.update(date='2026-10-04',scope='A09 current synthetic replay and A10 selected figures internally checked; Word and physical integration pending',plan_sha256=sha(ROOT/'docs/三阶段分项执行与验收标准.md'),this_turn='A09/A10 24 observed traces, 19 workflows, 9 selected figures and 12 manually viewed proofs',next='A01/A03/A11 school-template argument, editable tables and native Word/PDF page review')
    sources=[Path(__file__),doc,ROOT/'docs/三阶段分项执行与验收标准.md',ROOT/'scripts/verify_presentation_site.mjs',ROOT/'scripts/system_portal.js',ROOT/'scripts/system_portal.template.html',ROOT/'scripts/build_portal.py']+list(DATA.glob('*.json'))+[FIG/'figure_provenance.json',FIG/'statistics_provenance.json',ROOT/'deliverables/index.html',ROOT/'deliverables/研究与答辩资料.html',ROOT/'deliverables/申报图文取舍与呈现审阅.html']
    result={'date':'2026-10-04','version':'20261004-A09A10-v1','task_ids':['A09','A10'],'status':'passed_selected_software_and_asset_checks_word_pending','physical_validation':False,'application_integration_complete':False,'base_commit_for_preservation':BASE,'task_statuses':statuses,'site_checks':{'navigation':24,'replay_choices':24,'workflow_groups':19,'download_files':3,'frozen_value_comparisons':comparisons,'record':'simulation/presentation_review/site_checks.json'},'figure_checks':assets['figures'],'proofs':assets['proofs'],'manual_review':manual,'native_captures':[{'name':f['name'],'sha256':f['sha256'],'minimum_font_pt_at_425pt':f['minimumTextPtAt425pt']} for f in capture['screenshots']],'local_links_checked':links,'original_artifacts_unchanged':preserved,'limitations':['uncalibrated synthetic inputs, no serial/RF/PC SQLite integration with website','operation/comparability gate in diagnosis diagram is proposed, not implemented','full desktop screenshots excluded from Word body because reduced text is too small','425pt browser proof is not native Word pagination acceptance','old documents, PPT and research statistics remain historical versions','independent external review and physical validation not performed'],'source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sources}}
    write(report_path,result);write(ROOT/'deliverables/分项验收进度.json',progress)
    delivery=read(ROOT/'deliverables/交付检查.json')
    delivery['operations_site']={'status':'passed_offline_software_only','artifact':'index.html','source_sha256':site['source_sha256'],'record':'../simulation/presentation_review/site_checks.json','widths':site['widths'],'navigation_checks':24,'replay_choices':24,'workflow_checks':19,'export_files':3,'physical_validation':False}
    delivery['staged_presentation_review']={'record':report_path.name,'report':'../docs/网站佐证与申报图表分项验收.md','review':'申报图文取舍与呈现审阅.html','status':result['status'],'figures_selected':9,'proofs_viewed':12,'word_integration_complete':False,'physical_validation':False,'research_page_scope':'historical notice and root overflow at four widths only; original receipt remains historical'}
    write(ROOT/'deliverables/交付检查.json',delivery)
    print(f'A09/A10 passed scoped checks: {comparisons} adapter values, 19 workflows, 9 selected assets, 12 viewed proofs; {len(preserved)} artifacts preserved, {links} links. Word pending.')

if __name__=='__main__':main()
