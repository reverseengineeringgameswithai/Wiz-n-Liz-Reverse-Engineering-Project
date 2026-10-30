"""Native return-only transport goldens, inactivity and rejection boundaries."""
import subprocess
import sys
from return_only_cases import case
exe=sys.argv[1]
def run(rows):
    return subprocess.run([exe],input='\n'.join(' '.join(map(str,r)) for r in rows)+'\n',capture_output=True,text=True,timeout=10)
rows=[case(counter=1),case(mode=0x8b,first=916,counter=1),case(mode=5,counter=1,target=921,repeats=256),case(counter=0)]
p=run(rows);assert p.returncode==0,p.stderr
a,b,c,d=[list(r[:12]) for r in rows];a[4]=916;a[7]=5;b[3]=0x89;b[7]=5;d[7]=255
assert [tuple(map(int,l.split())) for l in p.stdout.splitlines()]==[(8,*r) for r in (a,b,c,d)],p.stdout
for row in ((),case(mode=256),case(x=65536),case(counter=256),case(control=2**32),case(mode=0x85,counter=1,target=921),case(repeats=0),case(repeats=257),(*rows[0],0),('garbage',),(-1,)):
    p=run([row]);assert p.returncode==2 and not p.stdout,(row,p)
from pair_initializer_cases import case as pair
def run_mode(mode,rows):
    return subprocess.run([exe,mode],input='\n'.join(' '.join(map(str,r)) for r in rows)+'\n',capture_output=True,text=True,timeout=10)
first=(161,270,0,129,916,916,921,4,4);second=(164,270,2048,129,919,916,921,5,5)
rows=[pair(),pair(count=1),pair(count=0),pair(b01=1),pair(count=2,callback_2=0xfaa4),pair(count=1,private=1),pair(target=921,countdown=7,link=0xffff0690,target_2=1,countdown_2=2,link_2=3)]
p=run_mode('--pair',rows);assert p.returncode==0,p.stderr
assert [tuple(map(int,l.split())) for l in p.stdout.splitlines()]==[(1,59,58,58,66,*first,0,0,0,*second,0,0,0),(0,1),(0,1),(0,2),(0,2),(0,2),
    (1,59,58,58,66,*first,921,7,0xffff0690,*second,1,2,3)],p.stdout
for row in (pair(count=69),pair(top=68),pair(second=59),pair(fill=256),pair(b01=256),pair(target=65536),pair(private_2=256),pair()[:-1],(*pair(),0)):
    p=run_mode('--pair',[row]);assert p.returncode==2 and not p.stdout,(row,p)
# Seeded pool: top slot 1 then slot 0, a reservation and a dormant occupied slot.
dormant=(8,*case(mode=0,first=541,counter=0,reload=0)[:12])
seed=[(4,2,2),(0,1),(9,0,0,0),(9,921,5,7),(1,),dormant]
p=run_mode('--pair-pool',seed);assert p.returncode==0,p.stderr
lines=[tuple(map(int,l.split())) for l in p.stdout.splitlines()]
assert lines[0]==(1,1,0,1,1,0,1,0,8,*first,921,5,7,8,*second,0,0,0),lines[0]
assert lines[1]==(3,1,0,1,8,*second[:7],4,5,0,0,0,1,1,1,8,*first[:7],3,4,921,5,7,3,3,1,*dormant),lines[1]
assert lines[2][0]==3 and lines[2][4:17]==(8,*second[:7],3,5,0,0,0),lines[2]
for bad in ([(4,2,0),(0,1),(0,),(9,0,0,0),(1,),dormant],[(4,2,0),(0,1),(9,0,0,0),(0,),(1,),dormant],
            [(4,1,0),(1,),(1,),(9,0,0,0),(1,),dormant],[(4,2,0),(0,1),(9,0,0,0),(9,0,0,0),(1,),dormant,(0,)],
            [(4,2,4097),(0,1),(9,0,0,0),(9,0,0,0),(1,),dormant],[(4,2),(0,1)]):
    p=run_mode('--pair-pool',bad);assert p.returncode==2 and not p.stdout,(bad,p)
# Reversed free order pops slot 0 first; the anchor follows the second pop.
p=run_mode('--pair-pool',[(4,2,0),(1,0),(9,0,0,0),(9,0,0,0),dormant,dormant]);assert p.returncode==0,p.stderr
assert tuple(map(int,p.stdout.split()))[:8]==(0,1,1,1,1,1,1,0),p.stdout
assert run_mode('--bogus',[]).returncode==2
# 6EC8/6EDC dormant pool: header slots free phases anchor; the popped slot needs
# a ten-field tag 9 row (target countdown link w08 w0a c0c r0d x y). Dormant
# objects emit inactive observations; FF31B4/FF31B8/FF31C0 print in that order.
full=(9,900,1,2,10,20,30,40,150,262)
p=run_mode('--dormant-pool',[(3,2,2,1),(0,1),(0,),full,(1,)]);assert p.returncode==0,p.stderr
asleep=(8,150,262,0,0,0x21d,10,20,30,40,900,1,2)
lines=[tuple(map(int,l.split())) for l in p.stdout.splitlines()]
assert lines==[(1,1,0,0,0,1,1,1,0,0,0,1,0,*asleep),(1,3,1,1,*asleep),(1,3,1,1,*asleep)],lines
for bad in ([(3,2,0,2),(0,1),(0,),full,(1,)],[(3,2,0,0),(0,1),(0,),full[:8],(1,)],[(3,2,0,0),(0,1),(0,),full[:4],(1,)],
            [(3,1,0,0),(0,),(0,),full,(1,)],[(3,2,0),(0,1),(0,),full,(1,)],[(3,2,0,0),(0,1),(0,),(*full[:9],65536),(1,)]):
    p=run_mode('--dormant-pool',bad);assert p.returncode==2 and not p.stdout,(bad,p)
