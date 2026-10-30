"""Independent score trace boundaries and narrowly scoped validator extensions."""
import copy,json,unittest
from pathlib import Path
from test_exit_tally import fixture as exit_fixture
from genesis_score_capture import validate,RANGES
from score_cases import goldens,decode


def fixture(consume=True):
    original=exit_fixture();template=original['events'][0];events=[];sp=0xffffeffc
    secondary=2;timer=65535 if consume else 0;value=0x10000;threshold=0x10000;reward=8;scratch=0xdeadbeef;mailbox=None
    def event(pc,stack=None,ret=0xf906):
        e=copy.deepcopy(template);e.update(pc=pc,sequence=len(events));r=e['registers'];r['M68K A7']=sp if stack is None else stack;r['M68K A0']=0x12646 if pc==0xf90a else 0x5132
        for b in e['ranges']:
            d=bytearray.fromhex(b['hex']);l=b['label']
            if l=='control':d[0x6e:0x70]=(value>>16).to_bytes(2,'big')
            if l=='stack':d[:]=ret.to_bytes(4,'big')
            if l=='remaining':d[:]=bytes(2)
            if l=='tally_countdown':d[:]=timer.to_bytes(2,'big')
            if l=='secondary_gate':d[:]=b'\0\1'
            if l=='secondary_remaining':d[:]=secondary.to_bytes(2,'big')
            if l=='mailbox' and mailbox:d[:]=b''.join(v.to_bytes(2,'big') for v in mailbox)
            b['hex']=d.hex()
        for (l,o,n),v in zip(RANGES,(value,threshold,0x10000,reward,scratch)):e['ranges'].append(dict(label=l,hex=v.to_bytes(n,'big').hex()))
        if pc==0xed6e6:r.update({'M68K D0':0xf25ea,'M68K D1':230,'M68K D2':0x20e4})
        if pc==0xfcb32:next(b for b in e['ranges'] if b['label']=='sound')['hex']='008c000600c00001'
        events.append(e)
    for pc in (0xf8f6,0xf8fc,0xf900,0xf904):event(pc,sp+4,0x5f3a)
    event(0x5132);event(0xa148,sp-4,0x513c);event(0xa15c,sp-4,0x513c);event(0x513c);event(0x53f2)
    if consume:
        event(0x541a);secondary=1;event(0x5424);event(0xae1a,sp-4,0x5428);event(0xadf4,sp-12,0xae20)
        value=0x20000;scratch=0x10000;event(0xae18,sp-12,0xae20);event(0xae20,sp-8,0x5a5a0002)
        event(0xaf28,sp-12,0xae36);event(0xed6e6,sp-32,0xaf44);mailbox=(230,0x20e4,0xa5ea,30);event(0xed714,sp-32,0xaf44)
        event(0xaf48,sp-12,0xae36);reward=9;event(0xaf5a,sp-12,0xae36);event(0xae4c,sp-12,0xae40)
        threshold=0x20000;event(0xae70,sp-12,0xae40);event(0xae2e,sp-4,0x5428);event(0x5428);event(0xfcb32,sp-4,0x544e)
        timer=3;event(0x5456)
    else:timer=65535;event(0x5418)
    for pc in (0xf906,0xf90a,0x12646,0xf90c,0xf936,0x5f3a):event(pc,sp if pc==0x12646 else sp+8 if pc==0x5f3a else sp+4,0xf90c if pc==0x12646 else 0x5f3a)
    original['events']=events;return original


class ScoreEvidenceTests(unittest.TestCase):
    def test_authored_consumption_and_countdown(self):
        for consume in (False,True):self.assertEqual(len(validate(fixture(consume),100,101)),1)

    def test_exact_stack_and_boundaries(self):
        for pc in (0x53f2,0x541a,0x5424,0xae1a,0xadf4,0xae18,0xae20,0xaf28,0xaf5a,0xae4c,0xae70,0xae2e,0x5428,0x5456):
            t=fixture();t['events']=[e for e in t['events'] if e['pc']!=pc]
            with self.subTest(pc=pc),self.assertRaises(ValueError):validate(t,100,101)
        for pc in (0xae1a,0xadf4,0xaf28,0xed6e6,0xae4c,0xae70):
            t=fixture();next(e for e in t['events'] if e['pc']==pc)['registers']['M68K A7']+=4
            with self.assertRaises(ValueError):validate(t,100,101)

    def test_uncontracted_effects_and_incomplete_trace(self):
        for pc,label in ((0xaf5a,'score_rewards'),(0xed714,'mailbox'),(0x5456,'tally_countdown'),(0x5f3a,'score_increment')):
            t=fixture();b=next(b for e in t['events'] if e['pc']==pc for b in e['ranges'] if b['label']==label);d=bytearray.fromhex(b['hex']);d[-1]^=1;b['hex']=d.hex()
            with self.assertRaises(ValueError):validate(t,100,101)
        t=fixture();b=next(b for e in t['events'] if e['pc']==0xf906 for b in e['ranges'] if b['label']=='control');b['hex']=b['hex'][:-4]
        with self.assertRaises(ValueError):validate(t,100,101)
        for k,v in (('overflow',True),('dropped',1),('error','bad')):
            t=fixture();t[k]=v
            with self.assertRaises(ValueError):validate(t,100,101)

    def test_old_contract_does_not_accept_score_edits(self):
        from genesis_dispatch_capture import validate_dispatch
        with self.assertRaises(ValueError):validate_dispatch(fixture(),100,101)

    def test_metadata_and_goldens(self):
        root=Path(__file__).resolve().parents[1];m=json.loads((root/'re/score_step.json').read_text())
        self.assertEqual(sum(r['end_exclusive']-r['start'] for r in m['regions'] if not r.get('previously_classified')),280)
        self.assertEqual(sum(r['instruction_count'] for r in m['regions']),72)
        rows=goldens();self.assertEqual(len(rows),20)
        self.assertEqual(decode(('\n'.join(' '.join(map(str,e)) for c,e in rows)+'\n').encode(),len(rows)),[e for c,e in rows])

if __name__=='__main__':unittest.main()
