"""Native coasting transport and a continuous initializer-to-wrapper sequence."""
import subprocess
import sys
import tempfile
from pathlib import Path
from movement_cases import fixture
from coasting_cases import case,decode,goldens,entry_goldens
from terrain_cases import encode_cases

with tempfile.TemporaryDirectory() as d:
    directory=Path(d);scene,bank=fixture(True)
    (directory/'scene.bin').write_bytes(scene);(directory/'bank.bin').write_bytes(bank)
    cmd=[sys.argv[1],'test.scene',str(directory/'scene.bin'),'test.bank',str(directory/'bank.bin')]
    for mode,rows in (('--coast-entry',entry_goldens()),('--transition',goldens())):
        p=subprocess.run(cmd+[mode],input=encode_cases([c for c,_ in rows]),capture_output=True,timeout=20)
        assert p.returncode==0,p.stderr
        assert decode(p.stdout,len(rows))==[e for _,e in rows]
    initial=case(handler=7,mode=0,speed=1)
    first=case(first=541,speed=1,tracking_selector=65535)
    second=case(first=541,x=201,y=108,speed=0,tracking_selector=65535,tracking_x=0xff80,tracking_y=0xff80,sx=85,sy=4)
    p=subprocess.run(cmd+['--coast-sequence'],input=encode_cases([initial,first,second]),capture_output=True,timeout=20)
    assert p.returncode==0,p.stderr
    rows=decode(p.stdout,3);assert rows[0][1:4]==(200,109,1) and rows[1][1:4]==(201,108,0) and rows[2][1:4]==(201,108,0)
    for index in (0,1,8,43,45):
        bad=list(first);bad[index]^=1
        p=subprocess.run(cmd+['--coast-sequence'],input=encode_cases([initial,bad]),capture_output=True,timeout=20)
        assert p.returncode==2 and b'continuity mismatch' in p.stderr,p.stderr
print('coasting entry/update goldens, deferred sequence and continuity rejection passed')
