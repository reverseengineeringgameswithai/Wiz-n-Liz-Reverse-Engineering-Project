"""Synthetic evidence rejection tests; no proprietary trace fixture is checked in."""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from genesis_transition_capture import validate,transition_fields
from transition_cases import decode,goldens,timer_goldens


def fixture():
    actor=bytearray(78);actor[0]=128;actor[2:6]=bytes.fromhex('00c8006d')
    actor[0x16:0x1a]=(0x710e).to_bytes(4,'big');actor[0x1a:0x1e]=(0xcafe).to_bytes(4,'big')
    actor[0x46:0x4a]=(0x12646).to_bytes(4,'big');actor[0x4a:]=(0xffff0690).to_bytes(4,'big')
    blocks={'actor':actor,'control':bytearray(112),'scratch':bytearray(4),'gate':bytearray(2),'sound':bytearray(8),
            'action_globals':bytearray(10),'mailbox':bytearray(8),'tracking_selector':bytearray(2),
            'transition':bytearray(20),'palette_flags':bytearray(4),'requested_position':bytearray(4),'saved_position':bytearray(4)}
    events=[]
    pcs=(0x1345a,0x134b0,0xebf2,0xf8f6,0xf8fc,0xf900,0xf904,0x710e,0xa148,0x7118,0x13208,0x1324c,0xf906,0xf90a,0x12646,0xf90c,0xf928,0x6986)
    for pc in pcs:
        sp=0xfffff000;ret=0x6986
        if pc in (0x1345a,0x134b0):ret=0xebf2
        elif pc==0xebf2:sp+=4
        elif pc==0xa148:sp-=8;ret=0x7118
        elif pc in (0x710e,0x7118,0x13208,0x1324c):sp-=4;ret=0xf906
        elif pc==0x12646:sp-=4;ret=0xf90c
        elif pc==0x6986:sp+=4
        if pc==0x13208:blocks['actor'][0x16:0x1a]=(0x7126).to_bytes(4,'big')
        if pc==0x1324c:blocks['transition'][:]=bytes.fromhex('000100010001000e0001356a0001356a000135aa')
        if pc==0xf928:blocks['control'][0x42:0x46]=bytes.fromhex('00cc0073')
        events.append({'pc':pc,'frame':100,'sequence':len(events),'kind':'entry',
            'registers':{'M68K A5':0xffff0690,'M68K A6':0xffff1ab4,'M68K A7':sp,'M68K A0':0x12646 if pc==0xf90a else 0x710e},
            'ranges':[{'label':l,'hex':bytes(d).hex()} for l,d in blocks.items()]+[{'label':'stack','hex':ret.to_bytes(4,'big').hex()}]})
    return {'schemaVersion':1,'boundary':'instruction-pre-execute','overflow':False,'dropped':0,'error':None,'events':events}


class TransitionEvidenceTests(unittest.TestCase):
    def test_tail_call_and_separate_timer(self):
        pairs,timers=validate(fixture(),100,101)
        self.assertEqual(len(pairs),1);self.assertEqual(len(timers),1)
        self.assertEqual(pairs[0]['handlers'][0]['pc'],0x710e)
        self.assertEqual(transition_fields(pairs[0]['return'])[:7],(1,1,1,14,1,1,2))

    def test_missing_boundaries_and_return_stack_reject(self):
        for pc in (0x1345a,0x134b0,0xebf2,0xf8f6,0xf900,0xf904,0x710e,0xa148,0x7118,0x13208,0x1324c,0xf906,0x12646,0xf928,0x6986):
            t=fixture();t['events']=[e for e in t['events'] if e['pc']!=pc]
            with self.subTest(pc=hex(pc)),self.assertRaises(ValueError):validate(t,100,101)
        for pc in (0x1345a,0x134b0,0xebf2,0xf8f6,0xa148,0x7118,0x13208,0x1324c,0xf90a,0x12646,0xf90c,0xf928,0x6986):
            t=fixture();next(e for e in t['events'] if e['pc']==pc)['registers']['M68K A7']+=4
            with self.subTest(pc=hex(pc)),self.assertRaises(ValueError):validate(t,100,101)

    def test_uncontracted_effects_and_overflow_reject(self):
        for pc,label in ((0xebf2,'actor'),(0xebf2,'palette_flags'),(0xf8f6,'transition'),(0x12646,'transition'),(0x6986,'control')):
            t=fixture();e=next(e for e in t['events'] if e['pc']==pc);b=next(b for b in e['ranges'] if b['label']==label)
            d=bytearray.fromhex(b['hex']);d[-1]^=1;b['hex']=d.hex()
            with self.subTest(pc=hex(pc),label=label),self.assertRaises(ValueError):validate(t,100,101)
        t=fixture();events=t['events'];a=next(i for i,e in enumerate(events) if e['pc']==0xa148);b=a+1
        events[a],events[b]=events[b],events[a]
        for i,e in enumerate(events):e['sequence']=i
        with self.assertRaises(ValueError):validate(t,100,101)
        for key,value in (('overflow',True),('dropped',1),('error','capture failed')):
            t=fixture();t[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate(t,100,101)

    def test_retained_curves_cannot_silently_change(self):
        a=fixture()['events'][0];b=copy.deepcopy(a)
        data=next(r for r in b['ranges'] if r['label']=='transition');data['hex']='0000000000000000000000010000000000000000'
        with self.assertRaises(ValueError):transition_fields(b,a)

    def test_ranges_and_independent_goldens(self):
        meta=json.loads((ROOT/'re/transition_step.json').read_text());self.assertEqual(sum(r['instruction_count'] for r in meta['regions']),68)
        self.assertEqual(sum(r['end_exclusive']-r['start'] for r in meta['regions']),342)
        rows=goldens()+timer_goldens();data=('\n'.join(' '.join(map(str,e)) for _,e in rows)+'\n').encode()
        self.assertEqual(decode(data,len(rows)),[e for _,e in rows]);self.assertEqual(len(rows),16)
        with self.assertRaises(ValueError):decode(data+b'1\n',len(rows))
        ranges=[]
        for name in (*meta['dependencies'],'transition_step'):
            ranges.extend((r['start'],r['end_exclusive']) for r in json.loads((ROOT/f're/{name}.json').read_text())['regions'] if r['execution_compared'])
        ranges.sort();self.assertTrue(all(a[1]<=b[0] for a,b in zip(ranges,ranges[1:])))

if __name__=='__main__':unittest.main()
