"""Adapt frozen A06/A07 traces for the operations site; no new model fitting."""
from pathlib import Path
import hashlib,json,math
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'simulation/presentation_review'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    OUT.mkdir(exist_ok=True)
    source=ROOT/'simulation/diagnosis_review/summary.json';data=json.loads(source.read_text(encoding='utf-8'))
    traces={}
    for key,t in data['traces'].items():
        rows=t['observed'];assert len(rows)==len(t['state'])==601
        assert t['seed']==10300 and t['method']=='physical'
        assert all(len(row)==3 and all(math.isfinite(v) for v in row) for row in rows)
        output={k:t[k] for k in ('t','k','r','state','kind','seed','trial_id','k0','r0')}
        output.update(p0=[row[0] for row in rows],p1=[row[1] for row in rows],q=[row[2] for row in rows],pressure_noise_kpa=t['pressure_sigma_kpa'],record_value_type='synthetic_noisy_observation',feature_value_type='ten_sample_mean_derived',physical_data=False)
        traces[t['kind']+'_'+format(t['pressure_sigma_kpa'],'.1f')]=output
    assert len(traces)==24
    result={'classification':'uncalibrated_synthetic_observation_replay','physical_data':False,'protocol_version':data['protocol_version'],'source_summary':'simulation/diagnosis_review/summary.json','source_summary_sha256':sha(source),'reference':'20261004-A06A07-v1/seed10300','operation_state_gating_implemented':False,'settings':data['settings'],'traces':traces,'adapter_sha256':sha(Path(__file__))}
    (OUT/'web_replay.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'),allow_nan=False),encoding='utf-8',newline='\n')
    print('24 frozen observed traces adapted, 601 samples each; no diagnosis or measurement recomputation.')
if __name__=='__main__':main()
