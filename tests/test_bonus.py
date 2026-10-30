"""Synthetic bonus call/return contracts, ordered writes and rejection evidence."""
import copy,json,unittest
from pathlib import Path
from test_tally import fixture as tally_fixture
from genesis_bonus_capture import validate,RANGES,edits
from bonus_cases import ASSIGNED,CHOICES,goldens,decode
ROOT=Path(__file__).resolve().parents[1]


def fixture(exhausted=False):
    t=tally_fixture();template=t['events'][0];events=[];sp=0xfffff000-4
    assigned=list((*CHOICES[:5],*ASSIGNED[5:]) if exhausted else ASSIGNED);cursor=1;gate=0;mail=False;complete=False
    def event(pc,*,stack=None,ret=0xf906,**registers):
        e=copy.deepcopy(template);e.update(pc=pc,frame=100,sequence=len(events));r=e['registers']
        r.update({'M68K A7':sp if stack is None else stack,'M68K A5':0xffff0690,'M68K A6':0xffff1ab4,'M68K A0':0x12646 if pc==0xf90a else 0x51c8,'M68K SR':0x2004});r.update(registers)
        for b in e['ranges']:
            d=bytearray.fromhex(b['hex']);l=b['label']
            if l=='actor':d[22:26]=(0x51c8).to_bytes(4,'big')
            if l=='control':d[0x14]=0x10;d[0x21]=255;d[0x42:0x46]=bytes.fromhex('ff80ff80')
            if l=='stack':d[:]=ret.to_bytes(4,'big')
            if l=='special_gate':d[:]=gate.to_bytes(2,'big')
            if l=='action_globals' and complete:d[8:10]=b'\0\3'
            if l=='mailbox' and mail:d[:]=bytes.fromhex('00c80f148000001e')
            b['hex']=d.hex()
        for l,o,n in RANGES:
            data=assigned if l=='bonus_assigned' else CHOICES if l=='bonus_choices' else (6,cursor)
            e['ranges'].append(dict(label=l,hex=b''.join(v.to_bytes(2,'big') for v in data).hex()))
        events.append(e)
    for pc in (0xf8f6,0xf8fc,0xf900,0xf904):event(pc,stack=sp+4,ret=0x5f3a)
    event(0x51c8);event(0x5222);event(0xa148,stack=sp-4,ret=0x522c);event(0xa15c,stack=sp-4,ret=0x522c);event(0x522c);event(0x5266)
    event(0xed6e6,stack=sp-20,ret=0x5282,**{'M68K D0':0xf0000,'M68K D1':200,'M68K D2':0xf14})
    mail=True;event(0xed714,stack=sp-20,ret=0x5282);event(0x5282,stack=sp-16)
    gate=65535;event(0x528e)
    for j in ([None] if exhausted else [4,3,2,1,0]):
        event(0x5290);event(0x451a,stack=sp-4,ret=0x5294)
        reads=6 if exhausted else 1
        for i in range(reads):event(0x451e,stack=sp-4,ret=0x5294,**{'M68K A0':0xffff0802+2*i})
        regs={'M68K A0':0xffff0802+2*reads,'M68K SR':0x2008 if exhausted else 0x2004}
        event(0x4524,stack=sp-4,ret=0x5294,**regs);event(0x5294,**regs)
        if j is None:break
        event(0x4770,stack=sp-6,ret=0x529e,**{'M68K D2':0});event(0x477c,stack=sp-6,ret=0x529e)
        cursor+=1;regs={'M68K A1':0xffff0802+2*j,'M68K D3':CHOICES[j]}
        event(0x47b0,stack=sp-6,ret=0x529e,**regs);event(0x529e,stack=sp-2,**regs);event(0x52a0,**regs)
        assigned[j]=CHOICES[j];event(0x52a2)
    event(0x52a6);complete=True;event(0x52ae)
    for pc in (0xf906,0xf90a,0x12646,0xf90c,0xf936,0x5f3a):
        event(pc,stack=sp if pc==0x12646 else sp+8 if pc==0x5f3a else sp+4,ret=0xf90c if pc==0x12646 else 0x5f3a)
    t['events']=events;return t


