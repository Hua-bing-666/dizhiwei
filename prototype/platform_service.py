"""Loopback operations service. Compiled C diagnosis; synthetic host replay only.

No MCU, serial driver, RF, or physical valve success is claimed. Receiver frames
are durable before ACK. Synthetic cursor time is deliberately not wall time.
"""
from pathlib import Path
import hashlib, json, math, shutil, subprocess, sys, time, uuid
from dataclasses import asdict
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'simulation'))
sys.path.insert(0, str(ROOT/'prototype'))
from acquisition_pipeline import AcquisitionPipeline
from acquisition_timing import PressureRead
from compact_protocol import Frame, Snapshot, SAMPLE, EVENT, TELEMETRY, MISSING, decode
from session_transport import SessionReceiver
from control_simulation import DemoController, Command

VERSION = '20261007-platform-c-v1'
SCENES = {'normal':'normal', 'supply':'supply_step', 'leak':'leak_r90',
          'restriction':'restriction_r90', 'drift':'drift_p0', 'pulse':'pulse8',
          'missing':'nan_pressure', 'range':'spike_range', 'counter':'counter_reset'}
STATUS_LABELS = ['有效', '健康参照未确认', '参照不可用', '压力质量异常', '窗口重建', '超出工作范围']
PATTERN_LABELS = ['未见持续偏离', '等效泄漏候选', '等效受限候选', '异常待核查', '暂停判断']
EVENT_LABELS = {1:'质量状态变化',2:'测量质量异常',3:'短窗关注提示',4:'等效泄漏候选',5:'等效受限候选',6:'异常待核查'}

def clean(value):
    if isinstance(value, dict): return {k:clean(v) for k,v in value.items()}
    if isinstance(value, (tuple,list)): return [clean(v) for v in value]
    if hasattr(value, 'item'): return clean(value.item())
    if isinstance(value, float) and not math.isfinite(value): return None
    return value

def dump(value): return json.dumps(clean(value), ensure_ascii=False, allow_nan=False, separators=(',',':'))

def compile_bridge():
    exe = ROOT/'tmp/platform_runtime/acquisition_bridge.exe'
    exe.parent.mkdir(parents=True, exist_ok=True)
    sources = [ROOT/'firmware/integer_diagnosis.c', ROOT/'firmware/integer_diagnosis.h', ROOT/'firmware/acquisition_bridge.c']
    digest = hashlib.sha256(b''.join(p.read_bytes() for p in sources)).hexdigest()
    receipt = exe.with_suffix('.sha256')
    if not exe.exists() or not receipt.exists() or receipt.read_text() != digest:
        gcc = shutil.which('gcc') or ('D:/bin/gcc.exe' if Path('D:/bin/gcc.exe').exists() else None)
        if not gcc: raise RuntimeError('找不到 GCC：安装 C 编译器后重新启动；网页仍可离线打开。')
        args = [gcc,'-std=c11','-Wall','-Wextra','-Werror','-Wconversion','-O2','-ftrapv',str(sources[0]),str(sources[2]),'-o',str(exe)]
        result = subprocess.run(args, capture_output=True, text=True)
        if result.returncode: raise RuntimeError(result.stderr)
        receipt.write_text(digest, encoding='ascii')
    return exe, digest

def reference_profile(sigma=.3):
    """Independent healthy trace only; no monitored fault used for calibration."""
    from review_quality_intervals import inputs
    from integrated_monitor import Monitor
    from review_integer_diagnosis import profile
    baseline=json.loads((ROOT/'simulation/quality_interval_review/frozen_parameters.json').read_text(encoding='utf-8'))
    _, obs, counts = inputs('normal', sigma, 69001)
    m=Monitor(baseline['reference'], baseline['limits']['1'], 'independent-health-69001', healthy_reference_approved=True)
    for t in range(130): m.update(t, int(counts[t]), obs[t,:2])
    return profile(m, baseline['reference'])

def observation_trace(scene, sigma=.3, seed=70001):
    from review_quality_intervals import inputs
    if scene not in SCENES or sigma not in (.3,3.,10.): raise ValueError('未知场景或噪声档位')
    kind=SCENES[scene]
    return inputs(kind, sigma, seed, scene in ('drift','missing','range','counter'))

