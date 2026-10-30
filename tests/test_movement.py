"""ROM-free movement metadata, call graph, fixture and comparison corpus guards."""
import hashlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from movement_probe import closed_graph,transfer,validate
from movement_compare import flat_cases,authored_cases,real_cases
from movement_cases import fixture,goldens,decode_results
from terrain_compare import reference_resources


class MovementEvidenceTests(unittest.TestCase):
    def test_dbf_and_tail_branch_targets(self):
        self.assertEqual(transfer(bytes.fromhex('51cffffe'),0),0)
        self.assertEqual(transfer(bytes.fromhex('60000004'),0),6)
        self.assertEqual(transfer(bytes.fromhex('61000004'),0),6)
        self.assertIsNone(transfer(bytes.fromhex('4e75'),0))

    def test_closed_graph_accepts_call_and_rejects_escape(self):
        data=bytes.fromhex('610000044e754e75');rows=[{'address':0,'size':4},{'address':4,'size':2},{'address':6,'size':2}]
        result=closed_graph(data,rows);self.assertEqual(result['instructions'],3)
        self.assertEqual(result['edges'],[[0,4],[0,6]])
        with self.assertRaises(ValueError):closed_graph(data,rows[:2])
        with self.assertRaises(ValueError):closed_graph(bytes.fromhex('4ed0'),[{'address':0,'size':2}])

    def test_metadata_hash_and_transfer_guards(self):
        data=bytes.fromhex('610000024e75');digest=hashlib.sha256(data).hexdigest()
        meta={'schema_version':1,'address_space':'rom_file_offset','rom_sha256':digest,
              'regions':[{'start':0,'end_exclusive':6,'sha256':digest}],'transfers':[{'pc':0,'target':4}]}
        self.assertEqual(validate(data,meta),{'regions':1,'transfers':1})
        meta['transfers'][0]['target']=2
        with self.assertRaises(ValueError):validate(data,meta)
        with self.assertRaises(ValueError):validate(data+b'x',meta)

    def test_fixtures_cover_record_join_and_attributes(self):
        scene,bank=fixture();map_data,records=reference_resources(scene,bank,257)
        self.assertEqual(len(records),32);self.assertEqual(records[:8],bytes([5]*8))
        words=[int.from_bytes(map_data[i:i+2],'big') for i in range(0,8192,2)]
        self.assertEqual({w&0xf800 for w in words},{i<<11|0x4000 for i in range(32)})
        self.assertEqual({(w&2047)-257 for w in words},{0,1,2,3})

    def test_corpus_counts_and_independent_goldens(self):
        self.assertEqual(len(goldens()),26)
        self.assertEqual(len(flat_cases()),262265)
        self.assertEqual(len(authored_cases()),8192)
        self.assertEqual(len(real_cases()),11776)
        self.assertEqual(flat_cases()[:26],[c for c,_ in goldens()])
        for payload in (b'',b'1 2 3\n',b'x '*16):
            with self.assertRaises(ValueError):decode_results(payload,1)


if __name__=='__main__':unittest.main()
