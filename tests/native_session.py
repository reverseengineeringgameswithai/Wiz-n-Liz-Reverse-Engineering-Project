"""Session transport accepts one seed, then physical held sets only."""
from pathlib import Path
import subprocess
import sys
import tempfile
from movement_cases import fixture
from actor_cases import case
from terrain_cases import encode_cases

exe=sys.argv[1]
p=subprocess.run([exe,'--pad'],input=b'255\n0\n191\n231\n',capture_output=True,timeout=10)
assert p.returncode==0,p.stderr
assert [tuple(map(int,r.split())) for r in p.stdout.splitlines()]==[
    (255,0,0,0,0,0,0,0,0,0,0,0),(0,255,255,255,0,0,0,0,255,255,255,255),
    (191,255,0,255,0,0,0,0,255,0,0,0),(231,255,255,0,0,0,0,255,0,255,0,0)]
for data in (b'256\n',b'-1\n',b'0 1\n',b'x\n'):
    p=subprocess.run([exe,'--pad'],input=data,capture_output=True,timeout=10);assert p.returncode==2 and not p.stdout
with tempfile.TemporaryDirectory() as d:
    path=Path(d);scene,bank=fixture(True)
    (path/'scene').write_bytes(scene);(path/'bank').write_bytes(bank)
    cmd=[exe,'test.scene',str(path/'scene'),'test.bank',str(path/'bank')]
    actor=case(mode=128,first=2,begin=0,end=5,counter=4,reload=4,target=0,cycles=0)
    seed=(*actor[:25],actor[31],*actor[32:34],1,0,0,0)
    rows=[seed,(8,),(8,),(40,),(8,)]
    p=subprocess.run(cmd,input=encode_cases(rows),capture_output=True,timeout=10);assert p.returncode==0,p.stderr
    result=[tuple(map(int,r.split())) for r in p.stdout.splitlines()]
    assert [r[0] for r in result]==[1,2,3,4]
    assert [r[1] for r in result]==[3,3,1,1] and [r[5] for r in result]==[0,0,29,25]
    assert result[2][39]==2 and result[2][40:]==(60,1,192,1,107,1,192,2)
    for tail in (b'256\n',b'8 8\n',b'128\n',b'1\n'):
        p=subprocess.run(cmd,input=encode_cases([seed])+tail,capture_output=True,timeout=10);assert p.returncode==2 and not p.stdout
    p=subprocess.run(cmd,input=encode_cases([seed]+[(0,)]*601),capture_output=True,timeout=10)
    assert p.returncode==2 and b'invocation budget' in p.stderr and len(p.stdout.splitlines())==600
print('pad goldens, one-seed button session, malformed/unsupported inputs and invocation cap passed')
for data,expected in [(b'0 0 6 77 99\n',(77,6,0,58112,1,1,58168)),(b'3 55 65535 77 99\n',(77,65535,7,57216,0,0,0))]:
    p=subprocess.run([exe,'--banner'],input=data,capture_output=True,timeout=10)
    assert p.returncode==0 and tuple(map(int,p.stdout.split()))==expected,(p.stdout,p.stderr)
for data in (b'4 0 6 0 0\n',b'0 65536 6 0 0\n',b'0 0 6 0 0 1\n'):
    p=subprocess.run([exe,'--banner'],input=data,capture_output=True,timeout=10);assert p.returncode==2 and not p.stdout
with tempfile.TemporaryDirectory() as d:
    path=Path(d);scene,bank=fixture(True);(path/'scene').write_bytes(scene);(path/'bank').write_bytes(bank)
    cmd=[exe,'test.scene',str(path/'scene'),'test.bank',str(path/'bank'),'--level-banner']
    p=subprocess.run(cmd,input=encode_cases([(*seed,0,0,6),(8,),(40,)]),capture_output=True,timeout=10)
    assert p.returncode==0,p.stderr
    result=[tuple(map(int,r.split())) for r in p.stdout.splitlines()]
    assert len(result)==2 and all(r[-5:]==(0,58112,1,1,58168) for r in result)
    assert all(len(r)==45+4*r[39] for r in result)
