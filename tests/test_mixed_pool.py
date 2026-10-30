"""Independent malformed pool/occupancy and reservation evidence checks."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from genesis_mixed_session import slot,free_fields,initial,BASE,STRIDE,SLOTS,private_fields,validate_private_globals,table_fields,validate_table_input
from genesis_collision_evidence import collision_fields,validate_inputs
from genesis_return_only_evidence import return_only_fields,validate_phase,validate_write


def free_block(indices):
    b=bytearray(280)
    for i,index in enumerate(indices):b[4+4*i:8+4*i]=(BASE+STRIDE*index).to_bytes(4,'big')
    b[276:280]=(0xffff300c+4*len(indices)).to_bytes(4,'big');return b


def reserved(handler=0x12646,mode=0x80,callback=0,service=0x12646):
    b=bytearray(78);b[0]=mode
    for o,v in ((0x16,handler),(0x1a,callback),(0x46,service)):b[o:o+4]=v.to_bytes(4,'big')
    return b


class MixedPoolEvidenceTests(unittest.TestCase):
    def test_collision_selectors_and_extent(self):
        b=reserved(service=0x78ee);b[30:34]=bytes.fromhex('00380008');b[74:78]=(0xffff0690).to_bytes(4,'big')
        self.assertEqual(collision_fields(b),(0,0,0,128,0,0,0,0,0,0,0,1,56,8))
        for o,n,v in ((22,4,0x7808),(26,4,0x79b6),(70,4,0x12646),(74,4,1),(20,2,1)):
            bad=b.copy();bad[o:o+n]=v.to_bytes(n,'big')
            with self.assertRaises(ValueError):collision_fields(bad)
        with self.assertRaises(ValueError):collision_fields(b[:-1])
        with self.assertRaises(ValueError):return_only_fields(b)

    def test_collision_fixed_and_tracking_writers(self):
        ram=bytearray(65536);ram[0x13ae:0x13b0]=bytes.fromhex('03ff')
        event=dict(frame=1066,pc=0xac5e,registers={'M68K A6':0xffff2e82,'M68K A5':0xffff0690},ranges=[dict(label='control',hex=bytes(112).hex()),dict(label='control2',hex=bytes(112).hex()),dict(label='collision_mask',hex='03ff'),dict(label='multiplayer',hex='0000')])
        pairs=[dict(wrapper=event,return_=event)];pairs[0]['return']=pairs[0].pop('return_')
        writes=[dict(frame=1066,cpu='M68K',pc=pc,address=a,width=2,value=0,registers={'M68K A5':0xffff0690,'M68K A6':0xffff1ab4}) for pc,a in ((0xf91e,0xff06d2),(0xf928,0xff06d4))]
        self.assertEqual(validate_inputs([event],writes,ram,ram,pairs)['primary_tracking_writes'],2)
        for a,n in ((0xff13ad,2),(0xff33e2,2),(0xff087a,4),(0xff087d,1),(0xff06d1,2)):
            with self.assertRaises(ValueError):validate_inputs([event],[*writes,dict(writes[0],address=a,width=n)],ram,ram,pairs)
        for changes in (dict(pc=0),dict(value=1),dict(frame=1067),dict(registers={'M68K A5':0xffff0838,'M68K A6':0xffff1ab4})):
            with self.assertRaises(ValueError):validate_inputs([event],[dict(writes[0],**changes),writes[1]],ram,ram,pairs)

    def test_free_order_and_extent(self):
        self.assertEqual(free_fields(free_block([4,1,67,0])),[4,1,67,0])
        for address in (BASE-1,BASE+1,BASE+SLOTS*STRIDE):
            with self.assertRaises(ValueError):slot(address)
        for b in (free_block([1,1]),free_block([68]),free_block([0])[:-1]):
            with self.assertRaises(ValueError):free_fields(b)
        for offset,value in ((0,1),(279,13)):
            b=free_block([0]);b[offset]=value
            with self.assertRaises(ValueError):free_fields(b)

    def test_return_only_requires_known_fields_and_selectors(self):
        self.assertEqual(return_only_fields(reserved()),(0,0,0,128,0,0,0,0,0,0,0,0))
        for b in (reserved(handler=0),reserved(callback=0xfaa4),reserved(service=0),reserved(service=0x78ee)):
            with self.assertRaises(ValueError):return_only_fields(b)
        for offset in (1,20,*range(30,70)):
            b=reserved();b[offset]=1
            with self.assertRaises(ValueError):return_only_fields(b)
        b=reserved();b[74:78]=(1).to_bytes(4,'big')
        with self.assertRaises(ValueError):return_only_fields(b)
        with self.assertRaises(ValueError):return_only_fields(b[:-1])

    def test_return_only_exact_writers(self):
        base=0xff2cfc
        e=dict(pc=0xf778,address=base+12,width=1,value=0,registers={'M68K A6':0xffff2cfc})
        validate_write(e,base,True)
        with self.assertRaises(ValueError):validate_write(e,base,False)
        for change in (dict(pc=0xf782),dict(width=2),dict(address=base+1),dict(registers={'M68K A6':0xffff2d4a})):
            with self.assertRaises(ValueError):validate_write(dict(e,**change),base,True)
        e.update(pc=0xb12a,address=base+20,width=2,value=0);validate_write(e,base,True)
        with self.assertRaises(ValueError):validate_write(dict(e,value=1),base,True)

    def test_return_only_dispatch_and_dormancy(self):
        import copy
        owner=0xffff2cfc;sp=0xffff00f8;b=reserved(mode=0x81)
        for offset,value in ((6,921),(8,916),(10,921)):b[offset:offset+2]=value.to_bytes(2,'big')
        b[12:14]=bytes((1,5));after=b.copy();after[12]=5;after[6:8]=(916).to_bytes(2,'big')
        def event(seq,pc,stack,ret,obj):
            return dict(sequence=seq,frame=1066,pc=pc,registers={'M68K A6':owner,'M68K A5':123,'M68K A7':stack,'M68K A0':0x12646},
                ranges=[dict(label='object',hex=obj.hex()),dict(label='stack',hex=ret.to_bytes(4,'big').hex())]+[dict(label=l,hex=bytes(n).hex()) for l,n in (('actor',78),('control',112),('control2',112),('scratch',4),('free',280),('random',8))])
        pcs=(0x69aa,0xf76c,0x69b6,0x12646,0x69bc,0x69c0,0x12646,0x69c2)
        events=[event(i,pc,sp-(4 if i in (1,3,6) else 0),{1:0x69b6,3:0x69bc,6:0x69c2}.get(i,0x1234),b if i<2 else after) for i,pc in enumerate(pcs)]
        self.assertTrue(validate_phase(events,events[0],events[-1]))
        with self.assertRaises(ValueError):validate_phase([event(-1,0xf76c,sp-4,0x69b6,b),*events],events[0],events[-1])
        for index,reg,value in ((3,'M68K A0',0),(6,'M68K A7',sp),(4,'M68K A5',999)):
            bad=copy.deepcopy(events);bad[index]['registers'][reg]=value
            with self.assertRaises(ValueError):validate_phase(bad,bad[0],bad[-1])
        b[0]=5;idle=[event(0,0x69aa,sp,0x1234,b),event(1,0x69c2,sp,0x1234,b)]
        self.assertFalse(validate_phase(idle,*idle))
        bad=copy.deepcopy(idle);bad[1]['ranges'][0]['hex']=bytes([128])+b[1:]
        bad[1]['ranges'][0]['hex']=bad[1]['ranges'][0]['hex'].hex()
        with self.assertRaises(ValueError):validate_phase(bad,*bad)

    def test_private_selector_and_identity(self):
        b=reserved(handler=0x7808,mode=0x81);b[74:78]=(0xffff0690).to_bytes(4,'big')
        self.assertEqual(private_fields(b),(0,0,0,0,129,0,0,0,0,0,0,0,1))
        b[22:26]=(0x7ca4).to_bytes(4,'big');b[74:78]=(0xffff0838).to_bytes(4,'big')
        self.assertEqual((private_fields(b)[0],private_fields(b)[-1]),(1,2))
        for offset,value in ((26,0x1),(70,0),(74,1),(22,0),(20,1)):
            bad=b.copy();bad[offset:offset+(2 if offset==20 else 4)]=value.to_bytes(2 if offset==20 else 4,'big')
            with self.assertRaises(ValueError):private_fields(bad)
        with self.assertRaises(ValueError):return_only_fields(b)
        for offset in (1,0x1e,0x30,0x45):
            bad=b.copy();bad[offset]=1
            with self.assertRaises(ValueError):private_fields(bad)

    def test_private_gate_transients_reject(self):
        before=bytes(65536);event={'ranges':[{'label':'private_gates','hex':'00000000'},{'label':'rise_gate','hex':'00000000'}]}
        self.assertEqual(validate_private_globals([event],[],before,before)['writes'],0)
        for address,width in ((0xff31a4,2),(0xff31a6,2),(0xff31b0,4),(0xff31a2,4),(0xff31b3,1)):
            with self.assertRaises(ValueError):validate_private_globals([event],[dict(address=address,width=width)],before,before)
        bad=bytearray(before);bad[0x31b0]=1
        with self.assertRaises(ValueError):validate_private_globals([],[],bad,bad)
        event['ranges'][1]['hex']='00010000'
        with self.assertRaises(ValueError):validate_private_globals([event],[],before,before)

    def test_table_selector_and_cursor(self):
        b=reserved(handler=0x7a88,mode=0x81,callback=0x79b6)
        b[46:50]=(0x7a58).to_bytes(4,'big');b[74:78]=(0xffff0690).to_bytes(4,'big')
        self.assertEqual(table_fields(b),(0,0,0,129,0,0,0,0,0,0,0,1,0,0,0))
        b[46:50]=(0x7a86).to_bytes(4,'big');self.assertEqual(table_fields(b)[12],23)
        for pointer in (0,0x7a56,0x7a59,0x7a88,0xff007a58,0xffff31bc):
            bad=b.copy();bad[46:50]=pointer.to_bytes(4,'big')
            with self.assertRaises(ValueError):table_fields(bad)
        for offset,value in ((26,0),(70,0),(74,1),(22,0),(20,1)):
            bad=b.copy();n=2 if offset==20 else 4;bad[offset:offset+n]=value.to_bytes(n,'big')
            with self.assertRaises(ValueError):table_fields(bad)
        with self.assertRaises(ValueError):return_only_fields(b)

    def test_table_input_transients_reject(self):
        before=bytearray(65536);before[0x31bf]=80
        event={'pc':0x7a88,'ranges':[{'label':'table_input','hex':'00000050'}]}
        self.assertEqual(validate_table_input([event],[],before,before)['loop_count'],0)
        for address,width in ((0xff31bc,2),(0xff31be,2),(0xff31bb,2),(0xff31bf,1),(0xff31ba,4)):
            with self.assertRaises(ValueError):validate_table_input([event],[dict(address=address,width=width)],before,before)
        bad=before.copy();bad[0x31bc]=1
        with self.assertRaises(ValueError):validate_table_input([],[],bad,bad)
        event['ranges'][0]['hex']='00010050'
        with self.assertRaises(ValueError):validate_table_input([event],[],before,before)
        event['ranges'][0]['hex']='00000050';event['pc']=0x7a4e
        with self.assertRaises(ValueError):validate_table_input([event],[],before,before)

    def test_initial_managed_and_occupancy(self):
        ram=bytearray(65536);ram[0x3008:0x3120]=free_block(list(range(53)))
        for i in range(53,SLOTS):ram[0x1b50+STRIDE*i:0x1b50+STRIDE*(i+1)]=reserved(mode=0)
        e=reserved(handler=0x6d8c,mode=0x81);e[0x4a:0x4e]=(0xffff0690).to_bytes(4,'big');ram[0x2b76:0x2bc4]=e
        objects,free=initial(ram);self.assertEqual((len(objects),len(free),sum(o[0]==8 for o in objects)),(68,53,14))
        self.assertEqual(objects[53][0],4)
        bad=ram.copy();bad[0x1b50]=128
        with self.assertRaises(ValueError):initial(bad)
        bad=ram.copy();bad[0x2b76]=0
        with self.assertRaises(ValueError):initial(bad)
        bad=ram.copy();bad[0x2bc4+0x16:0x2bc4+0x1a]=(0xdead).to_bytes(4,'big')
        with self.assertRaises(ValueError):initial(bad)
        with self.assertRaises(ValueError):initial(ram[:-1])

if __name__=='__main__':unittest.main()
