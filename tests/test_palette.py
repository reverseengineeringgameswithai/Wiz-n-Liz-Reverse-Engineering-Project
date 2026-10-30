"""Authored palette trace boundaries; reject incomplete, mis-scoped and mutated evidence."""
import copy,json,unittest
from pathlib import Path
from test_tally import fixture as tally_fixture
from genesis_palette_capture import validate,RANGES,edits
from palette_cases import COLORS,COMPONENTS,goldens,decode
ROOT=Path(__file__).resolve().parents[1]


def fixture():
    t=tally_fixture();template=t['events'][0];events=[]
    common=[0xf8f6,0xf8fc,0xf900,0xf904]
    tail=[0xf906,0xf90a,0x12646,0xf90c,0xf936,0x5f3a]
    groups=[
        [0x51c8,0x51d0,0xa148,0xa15c,0x51da,0x137ce,0x1372c,0x13752,0x137ee,0x137f4,0x51f4,0x1324e,0x13292,0x51fa,0x5202],
        [0x5204,0xa148,0xa15c,0x520e,0x4f8c],
        [0x5204,0xa148,0xa15c,0x520e,0x5218,0x5220],
        [0x5222,0xa148,0xa15c,0x522c,0x537c,0x53a2]]
    for f,middle in enumerate(groups):
        pcs=common+middle+tail
        for i,pc in enumerate(pcs):
            e=copy.deepcopy(template);e.update(pc=pc,frame=100+f,sequence=len(events));regs=e['registers'];regs.update({'M68K A1':0,'M68K D1':0})
            handler=(0x51c8,0x5204,0x5204,0x5222)[f]
            after_init=f>0 or i>=pcs.index(0x13292)
            prepared=f>0 or i>=pcs.index(0x13752)
            if f==0 and i>=pcs.index(0x5202):handler=0x5204
            if f==2 and i>=pcs.index(0x5220):handler=0x5222
            regs['M68K A0']=0x12646 if pc==0xf90a else handler
            regs['M68K A6']=0xffff1ab4;regs['M68K A5']=0xffff0690
            sp=0xfffff000;ret=0x5f3a
            if pc in middle:sp-=4;ret=0xf906
            if pc in (0xa148,0xa15c):sp-=4;ret=(0x51da,0x520e,0x520e,0x522c)[f]
            if pc in (0x137ce,0x137f4):sp-=4;ret=0x51f4
            if pc in (0x1372c,0x13752):sp-=20;ret=0x137ee
            if pc==0x137ee:sp-=16
            if pc in (0x1324e,0x13292):sp-=4;ret=0x51fa
            if pc==0x12646:sp-=4;ret=0xf90c
            if pc==0x5f3a:sp+=4
            regs['M68K A7']=sp
            if pc in (0x137ce,0x137f4):regs.update({'M68K A0':0xffff0ea8,'M68K D0':2})
            if pc in (0x1372c,0x13752):regs.update({'M68K A0':0xffff0ec8 if prepared else 0xffff0ea8,'M68K A1':0xffff0df8 if prepared else 0xffff0dc8,'M68K D0':65535 if prepared else 15})
            for b in e['ranges']:
                d=bytearray.fromhex(b['hex']);l=b['label']
                if l=='actor':d[22:26]=handler.to_bytes(4,'big')
                if l=='control':d[0x42:0x46]=bytes.fromhex('ff80ff80')
                if l=='stack':d[:]=ret.to_bytes(4,'big')
                if l=='tally_gate':d[:]=b'\0\1'
                if l=='remaining':d[:]=b'\0\5'
                if l=='tally_countdown':d[:]=(119 if f==3 and i>=pcs.index(0x53a2) else 120).to_bytes(2,'big')
                if l=='transition':
                    values=(0,0,1,14) if not after_init else (65535,6,0,0) if f==0 else (65535,5,0,0) if f==1 else (0,0,0,14)
                    d[:]=b''.join(v.to_bytes(2,'big') for v in values)+b''.join(v.to_bytes(4,'big') for v in ((0x135ea,)*3 if after_init else (0x1356a,0x1356a,0x135aa)))
                if l=='palette_flags':d[:]=b'\0\x7b\0\0' if after_init else b'\0\x7b\1\xc8'
                b['hex']=d.hex()
            for l,o,n in RANGES:
                data=b''.join(v.to_bytes(2,'big') for v in COLORS) if l=='palette_source' else bytes(COMPONENTS if prepared else range(48)) if l=='palette_components' else bytes(n)
                e['ranges'].append(dict(label=l,hex=data.hex()))
            events.append(e)
    t['events']=events;return t


