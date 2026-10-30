"""Native terrain transport checks, independent of ROM and reference tooling."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from terrain_cases import fixture, golden_cases, encode_cases, decode_results

EXECUTABLE = Path(sys.argv.pop(1)).resolve()


class TerrainTransport(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        scene, bank = fixture()
        (self.root / "scene").write_bytes(scene); (self.root / "bank").write_bytes(bank)

    def run_cases(self, content):
        return subprocess.run([str(EXECUTABLE),"test.scene",str(self.root/"scene"),"test.bank",str(self.root/"bank")],
                              input=content,capture_output=True,timeout=10,env=os.environ)

    def test_independent_goldens(self):
        cases = golden_cases()
        p = self.run_cases(encode_cases([c for c,_ in cases]))
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(decode_results(p.stdout,len(cases)), [expected for _,expected in cases])

    def test_all_byte_comparisons(self):
        # At row zero first 32 cells hold the 256 possible unsigned byte values.
        cases = [(2,116+value,105+within-1,0,0) for value in range(256) for within in range(1,9)]
        p = self.run_cases(encode_cases(cases)); self.assertEqual(p.returncode,0,p.stderr)
        for c,row in zip(cases,decode_results(p.stdout,len(cases))):
            lhs,rhs = c[2]-104,c[1]-116
            signed_lhs = lhs
            signed_rhs = rhs if rhs < 128 else rhs-256
            unsigned_result = (lhs-rhs)%256
            overflow = not -128 <= signed_lhs-signed_rhs <= 127
            flags = (8 if unsigned_result>=128 else 0)+(4 if lhs==rhs else 0)+(2 if overflow else 0)+(1 if lhs<rhs else 0)
            self.assertEqual(row[4:7],(rhs,lhs,flags))

    def test_invalid_address_and_transport(self):
        for payload in (b"0 128 384 0 0\n",b"0 128 1152 0 0\n",b"0 128 32895 0 0\n",b"5 0 0 0 0\n",
                        b"0 65536 0 0 0\n",b"0 0 0 0\n",b"0 128 128 0 0 extra\n",b"-1 0 0 0 0\n"):
            with self.subTest(payload=payload):
                p=self.run_cases(payload); self.assertEqual(p.returncode,2); self.assertEqual(p.stdout,b"")

    def test_malformed_resources(self):
        (self.root/"scene").write_bytes(b"truncated")
        p=self.run_cases(b"0 128 128 0 0\n")
        self.assertEqual(p.returncode,2); self.assertEqual(p.stdout,b"")


if __name__ == "__main__": unittest.main()
