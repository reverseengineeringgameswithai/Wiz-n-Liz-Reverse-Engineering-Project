"""Tally goldens, continuous state and explicit unsupported transport paths."""
import subprocess
import sys
import tempfile
from pathlib import Path
from movement_cases import fixture
from tally_cases import case,decode,goldens
from terrain_cases import encode_cases

with tempfile.TemporaryDirectory() as d:
    directory=Path(d);scene,bank=fixture(True)
    (directory/'scene.bin').write_bytes(scene);(directory/'bank.bin').write_bytes(bank)
    cmd=[sys.argv[1],'test.scene',str(directory/'scene.bin'),'test.bank',str(directory/'bank.bin')]
    rows=goldens();p=subprocess.run(cmd+['--tally'],input=encode_cases([c for c,_ in rows]),capture_output=True,timeout=20)
    assert p.returncode==0,p.stderr
    assert decode(p.stdout,len(rows))==[e for _,e in rows]
    initial=case(remaining=1,start=255)
    nextrow=case(remaining=0,skip=65535,tally_countdown=3,credit=3,tracking_x=204,tracking_y=115)
    p=subprocess.run(cmd+['--tally-sequence'],input=encode_cases([initial,nextrow]),capture_output=True,timeout=20)
    assert p.returncode==0,p.stderr
    output=decode(p.stdout,2);assert output[0][-6:]==output[1][-6:]==(0,0,65535,3,3,0)
    for index in (0,1,43,45,61,62,63,64):
        bad=list(nextrow);bad[index]^=1
        p=subprocess.run(cmd+['--tally-sequence'],input=encode_cases([initial,bad]),capture_output=True,timeout=20)
        assert p.returncode==2 and b'continuity mismatch' in p.stderr,p.stderr
    for c,message in ((case(palette_gate=1),b'palette path'),(case(remaining=0,start=255,raw=0x10),b'bonus allocation path'),(case(start=256),b'outside range')):
        p=subprocess.run(cmd+['--tally'],input=encode_cases([c]),capture_output=True,timeout=20)
        assert p.returncode==2 and message in p.stderr,p.stderr
print('tally goldens, continuous actor/counters, drift and unsupported-path rejection passed')
