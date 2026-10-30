"""Native collision transport goldens and rejection boundaries."""
import subprocess
import sys
from collision_cases import case
exe=sys.argv[1]
def run(rows,mode='--scheduled'):
    return subprocess.run([exe,mode],input='\n'.join(' '.join(map(str,r)) for r in rows)+'\n',capture_output=True,text=True,timeout=10)
a=case(mode=0x81,counter=2,reload=2);b=case(secondary_gate=0x8000,secondary_present=1,secondary_x=30000,secondary_y=30000)
p=run([a,b]);assert p.returncode==0,p.stderr
ea=list(a[:14]);ea[7]=1
assert [tuple(map(int,l.split())) for l in p.stdout.splitlines()]==[(7,*ea),(7,*b[:14])]
p=run([(100,100,56,8,84,88,1023),(100,100,56,8,83,88,1023),(16,12,65520,65524,0,0,65535)],'--overlap')
assert p.returncode==0 and p.stdout=='1\n0\n1\n',p
for row in ((),case(mode=256),case(x=65536),case(control=2**32),case(x_extent=65536),case(mask=65536),case(secondary_gate=65536),case(secondary_present=2),case(secondary_x=1),case(repeats=0),case(repeats=257),case(mode=0x85,first=7,counter=1,target=7),case(primary_x=150,primary_y=262),case(secondary_gate=1),case(secondary_gate=1,secondary_present=1,secondary_x=150,secondary_y=262),(*a,0),('garbage',),(-1,)):
    p=run([row]);assert p.returncode==2 and not p.stdout,(row,p)
# 783A authored cases: probe then three return-only members, inherited
# +08..+0D/target/countdown, caller control only on the probe.
from pair_initializer_cases import quad_case
inh={f'{n}_{m}':v for m in range(4) for n,v in (('target',900+m),('countdown',m),('link',m),('w08',10+m),('w0a',20+m),('c0c',30+m),('r0d',40+m))}
p=run([quad_case(**inh),quad_case(count=3),quad_case(count=0),quad_case(b01_2=1),quad_case(count=4,callback_3=0xfaa4)],'--quad');assert p.returncode==0,p.stderr
probe=(150,262,0,0x80,912,10,20,30,40,900,0,0xffff0690,0x38,8)
members=[(x,y,0,0x80,f,10+m,20+m,30+m,40+m,900+m,m,m) for m,(x,y,f) in enumerate(((182,262,913),(150,294,914),(182,294,915)),1)]
assert [tuple(map(int,l.split())) for l in p.stdout.splitlines()]==[(1,63,62,61,60,64,*probe,*(v for m in members for v in m)),(0,1),(0,1),(0,2),(0,2)],p.stdout
for row in (quad_case(count=69),quad_case(s0=68),quad_case(s1=63),quad_case(a5=2**32),quad_case(w08_0=65536),quad_case(c0c_3=256),quad_case()[:-1]):
    p=run([row],'--quad');assert p.returncode==2 and not p.stdout,(row,p)
# Seeded 783A pool: header slots free phases control; tag 9 rows carry the
# +08..+0D tail; each phase supplies explicit collision inputs.
free=[0,4,3,2,1];slots=[(0,),(9,900,0,0,10,20,30,40),(9,901,1,1,11,21,31,41),(9,902,2,2,12,22,32,42),(9,903,3,3,13,23,33,43),(1,)]
seed=[(6,5,2,1),tuple(free),*slots,(0,0,1023,0,0,0,0),(5,5,1023,1,1,9,9)]
p=run(seed,'--quad-pool');assert p.returncode==0,p.stderr
lines=[tuple(map(int,l.split())) for l in p.stdout.splitlines()]
# Bottom-to-top free row: slot 1 is the top and becomes the probe.
want=[(7,150,262,0,0x80,912,10,20,30,40,900,0,1,0x38,8)]+[(8,x,y,0,0x80,f,10+m,20+m,30+m,40+m,900+m,m,m) for m,(x,y,f) in enumerate(((182,262,913),(150,294,914),(182,294,915)),1)]
assert lines[0]==(1,1,2,1,3,1,4,1,1,0,*(v for w in want for v in w)),lines[0]
assert lines[1][0]==lines[2][0]==4 and lines[1]==lines[2],lines[1:]
for bad in ([seed[0][:3],*seed[1:]],[*seed[:-1]],[*seed,(0,)],[*seed[:-1],(5,5,1023,0,0,9,9)],[*seed[:-1],(5,5,1023,1,2,9,9)],
            [*seed[:2],slots[0],(9,900,0,0),*slots[2:],*seed[-2:]]):
    p=run(bad,'--quad-pool');assert p.returncode==2 and not p.stdout,(bad,p)
