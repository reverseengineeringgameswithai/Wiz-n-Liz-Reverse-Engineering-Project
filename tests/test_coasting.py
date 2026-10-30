"""Authored initializer/tail evidence with missing-boundary and mutation rejection."""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from test_transition import fixture as transition_fixture
from genesis_coasting_capture import validate
from coasting_cases import goldens,entry_goldens,decode


def fixture():
    template=transition_fixture()['events'][0]
    def event(pc,frame,sp,return_pc,initialized=False,tracked=False):
        e=copy.deepcopy(template);e.update(pc=pc,frame=frame,sequence=len(events))
        e['registers'].update({'M68K A7':sp,'M68K A6':0xffff2fba if frame==100 else 0xffff1ab4,
                              'M68K A4':0xffff1ab4,'M68K A0':0x12646 if pc==0xf90a else 0x632a})
        for b in e['ranges']:
            d=bytearray.fromhex(b['hex'])
            if b['label']=='actor':
                d[0]=128 if initialized else 0;d[6:8]=(541 if initialized else 0).to_bytes(2,'big')
                d[22:26]=(0x632a if initialized else 0xa1be).to_bytes(4,'big')
            elif b['label']=='control':
                d[:4]=(0xffff1ab4).to_bytes(4,'big')
                if tracked:d[0x42:0x46]=bytes.fromhex('ff80ff80')
            elif b['label']=='tracking_selector':d[:]=(65535 if initialized else 0).to_bytes(2,'big')
            elif b['label']=='stack':d[:]=return_pc.to_bytes(4,'big')
            b['hex']=d.hex()
        events.append(e)
    events=[]
    event(0x630a,100,0xfffff000,0x62f8)
    event(0x6328,100,0xfffff000,0x62f8,True)
    event(0x62f8,100,0xfffff004,0xdead,True)
    for pc in (0xf8f6,0xf8fc,0xf900,0xf904,0x632a,0xa148,0xa15c,0xf906,0xf90a,0x12646,0xf90c,0xf936,0x5f3a):
        sp=0xfffff000;ret=0x5f3a
        if pc in (0x632a,0xa148,0xa15c):sp-=4;ret=0xf906
        elif pc==0x12646:sp-=4;ret=0xf90c
        elif pc==0x5f3a:sp+=4
        event(pc,101,sp,ret,True,pc in (0xf936,0x5f3a))
    return dict(transition_fixture(),events=events)


class CoastingEvidenceTests(unittest.TestCase):
    def test_deferred_initializer_to_handler(self):
        (entry,returned),pairs=validate(fixture(),100,102)
        self.assertEqual(entry['frame'],100);self.assertEqual(returned['pc'],0x62f8)
        self.assertEqual(len(pairs),1);self.assertEqual(pairs[0]['handlers'][0]['pc'],0x632a)

    def test_missing_boundary_stack_and_tail_order_reject(self):
        for pc in (0x630a,0x6328,0x62f8,0xf8f6,0xf904,0x632a,0xa148,0xa15c,0xf906,0x12646,0xf936,0x5f3a):
            t=fixture();t['events']=[e for e in t['events'] if e['pc']!=pc]
            with self.subTest(pc=hex(pc)),self.assertRaises(ValueError):validate(t,100,102)
        for pc in (0x630a,0x6328,0x62f8,0x632a,0xa148,0xa15c):
            t=fixture();next(e for e in t['events'] if e['pc']==pc)['registers']['M68K A7']+=4
            with self.subTest(pc=hex(pc)),self.assertRaises(ValueError):validate(t,100,102)
        t=fixture();es=t['events'];i=next(i for i,e in enumerate(es) if e['pc']==0xa148);es[i],es[i+1]=es[i+1],es[i]
        for i,e in enumerate(es):e['sequence']=i
        with self.assertRaises(ValueError):validate(t,100,102)

    def test_uncontracted_motion_owner_and_shared_changes_reject(self):
        for pc,label,index in ((0x6328,'actor',2),(0x62f8,'tracking_selector',0),(0xa148,'transition',0),(0xf8f6,'actor',2)):
            t=fixture();e=next(e for e in t['events'] if e['pc']==pc);b=next(b for b in e['ranges'] if b['label']==label)
            data=bytearray.fromhex(b['hex']);data[index]^=1;b['hex']=data.hex()
            # Mutating A148's input alone is outside the final-output snapshot;
            # bind the tail entry state to the selected handler, as in the real trace.
            with self.subTest(pc=hex(pc)),self.assertRaises(ValueError):validate(t,100,102)
        t=fixture();next(e for e in t['events'] if e['pc']==0x6328)['registers']['M68K A4']+=78
        with self.assertRaises(ValueError):validate(t,100,102)

    def test_overflow_and_unmodeled_frame_reject(self):
        for field,value in (('overflow',True),('dropped',1),('error','failed')):
            t=fixture();t[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):validate(t,100,102)
        t=fixture();t['events'][0]['frame']=99
        with self.assertRaises(ValueError):validate(t,100,102)

    def test_ranges_and_authored_outputs(self):
        meta=json.loads((ROOT/'re/coasting_step.json').read_text());self.assertEqual(sum(r['instruction_count'] for r in meta['regions']),8)
        self.assertEqual(sum(r['end_exclusive']-r['start'] for r in meta['regions']),42)
        rows=goldens()+entry_goldens();data=('\n'.join(' '.join(map(str,e)) for _,e in rows)+'\n').encode()
        self.assertEqual(decode(data,len(rows)),[e for _,e in rows]);self.assertEqual(len(rows),11)
        ranges=[]
        for name in (*meta['dependencies'],'coasting_step'):
            ranges.extend((r['start'],r['end_exclusive']) for r in json.loads((ROOT/f're/{name}.json').read_text())['regions'] if r['execution_compared'])
        ranges.sort();self.assertTrue(all(a[1]<=b[0] for a,b in zip(ranges,ranges[1:])))

if __name__=='__main__':unittest.main()