class PaletteEvidenceTests(unittest.TestCase):
    def test_deferred_handlers_and_fixed_helper_returns(self):
        pairs,initialized,completed=validate(fixture(),100,104)
        self.assertEqual(initialized,[100]);self.assertEqual(completed,[102]);self.assertEqual([p['handlers'][0]['pc'] for p in pairs],[0x51c8,0x5204,0x5204,0x5222])

    def test_missing_boundaries_and_wrong_stacks_reject(self):
        for pc in (0x51d0,0x51da,0x137ce,0x1372c,0x13752,0x137ee,0x137f4,0x51f4,0x1324e,0x13292,0x51fa,0x5202,0x520e,0x5218,0x5220,0x53a2):
            t=fixture();t['events']=[e for e in t['events'] if e['pc']!=pc]
            with self.subTest(pc=pc),self.assertRaises(ValueError):validate(t,100,104)
        for pc in (0x137ce,0x1372c,0x13752,0x137ee,0x137f4,0x1324e,0x13292,0x5202,0x5220):
            t=fixture();next(e for e in t['events'] if e['pc']==pc)['registers']['M68K A7']+=4
            with self.subTest(pc=pc),self.assertRaises(ValueError):validate(t,100,104)

    def test_wrong_bank_extent_and_uncontracted_mutations_reject(self):
        for pc,reg in ((0x137ce,'M68K D0'),(0x1372c,'M68K A1'),(0x13752,'M68K A0')):
            t=fixture();next(e for e in t['events'] if e['pc']==pc)['registers'][reg]^=1
            with self.assertRaises(ValueError):validate(t,100,104)
        for pc,label in ((0x137f4,'palette_source'),(0x13292,'palette_other_before'),(0x51fa,'palette_flags'),(0x5202,'remaining'),(0x5220,'palette_components')):
            t=fixture();e=next(e for e in t['events'] if e['pc']==pc);b=next(b for b in e['ranges'] if b['label']==label);d=bytearray.fromhex(b['hex']);d[0]^=1;b['hex']=d.hex()
            with self.subTest(pc=pc),self.assertRaises(ValueError):validate(t,100,104)

    def test_overflow_and_edits_are_explicit(self):
        for k,v in (('overflow',True),('dropped',1),('error','bad')):
            t=fixture();t[k]=v
            with self.assertRaises(ValueError):validate(t,100,104)
        ram=bytearray(65536);ram[0xb90:0xb98]=bytes.fromhex('000000000001000e')
        self.assertEqual(len(edits(ram,False)['writes']),1);self.assertEqual(len(edits(ram,True)['writes']),5)
        ram[0x33ce]=1
        with self.assertRaises(ValueError):edits(ram,True)

    def test_ranges_and_authored_outputs(self):
        m=json.loads((ROOT/'re/palette_step.json').read_text());self.assertEqual(sum(r['instruction_count'] for r in m['regions']),56)
        self.assertEqual(sum(r['end_exclusive']-r['start'] for r in m['regions']),232)
        self.assertIn(0x5266,m['rejected_boundaries']);self.assertNotIn(0x51d0,m['rejected_boundaries'])
        rows=goldens();self.assertEqual(len(rows),16);self.assertEqual(decode(('\n'.join(' '.join(map(str,e)) for c,e in rows)+'\n').encode(),len(rows)),[e for c,e in rows])
        ranges=[]
        for name in (*m['dependencies'],'palette_step'):
            ranges.extend((r['start'],r['end_exclusive']) for r in json.loads((ROOT/f're/{name}.json').read_text())['regions'] if r['execution_compared'])
        ranges.sort();self.assertTrue(all(a[1]<=b[0] for a,b in zip(ranges,ranges[1:])))

if __name__=='__main__':unittest.main()
