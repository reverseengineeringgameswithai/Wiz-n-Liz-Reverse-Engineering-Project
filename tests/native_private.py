"""Private transport goldens and bounded failures, no ROM required."""
import subprocess
import sys
from private_cases import case
exe=sys.argv[1]
def run(rows,mode='--scheduled'):
    return subprocess.run([exe,mode],input='\n'.join(' '.join(map(str,r)) for r in rows)+'\n',capture_output=True,text=True,timeout=10)
a=case(countdown=0,y=0,rise=65536);b=case(kind=1,flags_gate=32768,hide=256)
p=run([a,b]);assert p.returncode==0,p.stderr
expected_a=list(a[:13]);expected_a[2]=65535;expected_a[8]=1;expected_a[11]=8
expected_b=list(b[:13]);expected_b[1]=expected_b[2]=0xff80;expected_b[3]=0x2000;expected_b[8]=1
assert [tuple(map(int,l.split())) for l in p.stdout.splitlines()]==[(5,*expected_a),(5,*expected_b)]
for row in ((),case(kind=2),case(mode=256),case(x=65536),case(rise=2**32),case(flags_gate=65536),case(repeats=0),case(repeats=257),case(mode=0x85,counter=1,target=7),(*a,0),('garbage',),(-1,)):
    p=run([row]);assert p.returncode==2 and not p.stdout,(row,p)
from pair_initializer_cases import case as pair
first=(287,152,0,129,892,892,901,5,5);second=(287,184,0,129,902,902,911,5,5)
p=run([pair(),pair(count=1),pair(count=0),pair(b01=1),pair(count=2,callback_2=0xfaa4),pair(target=921,countdown=7,link=0xffff0690)],'--pair');assert p.returncode==0,p.stderr
assert [tuple(map(int,l.split())) for l in p.stdout.splitlines()]==[(1,59,58,66,*first,0,0,0,*second,0,0,0),(0,1),(0,1),(0,2),(0,2),(1,59,58,66,*first,921,7,0xffff0690,*second,0,0,0)],p.stdout
for row in (pair(count=69),pair(top=68),pair(second=59),pair()[:-1]):
    p=run([row],'--pair');assert p.returncode==2 and not p.stdout,(row,p)
# Seeded pool: phases each carry rise/flags/hide gates; the second sets flags 2000.
seed=[(3,2,2),(2,1),(1,),(9,0,0,0),(9,0,0,0),(0,0,0),(0,1,0)]
p=run(seed,'--pair-pool');assert p.returncode==0,p.stderr
lines=[tuple(map(int,l.split())) for l in p.stdout.splitlines()]
assert lines[0]==(1,1,2,1,0,5,1,*first,0,0,0,5,1,*second,0,0,0),lines[0]
assert lines[1]==(2,1,1,1,5,1,*first[:7],4,5,0,0,0,1,2,1,5,1,*second[:7],4,5,0,0,0),lines[1]
assert lines[2][8]==0x2000 and lines[2][25]==0x2000,lines[2]
for bad in ([(3,2,2),(2,1),(1,),(9,0,0,0),(9,0,0,0),(0,0,0)],[(3,2,1),(2,1),(1,),(9,0,0,0),(9,0,0,0),(0,0,0),(0,0,0)],
            [(3,2,1),(2,1),(1,),(0,),(9,0,0,0),(0,0,0)],[(3,2,1),(2,1),(1,),(9,0,0,0),(9,0,0,0),(0,65536,0)],[(3,2,1),(2,1),(1,),(9,0,0,0),(9,0,0,0),(0,0)]):
    p=run(bad,'--pair-pool');assert p.returncode==2 and not p.stdout,(bad,p)
r1=(158,262,0,129,922,922,927,5,5);r2=(190,262,0,129,928,928,933,5,5)
p=run([pair(a6=0xffff0690),pair(count=1),pair(b01=1),pair(a6=7,target=921,countdown=7,link=3,target_2=5,countdown_2=6,link_2=9)],'--rising-pair');assert p.returncode==0,p.stderr
assert [tuple(map(int,l.split())) for l in p.stdout.splitlines()]==[(1,59,58,66,*r1,0,0,0xffff0690,*r2,0,0,0xffff0690),(0,1),(0,2),(1,59,58,66,*r1,921,0,7,*r2,5,0,7)],p.stdout
seed=[(3,2,1,1),(2,1),(1,),(9,0,0,0),(9,0,0,0),(0,0,0)]
p=run(seed,'--rising-pair-pool');assert p.returncode==0,p.stderr
lines=[tuple(map(int,l.split())) for l in p.stdout.splitlines()]
assert lines[0]==(1,1,2,1,0,5,0,*r1,0,0,1,5,0,*r2,0,0,1),lines[0]
assert lines[1][15:18]==(0,8,1) and lines[1][32:35]==(0,8,1),lines[1]
for bad in ([(3,2,1),(2,1),(1,),(9,0,0,0),(9,0,0,0),(0,0,0)],[(3,2,1,2**32),(2,1),(1,),(9,0,0,0),(9,0,0,0),(0,0,0)],[(3,2,1,1),(2,1),(1,),(0,),(9,0,0,0),(0,0,0)]):
    p=run(bad,'--rising-pair-pool');assert p.returncode==2 and not p.stdout,(bad,p)
print('private transport goldens, widths, callback and budget rejections, visibility/rising pairs and seeded phases passed')