def pressure_reads(t, values):
    end=(t+1)*1000
    return [PressureRead(end-28,end-19,float(values[0]),True), PressureRead(end-18,end-9,float(values[1]),True)]

def display_snapshot(s, profile=None):
    def value(v, scale): return None if v==MISSING else v/scale
    p0,p1,q=value(s.p0,100),value(s.p1,100),value(s.q10,1000)
    result=dict(t_s=s.sample_seq-1, p0=p0,p1=p1,q=q, count=s.cumulative_pulses,
                status=s.status,status_label=STATUS_LABELS[s.status],pattern=s.pattern,
                pattern_label=PATTERN_LABELS[s.pattern],rapid_valid=bool(s.flags&4),rapid_active=bool(s.flags&8),
                synthetic=bool(s.flags&128),reference_approved=bool(s.flags&2),config_id=s.config_id,
                reference_id=s.reference_id,pressure_age_ms=[None if x==255 else x for x in (s.p0_age_ms,s.p1_age_ms)])
    return result

class Platform:
    def __init__(self, path=':memory:'):
        self.receiver=SessionReceiver(path);self.db=self.receiver.db
        self.db.execute('CREATE TABLE IF NOT EXISTS platform_runs(session INTEGER PRIMARY KEY, manifest TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS platform_notes(id INTEGER PRIMARY KEY, device INTEGER, session INTEGER, seq INTEGER, stage TEXT, note TEXT, created_ms INTEGER)')
        self.db.execute('CREATE TABLE IF NOT EXISTS platform_commands(id TEXT PRIMARY KEY, body TEXT NOT NULL)')
        self.db.commit();self.pipeline=None;self.trace=None;self.run=None;self.seq=0
        self.exe,self.digest=compile_bridge();self.control=DemoController()
        for body, in self.db.execute('SELECT body FROM platform_commands'):
            command=Command(**json.loads(body));self.control.commands[command.command_id]=command
    def close(self):
        if self.pipeline: self.pipeline.close();self.pipeline=None
        self.receiver.close()
    def runs(self): return [dict(session=s,**json.loads(m)) for s,m in self.db.execute('SELECT session,manifest FROM platform_runs ORDER BY session DESC')]
    def start(self, scene='leak', sigma=.3):
        sigma=float(sigma);tr,obs,counts=observation_trace(scene,sigma)
        profile=reference_profile(sigma)
        if self.pipeline:self.pipeline.close()
        session=self.db.execute('SELECT COALESCE(MAX(session),0)+1 FROM platform_runs').fetchone()[0]
        manifest=dict(version=VERSION,scene=scene,sigma=sigma,synthetic=True,physical_data=False,
                      c_sha256=self.digest,profile=profile,calibration_seed=69001,monitoring_seed=70001,
                      healthy_reference_approved=True,approval_evidence='synthetic healthy training manifest, not field approval',
                      clock='synthetic_cursor_not_wall_clock',transport='host_loopback_not_RF',created_ms=int(time.time()*1000))
        self.receiver.register(1,session,1,dict(synthetic=True,healthy_reference_approved=True,profile=profile))
        self.receiver.register_time_mapping(1,session,0,0,'shared synthetic replay clock only')
        with self.db:self.db.execute('INSERT INTO platform_runs VALUES(?,?)',(session,dump(manifest)))
        self.run=dict(session=session,**manifest);self.trace=(obs,counts);self.seq=0
        self.pipeline=AcquisitionPipeline(profile,self.exe,config_id=session,reference_id=1,synthetic=True)
        return self.state()
    def step(self,n=1):
        if not isinstance(n,int) or isinstance(n,bool) or not 1<=n<=32:raise ValueError('每批允许 1—32 个采样点')
        if not self.pipeline:raise ValueError('先建立新的回放会话；历史会话只读')
        obs,counts=self.trace
        for _ in range(n):
            t=self.pipeline.clock+1
            if t>=len(counts):break
            self.ingest_raw(t,int(counts[t]),(t+1)*1000,pressure_reads(t,obs[t,:2]))
        return self.state()
    def ingest_raw(self,t,count,latch_ms,reads):
        if not self.pipeline:raise ValueError('先启动软件测试会话')
        r,fresh=self.pipeline.update(t,count,latch_ms,reads)
        # Each host sample is persisted for software inspection. This is not a
        # proposed once-per-second RF transmission schedule.
        for kind,payload in [(TELEMETRY,r['snapshot'].pack())]+[(EVENT,e['payload']) for e in fresh]:
            self.seq+=1
            frame=Frame(kind,1,self.run['session'],self.seq,payload)
            self.receiver.accept(frame.wire(),(t+1)*1000)
        return r
    def ingest_wire(self,wire,now_ms):
        # Only pre-registered configurations are accepted. This endpoint does
        # not silently label an unknown physical node as synthetic or healthy.
        return self.receiver.accept(wire,now_ms)
    def samples(self,session=None):
        if session is None:
            row=self.db.execute('SELECT MAX(session) FROM platform_runs').fetchone();session=row[0]
        if session is None:return []
        return [display_snapshot(Snapshot.unpack(body)) for body, in self.db.execute('SELECT body FROM samples WHERE device=1 AND session=? ORDER BY sample_seq',(session,))]
    def events(self):
        result=[]
        for d,s,q,body,received in self.db.execute('SELECT device,session,seq,body,received_ms FROM frames ORDER BY session DESC,seq DESC'):
            if body[1]!=EVENT:continue
            f=Frame(EVENT,d,s,q,body[16:]);snap=Snapshot.unpack(f.payload[:SAMPLE.size]);code,detail=f.payload[SAMPLE.size:]
            notes=[dict(stage=st,note=no,created_ms=ms) for st,no,ms in self.db.execute('SELECT stage,note,created_ms FROM platform_notes WHERE device=? AND session=? AND seq=? ORDER BY id',(d,s,q))]
            result.append(dict(id=f'{d}:{s}:{q}',session=s,code=code,label=EVENT_LABELS[code],detail=detail,
                               snapshot=display_snapshot(snap),transport='SQLite committed; host ACK, not RF receipt',notes=notes,
                               stage=notes[-1]['stage'] if notes else 'open'))
        return result
    def annotate(self,event_id,stage,note,proof=''):
        if stage not in ('viewed','pending_recheck','needs_check','archived'):raise ValueError('未知核查状态')
        note=note.strip()
        if not note or len(note)>2000:raise ValueError('填写 1—2000 字核查依据')
        event=next((e for e in self.events() if e['id']==event_id),None)
        if not event:raise ValueError('事件不存在')
        if stage=='archived' and not any(n['stage']=='viewed' for n in event['notes']):raise ValueError('先记录已查看，再填写复测依据；归档不改变诊断结果')
        if stage=='archived':
            if not isinstance(proof,str) or not proof.strip() or len(proof)>2000:raise ValueError('归档须填写单独的复测依据')
            current=self.samples()
            if not current or current[-1]['status']!=0:raise ValueError('当前测量质量未满足要求，保留待复测状态')
            note+='\n复测依据（人工记录，未自动认证）：'+proof.strip()
        with self.db:self.db.execute('INSERT INTO platform_notes(device,session,seq,stage,note,created_ms) VALUES(?,?,?,?,?,?)',(*map(int,event_id.split(':')),stage,note,int(time.time()*1000)))
        return self.events()
    def command(self,action,cid=None):
        if action=='request':
            cid=cid or uuid.uuid4().hex
            c=self.control.trigger_valve_close(cid,'manual','operator requested host-only LED demonstration')
        elif action=='receive':c=self.control.acknowledge_receipt(cid,'A')
        elif action=='execute':c=self.control.mock_execute(cid)
        elif action=='reset':c=self.control.manual_reset(cid)
        else:raise ValueError('未知演示指令')
        with self.db:self.db.execute('INSERT OR REPLACE INTO platform_commands VALUES(?,?)',(c.command_id,dump(asdict(c))))
        return asdict(c)
    def state(self):
        runs=self.runs();run=self.run or (runs[0] if runs else None);samples=self.samples(run['session'] if run else None)
        return dict(version=VERSION,physical_data=False,rf_connected=False,mode='host_replay',active=bool(self.pipeline and not self.pipeline.halted),
                    run={k:v for k,v in run.items() if k!='profile'} if run else None,current=samples[-1] if samples else None,
                    freshness='replay_cursor_not_live' if self.pipeline else 'history_not_live',count=len(samples),
                    configuration=run.get('profile') if run else None,
                    events=self.events(),commands=[asdict(c) for c in self.control.commands.values()],runs=[{k:v for k,v in r.items() if k!='profile'} for r in runs])
