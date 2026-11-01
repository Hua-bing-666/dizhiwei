"""Freeze A04/A08 internal evidence; never mark procurement/build/RF passed."""
from pathlib import Path
import hashlib,json,re,subprocess,xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'simulation/interface_review';FIG=ROOT/'application/figures/interface_review'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,data):p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')

def main():
    protocol=read(DATA/'protocol_checks.json');hardware=read(DATA/'hardware_checks.json')
    proof=read(FIG/'figure_provenance.json');layout=read(DATA/'figure_layout_checks.json')
    manual=read(DATA/'manual_review.json');sources=read(DATA/'source_checks.json')
    market=read(DATA/'market_observations.json')
    assert market['date']=='2026-10-04', 'New market observation requires updating this frozen report/version'
    prices={r['model']:r.get('display_price_cny') for r in market['records']}
    assert prices['SEN0549']==109 and prices['DFR0553']==79 and prices['E220-400T22D'] is None
    assert all(r.get('http_status')==200 and not r.get('error') and not r['stock_verified'] for r in market['records'])
    assert protocol['status']=='passed_host_bytes_and_file_transactions_only'
    assert hardware['status']=='conditional_arithmetic_passed_build_and_procurement_unverified'
    assert len(protocol['checks'])==12 and all(c['status']=='passed' for c in protocol['checks'])
    assert not any(protocol[k] for k in ('physical_data','power_loss_tested','serial_hardware_tested','rf_airtime_measured','website_integrated'))
    assert hardware['pin_assignment_count']==17 and hardware['pin_conflicts']==[] and hardware['fault_22ma_at_adc_supply_rail_requires_protection']
    assert len(hardware['unverified_gates'])==8 and len(sources['sources'])==8
    assert protocol['event_bytes']==44 and protocol['ack_bytes']==24 and protocol['legacy_rows_reproduced']==1920
    for record in (protocol,hardware,proof):
        for path,digest in record['source_sha256'].items():assert sha(ROOT/path)==digest,('Stale evidence',path)
    assert layout['status']=='passed' and len(layout['figures'])==len(proof['figures'])==len(manual['figures'])==3
    assert sha(ROOT/'scripts/verify_interface_figures.mjs')==layout['source_sha256']['script']
    assert sha(FIG/'figure_provenance.json')==layout['source_sha256']['provenance']
    for f in layout['figures']:
        assert not f['outside'] and not f['overlaps'] and not f['boxErrors'] and f['minimumTextPtAt425pt']>=9
        p=next(v for v in proof['figures'] if v['name']==f['name'])
        m=next(v for v in manual['figures'] if v['name']==f['name'])
        for ext,digest in f['sha256'].items():assert sha(FIG/(f['name']+'.'+ext))==digest
        assert p['svg_sha256']==f['sha256']['svg'] and m['png_sha256']==f['sha256']['png'] and m['viewed']
        # Verify provenance line coordinates against actual SVG path data,
        # rather than treating unrendered metadata as an anchor check.
        svg=ET.parse(FIG/(f['name']+'.svg'));paths={e.attrib['d'] for e in svg.iter() if e.tag.endswith('path') and 'd' in e.attrib}
        for c in p['connections']:
            expected='M '+' L '.join(f'{x} {y}' for x,y in c['points'])
            assert expected in paths,('Connection metadata differs from SVG',c['meaning'])
    assert not manual['independent_external_review'] and not manual['physical_validation']
    document=ROOT/'docs/硬件接口与LoRa通信论证分项验收.md'
    # Relative links must remain usable in the source/evidence package.
    checked_links=0
    for target in re.findall(r'\]\(([^)]+)\)',document.read_text(encoding='utf-8')):
        if '://' in target or target.startswith('#'):continue
        dest=(document.parent/target.split('#')[0]).resolve()
        if dest==ROOT/'deliverables/接口与通信分项验收记录.json':continue
        assert dest.is_file(),('Missing report link',target);checked_links+=1
    base=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    tracked=subprocess.run(['git','ls-tree','-r','--name-only','-z','HEAD'],cwd=ROOT,capture_output=True,check=True).stdout.decode('utf-8').split('\0')
    prefixes=['application/models/','application/figures/collection_review/','application/figures/diagnosis_review/','simulation/diagnosis_review/','simulation/diagnosis_results/','simulation/hardware_results/','simulation/communication_results/']
    preserved=['deliverables/大创申报书_模板填写稿.docx','deliverables/大创申报书_模板审阅版.pdf','deliverables/项目书审阅版.pdf','deliverables/立项答辩.pptx','deliverables/立项答辩审阅版.pdf','deliverables/index.html','deliverables/研究与答辩资料.html','deliverables/台架三维结构交互模型.html','deliverables/台架三维结构交互模型_收集优化候选版.html','deliverables/三维分项验收记录.json','deliverables/仿真分项验收记录.json','application/references.json','docs/三维台架建模论证与本轮验收.md','docs/仿真建模与诊断证据分项验收.md','simulation/diagnosis_feasibility.py','simulation/review_diagnosis.py','simulation/communication_feasibility.py','simulation/run_simulation.py']
    names=sorted(set(preserved+[p for p in tracked if any(p.startswith(x) for x in prefixes)]));unchanged=[]
    for path in names:
        prior=subprocess.run(['git','show','HEAD:'+path],cwd=ROOT,capture_output=True,check=True).stdout
        assert (ROOT/path).read_bytes()==prior,('Out-of-scope change',path)
        unchanged.append({'path':path,'sha256':sha(ROOT/path)})
    progress=read(ROOT/'deliverables/分项验收进度.json')
    previous=[t.copy() for t in progress['tasks'] if t['id'] in ('A05','A06','A07')]
    progress.update(date='2026-10-04',scope='A05 concept and A06/A07 uncalibrated evidence; A04/A08 partial interface/host checks; application integration pending',plan_sha256=sha(ROOT/'docs/三阶段分项执行与验收标准.md'),this_turn='A04/A08 candidate arithmetic, host bytes/transactions and three figures checked; build/procurement/RF unverified',next='A09/A10 current website evidence and selective figure integration planning')
    for t in progress['tasks']:
        if t['id'] in ('A04','A08'):t.update(status='partial_internal_checks_passed_build_release_pending',record='deliverables/接口与通信分项验收记录.json')
    assert previous==[t for t in progress['tasks'] if t['id'] in ('A05','A06','A07')]
    report={
        'date':'2026-10-04','version':'20261004-A04A08-v1','task_ids':['A04','A08'],
        'status':'partial_internal_checks_passed_build_release_pending','physical_validation':False,
        'application_integration_complete':False,'base_commit_for_preservation':base,
        'hardware_checks':{k:v for k,v in hardware.items() if k!='source_sha256'},
        'host_protocol_checks':protocol['checks'],
        'figure_checks':[{'name':f['name'],'text_count':f['textCount'],'outside':f['outside'],'overlaps':f['overlaps'],'box_errors':f['boxErrors'],'minimum_font_pt_at_425pt':f['minimumTextPtAt425pt'],'sha256':f['sha256']} for f in layout['figures']],
        'connection_coordinates_matched_to_svg':sum(len(f['connections']) for f in proof['figures']),
        'manual_review':manual,'report_relative_links_checked':checked_links,
        'market_scope':'public manufacturer display prices and supplier outbound links; no SKU/stock/checkout/pressure quote verification',
        'corrections':['sensor 5V pulses require tolerant 3.3V buffer','module 5V VCC is not 5V UART','22mA reaches ADC rail; protection values unreleased','AUX is firmware/config dependent, not persistent delivery ACK','normal ACK and ACK-loss path explicitly separated','FIFO lost-ACK counterexample: next event first dispatch delayed 61s'],
        'limitations':protocol['limitations']+['pressure quotation and source/reference borrowing not secured','RC/input clamp not build-released','power allowances not worst-case guarantees or measured consumption','discrete sampling not merged with diagnosis simulation','MCU resource usage, flash boot allocation and SD recovery not verified','old report hashes identify their frozen versions, not amended current plan'],
        'original_artifacts_unchanged':unchanged,
        'source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in [Path(__file__),document,ROOT/'docs/三阶段分项执行与验收标准.md',DATA/'hardware_checks.json',DATA/'protocol_checks.json',DATA/'source_checks.json',DATA/'market_observations.json',DATA/'figure_layout_checks.json',DATA/'manual_review.json',FIG/'figure_provenance.json']}
    }
    write(ROOT/'deliverables/接口与通信分项验收记录.json',report);write(ROOT/'deliverables/分项验收进度.json',progress)
    delivery=read(ROOT/'deliverables/交付检查.json');delivery['staged_interface_review']={'task_ids':['A04','A08'],'status':report['status'],'record':'接口与通信分项验收记录.json','report':'../docs/硬件接口与LoRa通信论证分项验收.md','figures':3,'host_check_groups':12,'physical_validation':False,'build_released':False,'application_integration_complete':False};write(ROOT/'deliverables/交付检查.json',delivery)
    print(f'A04/A08 partial: 12 host checks, 3 SVG/PNG pairs; {len(names)} original artifacts preserved; A05/A06/A07 retained. No build/procurement/RF pass.')

if __name__=='__main__':main()
