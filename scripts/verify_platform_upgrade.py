"""Targeted acceptance: C/SQLite/API boundary and immutable event workflow."""
from pathlib import Path
import json,sys,tempfile,hashlib,time
from contextlib import ExitStack
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'prototype'),str(ROOT/'simulation')]
from platform_service import *
from integer_diagnosis_reference import IntegerOracle,FIELDS
from acquisition_pipeline import SessionResetRequired
from compact_protocol import ACK,EVENT_DETAIL
from reference_calibration import fit_reference
checks=[]
def check(name,condition):
    assert condition,name;checks.append(name)
def rejects(name,fn):
    try:fn()
    except (ValueError,SessionResetRequired):checks.append(name)
    else:raise AssertionError(name)

with tempfile.TemporaryDirectory(prefix='platform-upgrade-') as tmp, ExitStack() as resources:
    path=Path(tmp)/'operations.sqlite';p=Platform(path);resources.callback(p.close);p.start('leak',.3)
    oracle=IntegerOracle(p.run['profile']);obs,counts=p.trace
    for t,count in enumerate(counts):
        r=p.ingest_raw(t,int(count),(t+1)*1000,pressure_reads(t,obs[t,:2]))
        expect=oracle.update(t,int(count),round(float(obs[t,0])*100),round(float(obs[t,1])*100),0)
        assert [r['fields'][k] for k in FIELDS]==expect
    check('631_C_samples_match_independent_rational_oracle',len(p.samples())==631)
    candidates=[e for e in p.events() if e['code']>=4];check('candidate_created',bool(candidates))
    e=candidates[0];frozen=dump(e['snapshot'])
    rejects('archive_requires_view_record',lambda:p.annotate(e['id'],'archived','retest'))
    rejects('empty_evidence_rejected',lambda:p.annotate(e['id'],'viewed',' '))
    p.annotate(e['id'],'viewed','synthetic check <script> fixture');p.annotate(e['id'],'pending_recheck','same-condition retest pending')
    rejects('archive_requires_separate_retest_evidence',lambda:p.annotate(e['id'],'archived','close item'))
    p.annotate(e['id'],'archived','manual fixture only, no physical recovery','independent manual evidence fixture, not physical')
    check('notes_append_without_rewriting_algorithm_snapshot',dump(next(x for x in p.events() if x['id']==e['id'])['snapshot'])==frozen)
    entry=p.receiver.frames()[-1];key,body,ms=entry['key'],entry['body'],entry['received_ms']
    frame=Frame(body[1],*key,body[16:]);before=p.db.execute('SELECT COUNT(*) FROM frames').fetchone()[0]
    ack=decode(p.ingest_wire(frame.wire(),ms+1));check('duplicate_ACK_idempotent',ack.kind==ACK and p.db.execute('SELECT COUNT(*) FROM frames').fetchone()[0]==before)
    altered=bytearray(frame.payload);altered[14]^=1
    rejects('same_message_or_snapshot_conflict_no_ACK',lambda:p.ingest_wire(Frame(frame.kind,*frame.key,bytes(altered)).wire(),ms+2))
    corrupt=bytearray(frame.wire());corrupt[3]^=1
    rejects('CRC_corruption_no_ACK',lambda:p.ingest_wire(bytes(corrupt),ms+2))
    unknown=Frame(frame.kind,999,999,1,frame.payload)
    rejects('unknown_configuration_no_ACK',lambda:p.ingest_wire(unknown.wire(),ms+3))
    # ACK-loss replay must find the committed frame; read the independent DB.
    import sqlite3
    other=sqlite3.connect(path);check('ACK_refers_to_committed_database',other.execute('SELECT body FROM frames WHERE device=? AND session=? AND seq=?',frame.key).fetchone()[0]==body);other.close()
    c=p.command('request','fixture-control');rejects('execution_without_receive_rejected',lambda:p.command('execute',c['command_id']))
    p.command('receive',c['command_id']);first=p.command('execute',c['command_id']);p.command('execute',c['command_id'])
    check('control_simulation_idempotent_and_not_physical',p.control.output_count==1 and first['physical_verified'] is False)
    p.close();p=Platform(path);resources.callback(p.close)
    check('restart_history_is_not_live',not p.state()['active'] and p.state()['freshness']=='history_not_live' and len(p.samples())==631)
    check('notes_and_control_survive_restart',len(next(x for x in p.events() if x['id']==e['id'])['notes'])==3 and p.state()['commands'][0]['status']=='demo_confirmed')
    p.command('reset','fixture-control');check('manual_reset_is_separate',p.state()['commands'][0]['output']=='off')
    p.start('missing',.3)
    while p.pipeline.clock<365:p.step(min(32,365-p.pipeline.clock))
    rr=p.samples();check('missing_pressure_explicit_null_and_rebuild',rr[360]['p0'] is None and rr[360]['p1'] is None and rr[360]['status']==3 and rr[365]['status']!=0)
    p.step(20);check('window_recovers_only_after_valid_points',p.samples()[-1]['status']==0)
    rejects('clock_gap_halts_session',lambda:p.ingest_raw(p.pipeline.clock+2,10000,(p.pipeline.clock+3)*1000,pressure_reads(p.pipeline.clock+2,[100,80])))
    check('halted_session_not_active',not p.state()['active'])
    p.start('counter',.3)
    while p.pipeline.clock<430:p.step(min(32,430-p.pipeline.clock))
    check('counter_reset_event_retained',any(e['code']==2 and e['detail']==3 for e in p.events() if e['session']==p.run['session']))
    check('sessions_do_not_overwrite_old_samples',len(p.samples(1))==631)
    active=p.run['session'];before=p.state()['current']
    archive=p.history(1)
    check('history_reads_old_run_without_switching_current',archive['run']['session']==1 and len(archive['samples'])==631 and p.run['session']==active and p.state()['current']==before)
    check('history_notes_are_scoped_to_selected_session',all(e['session']==1 for e in archive['events']) and any(e['notes'] for e in archive['events']))
    rejects('unknown_history_session_rejected',lambda:p.history(999999))
    bundle=p.export()
    check('export_state_and_samples_share_same_snapshot',bundle['state']['current']==bundle['samples'][-1] and bundle['state']['count']==len(bundle['samples']) and 'samples' not in bundle['state'])
    p.close()
