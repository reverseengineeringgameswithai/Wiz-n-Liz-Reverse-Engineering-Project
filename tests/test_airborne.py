"""ROM-free airborne comparison scope and continuation-boundary checks."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from airborne_probe import validate
from movement_probe import closed_graph
from airborne_cases import goldens,decode_results
from airborne_compare import flat_cases,authored_cases,real_cases


class AirborneEvidenceTests(unittest.TestCase):
    def test_explicit_fallthrough_boundary(self):
        data=bytes.fromhex('4e714e75');rows=[{'address':0,'size':2}]
        with self.assertRaises(ValueError):closed_graph(data,rows)
        graph=closed_graph(data,rows,[2]);self.assertEqual(graph['continuations'],[[0,2]])
        self.assertEqual(graph['returns'],[])
        with self.assertRaises(ValueError):closed_graph(data,rows+[{'address':2,'size':2}],[2])

    def test_continuation_does_not_allow_arbitrary_escape(self):
        data=bytes.fromhex('60000006');rows=[{'address':0,'size':4}]
        with self.assertRaises(ValueError):closed_graph(data,rows,[4])
        self.assertEqual(closed_graph(data,rows,[8])['continuations'],[[0,8]])

    def test_hashed_ranges_and_transfers(self):
        data=bytes.fromhex('610000024e75');digest=hashlib.sha256(data).hexdigest()
        meta={'schema_version':1,'address_space':'rom_file_offset','rom_sha256':digest,
              'regions':[{'start':0,'end_exclusive':6,'sha256':digest}],'transfers':[{'pc':0,'target':4}],'continuation_boundaries':[{'pc':0xa1be},{'pc':0xa246}]}
        self.assertEqual(validate(data,meta),{'regions':1,'transfers':1})
        meta['regions'][0]['sha256']='0'*64
        with self.assertRaises(ValueError):validate(data,meta)

    def test_corpus_and_goldens(self):
        self.assertEqual([len(flat_cases()),len(authored_cases()),len(real_cases())],[393924,10240,11776])
        self.assertEqual(len(goldens()),36)
        c,result=goldens()[-1]
        self.assertEqual(c[-1],16);self.assertEqual(result[18:20],(2,1))
        self.assertEqual(result[5],8) # Explicit idle-left boundary stops the sequence.
        for payload in (b'',b'1 2\n',b'x '*21):
            with self.assertRaises(ValueError):decode_results(payload,1)

    def test_metadata_scope_is_disjoint_and_bounded(self):
        meta=json.loads((ROOT/'re/airborne_update.json').read_text());regions=meta['regions']
        intervals=sorted((r['start'],r['end_exclusive']) for r in regions)
        self.assertTrue(all(a[1]<=b[0] for a,b in zip(intervals,intervals[1:])))
        self.assertEqual(sum(b-a for a,b in intervals),706)
        self.assertEqual(sum(r['instruction_count'] for r in regions),172)
        self.assertEqual([c['pc'] for c in meta['continuation_boundaries']],[0xa1be,0xa246])


if __name__=='__main__':unittest.main()
