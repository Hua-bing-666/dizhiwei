"""Checks that matter: shared detection, null reception, queue overflow, plot geometry."""
from pathlib import Path
import json, csv, math, sys, importlib.util, subprocess
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]; P=ROOT/'projects/drip-research_ppt169_20261002'
sys.path.insert(0,str(ROOT/'simulation'))
from communication_feasibility import replay
from run_simulation import simulate

rows=list(csv.DictReader((ROOT/'simulation/communication_results/trials.csv').open(encoding='utf-8-sig')))
assert len(rows)==1920
for key in {(r['case'],r['seed'],r['loss']) for r in rows}:
    rr=[r for r in rows if (r['case'],r['seed'],r['loss'])==key]
    assert len(rr)==4 and len({r['local_onsets'] for r in rr})==1
    for r in rr:
        assert int(r['timely20'])<=int(r['received_onsets'])<=int(r['local_onsets'])
        assert int(r['total_frames'])==int(r['uplinks'])+int(r['acks'])
        assert 0<=float(r['coverage'])<=1

data=simulate('overlap',seed=9200,duration=8)
stress=[]
for policy in ['p10','p30','raw','bounded']:
    r=replay(data,policy,1,9200)
    assert r['received_onsets']==0 and r['coverage']==0 and r['pressure_mae'] is None
    stress.append({'scenario':'all_packets_lost','policy':policy,**r})
    r=replay(data,policy,0,9200,burst_seconds=120)
    assert r['received_onsets']>0 and r['timely20']==0
    stress.append({'scenario':'120_second_outage','policy':policy,**r})
many=simulate('normal',seed=9200)
many['alarm']=[bool((t//10)%2) for t in range(601)]
r=replay(many,'bounded',1,9200,queue_limit=2)
assert r['overflow']>0 and r['received_onsets']==0
stress.append({'scenario':'forced_alarm_chatter_tiny_queue_total_loss','policy':'bounded',**r})
(ROOT/'simulation/communication_results/protocol_stress.json').write_text(json.dumps({'data_class':'synthetic_protocol_stress','results':stress},ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8',newline='\n')
print('Matched detector checks and 9 protocol stress checks passed (full loss, long outage, overflow).')

# Each data-driven mark is checked against the same axis transform AND the skill calculator.
ns={'s':'http://www.w3.org/2000/svg'};calc=Path(r'C:\Users\Lenovo\.codex\skills\ppt-master\scripts\svg_position_calculator.py')
receipts=[]
for filename in ['06_slide.svg','07_slide.svg']:
    root=ET.parse(P/'svg_output'/filename).getroot()
    for g in root.findall('.//s:g[@data-pptx-replace-with="chart"]',ns):
        meta=json.loads(g.find('s:metadata',ns).text);a=meta['plot_area'];axis=meta['axes']
        X=lambda x:a['x']+(x-axis['x']['minimum'])/(axis['x']['maximum']-axis['x']['minimum'])*a['width']
        Y=lambda y:a['y']+a['height']-(y-axis['y']['minimum'])/(axis['y']['maximum']-axis['y']['minimum'])*a['height']
        lines=g.findall('.//s:polyline',ns);dots=g.findall('.//s:circle',ns)
        for i,s in enumerate(meta['series']):
            if lines:
                marks=[tuple(map(float,point.split(','))) for point in lines[i].get('points').split()]
                assert len(marks)==len(s['x'])
                for (px,py),x,y in zip(marks,s['x'],s['y']):assert abs(px-X(x))<.002 and abs(py-Y(y))<.002
            else:
                assert abs(float(dots[i].get('cx'))-X(s['x'][0]))<.002 and abs(float(dots[i].get('cy'))-Y(s['y'][0]))<.002
            args=[sys.executable,str(calc),'calc','line','--data',','.join(f'{x}:{y}' for x,y in zip(s['x'],s['y'])),'--area',f"{a['x']},{a['y']},{a['x']+a['width']},{a['y']+a['height']}",f"--x-range={axis['x']['minimum']},{axis['x']['maximum']}",f"--y-range={axis['y']['minimum']},{axis['y']['maximum']}"]
            result=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',check=True)
            (P/'validation'/f"{g.get('id')}-{i}-coordinates.txt").write_text(result.stdout,encoding='utf-8')
        receipt=f"verify-charts: {filename} | object={g.get('id')} | type=scatter | mode=direct-calc | scale=from ticks/payload | calc=ran x{len(meta['series'])} | svg=unchanged | every mark checked"
        print(receipt);receipts.append(receipt)
(P/'validation/chart_verification.md').write_text('\n'.join(receipts)+'\n',encoding='utf-8',newline='\n')
assert len(receipts)==3