data=json.loads((ROOT/'simulation/platform_upgrade/web_data.json').read_text(encoding='utf-8'))
check('offline_replay_independent_health_training',data['c_calibration_seed']!=data['c_replay_seed'] and len(data['traces'])==27)
trials=json.loads((ROOT/'simulation/platform_upgrade/scheduling_trials.json').read_text(encoding='utf-8'))
check('432_scheduler_trials_include_all_phases',len(trials)==432 and len({(r['period'],r['phase']) for r in trials})==8)
text='p0_kpa,p1_kpa,q_l_min\n'+'\n'.join(f'{p+.8*(2.8*(p/100)**.3)**2},{p},{2.8*(p/100)**.3}' for p in range(50,131,10))
reference=fit_reference(text)
check('multi_pressure_reference_recovers_synthetic_power_law',abs(reference['n_fitted']-.3)<1e-12 and abs(reference['a_l_min']-2.8)<1e-12)
check('candidate_reference_does_not_self_approve_or_claim_physical',reference['profile']['approved']==0 and not reference['physical_verified'] and reference['profile']['rapid_available']==0)
rejects('calibration_bad_header',lambda:fit_reference('P0,P1,Q\n1,2,3'))
rejects('calibration_missing_or_nonfinite',lambda:fit_reference(text.replace('50,','NaN,',1)))
rejects('calibration_insufficient_pressure_span',lambda:fit_reference('p0_kpa,p1_kpa,q_l_min\n'+'\n'.join(f'{100+i/10},{90+i/10},2.8' for i in range(9))))
cross=json.loads((ROOT/'simulation/platform_upgrade/cross_operating_points.json').read_text(encoding='utf-8'))
check('cross_operating_seeds_disjoint_and_failures_retained',len(cross['trials'])==72 and 69001 not in cross['test_seeds'] and any(r['false_onsets'] for r in cross['trials']) and not cross['profile_retuned_on_test'])
out=ROOT/'simulation/platform_upgrade/service_acceptance.json';out.write_text(json.dumps(dict(checks=checks,passed=len(checks),classification='host_software_checks_not_hardware',physical_data=False),ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
print(f'{len(checks)} service acceptance checks passed')