# A probe hit is unsupported: the phase rejects after the streamed init line.
p=run([*seed[:-2],(150,262,1023,0,0,0,0),seed[-1]],'--quad-pool')
assert p.returncode==2 and p.stdout.count('\n')==1 and 'collision-hit7910' in p.stderr,p
# 6BD6 pickups take the same 22 fields on record 0: misses animate, hits reject at 6C00.
p=run([a,b],'--pickup-scheduled');assert p.returncode==0,p.stderr
assert [tuple(map(int,l.split())) for l in p.stdout.splitlines()]==[(9,*ea,0),(9,*b[:14],0)],p.stdout
p=run([case(primary_x=150,primary_y=262)],'--pickup-service');assert p.returncode==2 and not p.stdout and 'pickup-hit 6C00 (primary)' in p.stderr,p
# 6C00 hits (114-field rows): one walk onto the ordinary pickup converts P1's
# dormant link into the carrying emitter; family frames and a collectable
# callback stop; malformed rows reject.
from pickup_hit_cases import case as hit, emitter as carrying
p=run([hit(),hit(w08=0x20d),hit(mode=0x85,w06=900,c0c=1)],'--pickup-hit');assert p.returncode==0,p.stderr
lines=[tuple(map(int,l.split())) for l in p.stdout.splitlines()]
pickup=(1,0,0x368,0xb0,0,0x85,0x21e,0x21e,0x227,3,3,0x227,0,0xffff0690,16,16,1,1)
link1=(1,0x370,0xb0,0,0x81,0x284,0x284,0x289,4,5,900,0,0,*(0xff80,)*10,0xffff0690,16,16,1)
link2=(0,0x1234,0x567,0,0,0x21d,9,11,13,15,900,3,0xffff0690)
assert lines==[(*pickup,*link1,*link2,4,0,2,1,*(0,16)*14,1,0x89,6,0xc0,1,4,99),(0,1),(0,2)],lines
p=run([hit(walks=64,**carrying(1))],'--pickup-hit');assert p.returncode==0 and p.stdout.split()[17]=='2',p   # Exchanged and hit again.
for bad in (hit()[:-1],(*hit(),0),hit(walks=0),hit(walks=65),hit(s=53),hit(record=16),hit(entry_1=17)):
    p=run([bad],'--pickup-hit');assert p.returncode==2 and not p.stdout,(bad,p)
