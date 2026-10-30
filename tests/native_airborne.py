"""ROM-free native airborne transport and independently worked state cases."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from airborne_cases import fixture,case,goldens,decode_results
from terrain_cases import encode_cases

EXECUTABLE=Path(sys.argv.pop(1)).resolve()


class AirborneTransport(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup);self.root=Path(temporary.name)
        scene,bank=fixture(True);(self.root/'scene').write_bytes(scene);(self.root/'bank').write_bytes(bank)

    def run_input(self,data):
        return subprocess.run([str(EXECUTABLE),'scene',str(self.root/'scene'),'bank',str(self.root/'bank')],input=data,capture_output=True,timeout=10)

    def test_independent_goldens_and_continuation(self):
        cases=goldens();p=self.run_input(encode_cases([c for c,_ in cases]));self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(decode_results(p.stdout,len(cases)),[e for _,e in cases])

    def test_invalid_state_transport_and_resource(self):
        for data in (b'0 1\n',encode_cases([case(op=7)]),encode_cases([case(update=8)]),encode_cases([case(boost=256)]),
                     encode_cases([case(repeats=17)]),encode_cases([case(op=4,repeats=2)]),encode_cases([case(y=361)])):
            p=self.run_input(data);self.assertEqual(p.returncode,2,p.stderr);self.assertEqual(p.stdout,b'')
        (self.root/'scene').write_bytes(b'bad')
        self.assertEqual(self.run_input(encode_cases([case()])).returncode,2)


if __name__=='__main__':unittest.main()