# [6886,68A4) authored cases: twelve pops; ordinary slots 67..56 with zero residue.
from pair_initializer_cases import prefix_case
p=run_mode('--prefix',[prefix_case(),prefix_case(count=11),prefix_case(count=0),prefix_case(b01_7=1),prefix_case(count=5,callback_4=0xfaa4)]);assert p.returncode==0,p.stderr
lines=[tuple(map(int,l.split())) for l in p.stdout.splitlines()]
c=0xffff0690
want=[(0,0,0,0,0x21d,0,0,0,0,0,0,0)]*2+[(158,262,0,0x81,922,922,927,5,5,0,0,c),(190,262,0,0x81,928,928,933,5,5,0,0,c),
      (150,262,0,0x80,912,0,0,0,0,0,0,c,0x38,8),(182,262,0,0x80,913,0,0,0,0,0,0,0),(150,294,0,0x80,914,0,0,0,0,0,0,0),(182,294,0,0x80,915,0,0,0,0,0,0,0),
      (161,270,0,0x81,916,916,921,4,4,0,0,0),(164,270,0x800,0x81,919,916,921,5,5,0,0,0),(287,152,0,0x81,892,892,901,5,5,0,0,0),(287,184,0,0x81,902,902,911,5,5,0,0,0)]
assert lines[0]==(1,*range(67,55,-1),67,66,58,56,*(v for m in want for v in m)),lines[0]
assert lines[1:]==[(0,1),(0,1),(0,2),(0,2)],lines[1:]
for row in (prefix_case(count=69),prefix_case(s3=68),prefix_case(s1=67),prefix_case(x_0=65536),prefix_case()[:-1]):
    p=run_mode('--prefix',[row]);assert p.returncode==2 and not p.stdout,(row,p)
# Seeded prefix pool: identities and all twelve objects; no phases are stepped.
seed=[(13,13,0,1),tuple(range(13)),*([(9,0,0,0,0,0,0,0,0,0)]*13)]
p=run_mode('--prefix-pool',seed);assert p.returncode==0,p.stderr
line=tuple(map(int,p.stdout.split()))
assert line[:24]==tuple(x for s in range(12,0,-1) for x in (s,1)) and line[24:33]==(1,12,1,1,11,1,1,3,1) and line[33:35]==(1,0),line[:35]
for bad in ([(13,13,0),*seed[1:]],[seed[0],*seed[1:-1],(9,0,0,0)]):
    p=run_mode('--prefix-pool',bad);assert p.returncode==2 and not p.stdout,(bad,p)
# [68A4,68BC) authored: pickups 55/54 (kinds 5/6) then links 53/52; stale
# records, FF31AC and the rise gate are cleared.
from pair_initializer_cases import tail_case
p=run_mode('--tail',[tail_case(),tail_case(count=3),tail_case(b01_1=1)]);assert p.returncode==0,p.stderr
lines=[tuple(map(int,l.split())) for l in p.stdout.splitlines()]
records=(56,0,55,1)+(0,0)*14
pick=lambda x,f,r:(x,176,0,0x81,f,f,f+5,5,5,0,0,0xffff0690,16,16,r)
assert lines[0]==(1,2,55,54,53,52,*records,0,0,64,*pick(720,0x27e,0),*pick(880,0x284,1),*(0,0,0,0,0x21d,0,0,0,0,0,0,0)*2),lines[0]
assert lines[1:]==[(0,1),(0,2)],lines[1:]
for row in (tail_case(count=69),tail_case(s0=68),tail_case(s1=55),tail_case(kind_0=65536),tail_case()[:-1]):
    p=run_mode('--tail',[row]);assert p.returncode==2 and not p.stdout,(row,p)
