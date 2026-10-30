"""Bonus transport goldens, retained tables/gate and failure checks."""
import subprocess,sys,tempfile
from pathlib import Path
from movement_cases import fixture
from bonus_cases import case,decode,goldens,split,CHOICES,ASSIGNED
from terrain_cases import encode_cases

with tempfile.TemporaryDirectory() as d:
    directory=Path(d);scene,bank=fixture(True)
    (directory/'scene.bin').write_bytes(scene);(directory/'bank.bin').write_bytes(bank)
    cmd=[sys.argv[1],'test.scene',str(directory/'scene.bin'),'test.bank',str(directory/'bank.bin')]
    rows=goldens();p=subprocess.run(cmd+['--bonus'],input=encode_cases([c for c,_ in rows]),capture_output=True,timeout=20)
    assert p.returncode==0,p.stderr
    actual=decode(p.stdout,len(rows))
    for i,(a,(_,e)) in enumerate(zip(actual,rows)):assert a==e,(i,a,e)
    initial=case();following=case(assigned=(*CHOICES[:5],*ASSIGNED[5:]),cursor=6,special_gate=65535,world_mode=3,mailbox_count=200,mailbox_parameter=0xf14,mailbox_offset=0x8000,mailbox_bank=30,tracking_x=204,tracking_y=115)
    p=subprocess.run(cmd+['--bonus-sequence'],input=encode_cases([initial,following]),capture_output=True,timeout=20)
    assert p.returncode==0,p.stderr
    output=decode(p.stdout,2);assert len(split(output[0])[3])==5 and not split(output[1])[3]
    for index in (1,43,45,61,62,63,64,65,68,69,79):
        bad=list(following);bad[index]^=1
        p=subprocess.run(cmd+['--bonus-sequence'],input=encode_cases([initial,bad]),capture_output=True,timeout=20)
        assert p.returncode==2 and b'continuity mismatch' in p.stderr,p.stderr
    for c in (case(count=0),case(count=12),case(assigned=(1,)*11),case(count=1,assigned=(1,0,65535)+(0,)*8)):
        p=subprocess.run(cmd+['--bonus'],input=encode_cases([c]),capture_output=True,timeout=20)
        assert p.returncode==2 and not p.stdout,p.stderr
    for c in (initial[:-1],(*initial,1),case(cursor=65536)):
        p=subprocess.run(cmd+['--bonus'],input=encode_cases([c]),capture_output=True,timeout=20);assert p.returncode==2
print('bonus goldens, retained table/gate/cursor, drift and malformed/nonterminating inputs passed')
