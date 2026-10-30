"""ROM-free guards for physical-input and writer evidence contracts."""
import json
import hashlib
from pathlib import Path
import sys
import unittest
import tempfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from genesis_session_capture import (CONVERSIONS,EARLY_CONVERSIONS,FADE_CONVERSIONS,FIXED,physical_fields,validate_producers,validate_writes,validate_banner,decode)
from genesis_effect_session import validate_initial, fixture_reader, validate_endpoint, END


def producer_fixture(conversions=CONVERSIONS):
    ranges={k:bytes(n) for k,n in [('actor',78),('scratch',4),('gate',2),('action_globals',10),('mailbox',8),('tracking_selector',2),('transition',20)]}
    control=bytearray(112);control[20]=255;ranges.update(control=control,control2=control)
    events=[]
    for a5,caller in conversions:
        for pc in (0x14e4e,0x14f22):
            events.append(dict(sequence=len(events),pc=pc,frame=100,registers={'M68K A5':a5,'M68K A7':0xfffff000},
                ranges=[dict(label=k,hex=v.hex()) for k,v in (ranges|{'stack':caller.to_bytes(4,'big')}).items()]))
    return events


def writer_fixture():
    events=[dict(sequence=i,frame=100,type=65536) for i in range(8)]
    for pc,address,value in ((0x99e4,0xff4442,84),(0x99ea,0xff4444,4)):
        events.append(dict(sequence=len(events),frame=100,type=4,cpu='M68K',pc=pc,address=address,width=2,value=value,registers={'M68K A6':0xffff1ab4}))
    return dict(schemaVersion=1,dropped=0,capacity=4096,events=events)


