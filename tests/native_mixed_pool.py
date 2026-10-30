"""Authored mixed-pool transport and one-seed-only boundary checks."""
from pathlib import Path
import subprocess
import sys
import tempfile
from movement_cases import fixture
from actor_cases import case
from trail_cases import case as trail
from private_cases import case as private
from table_motion_cases import case as table
from collision_cases import case as collision
from return_only_cases import case as passive
from terrain_cases import encode_cases
exe=sys.argv[1]
with tempfile.TemporaryDirectory() as d:
    p=Path(d);scene,bank=fixture(True);(p/'scene').write_bytes(scene);(p/'bank').write_bytes(bank)
    cmd=[exe,'test.scene',str(p/'scene'),'test.bank',str(p/'bank'),'--mixed-session']
    actor=case(x=65534,y=100,mode=0,cycles=0)
    seed=(*actor[:25],actor[31],*actor[32:34],1,0,0,0,0,0,6)
    emitter=(4,*trail(random=1)[:22])
    prefix=[seed,(3,1,1,99),(0,),(0,),emitter,(1,)]
    def run(rows):return subprocess.run(cmd,input=encode_cases(rows),capture_output=True,timeout=10)
    r=run(prefix+[(0,),(0,)]);assert r.returncode==0,r.stderr
    rows=[tuple(map(int,l.split())) for l in r.stdout.splitlines()]
    assert len(rows)==2 and rows[0][0]==1 and rows[1][0]==2
    spawn=(0,0,1,3,96,197,0,133,227,227,234,2,2,234)
    first_emitter=(1,1,1,4,90,100,3,2,100,10,20,30,40,50,60,70,80,129,638,638,643,4,5,0,2048,1)
    assert rows[0][45:]==(0,258,258,2,*spawn,*first_emitter),rows[0][45:]
    # The earlier-slot child receives its first update on the second invocation.
    assert rows[1][45:63]==(0,258,258,2,1,0,1,3,96,197,0,133,227,227,234,1,2,234),rows[1][45:]
    obj=(5,*private(countdown=0,y=0)[:13]);head=(1,0,1,99,65536,0,0)
    r=run([seed,head,(),obj,(0,),(0,)])
    assert r.returncode==0,r.stderr
    result=[tuple(map(int,l.split())) for l in r.stdout.splitlines()]
    expected=list(obj);expected[3]=65535;expected[9]=1;expected[12]=8
    assert result[0][45:]==(0,1,99,1,1,0,1,*expected),result[0][45:]
    expected[6]=8;expected[9]=2;expected[12]=7
    assert result[1][45:]==(0,1,99,1,1,0,1,*expected),result[1][45:]
    obj_table=(6,*table(countdown=0,x=0,y=65535)[:15]);head_table=(1,0,1,99,0,0,0,0)
    r=run([seed,head_table,(),obj_table,(0,),(0,)])
    assert r.returncode==0,r.stderr
    result=[tuple(map(int,l.split())) for l in r.stdout.splitlines()]
    expected=list(obj_table);expected[1]=65535;expected[2]=0;expected[8]=1;expected[11]=28;expected[13]=1;expected[14]=1;expected[15]=1
    assert result[0][45:]==(0,1,99,1,1,0,1,*expected),result[0][45:]
    expected[5]=8;expected[8]=2;expected[15]=0
    assert result[1][45:]==(0,1,99,1,1,0,1,*expected),result[1][45:]
    probe=(7,*collision()[:14]);head_collision=(*head_table,1023,0,0,0,0)
    r=run([seed,head_collision,(),probe,(0,),(0,)])
    assert r.returncode==0,r.stderr
    result=[tuple(map(int,l.split())) for l in r.stdout.splitlines()]
    assert all(row[45:]==(0,1,99,1,1,0,1,*probe) for row in result),result
    dormant=(8,*passive(mode=5,counter=1,target=921)[:12]);active=(8,*passive(counter=1)[:12])
    head_passive=(3,1,1,99)
    r=run([seed,head_passive,(2,),dormant,active,(0,),(0,)])
    assert r.returncode==0,r.stderr
    result=tuple(map(int,r.stdout.split()));advanced=list(active);advanced[5]=916;advanced[8]=5
    assert result[45:]==(1,2,1,99,2,3,0,1,*dormant,1,1,1,*advanced),result[45:]
    # Size-14 header retains FF31C0 as a logical identity and prints it after RNG.
    # A tag-9 free slot carries verified inherited fields without occupancy.
    for free_row in ((0,),(9,0,0,0),(9,921,7,1)):
        r=run([seed,(3,1,1,99,0,0,0,0,1023,0,0,0,0,2),(2,),dormant,active,free_row,(0,)])
        assert r.returncode==0,r.stderr
        result=tuple(map(int,r.stdout.split()))
        assert result[45:]==(1,2,1,99,1,1,1,2,3,0,1,*dormant,1,1,1,*advanced),result[45:]
    # The anchor field extends, and must not drop, the thirteen-field collision context.
    r=run([seed,(2,0,1,99,0,0,0,0,1023,0,0,0,0,2),(),probe,active,(0,)])
    assert r.returncode==0,r.stderr
    assert tuple(map(int,r.stdout.split()))[45:]==(0,1,99,1,1,1,2,1,0,1,*probe,1,1,1,*advanced),r.stdout
    r=run([seed,(*head_collision,0),(),probe,(0,)])
    assert r.returncode==0 and tuple(map(int,r.stdout.split()))[45:]==(0,1,99,0,0,0,1,1,0,1,*probe),(r.stdout,r.stderr)
    r=run([seed,(3,1,1,99,0,0,0,0,1023,0,0,0,0,0),(2,),dormant,active,(0,),(0,)])
    assert r.returncode==0 and tuple(map(int,r.stdout.split()))[45:52]==(1,2,1,99,0,0,0),r.stdout
    for bad in [[seed,(2,0,1,99,0,0,0,0,1023,0,0,0,0,1),(),probe,active,(0,)],
                [seed,(3,1,1,99,0,0,0,0,1023,0,0,0,0,3),(2,),dormant,active,(0,),(0,)],
                [seed,(3,1,1,99,0,0,0,0,1023,0,0,0,0,4),(2,),dormant,active,(0,),(0,)],
                [seed,(3,1,1,99,0,0,0,0,1023,0,0,0,0,2),(0,),(0,),emitter,(1,),(1,)],
                [seed,(3,1,1,99,0,0,0,0,1023,0,0,0,0,2,0),(2,),dormant,active,(0,),(0,)],
                [seed,(3,1,1,99),(2,),dormant,active,(9,0,0),(0,)],
                [seed,(3,1,1,99),(2,),dormant,active,(9,65536,0,0),(0,)],
                [seed,(3,1,1,99),(),dormant,active,(9,0,0,0),(0,)],
                [seed,(1,1,1,99),(0,),dormant,(0,)],
                [seed,(1,0,1,99),(),(8,*passive(mode=0x85,counter=1,target=921)[:12]),(0,)],
                [seed,(1,0,1,99),(),(*dormant,0),(0,)],
                [seed,(1,0,1,99),(),(*dormant[:4],256,*dormant[5:]),(0,)],
                [seed,head_table,(),probe,(0,)],
                [seed,(*head_table,65536,0,0,0,0),(),probe,(0,)],
                [seed,(*head_table,1023,65536,0,0,0),(),probe,(0,)],
                [seed,(*head_table,1023,1,0,0,0),(),probe,(0,)],
                [seed,(*head_table,1023,1,1,150,262),(),probe,(0,)],
                [seed,(*head_table,1023,0,2,0,0),(),probe,(0,)],
                [seed,(*head_table,1023,0,0,1,0),(),probe,(0,)],
                [seed,head_collision,(),(*probe[:-1],65536),(0,)],
                [seed,(1,0,1,99,0,0,0),(),obj_table,(0,)],
                [seed,(*head_table[:7],65536),(),obj_table,(0,)],
                [seed,(*head_table[:7],4096),(),obj_table,(0,)],
                [seed,head_table,(),(*obj_table[:13],24,*obj_table[14:]),(0,)],
                [seed,(1,0,1,99),(),obj,(0,)], [seed,(1,0,1,99,0,65536,0),(),obj,(0,)],
                [seed,head,(),(5,99,*obj[2:]),(0,)], [seed,head,(),obj,(0,0)], prefix+[(0,1)],prefix+[(1,)],prefix+[(128,)],
                [seed,(4097,0,0,0)], [seed,(3,2,1,99),(0,0),(0,),emitter,(1,)],
                [seed,(3,1,1,99),(2,),(0,),emitter,(1,)],
                [seed,(1,0,0,0),(),(99,)], [seed,(1,0,0,0),(),(4,*trail()[:21],2),(0,)]]:
        r=run(bad);assert r.returncode==2 and not r.stdout,(bad,r.stdout,r.stderr)
    # --world-session: the retained world's setup and two supplied loops (equal to
    # --world-pool's lines on the same rows), then P1 natively for two frames;
    # the second applies two external E918 calls and P1's message update.
    from world_cases import world_input, phase, phase_line
    world=world_input([phase(),phase(calls=1)])
    pool=subprocess.run([str(Path(exe).parent/'wiznliz-collision'),'--world-pool'],input=encode_cases(world),capture_output=True,timeout=10);assert pool.returncode==0,pool.stderr
    expect=[tuple(map(int,l.split())) for l in pool.stdout.splitlines()]
    frames=[(0,0,0,0,0,0,0,0,0,0),(0,2,1,0,100,12,0,0,0,0)]
    # A level-start fade timer: negative direction, countdown 1, reload 1, level 12,
    # retained curves, FF4446/48 (0,30), FF0732/34 (0,0) and the action globals.
    timer=(0xffff,1,1,12,0,0,0,0,0x30,0,0,0,0,0)
    session=[seed,timer,world[0][:2],*world[1:-2],(1023,0,0,0,0),(2,),*world[-2:],*frames]
    def world_run(rows):return subprocess.run(cmd[:-1]+['--world-session'],input=encode_cases(rows),capture_output=True,timeout=10)
    r=world_run(session);assert r.returncode==0,r.stderr
    out=[tuple(map(int,l.split())) for l in r.stdout.splitlines()];assert len(out)==5 and out[:3]==expect,out[:3]
    loops=[(o[0],phase_line(o[40+4*o[39]+15:])) for o in out[3:]]
    # 1345A runs before the banner: the countdown ends, then level 12 steps to 14;
    # the curves, saved position and FF33E0 stay as seeded.
    assert [o[40+4*o[39]+5:40+4*o[39]+15] for o in out[3:]]==[(0xffff,0,1,12,0,0,0,0,0,0),(0xffff,1,1,14,0,0,0,0,0,0)],out[3:]
    assert [n for n,_ in loops]==[1,2] and loops[0][1][1]['random']==(65536,65536) and loops[1][1][1]['random']==(0x01020001,0x01020001),loops
    assert loops[0][1][1]['messages'][0]==(1,0x64,3) and loops[1][1][1]['messages'][0]==(0,100,12),loops
    for bad,why in (([*session[:-1],frames[1][:9]],'incomplete'),([*session[:-1],(0,65,*frames[1][2:])],'E918'),([*session[:-1],(0,0,2,0,0,0,0,0,0,0)],'presence')):
        r=world_run(bad);assert r.returncode==2 and r.stdout.count(b'\n')==4 and why in r.stderr.decode(),(bad,r.stderr)
    for bad in ([seed,session[1],world[0],*session[3:]],[seed,timer[:-1],*session[2:]],[seed,(65536,*timer[1:]),*session[2:]],[seed,(*timer[:4],4,*timer[5:]),*session[2:]],[*session[:-5],(2,0),*session[-4:]],[*session[:-6],(1023,0,0,1,0),*session[-5:]]):
        r=world_run(bad);assert r.returncode==2 and not r.stdout,(bad,r.stderr)
print('mixed seed, exact authored allocation/events, retained state, the joined world session and malformed/unsupported transport passed')
