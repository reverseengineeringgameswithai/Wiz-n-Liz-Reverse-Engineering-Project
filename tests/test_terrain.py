"""ROM-free metadata, reference fixture and original arithmetic coverage checks."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from terrain_cases import fixture, golden_cases, encode_cases, decode_results
from terrain_compare import reference_resources, authored_cases
from terrain_probe import validate, routine_cfg
import build_terrain_reference as builder


class TerrainEvidenceTests(unittest.TestCase):
    def test_reference_resource_join_and_relocation(self):
        scene,bank=fixture()
        map_data,records=reference_resources(scene,bank,257)
        self.assertEqual(len(map_data),8192)
        self.assertEqual(records,bytes([8]*8)+bytes(range(256)))
        self.assertEqual(struct.unpack_from(">H",map_data)[0],0x4102)
        self.assertEqual(struct.unpack_from(">H",map_data,64)[0],0x4902)
        self.assertEqual(struct.unpack_from(">H",map_data,128)[0],0x5102)

    def test_relocation_alias_and_missing_records_rejected(self):
        scene,bank=fixture()
        for base in (-1,2016,2048):
            with self.assertRaises(ValueError): reference_resources(scene,bank,base)
        changed=bytearray(scene);struct.pack_into(">H",changed,532,33)
        with self.assertRaises(ValueError):reference_resources(changed,bank,0)

    def test_case_corpus_and_transport(self):
        cases=authored_cases()
        self.assertEqual(len(cases),110610)
        self.assertEqual(cases[:18],[c for c,_ in golden_cases()])
        self.assertIn((0,65535,128,3,7),cases)
        self.assertNotIn((0,135,0x807f,6,7),cases)
        self.assertIn((0,135,2176,6,7),cases)
        self.assertEqual(encode_cases([(0,128,128,0,0)]),b"0 128 128 0 0\n")
        for payload in (b"",b"0 1 2\n",b"0 1 2 3 4 5 6 x\n"):
            with self.assertRaises(ValueError):decode_results(payload,1)

    def test_static_hashes_returns_and_call_targets(self):
        # Authored BSR.W to RTS, not bytes from the game.
        data=bytes.fromhex("610000024e75")
        meta={"schema_version":1,"address_space":"rom_file_offset","rom_sha256":hashlib.sha256(data).hexdigest(),
              "regions":[{"start":0,"end_exclusive":6,"sha256":hashlib.sha256(data).hexdigest()}],
              "validated_calls":[{"pc":0,"target":4}]}
        self.assertEqual(validate(data,meta)["calls"],1)
        meta["validated_calls"][0]["target"]=2
        with self.assertRaises(ValueError):validate(data,meta)
        meta["validated_calls"]=[];meta["regions"][0]["end_exclusive"]=5
        with self.assertRaises(ValueError):validate(data,meta)
        with self.assertRaises(ValueError):validate(data+b"x",meta)

    def test_cfg_rejects_unreviewed_calls_and_mid_instruction_branches(self):
        data=bytes.fromhex("610000024e75")
        rows=[{"address":0,"size":4},{"address":4,"size":2}]
        self.assertEqual(routine_cfg(data,rows,{0:4})["reachable_instructions"],2)
        with self.assertRaises(ValueError):routine_cfg(data,rows,{})
        with self.assertRaises(ValueError):routine_cfg(bytes.fromhex("600000014e75"),rows,{})


class TerrainBuildEvidenceTests(unittest.TestCase):
    def test_stale_builder_harness_lock_or_binary_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);paths={name:root/name for name in ("harness","lock","executable")}
            for path in paths.values():path.write_bytes(b"authored fixture")
            report={key+"_sha256":builder.digest(path) for key,path in paths.items()}
            report["builder_sha256"]=builder.digest(Path(builder.__file__).resolve())
            manifest=root/"report";manifest.write_text(json.dumps(report))
            with patch.multiple(builder,HARNESS=paths["harness"],LOCK=paths["lock"],EXECUTABLE=paths["executable"],REPORT=manifest), \
                 patch.object(builder,"verify_sources"),patch.object(builder,"reject_symlinks"):
                self.assertEqual(builder.verify_executable(),paths["executable"])
                for key in report:
                    changed=dict(report);changed[key]="stale";manifest.write_text(json.dumps(changed))
                    with self.subTest(key=key), self.assertRaises(ValueError):builder.verify_executable()


if __name__ == "__main__": unittest.main()