# 7910 hits (86-field rows): the ordinary probe delivers P1's carrying link
# (sparkle in slot 48, copy in 47); one free entry exhausts, a probe callback
# stops, a dormant link returns; malformed rows reject.
from delivery_cases import case as touch, link as held, delivered, SPARKLE, COPY
p=run([touch(),touch(depth=1),touch(mode=0x85,w06=0,c0c=1,p1x=0),touch(**held(1,False))],'--probe-hit');assert p.returncode==0,p.stderr
lines=[tuple(map(int,l.split())) for l in p.stdout.splitlines()]
probe=(1,150,262,0,0x80,912,0,0,0,0,0,0,0xffff0690,0x38,8);dormant=(0,0x1234,0x567,0,0,0x21d,9,11,13,15,900,3,0xffff0690)
link1=(0,0xa4,0xf6,0,0,0x227,0x21e,0x227,3,3,0x21e,0,0xffff0690)
created=(2,0,48,0x2c8,0xa8,0,0x85,0x21e,0x21e,0x227,3,3,0x227,1,47,0xa4,0xf6,0,0x87,0x227,0x21e,0x227,3,3,0x21e,0,0xffff0690,0x27e,0x283,16,16,0)
assert lines==[(*probe,*link1,*dormant,*created,1,0x8c,6,0xc0,1,47),(0,1),(0,3),(*probe,*dormant,*dormant,0,0,49)],lines
for bad in (touch()[:-1],(*touch(),0),touch(walks=0),touch(walks=65),touch(s=53),touch(top=63),touch(top=47),touch(depth=65),touch(present=2)):
    p=run([bad],'--probe-hit');assert p.returncode==2 and not p.stdout,(bad,p)
# Later walks: the sparkle releases and the copy reaches 79B6 on the 30th.
p=run([delivered(SPARKLE,walks=29),delivered(SPARKLE,walks=30),delivered(COPY,walks=29),delivered(COPY,walks=30)],'--delivered');assert p.returncode==0,p.stderr
lines=[tuple(map(int,l.split())) for l in p.stdout.splitlines()]
assert lines==[(1,0,0x2c8,0xa8,0,0x85,0x227,0x21e,0x227,1,3,0x227,*(0,)*7,20),(1,1,0x2c8,0xa8,0,0,0x21e,0x21e,0x227,3,3,0x227,*(0,)*7,21),
               (1,0,0xa4,0xf6,0,0x87,0x21e,0x21e,0x227,1,3,0x21e,0,0xffff0690,0x27e,0x283,16,16,0,20),(0,2)],lines
for bad in (delivered(SPARKLE,count=1),delivered(COPY,kind=2),delivered(COPY,walks=0),delivered(COPY,slot=68),delivered(COPY,record=16)):
    p=run([bad],'--delivered');assert p.returncode==2 and not p.stdout,(bad,p)
# The copy's 30th walk (31-field rows): 79B6's first-ingredient path posts
# D20E (row clear at VRAM E00E), 7AD6 makes slot 67 the table object and the
# released copy runs 7A88 once; a held priority refuses the message; FF31AC
# set stops; an earlier walk only animates; malformed rows reject.
from delivery_cases import ingredient
p=run([ingredient(),ingredient(priority=0x64,message=1),ingredient(activation=1),ingredient(c0c=2)],'--ingredient');assert p.returncode==0,p.stderr
lines=[tuple(map(int,l.split())) for l in p.stdout.splitlines()]
residue=(0xab,0xfb,0,0,0x284,0x284,0x289,5,5,0x21e,0x0d,0xffff0690,1,0xffff,1);table=(0xac,0xfa,0,0x81,0x284,0x284,0x289,5,5,0x21e,0x0e,0xffff0690,0,0xffff,0)
assert lines==[(1,1,1,*residue,*table,67,67,1,3,1,0,1,0xe00e,0,0x50,21),(1,1,1,*residue,*table,67,67,1,0,0x64,0,0,0,0x50,21),(0,3),
               (1,0,0,0xa4,0xf6,0,0x87,0x21e,0x21e,0x227,1,3,0x21e,0,0xffff0690,0x284,0x289,16,16,1,20)],lines
for bad in (ingredient()[:-1],(*ingredient(),0),ingredient(walks=0),ingredient(control=1),ingredient(target_slot=47),ingredient(message=5),ingredient(record=16)):
    p=run([bad],'--ingredient');assert p.returncode==2 and not p.stdout,(bad,p)
