"""Authored full-wrapper evidence, including distinct RTS handler and service calls."""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from test_actions import fixture as action_fixture
from genesis_dispatch_capture import validate_dispatch
from genesis_actor_capture import block
from dispatch_cases import decode,goldens


def fixture():
    t=action_fixture();events=t['events'];entry=copy.deepcopy(events[0]);entry['pc']=0xf8f6
    for e in [entry,*events]:
        e['ranges'].append({'label':'tracking_selector','hex':'0000'})
        a=next(b for b in e['ranges'] if b['label']=='actor');data=bytearray.fromhex(a['hex']);data[0x46:0x4a]=(0x12646).to_bytes(4,'big');a['hex']=data.hex()
    next(b for b in entry['ranges'] if b['label']=='stack')['hex']='00005f3a'
    tail=[]
    for pc in (0xf90a,0x12646,0xf90c,0xf928,0x5f3a):
        e=copy.deepcopy(events[-1]);e['pc']=pc;e['registers']['M68K A0']=0x12646
        e['registers']['M68K A7']=0xffffeffc if pc==0x12646 else 0xfffff004 if pc==0x5f3a else 0xfffff000
        next(b for b in e['ranges'] if b['label']=='stack')['hex']='0000f90c' if pc==0x12646 else '00005f3a'
        if pc in (0xf928,0x5f3a):
            c=next(b for b in e['ranges'] if b['label']=='control');d=bytearray.fromhex(c['hex']);d[0x42:0x46]=bytes.fromhex('00cc0073');c['hex']=d.hex()
        tail.append(e)
    t['events']=[entry,*events,*tail]
    for i,e in enumerate(t['events']):e['sequence']=i
    return t


class DispatchEvidenceTests(unittest.TestCase):
    def test_full_wrapper_and_distinct_service(self):
        pairs=validate_dispatch(fixture(),100,101)
        self.assertEqual(len(pairs),1);self.assertEqual(pairs[0]['service']['pc'],0x12646)
        self.assertEqual(pairs[0]['return']['pc'],0x5f3a)

    def test_missing_boundaries_and_stack_reject(self):
        for pc in (0xf8f6,0xf8fc,0xf900,0xf904,0xf906,0xf90a,0x12646,0xf90c,0xf928,0x5f3a):
            t=fixture();t['events']=[e for e in t['events'] if e['pc']!=pc]
            with self.subTest(pc=hex(pc)),self.assertRaises(ValueError):validate_dispatch(t,100,101)
        for pc in (0xf8f6,0xf90a,0x12646,0xf90c,0xf928,0x5f3a):
            t=fixture();next(e for e in t['events'] if e['pc']==pc)['registers']['M68K A7']+=4
            with self.subTest(pc=hex(pc)),self.assertRaises(ValueError):validate_dispatch(t,100,101)

    def test_selector_uncontracted_writes_and_overflow_reject(self):
        for pc,label,index in ((0xf90a,'actor',0x49),(0x12646,'control',0),(0xf90c,'scratch',0),
                               (0xf928,'tracking_selector',0),(0x5f3a,'control',0x42),(0x5f3a,'actor',2)):
            t=fixture();e=next(e for e in t['events'] if e['pc']==pc);b=next(b for b in e['ranges'] if b['label']==label)
            d=bytearray.fromhex(b['hex']);d[index]^=1;b['hex']=d.hex()
            with self.subTest(pc=hex(pc),label=label),self.assertRaises(ValueError):validate_dispatch(t,100,101)
        t=fixture();t['overflow']=True
        with self.assertRaises(ValueError):validate_dispatch(t,100,101)

    def test_new_ranges_and_goldens(self):
        meta=json.loads((ROOT/'re/dispatch_step.json').read_text())
        self.assertEqual(sum(r['instruction_count'] for r in meta['regions']),15)
        self.assertEqual(sum(r['end_exclusive']-r['start'] for r in meta['regions']),52)
        rows=goldens();data=('\n'.join(' '.join(map(str,e)) for _,e in rows)+'\n').encode()
        self.assertEqual(decode(data,len(rows)),[e for _,e in rows]);self.assertEqual(len(rows),9)
        with self.assertRaises(ValueError):decode(data+b'1\n',len(rows))
        ranges=[]
        for name in (*meta['dependencies'],'dispatch_step'):
            ranges.extend((r['start'],r['end_exclusive']) for r in json.loads((ROOT/f're/{name}.json').read_text())['regions'] if r['execution_compared'])
        ranges.sort();self.assertTrue(all(a[1]<=b[0] for a,b in zip(ranges,ranges[1:])))

if __name__=='__main__':unittest.main()
