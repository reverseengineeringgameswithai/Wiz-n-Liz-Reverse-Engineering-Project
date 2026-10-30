import json
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from scene_probe import inspect_scene
from scene_preview import validate_metadata
from scene_cases import scene_fixture
from rnc import RncError


class SceneTests(unittest.TestCase):
    def test_exact_partition_and_record_count(self):
        scene, _ = scene_fixture()
        r = inspect_scene(scene)
        self.assertEqual(r["coordinate_count"], 1)
        self.assertEqual(r["additional_pattern_count"], 1)
        self.assertEqual(r["regions"]["patterns"]["range"], [16,48])
        self.assertEqual(r["regions"]["map"]["range"], [52,8244])
        self.assertEqual(r["regions"]["opaque_records"]["range"], [8244,8252])
        self.assertEqual(sum(v["size_bytes"] for v in r["regions"].values()), len(scene))
        self.assertEqual(r["maximum_relative_pattern_index"], 1)
        self.assertEqual(r["raw_attribute_counts"], {0:4093, 0x0800:1, 0x1000:1, 0x9800:1})
        self.assertIsNone(r["coordinate_purpose"])

    def test_truncation_extra_and_large_counts_rejected(self):
        scene,_ = scene_fixture()
        for cut in (0,1,2,5,13,15,16,47,51,52,8243,8251):
            with self.subTest(cut=cut), self.assertRaises(ValueError):
                inspect_scene(scene[:cut])
        for data in (scene+b"x", b"\xff\xff", scene[:14]+b"\xff\xff"+scene[16:]):
            with self.assertRaises(ValueError):
                inspect_scene(data)
        with self.assertRaises(ValueError): inspect_scene(scene,max_coordinates=0)
        with self.assertRaises(ValueError): inspect_scene(scene,max_patterns=0)

    def test_unsupported_dimensions_fail_explicitly(self):
        scene,_ = scene_fixture()
        for shape in ((64,64),(128,0),(0,32)):
            with self.assertRaisesRegex(ValueError,"unsupported scene shape"):
                inspect_scene(scene[:48]+struct.pack(">HH",*shape)+scene[52:])

    def test_metadata_is_strict(self):
        scene_entry = {"id":"scene", "structure":{"coordinate_count":1,"additional_pattern_count":1}}
        base_entry = {"id":"base", "structure":{"record_count":1}}
        good = dict(status="ok",schema_version=1,renderer="wiznliz-scene-preview",logical_id="scene",
                    base_bank_id="base",coordinates=1,additional_patterns=1,base_patterns=1,map_cells=4096,
                    width=1024,height=256,single_plane=True,palette_policy="normal-rgb3-rounded-v1")
        validate_metadata(good,scene_entry,base_entry,1024,256)
        for field,value in (("coordinates",True),("single_plane",1),("base_bank_id","wrong")):
            with self.assertRaises(RncError):validate_metadata(good|{field:value},scene_entry,base_entry,1024,256)


if __name__ == "__main__": unittest.main()