# The second copy's last walk (45-field rows): 79B6's second-ingredient path
# posts D22F (row clear at VRAM E60E), negates FF31AC's +32 (FFFF -> 0001) and
# 7AD6 makes slot 66 the FF31B0 table object, the anchor (58) takes 7B42 with
# countdown 012C and the released copy runs 7A88 once along the new drift; a
# held priority refuses the message; an earlier walk only animates; 8000 negates
# to itself; malformed rows reject.
from spell_cases import second, mix
p=run([second(),second(priority=0x64,message=1),second(c0c=2),second(delta=0x8000)],'--second-ingredient');assert p.returncode==0,p.stderr
lines=[tuple(map(int,l.split())) for l in p.stdout.splitlines()]
residue=lambda x=173,d=1:(x,251,0,0,638,638,643,5,5,542,13,0xffff0690,1,d,1);made=lambda d=1:(172,250,0,0x81,638,638,643,5,5,542,14,0xffff0690,0,d,0)
spell=(164,270,0x800,0x81,919,916,921,5,5,0,0x12c,0xffff0690,67,66,66,0)
assert lines==[(1,1,1,*residue(),*made(),*spell,4,1,12,1,0xe60e,0,0x50,21),(1,1,1,*residue(),*made(),*spell,0,0x64,12,0,0,0x50,21),
               (1,0,0,0xa4,0xf6,0,0x87,0x21e,0x21e,0x227,1,3,0x21e,0,0xffff0690,0x27e,0x283,16,16,0,20),(1,1,1,*residue(0xac+0x8000,0x8000),*made(0x8000),*spell,4,1,12,1,0xe60e,0,0x50,21)],lines
for bad in (second()[:-1],(*second(),0),second(walks=0),second(control=1),second(target_slot=48),second(message=5),second(record=16),second(slot=68)):
    p=run([bad],'--second-ingredient');assert p.returncode==2 and not p.stdout,(bad,p)
# The anchor (20-field rows): 7B42 counts +10 down; the walk that drives it
# negative runs 13294 (fade-out from the kept level 14, curves 135EA) and
# selects 7B58, which waits on FF0B90; with FF0B90 clear 7B58 reports its
# completion (4) and 7B8A installs 12646 (3); an inactive anchor is not walked.
from completion_cases import anchor, completion, sparkle, door, fruit_frame
p=run([anchor(),anchor(countdown=0),anchor(countdown=0,walks=3),anchor(phase=1),anchor(phase=2,walks=2),anchor(phase=2,direction=1),anchor(mode=0x7f,walks=7)],'--anchor')
assert p.returncode==0,p.stderr
fields=lambda c,counter=4,mode=129:f'164 270 2048 {mode} 919 916 921 {counter} 5 0 {c} 4294903440'
assert p.stdout.splitlines()==[f'0 {fields(2)} 0 0 0 14 0 0 0 0',f'1 {fields(65535)} 1 6 0 14 79338 79338 79338 0',f'1 {fields(65535,2)} 1 6 0 14 79338 79338 79338 0',
                               f'4 {fields(3)} 0 0 0 14 0 0 0 0',f'3 {fields(3,3)} 0 0 0 14 0 0 0 0',f'2 {fields(3)} 1 0 0 14 0 0 0 0',f'0 {fields(3,5,127)} 0 0 0 14 0 0 0 0'],p.stdout
for bad in (anchor()[:-1],anchor(walks=0),anchor(walks=513),anchor(slot=68),anchor(mode=256),anchor(phase=3),anchor(level=65536)):
    p=run([bad],'--anchor');assert p.returncode==2 and not p.stdout,(bad,p)
