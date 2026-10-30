"""Native research transport: authored outputs and actor continuity assertions."""
import subprocess
import sys
import tempfile
from pathlib import Path
from movement_cases import fixture
from transition_cases import case,decode,goldens,timer_goldens
from terrain_cases import encode_cases

with tempfile.TemporaryDirectory() as d:
    directory=Path(d);scene,bank=fixture(True)
    (directory/'scene.bin').write_bytes(scene);(directory/'bank.bin').write_bytes(bank)
    command=[sys.argv[1],'test.scene',str(directory/'scene.bin'),'test.bank',str(directory/'bank.bin')]
    for mode,rows in (('--transition',goldens()),('--transition-timer',timer_goldens())):
        p=subprocess.run(command+[mode],input=encode_cases([c for c,_ in rows]),capture_output=True,timeout=20)
        assert p.returncode==0,p.stderr
        assert decode(p.stdout,len(rows))==[e for _,e in rows]
    first=case();second=case(handler=22,direction=1,countdown=1,transition_reload=1,level=14,curve_r=1,curve_g=1,curve_b=2,palette_scope=0,tracking_x=204,tracking_y=115)
    p=subprocess.run(command+['--transition-sequence'],input=encode_cases([first,second]),capture_output=True,timeout=20)
    assert p.returncode==0,p.stderr
    for index in (1,43,45):
        bad=list(second);bad[index]^=1
        p=subprocess.run(command+['--transition-sequence'],input=encode_cases([first,bad]),capture_output=True,timeout=20)
        assert p.returncode==2 and b'continuity mismatch' in p.stderr,p.stderr
    for index in (51,52,53):
        bad=list(first);bad[index]=4
        p=subprocess.run(command+['--transition'],input=encode_cases([bad]),capture_output=True,timeout=20)
        assert p.returncode==2 and not p.stdout and b'invalid transition curve' in p.stderr,p.stderr
print('transition authored transport, timer, continuity and unknown resource rejection passed')
