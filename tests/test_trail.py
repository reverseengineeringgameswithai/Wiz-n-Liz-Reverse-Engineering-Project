"""Evidence guards for trail ownership, selectors and complete capture chunks."""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from genesis_trail_capture import emitter_fields,particle_fields,validate_chunks,START,END


def object_bytes(handler):
    b=bytearray(78)
    for offset,value in ((0x16,handler),(0x1a,0xfaa4),(0x46,0x12646),(0x4a,0xffff0690)):b[offset:offset+4]=value.to_bytes(4,'big')
    return b


class TrailEvidenceTests(unittest.TestCase):
    def test_owner_and_service(self):
        b=object_bytes(0x6d8c);self.assertEqual(len(emitter_fields(b)),22)
        for offset in (0x16,0x46,0x4a,0x14):
            changed=b.copy();changed[offset]^=1
            with self.assertRaises(ValueError):emitter_fields(changed)
        with self.assertRaises(ValueError):emitter_fields(b[:-1])

    def test_particle_selectors(self):
        b=object_bytes(0x5ae2);self.assertEqual(len(particle_fields(b)),10)
        for offset in (0x16,0x1a,0x46,0x14):
            changed=b.copy();changed[offset]^=1
            with self.assertRaises(ValueError):particle_fields(changed)

    def test_trace_loss_and_cadence(self):
        identity={'synthetic':True};chunks=[];writes=[]
        for i,frame in enumerate(range(START,END)):
            chunks.append(dict(identity=identity,dropped=0,overflow=False,error=None,events=[dict(kind='entry',frame=frame,sequence=i)]))
            writes.append(dict(identity=identity,dropped=0,capacity=4096,events=[dict(frame=frame,type=65536,sequence=4*i+j) for j in range(4)]))
        self.assertEqual(len(validate_chunks(chunks,writes,identity)[0]),END-START)
        for field,value in (('dropped',1),('overflow',True),('error','incomplete'),('identity',{})):
            bad=copy.deepcopy(chunks);bad[0][field]=value
            with self.assertRaises(ValueError):validate_chunks(bad,writes,identity)
        for field,value in (('dropped',1),('capacity',3),('identity',{})):
            bad=copy.deepcopy(writes);bad[0][field]=value
            with self.assertRaises(ValueError):validate_chunks(chunks,bad,identity)
        bad=copy.deepcopy(chunks);bad[0]['events'][0]['frame']+=1
        with self.assertRaises(ValueError):validate_chunks(bad,writes,identity)
        with self.assertRaises(ValueError):validate_chunks(chunks[:-1],writes,identity)

if __name__=='__main__':unittest.main()