# 7B58's completion (67-field rows): D269 (row 12 cleared at VRAM E60E), both
# ingredients off (fruit 6 and 5 in FF31C4/FF31C6, kinds FFFF), sounds 9C and
# 90, the sparkle (top pop) at (352,252), the sign and door (lower and higher
# of the next two pops), FF316C = FFFF and 1324E's fade-in; a held fade waits;
# each path outside recipe 8652 prints its stop.
p=run([completion(),completion(direction=1),completion(flags_a8=1),completion(a_w08=fruit_frame(0)),completion(a_w08=fruit_frame(14)),completion(pair_request=1),
       completion(two_player=1),completion(gate_a6=1),completion(gate_a4=1),completion(depth=2)],'--completion');assert p.returncode==0,p.stderr
lines=p.stdout.splitlines();made=' 2 156 7 192 1 144 11 192 1 19 352 252 0 128 541 64 16 16 17 0 0 0 128 541 18 344 248 0 128 541 30 4294903440 65535 65535 6 0 0 79338 79338 79338 0 17'
off='172 250 0 0 644 644 649 5 5 542 14 4294903440 0 65535 0 180 250 0 0 638 638 643 5 5 542 14 4294903440 0 1 0'
assert lines[0]==f'1 {fields(65535)} {off} 65535 65535 6 5 5 1 12 1 58894'+made,lines[0]
assert lines[1:]==[f'0 {fields(65535)} 20','2 32500','2 34642','2 37512','2 37250','2 28484','2 38530','2 38420','2 64030'],lines[1:]
for bad in (completion()[:-1],completion(slot_a=58),completion(record_b=1),completion(message=5),completion(control=1),completion(depth=66),completion(a_cursor=24)):
    p=run([bad],'--completion');assert p.returncode==2 and not p.stdout,(bad,p)
# 7F6A: a particle on the first walk (low byte at most 73, flags 4000 from the
# fourth E918), release on the 65th walk, an empty stack stops on walk 1.
p=run([sparkle(),sparkle(walks=65,depth=60),sparkle(depth=0,walks=40)],'--sparkle');assert p.returncode==0,p.stderr
lines=p.stdout.splitlines()
assert lines[0]=='0 352 252 0 128 541 63 16 16 514410974 514410974 1 19 356 252 16384 133 227 227 234 3 3 234 19' and lines[2]=='1 1',lines
v=list(map(int,lines[1].split()));assert v[:12]==[0,352,252,0,0,541,65535,16,16,227582453,227582453,32] and v[-1]==29,v[:12]
for bad in (sparkle()[:-1],sparkle(walks=0),sparkle(walks=97),sparkle(slot=68),sparkle(mode=256),sparkle(depth=68)):
    p=run([bad],'--sparkle');assert p.returncode==2 and not p.stdout,(bad,p)
# The door: 5964 on walk 31 (mode 87 from 0227), 6FCA on walk 61 (moved +8/-8,
# 00B0..00B7, extents 10/20, sound 95, the sign raised 24 above at 00D2), the
# sign bobbing next walk. Entering (7082): the sign released, the door vanishing
# at (-8,+8), FF0F00, the camera words (0048,0018), P1's actor (80, 021D, 710E)
# and +1A6 FFFF, the anchor's 12646, the sign's slot freed; with two players no
# camera words; a miss with two players stops at 7072, an active link at 70FE.
p=run([door(walks=31),door(walks=61),door(walks=62),door(walks=96,track_x=352,track_y=240),door(walks=96,two_player=1),door(bobbing=1,cursor=13,sx=352,sy=204,sframe=0xd2,walks=2),
       door(walks=96,track_x=352,track_y=240,two_player=1),door(walks=96,track_x=352,track_y=240,link_mode=0x81)],'--door')