class SessionEvidenceTests(unittest.TestCase):
    def test_initial_effect_ownership(self):
        ram=bytearray(65536);validate_initial(ram)
        for handler in (0xa87c,0xaa40):
            for offset in (0x1b50,0x3008-78):
                obj=bytearray(78);obj[0]=0x85;obj[0x16:0x1a]=handler.to_bytes(4,'big');obj[0x22:0x26]=(0xffff1ab4).to_bytes(4,'big')
                ram[offset:offset+78]=obj
                with self.assertRaises(ValueError):validate_initial(ram)
                ram[offset]=0;validate_initial(ram)
                ram[offset]=0x85;ram[offset+0x25]^=1;validate_initial(ram)
                ram[offset:offset+78]=bytes(78)
        with self.assertRaises(ValueError):validate_initial(ram[:-1])

    def test_effect_fixture_integrity(self):
        with tempfile.TemporaryDirectory() as d:
            directory=Path(d);data=b'synthetic input';(directory/'before.ram').write_bytes(data)
            parent=dict(ok=True,rom_unchanged=True,artifacts={'before.ram':hashlib.sha256(data).hexdigest()})
            read=fixture_reader(parent,directory);self.assertEqual(read('before.ram'),data)
            with self.assertRaises(ValueError):read('after.ram')
            for field in ('ok','rom_unchanged'):
                with self.assertRaises(ValueError):fixture_reader(parent|{field:False},directory)
            (directory/'before.ram').write_bytes(data+b'changed')
            with self.assertRaises(ValueError):fixture_reader(parent,directory)
            with self.assertRaises(ValueError):fixture_reader(parent|{'artifacts':{'../outside':'bad'}},directory)

    def test_effect_endpoint_equality(self):
        identity={'rom':'synthetic'}
        s=dict(identity=identity,frame=END,experimentalEdits=[],canonicalSha256='synthetic',hashScope='declared')
        self.assertEqual(validate_endpoint(s,s,identity)['scope'],'declared')
        for key,value in (('identity',{}),('frame',END-1),('experimentalEdits',[{}]),('canonicalSha256','changed'),('hashScope','changed')):
            with self.assertRaises(ValueError):validate_endpoint(s,s|{key:value},identity)

    def test_early_cadence_and_writer(self):
        self.assertEqual(validate_producers(producer_fixture(EARLY_CONVERSIONS),[],EARLY_CONVERSIONS)['sequence'],5)
        with self.assertRaises(ValueError):validate_producers(producer_fixture(EARLY_CONVERSIONS),[])
        t=writer_fixture();t['events']=t['events'][:4]+t['events'][8:]
        banner=dict(t['events'][-1],pc=0x63e8,address=0xff4444,value=6)
        t['events'].insert(4,banner)
        for i,e in enumerate(t['events']):e['sequence']=i
        self.assertEqual(len(validate_writes(t,100,early=True)),2)
        for key,value in (('value',7),('width',1),('pc',0x63e2),('address',0xff4442)):
            bad=json.loads(json.dumps(t));bad['events'][4][key]=value
            with self.assertRaises(ValueError):validate_writes(bad,100,early=True)
        t['events'].append(dict(banner,sequence=20,pc=0x6560,address=0xff33de,width=1,value=0))
        self.assertEqual(len(validate_writes(t,100,early=True)),2)
        t['events'][-1]['value']=1
        with self.assertRaises(ValueError):validate_writes(t,100,early=True)

    def test_second_level_fade_cadence(self):
        # During a fade 30C4 does not read the pads: three conversions and four polls.
        self.assertEqual(validate_producers(producer_fixture(FADE_CONVERSIONS),[],FADE_CONVERSIONS)['sequence'],5)
        with self.assertRaises(ValueError):validate_producers(producer_fixture(FADE_CONVERSIONS),[])
        with self.assertRaises(ValueError):validate_producers(producer_fixture(),[],FADE_CONVERSIONS)
        t=writer_fixture();t['events']=t['events'][4:]
        for i,e in enumerate(t['events']):e['sequence']=i
        self.assertEqual(len(validate_writes(t,100,polled=False)),2)
        with self.assertRaises(ValueError):validate_writes(t,100)
        with self.assertRaises(ValueError):validate_writes(writer_fixture(),100,polled=False)

    def test_banner_calls_and_tail(self):
        base=producer_fixture()[0];events=[]
        for pc in (0x17aa0,0x63e2,0x63e8,0x17532,0x6422,0x175d0,0x17aa8):
            e=json.loads(json.dumps(base));e.update(pc=pc,sequence=len(events))
            e['registers'].update({'M68K A6':0xffff32c2,'M68K D1':6,'M68K D0':1,'M68K A0':0x647c,'M68K A1':0xe338 if pc==0x175d0 else 0xe300})
            if pc==0x17532:e['registers']['M68K A7']-=4
            if pc in (0x17aa0,0x17aa8):e['registers']['M68K A7']+=4
            for r in e['ranges']:
                if r['label']=='scratch':r['hex']='004d0006' if len(events)>1 else '004d0063'
                if r['label']=='stack':r['hex']='00006422' if pc==0x17532 else '00017aa8'
            e['ranges'] += [dict(label=l,hex='0000') for l in ('difficulty','stage')];events.append(e)
        self.assertEqual(validate_banner(events)[2],(0,0xe300,1,1,0xe338))
        for index,reg in ((3,'M68K A7'),(5,'M68K A7'),(6,'M68K A7'),(3,'M68K A0'),(5,'M68K D0'),(2,'M68K A6')):
            bad=json.loads(json.dumps(events));bad[index]['registers'][reg]^=4
            with self.assertRaises(ValueError):validate_banner(bad)
        bad=json.loads(json.dumps(events));next(r for r in bad[2]['ranges'] if r['label']=='scratch')['hex']='004e0006'
        with self.assertRaises(ValueError):validate_banner(bad)

    def test_physical_rows_and_metadata(self):
        self.assertEqual(physical_fields(['P1 Right','P1 B']), (40,(231,255,255,0,0,0,0,255,0,255,0,0)))
        self.assertEqual(physical_fields(['P1 Up','P1 Down','P1 Left','P1 Right'])[1][4:8],(0,0,0,0))
        self.assertEqual(physical_fields(['P1 A','P2 C'],2)[1],(223,255,255,0,0,0,0,0,0,0,255,0))
        for row in (['Reset'],['P1 Z'],['P1 B','P1 B']):
            with self.assertRaises(ValueError):physical_fields(row)
        m=json.loads((ROOT/'re/input_conversion.json').read_text());r,=m['regions']
        self.assertEqual((r['start'],r['end_exclusive'],r['instruction_count']),(0x14e4e,0x14f24,54))

    def test_producer_order_and_owners(self):
        self.assertEqual(validate_producers(producer_fixture(),[])['sequence'],11)
        for i in range(12):
            events=producer_fixture();del events[i]
            with self.assertRaises(ValueError):validate_producers(events,[])
        for i in range(12):
            for reg in ('M68K A5','M68K A7'):
                events=producer_fixture();events[i]['registers'][reg]^=4
                with self.assertRaises(ValueError):validate_producers(events,[])

    def test_changed_producer_fields_reject(self):
        for label,index in [('control',0x14),('control',0x16),('control',0x18),('control',0x19),('control2',0x14),('actor',0),*[(k,0) for k in FIXED]]:
            events=producer_fixture();b=next(b for b in events[1]['ranges'] if b['label']==label);d=bytearray.fromhex(b['hex']);d[index]^=1;b['hex']=d.hex()
            with self.subTest(label=label,index=index),self.assertRaises(ValueError):validate_producers(events,[])

    def test_writer_scope_and_overflow(self):
        self.assertEqual(len(validate_writes(writer_fixture(),100)),2)
        for address in (0xff0f16,0xff06ea,0xff06ef,0xff33e0,0xff0ad8,0xff0836,0xff0b92):
            t=writer_fixture();t['events'][-1]['address']=address
            with self.assertRaises(ValueError):validate_writes(t,100)
        for name,value in (('dropped',1),('capacity',5)):
            t=writer_fixture();t[name]=value
            with self.assertRaises(ValueError):validate_writes(t,100)
        for key,value in (('pc',0x99de),('cpu','Z80'),('width',4),('frame',101),('sequence',0)):
            t=writer_fixture();t['events'][-1][key]=value
            with self.assertRaises(ValueError):validate_writes(t,100)
        t=writer_fixture();t['events'][-1]['registers']['M68K A6']=0xffff2000
        with self.assertRaises(ValueError):validate_writes(t,100)
        t=writer_fixture();t['events'].pop(0)
        with self.assertRaises(ValueError):validate_writes(t,100)
        terrain=dict(map_bus=0xff4d02,record_bus=0xff6d02,records=577)
        self.assertEqual(len(validate_writes(writer_fixture(),100,terrain)),2)
        for address in (0xff4d02,0xff6d02,0xff13a4,0xff13ae,0xff140e,0xff444e):
            t=writer_fixture();t['events'][-1]['address']=address
            with self.assertRaises(ValueError):validate_writes(t,100,terrain)

    def test_output_shape(self):
        row=(1,*([0]*39));data=(' '.join(map(str,row))+'\n').encode()
        self.assertEqual(decode(data,1),[row])
        for bad in (data+b'0\n',b'0\n',data.replace(b'1 ',b'1 0 ',1)):
            with self.assertRaises(ValueError):decode(bad,1)

if __name__=='__main__':unittest.main()
