"""Independent audit artifact and falsification checks; no claims about real equipment."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
import numpy as np
from run_simulation import equilibrium, simulate

ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'simulation/audit_results/audit.json').read_text(encoding='utf-8'))
manifest=json.loads((ROOT/'simulation/audit_results/manifest.json').read_text(encoding='utf-8'))
for relative,digest in manifest.items():
    assert hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()==digest,relative
assert len(data['examples'])==12 and len(data['summary'])==48 and len(data['link'])==120

# Analytic conservation identities across random positive steady-state parameters.
rng=np.random.default_rng(4201)
for _ in range(100):
    ps=float(rng.uniform(50,200));rc=float(rng.uniform(0,1));delta=float(rng.uniform(0,.2));extra=float(rng.uniform(0,10))
    for opened in [False,True]:
        for fault in ['', 'leak','restriction']:
            pc,pa,qa=equilibrium(opened,fault,source_pressure=ps,common_resistance=rc,leak_delta=delta,restriction_extra=extra)
            c=.35+(delta if fault=='leak' else 0)
            r=.8+(extra if fault=='restriction' else 0)
            gb=.35/np.sqrt(1+.8*.35**2) if opened else 0
            qb=gb*np.sqrt(pc)
            assert abs(ps-pc-rc*(qa+qb)**2)<1e-9
            assert abs(pc-r*qa**2-(qa/c)**2)<1e-9
            assert abs(pa-.8*qa**2-(qa/c)**2)<1e-9

# Analytic counterexamples must survive reruns. These are structural, not noise-dependent.
a=data['counterexamples']['indistinguishable_steady_states']
assert np.allclose([a['restriction_pressure'],a['restriction_flow']],[a['other_pressure'],a['other_flow']],rtol=1e-12)
healthy=simulate('normal',common_resistance=0,noise_pressure=0,noise_flow=0)
assert np.ptp(healthy['pressure'])==0 and np.ptp(healthy['flow'])==0

def row(case,method):
    return next(r for r in data['summary'] if r['case']==case and r['method']==method)
assert row('weak','candidate')['hits']==0
assert row('missing','candidate')['false_mean']>0
assert row('source','normalized')['false_mean']==0
assert row('short','wait')['hits']==0 and row('short','normalized')['hits']==20
assert row('noise','candidate')['event_mean']>row('noise','candidate')['priority_mean']
assert data['grid']['normal_false_mean'][-1]>data['grid']['normal_false_mean'][0]

for path in (ROOT/'application/figures').glob('*.svg'):ET.parse(path)
for filename in ['仿真演示.html','对抗性检验.html']:
    import re
    html=(ROOT/'application'/filename).read_text(encoding='utf-8')
    assert '__SCENARIOS__' not in html and '__AUDIT__' not in html
    script=re.search(r'<script>(.*?)</script>',html,re.S).group(1)
    temp=ROOT/'tmp'/'qa'/('check-'+filename+'.js');temp.parent.mkdir(parents=True,exist_ok=True);temp.write_text(script,encoding='utf-8')
    subprocess.run(['node','--check',str(temp)],check=True,capture_output=True)
print('PASS: 600 steady-state cases, structural counterexamples, audit provenance, falsification regressions, SVG parsing and both HTML script syntax checks. No field validation.')
