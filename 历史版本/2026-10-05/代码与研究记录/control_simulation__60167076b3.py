"""Host-only demonstration state machine. Does not operate a physical valve."""
from dataclasses import dataclass,asdict
from pathlib import Path
import json

@dataclass
class Command:
    command_id:str
    branch_id:str
    source:str
    reason:str
    status:str='requested'
    mode:str='simulation'
    physical_verified:bool=False
    output:str='off'

class DemoController:
    def __init__(self,branch='A'):
        self.branch=branch
        self.commands={}
        self.output_count=0
    def trigger_valve_close(self,cid,source,reason,valid=True,known=True,confirmed=True,protect=False):
        if source not in ('manual','automatic'):
            raise ValueError('unknown request source')
        if source=='automatic' and not (valid and known and confirmed and protect):
            return None
        prior=self.commands.get(cid)
        if prior:
            if (prior.source,prior.reason)!=(source,reason):
                raise ValueError('command identity/content conflict')
            return prior
        command=Command(cid,self.branch,source,reason)
        self.commands[cid]=command
        return command
    def acknowledge_receipt(self,cid,branch):
        c=self.commands[cid]
        if branch!=c.branch_id:raise ValueError('wrong branch')
        if c.status=='requested':c.status='received'
        return c
    def mock_execute(self,cid):
        c=self.commands[cid]
        if c.status not in ('received','demo_confirmed'):
            raise ValueError('request not received or already reset')
        if c.status!='demo_confirmed':
            self.output_count+=1
            c.output='mock_LED_on'
            c.status='demo_confirmed'
        return c
    def manual_reset(self,cid):
        c=self.commands[cid]
        c.output='off';c.status='manually_reset'
        return c

def self_check():
    d=DemoController();checks=[]
    def test(name,condition):
        assert condition,name
        checks.append(dict(name=name,passed=True))
    test('normal does not generate protection',d.trigger_valve_close('normal','automatic','normal',protect=False) is None)
    for name,arg in [('invalid','valid'),('unknown_operation','known'),('unconfirmed','confirmed')]:
        kw=dict(valid=True,known=True,confirmed=True,protect=True);kw[arg]=False
        test(name,d.trigger_valve_close(name,'automatic',name,**kw) is None)
    c=d.trigger_valve_close('demo-1','automatic','known severe candidate',protect=True)
    test('request is not actual or demo execution',c.status=='requested' and c.output=='off' and not c.physical_verified)
    test('duplicate is idempotent',d.trigger_valve_close('demo-1','automatic','known severe candidate',protect=True) is c)
    try:d.trigger_valve_close('demo-1','automatic','different',protect=True)
    except ValueError:checks.append(dict(name='conflicting content rejected',passed=True))
    else:raise AssertionError('content conflict not rejected')
    try:d.acknowledge_receipt('demo-1','B')
    except ValueError:checks.append(dict(name='wrong branch feedback rejected',passed=True))
    else:raise AssertionError('wrong branch accepted')
    d.acknowledge_receipt('demo-1','A')
    test('receipt does not imply output or valve closure',c.status=='received' and c.output=='off' and not c.physical_verified)
    d.mock_execute('demo-1');d.mock_execute('demo-1')
    test('repeated execution produces one demo effect',d.output_count==1 and c.status=='demo_confirmed' and not c.physical_verified)
    d.manual_reset('demo-1')
    test('manual reset stops demonstration',c.status=='manually_reset' and c.output=='off')
    m=d.trigger_valve_close('manual-2','manual','operator request')
    test('manual operation uses same request states',m.status=='requested' and not m.physical_verified)
    root=Path(__file__).resolve().parents[1];out=root/'simulation/control_review';out.mkdir(parents=True,exist_ok=True)
    (out/'checks.json').write_text(json.dumps(dict(classification='host_mock_only',hardware_compiled=False,
        physical_execution=False,checks=checks,commands=[asdict(c) for c in d.commands.values()]),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'{len(checks)} host control checks passed. No valve, firmware or physical IO tested.')

if __name__=='__main__':self_check()