assert p.returncode==0,p.stderr
entered='0 3 344 248 0 133 542 542 551 3 3 551 1 352 204 0 0 210 0 1 149 2 192 1 4294903440 {} 128 541 28942 4294903440 65535 75334 21'
assert p.stdout.splitlines()==['0 1 344 248 0 135 551 542 551 3 3 542 65535 0 0 0 0 0 0 128 541 0 0 20','0 2 352 240 0 129 176 168 183 3 3 542 65535 16 32 1 352 204 0 128 210 0 1 149 2 192 1 20',
                               '0 2 352 240 0 129 176 168 183 2 3 542 65535 16 32 1 352 205 0 128 210 1 1 149 2 192 1 20',entered.format('72 24'),'1 28786',
                               '0 0 344 248 0 128 541 0 0 0 0 0 28 0 0 1 352 205 0 128 210 1 0 20',entered.format('4660 22136'),'1 28926'],p.stdout
for bad in (door()[:-1],door(phase=3),door(bobbing=2),door(slot=40,sign_slot=40),door(link_slot=48),door(cursor=14),door(walks=0),door(mode=256),door(depth=65)):
    p=run([bad],'--door');assert p.returncode==2 and not p.stdout,(bad,p)
# 7CC8: FF31BE counts down and reloads 0028 with FF31BC + 1; no spell does
# nothing; the objects exchange only when FF31AC's drift is negative and the
# FF31B0 object lies higher.
p=run([mix(),mix(timer=0),mix(spell=0),mix(activation=0),mix(slots=(66,67))],'--spell-mix');assert p.returncode==0,p.stderr
lines=[tuple(map(int,l.split())) for l in p.stdout.splitlines()]
first=(172,250,644,644,649,5,5,14,0,0xffff,0,0x81,0,542,0xffff0690);other=(180,250,644,644,649,5,5,14,0,1,0,0x81,0,542,0xffff0690)
assert lines==[(39,0,*first,*other),(40,1,*first,*other),(40,0,*first,*other),(39,0,*first,*other),(39,0,*other,*first)],lines
for bad in (mix()[:-1],mix(spell=2),mix(slots=(67,67)),mix(slots=(67,68)),mix(first=(*mix()[6:16],24,*mix()[17:21]))):
    p=run([bad],'--spell-mix');assert p.returncode==2 and not p.stdout,(bad,p)
