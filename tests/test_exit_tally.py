"""Synthetic exact exit-tally returns, conditional writes and rejected evidence."""
import copy,json,unittest
from pathlib import Path
from test_tally import fixture as tally_fixture
from genesis_exit_tally_capture import validate,RANGES
from exit_tally_cases import goldens,decode
ROOT=Path(__file__).resolve().parents[1]


def fixture(wait=False,equal=True):
    t=tally_fixture();template=t['events'][0];events=[];sp=0xfffff000-4;handler=0x5188 if wait else 0x5132
    timer=120;marker=7;mode=0;saved=False
    def event(pc,*,stack=None,ret=0xf906):
        e=copy.deepcopy(template);e.update(pc=pc,frame=100,sequence=len(events));r=e['registers']
        r.update({'M68K A7':sp if stack is None else stack,'M68K A5':0xffff0690,'M68K A6':0xffff1ab4,'M68K A0':0x12646 if pc==0xf90a else handler})
        for b in e['ranges']:
            d=bytearray.fromhex(b['hex']);l=b['label']
            if l=='actor':d[22:26]=handler.to_bytes(4,'big')
            if l=='control':d[0x42:0x46]=bytes.fromhex('ff80ff80')
            if l=='stack':d[:]=ret.to_bytes(4,'big')
            if l=='remaining':d[:]=(5 if not wait else 0).to_bytes(2,'big')
            if l=='tally_countdown':d[:]=timer.to_bytes(2,'big')
            if l=='action_globals':d[8:10]=mode.to_bytes(2,'big')
            if l=='saved_position' and saved:d[:]=bytes.fromhex(next(b for b in e['ranges'] if b['label']=='requested_position')['hex'])
            b['hex']=d.hex()
        for (l,o),v in zip(RANGES,(0,0,marker,2,2 if equal else 3)):e['ranges'].append(dict(label=l,hex=v.to_bytes(2,'big').hex()))
        events.append(e)
    for pc in (0xf8f6,0xf8fc,0xf900,0xf904):event(pc,stack=sp+4,ret=0x5f3a)
    event(handler);ret=0x5192 if wait else 0x513c
    event(0xa148,stack=sp-4,ret=ret);event(0xa15c,stack=sp-4,ret=ret);event(ret)
    if wait:
        event(0x519c);saved=True;event(0x51ac)
        if equal:event(0x51ba);marker=0
        event(0x51be);mode=1;event(0x51c6)
    else:
        event(0x537c,stack=sp-4,ret=0x5146);timer=119;event(0x53a2,stack=sp-4,ret=0x5146);event(0x5146);event(0x4f8c)
    for pc in (0xf906,0xf90a,0x12646,0xf90c,0xf936,0x5f3a):event(pc,stack=sp if pc==0x12646 else sp+8 if pc==0x5f3a else sp+4,ret=0xf90c if pc==0x12646 else 0x5f3a)
    t['events']=events;return t


class ExitTallyEvidenceTests(unittest.TestCase):
    def test_nested_counter_and_conditional_completion(self):
        for wait,equal in ((False,True),(True,True),(True,False)):
            pairs=validate(fixture(wait,equal),100,101);self.assertEqual(len(pairs),1)

    def test_missing_boundaries_reject(self):
        for wait,pcs in ((False,(0x5132,0x513c,0x537c,0x53a2,0x5146,0x4f8c)),(True,(0x5188,0x5192,0x519c,0x51ac,0x51ba,0x51be,0x51c6))):
            for pc in pcs:
                t=fixture(wait);t['events']=[e for e in t['events'] if e['pc']!=pc]
                with self.subTest(pc=pc),self.assertRaises(ValueError):validate(t,100,101)

    def test_nested_stack_and_uncontracted_writes_reject(self):
        for wait,pc in ((False,0x537c),(False,0x53a2),(False,0x5146),(True,0x51c6)):
            t=fixture(wait);next(e for e in t['events'] if e['pc']==pc)['registers']['M68K A7']+=4
            with self.assertRaises(ValueError):validate(t,100,101)
        for wait,pc,label in ((True,0x51be,'exit_marker'),(True,0x51ac,'saved_position'),(False,0x5146,'remaining'),(False,0x5f3a,'credit')):
            t=fixture(wait);e=next(e for e in t['events'] if e['pc']==pc);b=next(b for b in e['ranges'] if b['label']==label);data=bytearray.fromhex(b['hex']);data[0]^=1;b['hex']=data.hex()
            with self.assertRaises(ValueError):validate(t,100,101)

    def test_overflow_and_secondary_score_reject(self):
        for k,v in (('overflow',True),('dropped',1),('error','bad')):
            t=fixture();t[k]=v
            with self.assertRaises(ValueError):validate(t,100,101)
        t=fixture();e=copy.deepcopy(t['events'][6]);e['pc']=0x53f2;t['events'].insert(7,e)
        for i,e in enumerate(t['events']):e['sequence']=i
        with self.assertRaises(ValueError):validate(t,100,101)

    def test_static_scope_and_goldens(self):
        m=json.loads((ROOT/'re/exit_tally_step.json').read_text());self.assertEqual(sum(r['end_exclusive']-r['start'] for r in m['regions']),150)
        self.assertEqual(sum(r['instruction_count'] for r in m['regions'] if r['execution_compared']),31);self.assertIn(0x53f2,m['rejected_boundaries'])
        rows=goldens();self.assertEqual(len(rows),22);self.assertEqual(decode(('\n'.join(' '.join(map(str,e)) for c,e in rows)+'\n').encode(),len(rows)),[e for c,e in rows])
        regions=[]
        for name in (*m['dependencies'],'exit_tally_step'):
            regions.extend((r['start'],r['end_exclusive']) for r in json.loads((ROOT/f're/{name}.json').read_text())['regions'] if r['execution_compared'])
        regions.sort();self.assertTrue(all(a[1]<=b[0] for a,b in zip(regions,regions[1:])))

if __name__=='__main__':unittest.main()
