"""ROM-free reversal scope, effect ownership and capture-completeness guards."""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from genesis_reversal_capture import effect_fields,validate_effects
from reversal_cases import actor_goldens,effect_goldens,decode_actor_rows,split_actor


def fixture():
    address=0xffff1b50;actor=bytearray(78);events=[];free=bytearray(280)
    def put(data,off,value,size=2):data[off:off+size]=value.to_bytes(size,'big')
    put(free,4,address,4);put(free,276,0xffff3010,4)
    def add(pc,obj,*,a6=address,a5=0xffff0690,frame=100,sp=0xffffeffc,ret=0x69b6,allocated=None):
        blocks={'object':bytes(obj),'actor':bytes(actor),'free':bytes(free),'stack':ret.to_bytes(4,'big'),'allocated':bytes(allocated or obj)}
        events.append({'pc':pc,'frame':frame,'kind':'entry','sequence':len(events),
            'registers':{'M68K A6':a6,'M68K A5':a5,'M68K A7':sp,'M68K SR':0x2700},
            'ranges':[{'label':k,'hex':v.hex()} for k,v in blocks.items()]})
    obj=bytearray(78);add(0xf994,obj,a6=0xffff1ab4,sp=0xffffe000,ret=0xa81c)
    put(free,276,0xffff300c,4);add(0xf9a8,obj,a6=0xffff1ab4,a5=address,sp=0xffffe000,ret=0xa81c)
    obj[0]=128;put(obj,6,541);put(obj,22,0x12646,4);put(obj,70,0x12646,4)
    add(0xf9ce,obj,a6=0xffff1ab4,a5=address,sp=0xffffe000,ret=0xa81c)
    obj[0]=133;put(obj,2,222);put(obj,4,124);put(obj,6,215);put(obj,8,215);put(obj,10,220)
    obj[12]=obj[13]=2;put(obj,14,220);put(obj,18,2048);put(obj,22,0xa87c,4);put(obj,26,0xfaa4,4);put(obj,34,0xffff1ab4,4)
    add(0xa87a,obj,a6=0xffff1ab4,a5=address,ret=0xa7ec)
    for i in range(12):
        put(actor,2,200+i);put(actor,4,109)
        add(0xf76c,obj,frame=100+i)
        # Authored six-frame animation, two invocations per frame; final
        # scheduler wrap precedes its release and final X-follow.
        obj[12]=1 if i%2==0 else 2
        if i%2:put(obj,6,215 if i==11 else 216+i//2)
        if i==11:
            add(0xfaa4,obj,frame=111);obj[0]=0;put(free,276,0xffff3010,4)
            add(0xfaba,obj,frame=111)
        add(0x69b6,obj,frame=100+i,sp=0xfffff000)
        add(0xa87c,obj,frame=100+i,ret=0x69bc)
        put(obj,2,222+i);add(0x69bc,obj,frame=100+i,sp=0xfffff000)
    return {'events':events}


class ReversalEvidenceTests(unittest.TestCase):
    def test_scope_disjoint_and_exhaustion_boundary(self):
        meta=json.loads((ROOT/'re/reversal_step.json').read_text());ranges=[]
        for name in (*meta['dependencies'],'reversal_step'):
            ranges.extend((r['start'],r['end_exclusive']) for r in json.loads((ROOT/f're/{name}.json').read_text())['regions'] if r['execution_compared'])
        ranges.sort();self.assertTrue(all(a[1]<=b[0] for a,b in zip(ranges,ranges[1:])))
        self.assertEqual(sum(r['instruction_count'] for r in meta['regions']),119)
        self.assertEqual(sum(r['end_exclusive']-r['start'] for r in meta['regions']),576)
        self.assertIn(0xf9d0,meta['rejected_boundaries'])

    def test_authored_goldens_and_strict_output_shape(self):
        rows=actor_goldens();encoded=('\n'.join(' '.join(map(str,e)) for _,e in rows)+'\n').encode()
        decoded=decode_actor_rows(encoded,2);self.assertEqual(decoded,[e for _,e in rows])
        self.assertEqual(split_actor(decoded[0])[1][0][0:4],(1,0,222,124));self.assertEqual(len(effect_goldens()),8)
        for bad in (b'',b'1 2\n',encoded.replace(b' 1 1 0 222',b' 2 1 0 222')):
            with self.assertRaises(ValueError):decode_actor_rows(bad,2)

    def test_complete_lifetime_and_release_then_follow(self):
        allocations,births,lives=validate_effects(fixture())
        self.assertEqual(len(allocations),1);self.assertEqual(len(births),1)
        life=lives[0xffff1b50];self.assertEqual(len(life['pairs']),12)
        self.assertEqual(life['fields'][2:4],(233,124));self.assertTrue(life['released'])

    def test_missing_allocation_and_phase_events_reject(self):
        original=fixture()
        for pc in (0xf994,0xf9a8,0xf9ce,0xa87a,0xf76c,0x69b6,0xa87c,0x69bc,0xfaa4,0xfaba):
            t=copy.deepcopy(original);i=next(i for i,e in enumerate(t['events']) if e['pc']==pc);del t['events'][i]
            with self.subTest(pc=hex(pc)),self.assertRaises(ValueError):validate_effects(t)

    def test_uncontracted_writes_and_wrong_ownership_reject(self):
        original=fixture()
        for pc,label,offset in ((0xf9ce,'allocated',16),(0xa87a,'allocated',37),(0x69bc,'object',4),(0xfaba,'free',1)):
            t=copy.deepcopy(original);e=next(e for e in t['events'] if e['pc']==pc);b=next(b for b in e['ranges'] if b['label']==label)
            data=bytearray.fromhex(b['hex']);data[offset]^=1;b['hex']=data.hex()
            with self.subTest(pc=hex(pc)),self.assertRaises(ValueError):validate_effects(t)

    def test_external_mutation_cannot_reseed_effect(self):
        t=fixture();e=next(e for e in t['events'] if e['pc']==0xf76c and e['frame']==101)
        b=next(b for b in e['ranges'] if b['label']=='object');data=bytearray.fromhex(b['hex']);data[2]^=1;b['hex']=data.hex()
        with self.assertRaisesRegex(ValueError,'continuity'):validate_effects(t)

if __name__=='__main__':unittest.main()
