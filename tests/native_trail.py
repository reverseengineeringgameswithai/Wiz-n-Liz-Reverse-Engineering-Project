"""Transport checks with authored trail and RNG results."""
import subprocess
import sys
from trail_cases import case
from terrain_cases import encode_cases
exe=sys.argv[1]
for mode,rows,expected in [('--rng',[(1,99,2),(0,99,1)],[(258,258,129),(0,0,0)]),
 ('--emitter',[case(random=1)],[(90,100,3,2,7,10,20,30,40,50,60,70,80,129,638,638,643,5,5,0,2048,1,258,258,15,1,96,197,0,133,227,227,234,2,2,234)]),
 ('--particle',[(10,20,99,133,227,227,234,2,2,234,16)],[(10,20,99,0,227,227,234,2,2,234,1)])]:
 p=subprocess.run([exe,mode],input=encode_cases(rows),capture_output=True,timeout=10)
 assert p.returncode==0 and [tuple(map(int,l.split())) for l in p.stdout.splitlines()]==expected,(p.stdout,p.stderr)
for mode,data in [('--emitter',encode_cases([case(capacity=0)])),('--emitter',encode_cases([case(available_owner=2)])),
 ('--scheduled',encode_cases([case(mode=133,first=7,counter=1,target=7)])),('--emitter',b'0\n'),('--rng',b'0 1 33\n'),
 ('--rng',b'4294967296 0 1\n'),('--particle',b'0 0 0 256 0 0 0 0 0 0 1\n')]:
 p=subprocess.run([exe,mode],input=data,capture_output=True,timeout=10);assert p.returncode==2 and not p.stdout,(mode,p.stdout,p.stderr)
print('authored trail/RNG/lifetime transport and unsupported inputs passed')
# Later rows carry deliberately wrong state/RNG seeds; sequence modes must retain
# their own outputs while consuming only the declared owner/capacity context.
p=subprocess.run([exe,'--sequence'],input=encode_cases([case(random=1),case(x=500,countdown=0,random=0xffffffff,mirror=0,owner_x=4,owner_y=9)]),capture_output=True,timeout=10)
assert p.returncode==0,p.stderr
rows=[tuple(map(int,l.split())) for l in p.stdout.splitlines()]
assert rows[1]==(70,80,2,8,9,2,7,10,20,30,40,50,60,129,638,638,643,3,5,0,2048,1,258,258,16,0)
p=subprocess.run([exe,'--particle-sequence'],input=encode_cases([(10,20,99,133,227,227,234,2,2,234,1),(500,600,1,0,0,0,0,0,0,0,1)]),capture_output=True,timeout=10)
assert p.returncode==0,p.stderr
assert tuple(map(int,p.stdout.splitlines()[1].split()))==(10,20,99,133,228,227,234,2,2,234,0)
print('sequence transport ignores later emitter/RNG/particle seeds')
