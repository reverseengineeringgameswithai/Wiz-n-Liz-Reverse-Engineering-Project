"""ROM-free checks of scheduler metadata and movie evidence boundaries."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from presentation_cases import case,goldens
from test_actor import actor_bytes
from genesis_movie_actor_capture import validate_trace,compare_window
from actor_cases import expected


def trace_fixture():
    before=case(handler=11,mode=0x87,first=2,begin=0,end=5,target=2,callback=3,flags=0x800)
    after=case(handler=4,mode=0x81,first=2,begin=0,end=5,target=2,callback=3,flags=0,counter=4,reload=4)
    events=[]
    for i,pc in enumerate((0xf8fc,0xa50e,0xf900,0xf904,0xa546,0xf906)):
        state=before if i<2 else after;sp=0xfffff000-(4 if i in (1,4) else 0)
        blocks={'actor':actor_bytes(state),'control':bytes(112),'scratch':bytes.fromhex('0009000a'),
                'gate':bytes(2),'sound':bytes(8),'stack':(0xf900 if i==1 else 0xf906).to_bytes(4,'big')}
        events.append({'kind':'entry','pc':pc,'sequence':i,'frame':100,
            'registers':{'M68K A5':0xffff0690,'M68K A6':0xffff1ab4,'M68K A7':sp,'M68K A0':0xa546},
            'ranges':[{'label':l,'hex':v.hex()} for l,v in blocks.items()]})
    return {'schemaVersion':1,'boundary':'instruction-pre-execute','dropped':0,'overflow':False,'error':None,'events':events},expected(after)


class PresentationEvidenceTests(unittest.TestCase):
    def test_scope_and_callback_selectors(self):
        meta=json.loads((ROOT/'re/presentation_step.json').read_text());ranges=[]
        for name in ('terrain_query','movement_step','airborne_update','actor_update','presentation_step'):
            ranges.extend((r['start'],r['end_exclusive']) for r in json.loads((ROOT/f're/{name}.json').read_text())['regions'] if r['execution_compared'])
        ranges.sort();self.assertTrue(all(a[1]<=b[0] for a,b in zip(ranges,ranges[1:])))
        self.assertEqual(sum(r['instruction_count'] for r in meta['regions']),90)
        self.assertEqual(meta['stop_boundaries'],[0xf906,0xf90c])
        self.assertEqual(meta['indirect_transfers'][0]['targets'],[0xcafe,0xa2e8,0xa380,0xa50e,0xa654,0xa774,0xa93a])
        self.assertEqual(len(goldens()),24)

    def test_callback_tail_and_selected_handler(self):
        trace,_=trace_fixture();pairs=validate_trace(trace,100,101)
        self.assertEqual(len(pairs),1);self.assertEqual(pairs[0]['callbacks'][0]['pc'],0xa50e)
        self.assertEqual(pairs[0]['handlers'][0]['pc'],0xa546)

    def test_missing_or_unbalanced_phases_rejected(self):
        original,_=trace_fixture()
        for i in range(len(original['events'])):
            trace=copy.deepcopy(original);del trace['events'][i]
            with self.subTest(missing=i),self.assertRaises(ValueError):validate_trace(trace,100,101)
        for i,field,value in ((1,'M68K A7',0xfffff000),(3,'M68K A0',0xa408),(5,'M68K A7',0xffffeffc)):
            trace=copy.deepcopy(original);trace['events'][i]['registers'][field]=value
            with self.assertRaises(ValueError):validate_trace(trace,100,101)

    def test_dropped_error_frame_and_order_rejected(self):
        original,_=trace_fixture()
        for field,value in (('dropped',1),('dropped',True),('overflow',True),('error','hook error'),('boundary','frame-end')):
            trace=copy.deepcopy(original);trace[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):validate_trace(trace,100,101)
        for mutate in (lambda t:t['events'][1].__setitem__('sequence',0),lambda t:t['events'][-1].__setitem__('frame',101)):
            trace=copy.deepcopy(original);mutate(trace)
            with self.assertRaises(ValueError):validate_trace(trace,100,101)

    def test_external_actor_change_is_not_silently_reseeded(self):
        trace,_=trace_fixture();second=copy.deepcopy(trace['events'])
        for e in second:e['sequence']+=6;e['frame']=101
        trace['events'].extend(second)
        with self.assertRaisesRegex(ValueError,'external actor change'):validate_trace(trace,100,102)

    def test_compare_modes_and_divergence(self):
        trace,out=trace_fixture();output=(' '.join(map(str,out))+'\n').encode()
        with tempfile.TemporaryDirectory() as d,patch('genesis_movie_actor_capture.subprocess.run') as run:
            run.return_value.returncode=0;run.return_value.stdout=output;run.return_value.stderr=b''
            result=compare_window(trace,Path(d),Path('authored-native'),b'scene',b'bank',100,101)
            self.assertEqual(result['calls'],1)
            self.assertEqual([c.args[0][-1] for c in run.call_args_list],['--presentation','--sequence'])
            wrong=list(out);wrong[8]=3;run.return_value.stdout=(' '.join(map(str,wrong))+'\n').encode()
            with self.assertRaisesRegex(ValueError,'divergence'):compare_window(trace,Path(d),Path('authored-native'),b'scene',b'bank',100,101)

if __name__=='__main__':unittest.main()
