"""Synthetic trace contracts for the immediate tally branch and original returns."""
import copy
import json
from pathlib import Path
import unittest
from test_coasting import fixture as coast_fixture
from genesis_tally_capture import validate,TALLY_RANGES
from tally_cases import goldens,decode
ROOT=Path(__file__).resolve().parents[1]


def fixture():
    t=coast_fixture();events=[e for e in t['events'] if e['frame']==101];out=[]
    def setblock(e,label,data):next(b for b in e['ranges'] if b['label']==label)['hex']=data.hex()
    for e in events:
        e['frame']=100;e['registers']['M68K A0']=0x12646 if e['pc']==0xf90a else 0x51c8
        a=bytearray.fromhex(next(b for b in e['ranges'] if b['label']=='actor')['hex']);a[22:26]=(0x51c8).to_bytes(4,'big');setblock(e,'actor',a)
        for l,o in TALLY_RANGES:e['ranges'].append(dict(label=l,hex='0078' if l=='tally_countdown' else '0000'))
        if e['pc']==0x632a:e['pc']=0x51c8
        if e['pc'] in (0xa148,0xa15c):
            e['registers']['M68K A7']-=4;setblock(e,'stack',(0x522c).to_bytes(4,'big'))
        out.append(e)
        if e['pc']==0x51c8:
            extra=copy.deepcopy(e);extra['pc']=0x5222;out.append(extra)
        if e['pc']==0xa15c:
            for pc in (0x522c,0x4f8c):
                extra=copy.deepcopy(e);extra['pc']=pc;extra['registers']['M68K A7']+=4;setblock(extra,'stack',(0xf906).to_bytes(4,'big'));out.append(extra)
    for i,e in enumerate(out):e['sequence']=i
    t['events']=out;return t


class TallyEvidenceTests(unittest.TestCase):
    def test_same_call_branch_and_actual_return(self):
        p,=validate(fixture(),100,101)
        self.assertEqual([e['pc'] for e in p['handlers']],[0x51c8,0x5222]);self.assertEqual(p['return']['pc'],0x5f3a)

    def test_missing_boundaries_and_stack_reject(self):
        for pc in (0xf8f6,0x51c8,0x5222,0xa148,0xa15c,0x522c,0x4f8c,0xf906,0xf936,0x5f3a):
            t=fixture();t['events']=[e for e in t['events'] if e['pc']!=pc]
            with self.subTest(pc=pc),self.assertRaises(ValueError):validate(t,100,101)
        for pc in (0x51c8,0x5222,0xa148,0xa15c,0x522c,0x4f8c):
            t=fixture();next(e for e in t['events'] if e['pc']==pc)['registers']['M68K A7']+=4
            with self.subTest(pc=pc),self.assertRaises(ValueError):validate(t,100,101)

    def test_changes_outside_handler_and_unknown_mode_reject(self):
        for pc,label in ((0x5222,'credit'),(0x5f3a,'remaining'),(0x4f8c,'transition'),(0xf906,'action_globals')):
            t=fixture();e=next(e for e in t['events'] if e['pc']==pc);b=next(b for b in e['ranges'] if b['label']==label)
            d=bytearray.fromhex(b['hex']);d[-1]=4;b['hex']=d.hex()
            with self.subTest(pc=pc),self.assertRaises(ValueError):validate(t,100,101)

    def test_unsupported_paths_and_overflow_reject(self):
        for pc in (0x51d0,0x5266):
            t=fixture();e=copy.deepcopy(t['events'][5]);e['pc']=pc;t['events'].insert(6,e)
            for i,e in enumerate(t['events']):e['sequence']=i
            with self.assertRaises(ValueError):validate(t,100,101)
        t=fixture();t['overflow']=True
        with self.assertRaises(ValueError):validate(t,100,101)

    def test_scope_and_authored_outputs(self):
        m=json.loads((ROOT/'re/tally_step.json').read_text());self.assertEqual(sum(r['instruction_count'] for r in m['regions']),48)
        self.assertEqual(sum(r['end_exclusive']-r['start'] for r in m['regions']),210)
        self.assertTrue({0x51d0,0x5266}<=set(m['rejected_boundaries']))
        rows=goldens();self.assertEqual(len(rows),19)
        self.assertEqual(decode(('\n'.join(' '.join(map(str,e)) for c,e in rows)+'\n').encode(),len(rows)),[e for c,e in rows])
        ranges=[]
        for name in (*m['dependencies'],'tally_step'):
            ranges.extend((r['start'],r['end_exclusive']) for r in json.loads((ROOT/f're/{name}.json').read_text())['regions'] if r['execution_compared'])
        ranges.sort();self.assertTrue(all(a[1]<=b[0] for a,b in zip(ranges,ranges[1:])))

if __name__=='__main__':unittest.main()