# The retained world: the whole setup over twenty slots, then carried phases.
# P1 touches pickup 7 (6C00: link 5 carries it), the emitter walks with owner
# positions (one external E918 call), emits into slot 3 once its history moves,
# then P1 touches the 783A probe in slot 15 (7910 delivers into 2 and 1).
from world_cases import world_input, phase, setup_line, phase_line
o1,o2=(40,50),(60,50)
steps=[phase(),phase((100,116)),phase(owner=o1),phase(owner=o1,calls=1),phase(owner=o1),phase(owner=o2),phase(owner=o2),phase((150,262),owner=o2)]
p=run(world_input(steps),'--world-pool');assert p.returncode==0,p.stderr
lines=[tuple(map(int,l.split())) for l in p.stdout.splitlines()];assert len(lines)==9,lines
ids,selection,s,made=setup_line(lines[0])
assert [tuple(x) for x in ids]==[(k,1) for k in range(19,3,-1)] and selection==(1,1,0xe000+14+(3<<7),0),(ids,selection)
assert s['free']==(0,1,2,3) and s['records'][:3]==[(1,7,1,0),(1,6,1,1),(0,0,0,0)] and s['activation']==[(0,0,0)],s
assert s['links']==[(1,5,1),(1,4,1)] and s['dormant']==[(1,19,1),(1,18,1)] and s['anchor']==[(1,10,1)] and s['messages']==[(1,0x64,3),(0,0,0)],s
assert s['private']==(0,0,0) and s['loop']==(0,0) and [k for k,_ in made]==[8,8,5,5,7,8,8,8,8,8,5,5,9,9,8,8],(s,made)
phases=[phase_line(l) for l in lines[1:]]
events,s=phases[0]
assert [(e[0],e[1]) for e in events]==[(3,4),(3,5),*((1,k) for k in range(6,18)),(3,18),(3,19)] and not s['sounds'],events
events,s=phases[1]
assert s['sounds']==[(0x89,6,0xc0,1)] and s['records'][0]==(1,5,1,0) and [k for k,_ in s['link_objects']]==[4,8],s
assert next(e for e in events if e[1]==7)[3:5]==(9,100-8) and next(e for e in events if e[1]==7)[-1]==1,events   # Vanishing at X - 8.
events,s=phases[2];emitter=next(e for e in events if e[1]==5)
assert emitter[:4]==(1,5,1,4) and emitter[4+11]==3 and emitter[4+12:4+14]==(44,50) and s['random']==(1,1),emitter
assert phases[3][1]['random']==(65536,65536) and not any(e[0]==0 for e in phases[5][0])
events,s=phases[6]
assert events[1]==(0,3,1,3,0xff80-3,0xff80-4,0,0x85,227,227,234,2,2,234) and events[2][:4]==(1,5,1,4),events[:3]
assert s['free']==(0,1,2) and s['random']==(0x01020001,0x01020001),s
events,s=phases[7];at=[(e[0],e[1],e[3]) for e in events]
assert at.index((0,2,3))+1==at.index((0,1,11)) and at.index((0,1,11))+1==at.index((1,15,7)) and (1,3,3) in at,at
assert s['sounds']==[(0x8c,6,0xc0,1)] and s['free']==(0,) and [k for k,_ in s['link_objects']]==[8,8],s
# An owner position no emitter consumes, and an emitter without one, reject.
p=run(world_input([phase(owner=o1)]),'--world-pool');assert p.returncode==2 and p.stdout.count('\n')==1 and 'unconsumed owner position' in p.stderr,p
p=run(world_input(steps[:2]+[phase()]),'--world-pool');assert p.returncode==2 and p.stdout.count('\n')==3 and 'trail owner unavailable' in p.stderr,p
good=world_input([phase()])
for bad in (good[:-1],[*good,phase()],[(20,20),*good[1:]],[*good[:-1],phase()[:-1]],[*good[:-1],(*phase()[:10],65,*phase()[11:])],
            [*good[:-1],phase(messages=((5,0,0),None))],[*good[:-1],(*phase()[:11],0,1,0,0,*phase()[15:])],[*good[:-1],(*phase()[:7],0,1,0,*phase()[10:])],
            [*good[:-3],(0,0,0,0,0,0,0,3),*good[-2:]]):
    p=run(bad,'--world-pool');assert p.returncode==2 and not p.stdout,(bad,p)
# The scene between levels. 60E6 over an empty pool: door 0 in 67 with its
# numbers in 66 and 65 ... door 7 in 46; 63A4 clears FF33DE and rewrites +8;
# exhaustion in F994 (F9D0) or F9E2 (FA1E) stops.
from hub_cases import doors_case, records, door as hub_door, OPEN
p=run([doors_case(),doors_case(depth=2),doors_case(depth=3,stage=1,recs=records(states=[0x8000]*9)),doors_case(two_player=1,stage=1,recs=records(states=[0x8000]*9,markers=[1]*9),depth=4)],'--hub-doors')
assert p.returncode==0,p.stderr
lines=p.stdout.splitlines();first=list(map(int,lines[0].split()))
assert first[:3]==[0,0,24] and first[3:19]==[67,1,129,432,164,176,0,0,0,66,65,168,183,3,3,60] and first[19:27]==[66,2,128,416,154,186,0,0] and first[-9:]==[0]*8+[65535],first
assert lines[1:]==['1 63952','1 64030','1 64030'],lines
# Door 0: open after 61 walks (extents 10/18); P1 at its 1742 tracking enters
# on walk 62 (17298 on FF0690, FF4446/FF4448 = 0098/0008, FF3398 = FF330C, the
# puff at (01AC,00AC), both numbers pushed, 630A on both controls, 13208); with
# two players P2's contact clears FF0838's message fields; the puff releases
# itself at 0227; a seeded callback stops.
p=run([hub_door(walks=61),hub_door(walks=62,p1x=0x1a1,p1y=0xbc),hub_door(**OPEN,p2x=0x1b0,p2y=0xa4,two_player=1),
       hub_door(phase=3,mode=0x85,w06=0x21e,w08=0x21e,w0a=0x227,c0c=3,r0d=3,target=0x227,countdown=0,x_extent=0x10,y_extent=0x18,walks=31),
       hub_door(mode=0x85,w06=0,target=0,c0c=1,walks=1)],'--hub-door')
