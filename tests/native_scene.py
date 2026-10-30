"""Headless scene executable checks with authored spatial expectations."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

EXECUTABLE = sys.argv.pop(1)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from bank_atlas import unpack_pam
from scene_reference import check_scene_image
from scene_cases import scene_fixture


class NativeSceneTests(unittest.TestCase):
    def run_scene(self, scene, bank, scene_id="authored.scene"):
        with tempfile.TemporaryDirectory(prefix="scene's fixtures ") as directory:
            a,b = Path(directory)/"scene.bin",Path(directory)/"bank.bin"
            a.write_bytes(scene);b.write_bytes(bank)
            return subprocess.run([EXECUTABLE,scene_id,str(a),"authored.bank",str(b)],capture_output=True,timeout=10)

    def test_all_flips_and_bank_boundary(self):
        scene,bank = scene_fixture()
        result=self.run_scene(scene,bank)
        self.assertEqual(result.returncode,0,result.stderr)
        width,height,rgba=unpack_pam(result.stdout)
        self.assertEqual((width,height),(1024,256))
        colors=[bytes((255,0,0,255)),bytes((0,255,0,255)),bytes((0,0,255,255)),bytes((255,255,0,255))]
        for i,color in enumerate(colors):self.assertEqual(rgba[i*32:i*32+4],color)
        self.assertEqual(check_scene_image(scene,bank,rgba,width,height)["pixels_compared"],262144)
        self.assertEqual(json.loads(result.stderr)["map_cells"],4096)

    def test_invalid_input_has_no_successful_image(self):
        scene,bank=scene_fixture()
        for bad,identifier in ((scene[:-1],"test"),(scene,"../bad"),
                                (scene[:52]+b"\x07\xff"+scene[54:],"test"),
                                (scene[:52]+b"\x20\x00"+scene[54:],"test")):
            result=self.run_scene(bad,bank,identifier)
            self.assertEqual(result.returncode,2)
            self.assertEqual(result.stdout,b"")
            self.assertEqual(json.loads(result.stderr)["status"],"error")


if __name__ == "__main__":unittest.main()
