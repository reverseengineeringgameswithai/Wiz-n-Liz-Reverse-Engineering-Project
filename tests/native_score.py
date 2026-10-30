"""Authored score transport expectations and retained-state assertions."""
import subprocess,sys,tempfile
from pathlib import Path
from movement_cases import fixture
from score_cases import case,decode,goldens
from terrain_cases import encode_cases
with tempfile.TemporaryDirectory() as d:
    root=Path(d);scene,bank=fixture(True);(root/'scene.bin').write_bytes(scene);(root/'bank.bin').write_bytes(bank)
    cmd=[sys.argv[1],'test.scene',str(root/'scene.bin'),'test.bank',str(root/'bank.bin')]
    rows=goldens();p=subprocess.run(cmd+['--score'],input=encode_cases([c for c,e in rows]),capture_output=True,timeout=20);assert p.returncode==0,p.stderr
    assert decode(p.stdout,len(rows))==[e for c,e in rows]
    a=case();b=case(secondary_remaining=1,tally_countdown=3,score=0x10000,score_scratch=0x10000,tracking_x=204,tracking_y=115)
    p=subprocess.run(cmd+['--score-sequence'],input=encode_cases([a,b]),capture_output=True,timeout=20);assert p.returncode==0,p.stderr
    for i in (68,72,73,74,75,76):
        bad=list(b);bad[i]^=1;p=subprocess.run(cmd+['--score-sequence'],input=encode_cases([a,bad]),capture_output=True,timeout=20)
        assert p.returncode==2 and b'continuity mismatch' in p.stderr,p.stderr
    for row in (case(score=0xa),case(threshold=0,increment=0),case(rewards=65536),a[:-1],(*a,0)):
        p=subprocess.run(cmd+['--score'],input=encode_cases([row]),capture_output=True,timeout=20);assert p.returncode==2 and not p.stdout,p.stderr
print('score goldens, sequence assertions, malformed data and loop-budget rejection passed')
