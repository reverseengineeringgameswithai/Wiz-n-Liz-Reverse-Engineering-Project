"""Independent native table transport goldens and explicit rejection boundaries."""
import subprocess
import sys
from table_motion_cases import case
exe=sys.argv[1]
def run(rows,mode='--scheduled'):
    return subprocess.run([exe,mode],input='\n'.join(' '.join(map(str,r)) for r in rows)+'\n',capture_output=True,text=True,timeout=10)
a=case(x=0,y=65535,countdown=0);b=case(cursor=23,toggle=1,loops=1,delta=1)
p=run([a,b]);assert p.returncode==0,p.stderr
expected_a=list(a[:15]);expected_a[0]=65535;expected_a[1]=0;expected_a[7]=1;expected_a[10]=28;expected_a[12]=1;expected_a[13]=1;expected_a[14]=1
expected_b=list(b[:15]);expected_b[0]=100;expected_b[7]=1;expected_b[10]=13;expected_b[12]=0
assert [tuple(map(int,l.split())) for l in p.stdout.splitlines()]==[(6,*expected_a),(6,*expected_b)]
for row in ((),case(mode=256),case(x=65536),case(control=2**32),case(cursor=24),case(cursor=2**32-1),case(delta=65536),case(toggle=65536),case(loops=65536),case(loops=4096),case(budget=0),case(budget=65537),case(repeats=0),case(repeats=257),case(mode=0x85,counter=1,target=7),(*a,0),('garbage',),(-1,)):
    p=run([row]);assert p.returncode==2 and not p.stdout,(row,p)
print('table transport goldens, widths, cursor, callback and work bounds passed')
