"""Authored evidence contract checks; no ROM, emulator or native binary required."""
import copy
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from actor_cases import case,goldens,decode_results,HANDLERS,CALLBACKS
from genesis_actor_capture import compare_trace,terrain_fixture


def actor_bytes(fields):
    data=bytearray(78)
    def put(offset,value,size=2):data[offset:offset+size]=value.to_bytes(size,'big')
    put(0,fields[7],1);put(0x16,HANDLERS[fields[0]],4)
    for i,offset in enumerate((2,4,0x22,0x26,0x2a,0x12)):put(offset,fields[i+1])
    for i,offset in enumerate((6,8,10)):put(offset,fields[i+8])
    put(12,fields[11],1);put(13,fields[12],1);put(14,fields[13]);put(16,fields[14]);put(0x1a,CALLBACKS[fields[15]],4)
    return bytes(data)


def trace_fixture():
    c,out=goldens()[0];control=bytearray(112)
    for i,offset in enumerate((0x5a,0x5c,0x66,0x60,0x6a,0x6c,0x5e,0x62,0x64)):
        control[offset:offset+2]=c[i+16].to_bytes(2,'big')
    events=[]
    for i,pc in enumerate((0xf904,0xa1be,0xf906)):
        values=out if i==2 else c
        blocks={'actor':actor_bytes(values),'control':control,'scratch':struct.pack('>2H',*(out[16:18] if i==2 else c[32:34])),
                'gate':bytes(2),'stack':bytes.fromhex('0000f906'),'sound':bytes(8)}
        events.append({'kind':'entry','pc':pc,'frame':100,'sequence':i,
                       'registers':{'M68K A5':0xffff0690,'M68K A6':0xffff1ab4,'M68K A7':0xfffff000-(4 if i==1 else 0)},
                       'ranges':[{'label':label,'hex':data.hex()} for label,data in blocks.items()]})
    return {'schemaVersion':1,'boundary':'instruction-pre-execute','dropped':0,'overflow':False,'error':None,'events':events},out


class ActorEvidenceTests(unittest.TestCase):
    def test_sound_output_shape_and_word_transport(self):
        c,out=next(row for row in goldens() if row[0][25])
        self.assertTrue(all(type(v) is int for v in c))
        encoded=(' '.join(map(str,out))+'\n').encode()
        self.assertEqual(decode_results(encoded,1),[out])
        for payload in (b'',b'1 2\n',encoded+b'1\n'):
            with self.assertRaises(ValueError):decode_results(payload,1)
        self.assertEqual(case(left=True)[29],1)

    def test_actor_scope_disjoint_from_previous_executable_ranges(self):
        meta=json.loads((ROOT/'re/actor_update.json').read_text())
        previous=[]
        for name in ('terrain_query','movement_step','airborne_update'):
            previous.extend(r for r in json.loads((ROOT/f're/{name}.json').read_text())['regions'] if r['execution_compared'])
        ranges=sorted((r['start'],r['end_exclusive']) for r in meta['regions']+previous)
        self.assertTrue(all(a[1]<=b[0] for a,b in zip(ranges,ranges[1:])))
        self.assertEqual(meta['rejected_boundaries'],[0x9c56,0x9d4e,0xa7a8,0xa96e,0xfcb42])
        self.assertEqual(sum(r['instruction_count'] for r in meta['regions']),315)

    def compare(self,trace,out):
        with tempfile.TemporaryDirectory() as temp:
            output=(' '.join(map(str,out))+'\n').encode()
            with patch('genesis_actor_capture.subprocess.run') as run:
                run.return_value.returncode=0;run.return_value.stdout=output;run.return_value.stderr=b''
                return compare_trace(trace,Path(temp),Path('authored-native'),b'scene',b'bank')

    def test_explicit_dispatcher_pair(self):
        trace,out=trace_fixture();r=self.compare(trace,out)
        self.assertEqual(r['calls'],1);self.assertEqual(r['pairs'][0]['handlers'],['0xa1be'])

    def test_overflow_hook_error_and_missing_boundary_rejected(self):
        original,out=trace_fixture()
        for key,value in (('dropped',1),('overflow',True),('error','hook failed'),('boundary','frame-end')):
            trace=copy.deepcopy(original);trace[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.compare(trace,out)
        for events in (original['events'][:-1],original['events'][1:],original['events'][::2]):
            trace=copy.deepcopy(original);trace['events']=events
            with self.assertRaises(ValueError):self.compare(trace,out)

    def test_stack_order_and_unmodeled_writes_rejected(self):
        original,out=trace_fixture()
        mutations=[lambda t:t['events'][2]['registers'].__setitem__('M68K A7',0xffffeffc),
                   lambda t:t['events'][1].__setitem__('sequence',0),
                   lambda t:t['events'][1].__setitem__('pc',0xa246)]
        for mutate in mutations:
            trace=copy.deepcopy(original);mutate(trace)
            with self.assertRaises(ValueError):self.compare(trace,out)
        trace=copy.deepcopy(original)
        actor=next(b for b in trace['events'][2]['ranges'] if b['label']=='actor')
        data=bytearray.fromhex(actor['hex']);data[0x4a]=1;actor['hex']=data.hex()
        with self.assertRaises(ValueError):self.compare(trace,out)

    def test_live_terrain_normalization_and_bounds(self):
        ram=bytearray(65536)
        def put(offset,v,size=2):ram[offset:offset+size]=v.to_bytes(size,'big')
        put(0x140e,257);put(0x4452,0xffff4d02,4);put(0x444e,0xffff8000-257*8,4)
        put(0x13a4,256);put(0x13ae,1023)
        ram[0x4d02:0x6d02]=struct.pack('>4096H',*([0x8901]*4096));ram[0x8000:0x8008]=bytes(range(8))
        scene,bank,meta=terrain_fixture(ram)
        self.assertEqual(meta['records'],1);self.assertEqual(scene[52:54],bytes.fromhex('8800'));self.assertEqual(bank[-8:],bytes(range(8)))
        put(0x13a4,128)
        with self.assertRaises(ValueError):terrain_fixture(ram)
        put(0x13a4,256);put(0x4452,0xfff000,4)
        with self.assertRaises(ValueError):terrain_fixture(ram)

if __name__=='__main__':unittest.main()
