"""ROM-free action evidence guards and independently authored continuation events."""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from actions_cases import case,goldens,presentation_goldens,scheduled_goldens,decode
from test_actor import actor_bytes
from genesis_actions_capture import validate_actions,action_case
from genesis_movie_actor_capture import validate_trace


def fixture(sample=False):
    before=case(handler=17,mode=135,first=31,begin=30,end=35,counter=1,reload=2,target=31,callback=10,down=1)
    advanced=case(handler=17,mode=135,first=30,begin=30,end=35,counter=2,reload=2,target=31,callback=10,down=1)
    idle=case(handler=7,mode=128,first=2,begin=30,end=35,counter=2,reload=2,target=31,callback=10,down=1)
    held=case(handler=18,mode=133,first=36,begin=36,end=41,counter=3,reload=3,target=40,callback=9,down=1)
    entries=[(0xf8fc,before),(0xa196,advanced),(0xa1be,idle),(0x9d4e,idle),(0x9d88,held),
             (0xf900,held),(0xf904,held),(0x9d88,held),(0xf906,held)]
    if sample:
        before=case(handler=16,mode=128,first=35,begin=30,end=35,target=34,counter=3,reload=3,callback=9,up=1,raw=0xbf)
        entries=[(pc,before) for pc in (0xf8fc,0xf900,0xf904,0x9c90,0xed6e6,0xed714,0xf906)]
    events=[]
    for i,(pc,state) in enumerate(entries):
        sp=0xfffff000 if pc in (0xf8fc,0xf900,0xf904,0xf906) else 0xffffeffc
        ret=0xf900 if i<5 and not sample else 0xf906
        cooldown,interval=65535,12;mailbox=bytes.fromhex('1111222233334444')
        if sample and pc in (0xed6e6,0xed714,0xf906):cooldown=2
        if sample and pc in (0xed714,0xf906):mailbox=bytes.fromhex('00c80f148000001e')
        if sample and pc==0xf906:interval=15
        if pc in (0xed6e6,0xed714):sp=0xffffefe8;ret=0x9ce8
        control=bytearray(112)
        control[20]=0xbf if sample else 0xfd;control[26 if sample else 27]=1
        shared=cooldown.to_bytes(2,'big')+interval.to_bytes(2,'big')+bytes(4)+bytes.fromhex('0013')
        blocks={'actor':actor_bytes(state),'control':control,'scratch':bytes.fromhex('0009000a'),
                'gate':bytes(2),'sound':bytes(8),'stack':ret.to_bytes(4,'big'),'action_globals':shared,'mailbox':mailbox}
        events.append({'kind':'entry','pc':pc,'frame':100,'sequence':i,
            'registers':{'M68K A5':0xffff0690,'M68K A6':0xffff1ab4,'M68K A7':sp,'M68K A0':0x9c90 if sample else 0x9d88,
                         'M68K D0':0xf0000,'M68K D1':200,'M68K D2':0xf14},
            'ranges':[{'label':k,'hex':v.hex()} for k,v in blocks.items()]})
    return {'schemaVersion':1,'boundary':'instruction-pre-execute','dropped':0,'overflow':False,'error':None,'events':events}


class ActionEvidenceTests(unittest.TestCase):
    def test_scope_excludes_unrelated_entries(self):
        meta=json.loads((ROOT/'re/actions_step.json').read_text());ranges=[]
        for name in (*meta['dependencies'],'actions_step'):
            ranges.extend((r['start'],r['end_exclusive']) for r in json.loads((ROOT/f're/{name}.json').read_text())['regions'] if r['execution_compared'])
        ranges.sort();self.assertTrue(all(a[1]<=b[0] for a,b in zip(ranges,ranges[1:])))
        self.assertEqual(sum(r['instruction_count'] for r in meta['regions']),81)
        self.assertEqual(sum(r['end_exclusive']-r['start'] for r in meta['regions']),412)
        self.assertFalse(any(a<=pc<b for a,b in ranges for pc in (0x9d28,0xed6f6)))

    def test_goldens_and_request_extent(self):
        rows=goldens()+presentation_goldens()+scheduled_goldens()
        data=('\n'.join(' '.join(map(str,e)) for _,e in rows)+'\n').encode()
        self.assertEqual(decode(data,len(rows)),[e for _,e in rows]);self.assertEqual(len(rows),18)
        with self.assertRaises(ValueError):decode(data+b'1\n',len(rows))
        with self.assertRaises(ValueError):decode(b'1 2\n',1)

    def test_callback_idle_and_second_handler_are_distinct(self):
        t=fixture();pair,=validate_actions(t,100,101)
        self.assertEqual([e['pc'] for e in pair['callback_handlers']],[0xa1be,0x9d88])
        self.assertEqual([e['pc'] for e in pair['handlers']],[0x9d88])
        with self.assertRaises(ValueError):validate_trace(t,100,101)
        for index in (0,1,2,5,6,7,8):
            damaged=copy.deepcopy(t);del damaged['events'][index]
            with self.subTest(index=index),self.assertRaises(ValueError):validate_actions(damaged,100,101)

    def test_callback_stack_and_scope_reject(self):
        for i in (1,2,7):
            t=fixture();t['events'][i]['registers']['M68K A7']+=4
            with self.subTest(index=i),self.assertRaises(ValueError):validate_actions(t,100,101)
        t=fixture();t['overflow']=True
        with self.assertRaises(ValueError):validate_actions(t,100,101)

    def test_sample_write_and_input_contract(self):
        t=fixture(True);pair,=validate_actions(t,100,101)
        self.assertEqual(len(pair['samples']),1)
        self.assertEqual(action_case(t['events'][0])[35:],(19,65535,12,0xbf,0x1111,0x2222,0x3333,0x4444))
        for pc in (0xed6e6,0xed714):
            damaged=copy.deepcopy(t);damaged['events']=[e for e in damaged['events'] if e['pc']!=pc]
            with self.assertRaises(ValueError):validate_actions(damaged,100,101)

    def test_sample_abi_stack_mailbox_and_global_mutations_reject(self):
        original=fixture(True)
        for field,value in (('M68K D0',0xf0002),('M68K D1',201),('M68K D2',0xf15),('M68K A7',0xffffefec)):
            t=copy.deepcopy(original);t['events'][4]['registers'][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):validate_actions(t,100,101)
        for index,label in ((5,'mailbox'),(5,'stack'),(5,'action_globals'),(6,'action_globals')):
            t=copy.deepcopy(original);b=next(b for b in t['events'][index]['ranges'] if b['label']==label)
            data=bytearray.fromhex(b['hex']);data[-1]^=1;b['hex']=data.hex()
            with self.subTest(label=label),self.assertRaises(ValueError):validate_actions(t,100,101)

if __name__=='__main__':unittest.main()
