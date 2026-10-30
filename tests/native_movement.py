"""ROM-independent semantic and transport tests for native movement."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from movement_cases import fixture,case,goldens,decode_results
from terrain_cases import encode_cases

EXECUTABLE=Path(sys.argv.pop(1)).resolve()


class MovementTransport(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup);self.root=Path(temporary.name)
        scene,bank=fixture(True);(self.root/"scene").write_bytes(scene);(self.root/"bank").write_bytes(bank)

    def run_input(self,data):
        return subprocess.run([str(EXECUTABLE),"scene",str(self.root/"scene"),"bank",str(self.root/"bank")],input=data,capture_output=True,timeout=10)

    def test_independent_goldens(self):
        cases=goldens();p=self.run_input(encode_cases([c for c,_ in cases]));self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(decode_results(p.stdout,len(cases)),[e for _,e in cases])

    def test_all_signed_speeds_damping_and_clamps(self):
        cases=[case(op=op,speed=v) for op in (3,4,5,6) for v in range(65536)]
        p=self.run_input(encode_cases(cases));self.assertEqual(p.returncode,0,p.stderr)
        for c,row in zip(cases,decode_results(p.stdout,len(cases))):
            signed=c[3] if c[3]<32768 else c[3]-65536
            if c[0] in (3,4):
                decrement=4 if c[0]==3 else 1
                expected=max(0,abs(signed)-decrement)*(1 if signed>=0 else -1)
            elif c[0]==5:expected=min(signed,192)
            else:expected=max(signed,-192)
            self.assertEqual(row[2],expected%65536)

    def test_bad_case_and_resource_rejected(self):
        for data in (encode_cases([case(op=8)]),encode_cases([case(repeats=0)]),encode_cases([case(x=65536)]),
                     b"0 1 2\n",encode_cases([case(y=361)])):
            p=self.run_input(data);self.assertEqual(p.returncode,2);self.assertEqual(p.stdout,b"")
        (self.root/"scene").write_bytes(b"bad")
        self.assertEqual(self.run_input(encode_cases([case()])).returncode,2)


if __name__=="__main__":unittest.main()
