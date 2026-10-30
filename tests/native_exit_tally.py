"""Exit tally transport goldens, unsupported score and continuous marker checks."""
import subprocess,sys,tempfile
from pathlib import Path
from movement_cases import fixture
from exit_tally_cases import case,decode,goldens
from terrain_cases import encode_cases
with tempfile.TemporaryDirectory() as d:
    root=Path(d);scene,bank=fixture(True);(root/'scene.bin').write_bytes(scene);(root/'bank.bin').write_bytes(bank)
    cmd=[sys.argv[1],'test.scene',str(root/'scene.bin'),'test.bank',str(root/'bank.bin')]
    rows=goldens();p=subprocess.run(cmd+['--exit-tally'],input=encode_cases([c for c,_ in rows]),capture_output=True,timeout=20);assert p.returncode==0,p.stderr
    for a,(_,e) in zip(decode(p.stdout,len(rows)),rows):assert a==e,(a,e)
    initial=case(remaining=1,start=255);second=case(remaining=0,skip=65535,credit=3,tally_countdown=60,tracking_x=204,tracking_y=115)
    p=subprocess.run(cmd+['--exit-tally-sequence'],input=encode_cases([initial,second]),capture_output=True,timeout=20);assert p.returncode==0,p.stderr
    assert decode(p.stdout,2)[1][0]==28
    for index in (1,43,45,61,62,63,64,69):
        bad=list(second);bad[index]^=1;p=subprocess.run(cmd+['--exit-tally-sequence'],input=encode_cases([initial,bad]),capture_output=True,timeout=20)
        assert p.returncode==2 and b'continuity mismatch' in p.stderr,p.stderr
    for c in (case(remaining=0,secondary_gate=1,secondary_remaining=1),case(marker=65536),initial[:-1],(*initial,0)):
        p=subprocess.run(cmd+['--exit-tally'],input=encode_cases([c]),capture_output=True,timeout=20);assert p.returncode==2 and not p.stdout,p.stderr
print('exit tally goldens, sequence assertions, malformed and unsupported-path rejections passed')
