"""Host file/byte/fault checks and unchanged historical-replay audit."""
from pathlib import Path
import csv,hashlib,json,math,random,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'simulation/interface_review'
sys.path.insert(0,str(OUT));sys.path.insert(0,str(ROOT/'simulation'))
from event_protocol import *
from communication_feasibility import replay,CASES,POLICIES
from run_simulation import simulate
checks=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def passed(name,detail):checks.append({'check':name,'status':'passed','detail':detail})
def count(receiver):return receiver.db.execute('SELECT count(*) FROM events').fetchone()[0]
def fails(action,kind):
    try:action()
    except kind:return
    raise AssertionError('Expected rejection')
def state(sender,key):return sender.db.execute('SELECT state,attempts FROM outbox WHERE device=? AND session=? AND seq=?',key).fetchone()

def main():
    (ROOT/'tmp').mkdir(exist_ok=True)
    assert crc16(b'123456789')==0x29b1
    rng=random.Random(470)
    for n in [0,1,23,253,254,255,256,511,1024]:
        for raw in (bytes(n),bytes(rng.randrange(256) for _ in range(n)),bytes([255])*n):assert cobs_decode(cobs_encode(raw))==raw
    passed('codec_known_crc_and_cobs_boundaries','CRC16 CCITT-FALSE check vector 0x29B1; 27 COBS byte patterns including 254-byte boundaries')
    payload=SNAPSHOT.pack(450000,1,1,1,0x80,12000,11200,3200)
    sample=Frame(EVENT,1,1,1,payload);wire=sample.wire();assert len(wire)==44
    ack_example=Frame(ACK,*sample.key,struct.pack('<I',sample.fingerprint)).wire();assert len(ack_example)==24
    assert decode(wire)==sample
    for split in range(1,len(wire)):
        stream=StreamDecoder();assert stream.feed(wire[:split])+stream.feed(wire[split:])==[sample]
    stream=StreamDecoder();assert stream.feed(wire+wire)==[sample,sample]
    assert stream.feed(b'\x01'*80+b'\x00'+wire)==[sample] and stream.errors==1
    for index in range(len(wire)-1):
        bad=bytearray(wire);bad[index]^=1
        # An inserted zero creates a new malformed boundary, both parts rejected.
        s=StreamDecoder();assert s.feed(bytes(bad))==[],index
    for f in (Frame(EVENT,1,0,1,payload),Frame(EVENT,1,1,0,payload),Frame(EVENT,1,1,1,payload[:-1]),Frame(ACK,1,1,1,b'\x00'),Frame(9,1,1,1,payload)):
        fails(lambda:decode(f.wire()),ValueError)
    for state_code,quality in ((5,0x80),(1,0x20),(1,0x40)):
        invalid=Frame(EVENT,1,1,1,SNAPSHOT.pack(450000,1,1,state_code,quality,12000,11200,3200))
        fails(lambda:decode(invalid.wire()),ValueError)
    passed('serial_fragmentation_and_corruption','43 split points, concatenation, oversized segment recovery and 43 single-bit corruption positions; invalid fields rejected')
    traces=[]
    with tempfile.TemporaryDirectory(prefix='interface-review-',dir=ROOT/'tmp') as folder:
        nodepath=str(Path(folder)/'node.db');rxpath=str(Path(folder)/'rx.db');s=Sender(nodepath);r=Receiver(rxpath)
        assert r.db.execute('PRAGMA synchronous').fetchone()[0]==3
        f=s.enqueue(payload,0);assert s.next_frame(0,aux_ready=False) is None and state(s,f.key)==('pending',0)
        assert s.next_frame(0)==f.wire();a=r.receive(f.wire(),1)
        other=__import__('sqlite3').connect(rxpath);assert other.execute('SELECT count(*) FROM events').fetchone()[0]==1;other.close()
        assert s.acknowledge(a) and state(s,f.key)==('acknowledged',1) and s.next_frame(5) is None
        traces.append({'case':'normal_commit_before_ack','key':list(f.key),'event_wire_hex':f.wire().hex(),'ack_wire_hex':a.hex(),'records_after_ack':count(r),'state':state(s,f.key)[0]})
        passed('actual_file_commit_before_ack','separate SQLite connection sees event before ACK is applied; DELETE/EXTRA configured; not power-cut testing')
        f=s.enqueue(payload,10);s.next_frame(10);fails(lambda:r.receive(f.wire(),11,crash='before_commit'),RuntimeError);assert count(r)==1
        r.close();r=Receiver(rxpath);assert count(r)==1;assert s.next_frame(14)==f.wire();a=r.receive(f.wire(),15);assert s.acknowledge(a) and count(r)==2
        passed('pre_commit_failure','injected exception rolls back; receiver reopened; retry persists then acknowledges')
        f=s.enqueue(payload,20);s.next_frame(20);fails(lambda:r.receive(f.wire(),21,crash='after_commit'),RuntimeError);assert count(r)==3
        r.close();r=Receiver(rxpath);s.close();s=Sender(nodepath);assert s.session==2
        assert s.next_frame(24)==f.wire();a=r.receive(f.wire(),25);assert s.acknowledge(a) and count(r)==3
        f_new=s.enqueue(payload,30);assert f_new.session==2 and f_new.seq==1 and f.key!=f_new.key
        passed('post_commit_restart_and_session_identity','post-commit pre-ACK stop; both host objects reopened; old frame/key retained and new committed boot identity allocated')
        assert s.next_frame(30)==f_new.wire();a=r.receive(f_new.wire(),31);duplicate=r.receive(f_new.wire(),32)
        assert a==duplicate and count(r)==4
        wrong_session=Frame(ACK,1,999,1,decode(a).payload).wire();wrong_fingerprint=Frame(ACK,*f_new.key,b'\x00'*4).wire()
        assert not s.acknowledge(wrong_session) and not s.acknowledge(wrong_fingerprint) and state(s,f_new.key)[0]=='pending'
        assert s.acknowledge(a)
        changed=Frame(EVENT,*f_new.key,SNAPSHOT.pack(450000,1,1,2,0x80,12000,11200,3200))
        fails(lambda:r.receive(changed.wire(),33),ValueError);assert count(r)==4
        passed('duplicate_conflict_and_ack_matching','identical duplicate returns identical ACK; wrong session/fingerprint ignored; same event key with changed payload rejected')
        f=s.enqueue(payload,40);sent=[]
        for now in range(40,121):
            w=s.next_frame(now)
            if w is not None:sent.append(now)
        assert sent==[40,44,48,52,62,72,82,92] and state(s,f.key)==('unconfirmed',8)
        late=r.receive(f.wire(),121);assert s.acknowledge(late) and state(s,f.key)[0]=='acknowledged_late'
        passed('bounded_attempts_and_late_ack','8 host dispatch attempts at fixed backoff; retained unconfirmed record; later matching stored ACK marked late')
        f=s.enqueue(payload,130);assert s.next_frame(430) is None and state(s,f.key)==('expired',0)
        passed('retention_deadline','300s expiration stops dispatch and retains expired record; no silent deletion')
        s.close();tiny=Sender(str(Path(folder)/'tiny.db'),queue_limit=2)
        f1=tiny.enqueue(payload,0);f2=tiny.enqueue(payload,1);assert tiny.enqueue(payload,2) is None
        assert tiny.db.execute('SELECT count(*) FROM rejected').fetchone()[0]==1 and state(tiny,f1.key)[0]=='pending' and state(tiny,f2.key)[0]=='pending';tiny.close()
        passed('queue_overflow_accounting','new event rejected when queue full; both old pending records retained; rejection snapshot stored in actual host DB')
        hol=Sender(str(Path(folder)/'hol.db'));head=hol.enqueue(payload,0);behind=hol.enqueue(payload,1);dispatch=None
        for now in range(63):
            w=hol.next_frame(now)
            if w is not None and decode(w).key==behind.key:dispatch=now;break
        assert dispatch==62 and dispatch-1>20;hol.close()
        passed('fifo_delay_counterexample','lost ACKs for head event cause the second event first dispatch at62s, 61s after creation; violates the 20s demonstration deadline')
        tm=Frame(TELEMETRY,1,2,1,payload);assert r.receive(tm.wire(),500) is None and r.db.execute('SELECT count(*) FROM telemetry').fetchone()[0]==1
        passed('telemetry_separate_from_event_ack','telemetry codec/store works without EVENT ACK; message types have separate sequence namespaces; no periodic driver or Web connection')
        r.close();s.close()
    # Legacy model is reproduced without running its output-writing main.
    with (ROOT/'simulation/communication_results/trials.csv').open(encoding='utf-8-sig',newline='') as f:historical=list(csv.DictReader(f))
    index={(r['case'],int(r['seed']),float(r['loss']),r['policy']):r for r in historical};assert len(index)==1920
    for case,_,kind,params in CASES:
        for seed in range(9200,9220):
            data=simulate(kind,seed=seed,**params)
            for loss in (0,.1,.3):
                for policy in POLICIES:
                    row=replay(data,policy,loss,seed);saved=index[(case,seed,loss,policy)]
                    for key,val in row.items():
                        if val is None:assert saved[key]==''
                        elif isinstance(val,(int,float)):assert math.isclose(float(saved[key]),val,abs_tol=1e-10,rel_tol=1e-10)
                    assert row['total_frames']==row['uplinks']+row['acks']
    passed('historical_1920_rows_reproduced','legacy simulation unchanged; reproduction validates arithmetic only, not new wire protocol, current dual-pressure detector or RF')
    sources=[Path(__file__),OUT/'event_protocol.py',ROOT/'simulation/communication_feasibility.py',ROOT/'simulation/run_simulation.py',ROOT/'simulation/communication_results/trials.csv',ROOT/'simulation/communication_results/summary.json',ROOT/'simulation/communication_results/protocol_stress.json']
    result={'date':'2026-10-04','status':'passed_host_bytes_and_file_transactions_only','physical_data':False,'checks':checks,'wire_examples':traces,'event_bytes':44,'ack_bytes':24,'uart_9600_8n1_event_ms':44*10/9600*1000,'uart_9600_8n1_ack_ms':24*10/9600*1000,'legacy_rows_reproduced':1920,'power_loss_tested':False,'serial_hardware_tested':False,'rf_airtime_measured':False,'website_integrated':False,'limitations':['exception injection is not an OS/power crash','SQLite filesystem/controller guarantees still required','MCU flash/microSD journal and atomic boot allocation not implemented','host wall-clock deadlines not MCU reboot timekeeping','UART byte time is not module air time or end-to-end latency','FIFO head-of-line delay remains a challenge','CRC/fingerprint do not authenticate sender'],'source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sources}}
    (OUT/'protocol_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    print(f'{len(checks)} host checks passed; 1920 historical rows reproduced; EVENT 44B / ACK 24B. No physical or power-cut validation.')
if __name__=='__main__':main()