# Seeded tail pool: header slots free phases control; a 64-word table row; then
# collision rows. Pickups update (and hit-reject); links are inactive.
free=[0,1,2,3];rows=[(4,4,2,1),tuple(free),*([(9,0,0,0,0,0,0,0,0,0)]*4),(5,0xffff,*([0xffff]*14),*([0]*16),100,100,*([0]*30))]
p=run_mode('--tail-pool',[*rows,(0,0,1023,0,0,0,0),(0,0,1023,0,0,0,0)]);assert p.returncode==0,p.stderr
out=[tuple(map(int,l.split())) for l in p.stdout.splitlines()]
assert out[0][:6]==(3,1,2,1,1,1) and out[0][6:12]==(1,2,1,1,1,1) and out[0][12:16]==(1,3,1,0) and out[0][16:76]==(0,0,0,0)*15 and out[0][76:78]==(1,0),out[0][:80]
assert out[1][0]==3 and out[1][1:4]==(3,1,1) and out[1][-1]==0 and out[2][0]==3,out[1:]
p=run_mode('--tail-pool',[*rows,(0,0,1023,0,0,0,0),(100,116,1023,0,0,0,0)]);assert p.returncode==2 and 'pickup-hit 6C00' in p.stderr and p.stdout.count('\n')==2,p
for bad in ([(4,4,0),*rows[1:]],[*rows[:-1]],[*rows,(0,0,1023,0,0,0,0)],[(4,4,1,1),*rows[1:]]):
    p=run_mode('--tail-pool',bad);assert p.returncode==2 and not p.stdout,(bad,p)
# [68BC,68C4) messages: MIX THOSE FRUIT shown at row 3; refused by a higher
# priority; FRUIT RETURNED clears FF31AA; two players leave 6EF0 open.
from pair_initializer_cases import message_case
rows=[message_case(),message_case(priority=0x70),message_case(fruit_returned=9),message_case(kind_1=0xffff),message_case(two_player=1),message_case(pair_request=2)]
p=run_mode('--message',rows);assert p.returncode==0,p.stderr
assert [tuple(map(int,l.split())) for l in p.stdout.splitlines()]==[(1,1,1,0x64,0,1,(0xe000+14+(3<<7))&65535),(1,1,0,0x70,0,0,0),(1,2,2,0x64,0,1,(0xe000+14+(3<<7))&65535),
    (1,0,3,0,0,0,0),(0,3),(0,3)],p.stdout
for row in (message_case(priority=256),message_case(two_player=65536),message_case()[:-1],(*message_case(),0)):
    p=run_mode('--message',[row]);assert p.returncode==2 and not p.stdout,(row,p)
# [68C4,68D4) gated pairs: pops 51/50, 49/48, ... exchange, so each partner is the
# lower slot. 7FBE's lead sits at the P2 control's (+3C - 8, +3E + 18).
from pair_initializer_cases import pairs_case
partner=lambda at:(at,at,0,0x80,0x21d,0,0,0,0,0,0,0)
lead=lambda x,y,countdown,code,mate:(x,y,0,0x80,0x21d,0,0,0,0,0,countdown,0xffff0690,code,mate)
p=run_mode('--pairs',[pairs_case(),pairs_case(gate_0=0,gate_2=0),pairs_case(count=3),pairs_case(b01_1=1)]);assert p.returncode==0,p.stderr
assert [tuple(map(int,l.split())) for l in p.stdout.splitlines()]==[
    (1,15,50,51,48,49,46,47,44,45,60,*partner(0xff80),*lead(712,184,60,0,50),*partner(0),*lead(784,176,30,1,48),*partner(0),*lead(924,102,30,2,46),*partner(0),*lead(564,120,30,3,44)),
    (1,10,50,51,48,49,64,*partner(0),*lead(784,176,30,1,50),*partner(0),*lead(564,120,30,3,48)),(0,1),(0,2)],p.stdout
for row in (pairs_case(count=69),pairs_case(s0=68),pairs_case(s1=51),pairs_case(gate_0=65536),pairs_case(p2x=65536),pairs_case(fill=256),pairs_case()[:-1],(*pairs_case(),0)):
    p=run_mode('--pairs',[row]);assert p.returncode==2 and not p.stdout,(row,p)
# Seeded: header slots free phases caller p1 gates p2x p2y. Slot 3 then 2 pop;
# the partner steps natively but the active lead's handler rejects the phase.
rows=[(4,4,0,1,2,0,1,0,0,0,0),(0,1,2,3),*([(9,0,0,0,0,0,0,0,0,0)]*4)]
p=run_mode('--pairs-pool',rows);assert p.returncode==0,p.stderr
assert tuple(map(int,p.stdout.split()))==(2,1,3,1,2,0,1,8,0,0,0,0x80,0x21d,0,0,0,0,0,0,0,10,784,176,0,0x80,0x21d,0,0,0,0,0,30,2,1,2,1),p.stdout
p=run_mode('--pairs-pool',[(4,4,1,*rows[0][3:]),*rows[1:]]);assert p.returncode==2 and p.stdout.count('\n')==1 and 'gated-pair lead handler' in p.stderr,p
for bad in ([(4,4,0,1,2,0,1,0,0,0),*rows[1:]],[(4,4,0,1,2,0,65536,0,0,0,0),*rows[1:]],[(4,4,0,1,2,1,0,0,0,0,0),*rows[1:-2],(0,),(0,)]):
    p=run_mode('--pairs-pool',bad);assert p.returncode==2 and not p.stdout,(bad,p)
print('return-only transport goldens, widths, inactive traps, callback rejection, pair/dormant/prefix/tail/message/gated-pair initialization, inheritance and exhaustion passed')