class BonusEvidenceTests(unittest.TestCase):
    def test_order_and_early_exhaustion(self):
        p=validate(fixture(),100,101);self.assertEqual(p['assignments'],((4,15),(3,14),(2,13),(1,12),(0,11)));self.assertEqual(p['probes'],10)
        p=validate(fixture(True),100,101);self.assertEqual(p['assignments'],());self.assertEqual(p['probes'],6)

    def test_missing_boundaries_and_saved_word_stack_reject(self):
        for pc in (0x5266,0xed6e6,0xed714,0x5282,0x528e,0x451a,0x451e,0x4524,0x5294,0x4770,0x47b0,0x529e,0x52a0,0x52a2,0x52a6,0x52ae):
            t=fixture();t['events']=[e for e in t['events'] if e['pc']!=pc]
            with self.subTest(pc=pc),self.assertRaises(ValueError):validate(t,100,101)
        for pc in (0x451a,0x4524,0x4770,0x47b0,0x529e,0x52a0,0xed6e6,0x5282):
            t=fixture();next(e for e in t['events'] if e['pc']==pc)['registers']['M68K A7']+=2
            with self.subTest(pc=pc),self.assertRaises(ValueError):validate(t,100,101)

    def test_wrong_flags_extent_and_source_reject(self):
        for pc,reg in ((0x4524,'M68K SR'),(0x451e,'M68K A0'),(0x4770,'M68K D2'),(0x52a0,'M68K D3'),(0x52a0,'M68K A1')):
            t=fixture();next(e for e in t['events'] if e['pc']==pc)['registers'][reg]^=4 if reg=='M68K SR' else 1
            with self.subTest(pc=pc),self.assertRaises(ValueError):validate(t,100,101)
        for pc,label in ((0x528e,'special_gate'),(0x47b0,'bonus_choices'),(0x52a2,'bonus_assigned'),(0x52ae,'remaining')):
            t=fixture();e=next(e for e in t['events'] if e['pc']==pc);b=next(b for b in e['ranges'] if b['label']==label);data=bytearray.fromhex(b['hex']);data[0]^=1;b['hex']=data.hex()
            with self.subTest(pc=pc),self.assertRaises(ValueError):validate(t,100,101)

    def test_overflow_and_edit_start_reject(self):
        for k,v in (('overflow',True),('dropped',1),('error','bad')):
            t=fixture();t[k]=v
            with self.assertRaises(ValueError):validate(t,100,101)
        ram=bytearray(65536);ram[0x82e:0x832]=bytes.fromhex('00060001');ram[0x80c:0x80e]=b'\xff\xff'
        self.assertEqual([len(edits(ram,k)['writes']) for k in ('five','partial-reset','exhausted')],[3,5,4])
        ram[0x82f]=0
        with self.assertRaises(ValueError):edits(ram,'five')

    def test_static_scope_and_authored_rows(self):
        m=json.loads((ROOT/'re/bonus_step.json').read_text());self.assertEqual(sum(r['instruction_count'] for r in m['regions']),43);self.assertEqual(sum(r['end_exclusive']-r['start'] for r in m['regions']),150)
        self.assertIn(0x47ba,m['rejected_boundaries']);self.assertNotIn(0x5266,m['rejected_boundaries'])
        rows=goldens();self.assertEqual(len(rows),16);self.assertEqual(decode(('\n'.join(' '.join(map(str,e)) for c,e in rows)+'\n').encode(),len(rows)),[e for c,e in rows])
        ranges=[]
        for name in (*m['dependencies'],'bonus_step'):
            ranges.extend((r['start'],r['end_exclusive']) for r in json.loads((ROOT/f're/{name}.json').read_text())['regions'] if r['execution_compared'])
        ranges.sort();self.assertTrue(all(a[1]<=b[0] for a,b in zip(ranges,ranges[1:])))

if __name__=='__main__':unittest.main()