print('banner request transport, bounds and retained banner session passed')
with tempfile.TemporaryDirectory() as d:
    path=Path(d);scene,bank=fixture(True);(path/'scene').write_bytes(scene);(path/'bank').write_bytes(bank)
    cmd=[exe,'test.scene',str(path/'scene'),'test.bank',str(path/'bank'),'--reversal-session']
    for right in (False,True):
        owned=list(seed)+[0,0,6,1]
        owned[0]=5 if right else 6;owned[3]=160 if right else 65376
        owned[6]=2048 if right else 0
        p=subprocess.run(cmd,input=encode_cases([owned,(4 if right else 8,)]+[(0,)]*12),capture_output=True,timeout=10)
        assert p.returncode==0,p.stderr
        result=[tuple(map(int,r.split())) for r in p.stdout.splitlines()]
        effects=[]
        for i,r in enumerate(result):
            offset=45+4*r[39]
            assert r[offset]==int(i>=11) and r[offset+1]==int(i==0)
            offset+=2
            if i==0:
                assert r[offset:offset+2]==(0,1);offset+=2
            assert r[offset]==int(i<12);offset+=1
            assert len(r)==offset+15*int(i<12)
            if i<12:
                e=r[offset:];effects.append(e)
                assert e[:4]==(0,1,1,0 if right else 1)
                assert e[4]==(r[2]+(22 if right else -6))%65536
                assert e[5]==(124 if right else 125) and e[-1]==int(i==11)
        assert effects[0][11]==1 and effects[-1][7]==0
        for capacity,reason in ((0,b'allocation exhausted'),(4097,b'storage budget')):
            owned[-1]=capacity
            p=subprocess.run(cmd,input=encode_cases([owned,(4 if right else 8,)]),capture_output=True,timeout=10)
            assert p.returncode==2 and not p.stdout and reason in p.stderr
print('one-seed reversal session, same-call birth/release, both facings and capacity failures passed')
# The scene between levels on the synthetic terrain: 60E6's doors over an empty
# pool (numbers in 44/45 ... door 0 in 67), then three loops of countdown.
from hub_cases import records as hub_records
with tempfile.TemporaryDirectory() as d:
    path=Path(d);scene,bank=fixture(True);(path/'scene').write_bytes(scene);(path/'bank').write_bytes(bank)
    cmd=[exe,'test.scene',str(path/'scene'),'test.bank',str(path/'bank'),'--hub-session']
    rows=[seed,(65535,10,1,0,1,1,2,0,48,0,48,0,0,7),(0,0,0,*hub_records()),(68,*range(68)),(1023,0,0,0,0),(0,),(0,),(0,)]
    p=subprocess.run(cmd,input=encode_cases(rows),capture_output=True,timeout=10);assert p.returncode==0,p.stderr
    result=[tuple(map(int,r.split())) for r in p.stdout.splitlines()];assert len(result)==4,result
    setup=result[0];assert setup[:45]==(44,*range(44)) and setup[-9:]==(0,)*8+(65535,),setup[:50]
    assert setup[45:65]==(44,128,0x408,0x5a,0xc9,0,0,0,0,0,0,0,0x12646,0x12646,0,0,0,0,0,0),setup[45:65]
    door=setup[45+20*2:45+20*3];assert door[:2]==(46,0x81) and door[10]==0x3c and door[12]==0x61f6,door
    for k,r in enumerate(result[1:]):
        n=r[39];tail=r[40+4*n:];assert tail[7:11]==(0,48,0,0) and tail[11]==0,tail[:12]
        image=tail[12:];assert image[:45]==(44,*range(44))
        assert image[45+20*2:45+20*3][10]==0x3c-1-k,image[45+40:45+60]
    p=subprocess.run(cmd[:-1]+['--game-session'],input=encode_cases(rows),capture_output=True,timeout=10)
    assert p.returncode==2 and not p.stdout and b'usage' in p.stderr,p
print('hub session setup, door countdowns and the game session usage boundary passed')