assert p.returncode==0,p.stderr
coast='65535 128 541 25386';cleared='4294967295 4294967295 0 0 0 0 0';entry='0 3 428 172 0 133 542 542 551 3 3 551 0 16 24 0 0 0 46 1 {} 152 8 4294914828 1 1 1 14 79210 79210 79274 0 '
assert p.stdout.splitlines()==['0 2 432 164 0 129 180 168 183 2 3 0 65535 16 24 0 128 128 44 0',entry.format(0)+f'{coast} {cleared} {coast} {cleared}',
                               entry.format(1)+f'{coast} 4294967295 4294967295 0 0 0 12 0 {coast} {cleared}','0 4 428 164 0 0 542 542 551 3 3 551 65535 16 24 0 128 128 45 0','1 51952'],p.stdout
for bad in (hub_door()[:-1],hub_door(phase=5),hub_door(slot=66),hub_door(walks=0),hub_door(walks=97),hub_door(depth=65),hub_door(mode=256),doors_case()[:-1]):
    p=run([bad],'--hub-door');assert p.returncode==2 and not p.stdout,(bad,p)
for bad in (doors_case()[:-1],doors_case(depth=69),doors_case(order=[0]*68),doors_case(two_player=65536)):
    p=run([bad],'--hub-doors');assert p.returncode==2 and not p.stdout,(bad,p)
p=run([(0xffff,0),(0xffff,1),(0xfffe,0)],'--hub-exit');assert p.returncode==0 and p.stdout=='1\n0\n0\n',p
p=run([(65536,0)],'--hub-exit');assert p.returncode==2 and not p.stdout,p
# The scene change: both actors rebuilt at their anchors + (0114, 00B0) (P1's
# from FF4446/48, wrapping to (0,0) from FEEC/FF50), 9952's limits (slow with
# +30 set), the fade-in timer (FFFF, 000A, 1, 0, 1356A/1356A/135AA), FF0EDE and
# FF0F16 cleared, and 68 reset slots with their free stack in address order.
from hub_cases import scene
p=run([scene(),scene(requested_x=0xfeec,requested_y=0xff50,p1_slow=1)],'--scene-change');assert p.returncode==0,p.stderr
actor='135 {} 551 542 551 542 0 2048 0 0 0 25 3 75334 43600 75334 {} {} 0 {}';fast='192 65344 8 12 28 10 3 11 4';tail='65535 10 1 0 79210 79210 79274 0 0 68 68 1'
p1,p2=(4294903440,4294908596),(4294903864,4294908674)
assert p.stdout.splitlines()==[' '.join((actor.format('276 224',*p1,fast),actor.format('276 224',*p2,fast),tail)),
                               ' '.join((actor.format('0 0',*p1,'96 65440 8 12 28 10 3 11 4'),actor.format('276 224',*p2,fast),tail))],p.stdout
for bad in (scene()[:-1],scene(seed=65536),(*scene(),0)):
    p=run([bad],'--scene-change');assert p.returncode==2 and not p.stdout,(bad,p)
print('collision transport goldens, widths, presence, hit and callback rejection, pickup service, 6C00 and 7910 hits, delivered, first- and second-ingredient walks, the spell countdown, completion, sparkle, door with its entry and producer, 783A quad cases, seeded phases, the carried world, the hub\'s doors and the scene change passed')
