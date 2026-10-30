"""ROM-free actor transport, complete outputs and rejection cases."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from actor_cases import fixture,case,goldens,decode_results
from terrain_cases import encode_cases
from presentation_cases import goldens as presentation_goldens,case as presentation_case
from reversal_cases import actor_goldens,effect_goldens,effect_case,decode_actor_rows

EXECUTABLE=Path(sys.argv.pop(1)).resolve()

class ActorTransport(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup);self.root=Path(temporary.name)
        scene,bank=fixture(True);(self.root/'scene').write_bytes(scene);(self.root/'bank').write_bytes(bank)

    def run_input(self,data,mode=None):
        command=[str(EXECUTABLE),'scene',str(self.root/'scene'),'bank',str(self.root/'bank')]
        if mode:command.append(mode)
        return subprocess.run(command,input=data,capture_output=True,timeout=10)

    def test_presentation_goldens_and_unsupported_callback(self):
        rows=presentation_goldens();p=self.run_input(encode_cases([c for c,_ in rows]),'--presentation')
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(decode_results(p.stdout,len(rows)),[e for _,e in rows])
        p=self.run_input(encode_cases([presentation_case(mode=0x85,target=2)]),'--presentation')
        self.assertEqual(p.returncode,2);self.assertEqual(p.stdout,b'')
        self.assertIn(b'unsupported presentation callback',p.stderr)

    def test_scheduled_sequence_retains_actor_instead_of_importing_each_row(self):
        first=presentation_case(mode=0x80,right=1)
        second=presentation_case(handler=3,mode=0x81,first=2,begin=0,end=5,counter=4,reload=4,right=1)
        p=self.run_input(encode_cases([first,second]),'--sequence')
        self.assertEqual(p.returncode,0,p.stderr)
        rows=decode_results(p.stdout,2)
        self.assertEqual(rows[1][1:4],(201,109,8));self.assertEqual(rows[1][11],3)
        corrupted=list(second);corrupted[11]=2
        p=self.run_input(encode_cases([first,corrupted]),'--sequence')
        self.assertEqual(p.returncode,2);self.assertIn(b'continuity mismatch',p.stderr)
        self.assertEqual(len(p.stdout.splitlines()),1)

    def test_independent_goldens(self):
        rows=goldens();p=self.run_input(encode_cases([c for c,_ in rows]));self.assertEqual(p.returncode,0,p.stderr)
        actual=decode_results(p.stdout,len(rows))
        for i,((c,e),a) in enumerate(zip(rows,actual)):
            with self.subTest(case=i,input=c):self.assertEqual(a,e)

    def test_rejections(self):
        for c in (case(handler=0),case(handler=21),case(callback=12),case(jump=256),case(repeats=17),
                  case(y=361),case(up=1),case(handler=5,left=1),case(handler=6,right=1)):
            p=self.run_input(encode_cases([c]));self.assertEqual(p.returncode,2,p.stderr);self.assertEqual(p.stdout,b'')
        self.assertEqual(self.run_input(b'1 2\n').returncode,2)

    def test_action_goldens_and_modes(self):
        from actions_cases import goldens, presentation_goldens, scheduled_goldens, decode, case
        for mode,rows in (('--actions',goldens()),('--actions-presentation',presentation_goldens()),('--actions-scheduled',scheduled_goldens())):
            with self.subTest(mode=mode):
                p=self.run_input(encode_cases([c for c,_ in rows]),mode)
                self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(decode(p.stdout,len(rows)),[e for _,e in rows])
        for c in (case(raw=256),case(world_mode=65536),case(interval=65536)):
            p=self.run_input(encode_cases([c]),'--actions');self.assertEqual(p.returncode,2);self.assertEqual(p.stdout,b'')

    def test_action_sequence_asserts_continuity(self):
        from actions_cases import case,decode
        first=case(mode=128,up=1)
        second=case(handler=16,mode=133,first=30,begin=30,end=35,target=34,counter=3,reload=3,callback=9,up=1,raw=0)
        p=self.run_input(encode_cases([first,second]),'--actions-sequence')
        self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(decode(p.stdout,2)[1][-3:],(0,200,0xf14))
        p=self.run_input(encode_cases([first,first]),'--actions-sequence')
        self.assertEqual(p.returncode,2);self.assertIn(b'continuity mismatch',p.stderr)

    def test_dispatch_goldens_and_tracking_continuity(self):
        from dispatch_cases import case,decode,goldens
        rows=goldens();p=self.run_input(encode_cases([c for c,_ in rows]),'--dispatch')
        self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(decode(p.stdout,len(rows)),[e for _,e in rows])
        first=case(handler=20,mode=128)
        second=case(handler=20,mode=128,tracking_x=204,tracking_y=115)
        p=self.run_input(encode_cases([first,second]),'--dispatch-sequence');self.assertEqual(p.returncode,0,p.stderr)
        p=self.run_input(encode_cases([first,first]),'--dispatch-sequence')
        self.assertEqual(p.returncode,2);self.assertIn(b'tracking sequence continuity',p.stderr)
        for c in (case(service=2),case(tracking_selector=65536),case(tracking_x=65536),case(handler=20,mode=128,service=0)):
            p=self.run_input(encode_cases([c]),'--dispatch');self.assertEqual(p.returncode,2);self.assertEqual(p.stdout,b'')

    def test_reversal_goldens(self):
        rows=actor_goldens();p=self.run_input(encode_cases([c for c,_ in rows]),'--reversal')
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(decode_actor_rows(p.stdout,len(rows)),[e for _,e in rows])

    def test_effect_goldens_and_ownership(self):
        rows=effect_goldens();p=self.run_input(encode_cases([c for c,_ in rows]),'--effect')
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual([tuple(map(int,l.split())) for l in p.stdout.splitlines()],[e for _,e in rows])
        for c in (effect_case(supplied_owner=2),effect_case(owner=0),effect_case(side=2),effect_case(mode=256),effect_case(repeats=257)):
            p=self.run_input(encode_cases([c]),'--effect');self.assertEqual(p.returncode,2);self.assertEqual(p.stdout,b'')

    def test_effect_sequence_does_not_reseed(self):
        first=effect_case();second=effect_case(x=322,counter=1,owner_x=301)
        p=self.run_input(encode_cases([first,second]),'--effect-sequence');self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(tuple(map(int,p.stdout.splitlines()[1].split()))[2:4],(323,100))
        p=self.run_input(encode_cases([first,first]),'--effect-sequence')
        self.assertEqual(p.returncode,2);self.assertIn(b'continuity mismatch',p.stderr)

if __name__=='__main__':unittest.main()
