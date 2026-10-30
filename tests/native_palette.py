"""Palette transport goldens, retained destination and malformed-input rejection."""
import subprocess,sys,tempfile
from pathlib import Path
from movement_cases import fixture
from palette_cases import case,decode,goldens,COMPONENTS,START
from terrain_cases import encode_cases

with tempfile.TemporaryDirectory() as d:
    directory=Path(d);scene,bank=fixture(True)
    (directory/'scene.bin').write_bytes(scene);(directory/'bank.bin').write_bytes(bank)
    cmd=[sys.argv[1],'test.scene',str(directory/'scene.bin'),'test.bank',str(directory/'bank.bin')]
    rows=goldens();p=subprocess.run(cmd+['--palette'],input=encode_cases([c for c,_ in rows]),capture_output=True,timeout=20)
    assert p.returncode==0,p.stderr
    assert decode(p.stdout,len(rows))==[e for _,e in rows]
    initial=case();waiting=case(**START,tracking_x=204,tracking_y=115,components=COMPONENTS)
    ready=case(**(START|dict(direction=0)),tracking_x=204,tracking_y=115,components=COMPONENTS)
    counting=case(**(START|dict(direction=0,handler=25)),tracking_x=204,tracking_y=115,components=COMPONENTS)
    p=subprocess.run(cmd+['--palette-sequence'],input=encode_cases([initial,waiting,ready,counting]),capture_output=True,timeout=20)
    assert p.returncode==0,p.stderr
    out=decode(p.stdout,4);assert [r[0] for r in out]==[26,26,25,25] and [r[-67] for r in out]==[120,120,120,119]
    for index in (0,1,43,45,61,62,63,64,83,100,130):
        bad=list(waiting);bad[index]=24 if index==0 else bad[index]^1
        p=subprocess.run(cmd+['--palette-sequence'],input=encode_cases([initial,bad]),capture_output=True,timeout=20)
        assert p.returncode==2 and b'continuity mismatch' in p.stderr,p.stderr
    for index,value in ((51,4),(67,65536),(83,256),(130,256),(66,256)):
        bad=list(initial);bad[index]=value
        p=subprocess.run(cmd+['--palette'],input=encode_cases([bad]),capture_output=True,timeout=20)
        assert p.returncode==2,p.stderr
    for bad in (initial[:-1],(*initial,1)):
        p=subprocess.run(cmd+['--palette'],input=encode_cases([bad]),capture_output=True,timeout=20);assert p.returncode==2
    p=subprocess.run(cmd+['--palette'],input=encode_cases([case(handler=25,remaining=0,start=255,raw=0x10)]),capture_output=True,timeout=20)
    assert p.returncode==2 and b'bonus allocation path' in p.stderr
print('palette goldens, continuous destination/tally state, drift and malformed-input rejection passed')
