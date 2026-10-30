"""Authored F9E2/7B9C free-stack, inherited-field and exhaustion corpus."""
import random
FIELDS=('count top second a6 fill b01 target countdown link callback private '
        'b01_2 target_2 countdown_2 link_2 callback_2 private_2').split()
DEFAULT=(68,59,58,0xffc00000,0xa5,0,0,0,0,0,0,0,0,0,0,0,0)
def case(**changes):
    assert not changes.keys()-set(FIELDS)
    return tuple((dict(zip(FIELDS,DEFAULT))|changes).values())
def representable(row,member):
    """Native inheritance is known only when the unrepresented bytes are zero."""
    j=5+6*member;return not row[j] and not row[j+4] and not row[j+5]
def expected_native_rejection(row):
    """First failure in native order; None when the pair is created."""
    for member in (0,1):
        if row[0]<=member:return 1
        if not representable(row,member):return 2
    return None
def corpus():
    rows=[]
    # Every free-stack depth, including both exhaustion boundaries, for top/second
    # pairs at both pool ends, the ordinary 59/58 pair and a non-adjacent pair.
    for count in range(69):
        for top,second in ((59,58),(67,66),(0,1),(1,0),(0,67),(33,12)):
            rows.append(case(count=count,top=top,second=second))
    # Inherited represented fields are retained exactly; written fields are not.
    for fill in (0,0x5a,0xa5,0xff):
        for target in (0,916,919,921,65535):
            for link in (0,0xffff0690,0xffff0838,0xffffffff):
                rows.append(case(fill=fill,target=target,countdown=target^0x1234,link=link,target_2=65535-target,countdown_2=target,link_2=link^1))
    # Unrepresented inherited bytes: the original keeps them; native rejects.
    for member in (0,1):
        j=5+6*member
        for k,value in ((0,1),(0,255),(4,0xfaa4),(4,0x12646),(5,1),(5,0xa5)):
            r=list(case());r[j+k]=value;rows.append(tuple(r))
            r[0]=member;rows.append(tuple(r))
    for a6 in (0,0xffff2d98,0xffff1ab4,0xffffffff):rows.append(case(a6=a6))
    rng=random.Random(0xf9e27b9c)
    for _ in range(8192):
        top,second=rng.sample(range(68),2)
        r=[rng.choice((rng.randrange(69),rng.randrange(2,69),rng.randrange(2,69),2,1,0)),top,second,rng.randrange(2**32),rng.randrange(256)]
        for _member in (0,1):
            clean=rng.random()<0.8
            r+= [0 if clean else rng.randrange(256),rng.randrange(65536),rng.randrange(65536),rng.randrange(2**32),
                 0 if clean else rng.randrange(2**32),0 if clean else rng.randrange(256)]
        rows.append(tuple(r))
    return rows


# 783A: four pops. Per member: b01 target countdown link callback private,
# then the +08/+0A words and +0C/+0D counter/reload that 783A never writes.
MEMBER=('b01','target','countdown','link','callback','private','w08','w0a','c0c','r0d')
QUAD_FIELDS=('count','s0','s1','s2','s3','a5','fill',*(f'{n}_{m}' for m in range(4) for n in MEMBER))
QUAD_DEFAULT=(68,63,62,61,60,0xffff0690,0xa5)+(0,)*40
def quad_case(**changes):
    assert not changes.keys()-set(QUAD_FIELDS)
    return tuple((dict(zip(QUAD_FIELDS,QUAD_DEFAULT))|changes).values())
def quad_representable(row,member):
    j=7+10*member;return not row[j] and not row[j+4] and not row[j+5]
def quad_expected_native_rejection(row):
    """First failure in native pop order; None when all four are created."""
    for member in range(4):
        if row[0]<=member:return 1
        if not quad_representable(row,member):return 2
    return None
def quad_corpus():
    rows=[]
    slot_sets=((63,62,61,60),(67,66,65,64),(0,1,2,3),(3,2,1,0),(0,67,33,12),(12,40,7,55))
    for count in range(69):
        for slots in slot_sets:rows.append(quad_case(count=count,**dict(zip(('s0','s1','s2','s3'),slots))))
    # Every inherited represented field per member, independently varied.
    for fill in (0,0x5a,0xa5,0xff):
        for k,(target,words,cadence) in enumerate(((0,(0,0),(0,0)),(912,(912,915),(1,1)),(65535,(65535,0),(255,0)),(1234,(0x8000,0x7fff),(0x80,0x7f)))):
            for link in (0,0xffff0690,0xffff0838,0xffffffff):
                r={}
                for m in range(4):
                    r|={f'target_{m}':target^m,f'countdown_{m}':(target+m)&65535,f'link_{m}':link^m,f'w08_{m}':words[0]^(m<<4),
                        f'w0a_{m}':words[1]^m,f'c0c_{m}':cadence[0]^m,f'r0d_{m}':cadence[1]^(m<<1)}
                rows.append(quad_case(fill=fill,**r))
    # Unrepresented inherited bytes: the original keeps them; native rejects.
    for member in range(4):
        j=7+10*member
        for k,value in ((0,1),(0,255),(4,0xfaa4),(4,0x12646),(5,1),(5,0xa5)):
            r=list(quad_case());r[j+k]=value;rows.append(tuple(r))
            r[0]=member;rows.append(tuple(r))
            r[0]=member+1;rows.append(tuple(r))
    for a5 in (0,0xffff0838,0xffff1ab4,0xffffffff):rows.append(quad_case(a5=a5))
    # 783A stores the probe position as immediates, so derived positions are
    # fixed here; derived-position word wrap is covered by native unit tests.
    rng=random.Random(0x783a78ee)
    for _ in range(8192):
        slots=rng.sample(range(68),4)
        r=[rng.choice((rng.randrange(69),rng.randrange(4,69),rng.randrange(4,69),4,3,2,1,0)),*slots,rng.randrange(2**32),rng.randrange(256)]
        for _member in range(4):
            clean=rng.random()<0.85
            r+=[0 if clean else rng.randrange(256),rng.randrange(65536),rng.randrange(65536),rng.randrange(2**32),
                0 if clean else rng.randrange(2**32),0 if clean else rng.randrange(256),
                rng.randrange(65536),rng.randrange(65536),rng.randrange(256),rng.randrange(256)]
        rows.append(tuple(r))
    return rows


# [6886,68A4): twelve pops in order (6EC8, 6EDC, 7772 ×2, 783A ×4, 7B9C ×2,
# 7C26 ×2). Per member as for 783A, plus the +02/+04 position the dormant
# 6EC8/6EDC objects keep. The prefix sets A5 itself, so there is no register field.
PREFIX_MEMBER=(*MEMBER,'x','y')
PREFIX_FIELDS=('count','fill',*(f's{m}' for m in range(12)),*(f'{n}_{m}' for m in range(12) for n in PREFIX_MEMBER))
PREFIX_DEFAULT=(68,0xa5,*range(67,55,-1))+(0,)*144
def prefix_case(**changes):
    assert not changes.keys()-set(PREFIX_FIELDS)
    return tuple((dict(zip(PREFIX_FIELDS,PREFIX_DEFAULT))|changes).values())
def prefix_representable(row,member):
    j=14+12*member;return not row[j] and not row[j+4] and not row[j+5]
def prefix_expected_native_rejection(row):
    """First failure in native pop order; None when the whole prefix commits."""
    for member in range(12):
        if row[0]<=member:return 1
        if not prefix_representable(row,member):return 2
    return None
def prefix_corpus():
    rows=[]
    slot_sets=(tuple(range(67,55,-1)),tuple(range(12)),tuple(range(11,-1,-1)),(0,67,33,12,40,7,55,21,60,3,48,29))
    for count in range(69):
        for slots in slot_sets:rows.append(prefix_case(count=count,**{f's{m}':s for m,s in enumerate(slots)}))
    # Every inherited represented field per member, independently varied.
    for fill in (0,0x5a,0xa5,0xff):
        for k,(target,words,cadence,pos) in enumerate(((0,(0,0),(0,0),(0,0)),(912,(912,915),(1,1),(150,262)),(65535,(65535,0),(255,0),(65535,65535)),(1234,(0x8000,0x7fff),(0x80,0x7f),(0x8000,0x7fff)))):
            for link in (0,0xffff0690,0xffff0838,0xffffffff):
                r={}
                for m in range(12):
                    r|={f'target_{m}':target^m,f'countdown_{m}':(target+m)&65535,f'link_{m}':link^m,f'w08_{m}':words[0]^(m<<4),f'w0a_{m}':words[1]^m,
                        f'c0c_{m}':cadence[0]^m,f'r0d_{m}':cadence[1]^(m<<1),f'x_{m}':pos[0]^(m<<8),f'y_{m}':pos[1]^(m<<2)}
                rows.append(prefix_case(fill=fill,**r))
    # Unrepresented inherited bytes: the original keeps them; native rejects.
    for member in range(12):
        j=14+12*member
        for k,value in ((0,1),(0,255),(4,0xfaa4),(4,0x12646),(5,1),(5,0xa5)):
            r=list(prefix_case());r[j+k]=value;rows.append(tuple(r))
            r[0]=member;rows.append(tuple(r))
            r[0]=member+1;rows.append(tuple(r))
    rng=random.Random(0x688668a4)
    for _ in range(8192):
        slots=rng.sample(range(68),12)
        r=[rng.choice((rng.randrange(69),rng.randrange(12,69),rng.randrange(12,69),12,rng.randrange(12))),rng.randrange(256),*slots]
        for _member in range(12):
            clean=rng.random()<0.97
            r+=[0 if clean else rng.randrange(256),rng.randrange(65536),rng.randrange(65536),rng.randrange(2**32),
                0 if clean else rng.randrange(2**32),0 if clean else rng.randrange(256),
                rng.randrange(65536),rng.randrange(65536),rng.randrange(256),rng.randrange(256),rng.randrange(65536),rng.randrange(65536)]
        rows.append(tuple(r))
    return rows


# [68A4,68BC): 6A94 makes one pickup per FF312C kind that is not FFFF (FF4C80
# positions consumed densely), then 6EB6 links P1 and P2: up to eighteen pops.
TAIL_FIELDS=('count','fill',*(f's{m}' for m in range(18)),*(f'kind_{k}' for k in range(16)),*(f'qty_{k}' for k in range(16)),
             *(f'{a}_{k}' for k in range(16) for a in ('px','py')),*(f'{n}_{m}' for m in range(18) for n in PREFIX_MEMBER))
TAIL_DEFAULT=(68,0xa5,55,54,53,52,*range(51,37,-1),5,6,*(0xffff,)*14,*(0,)*16,0x2d0,0xa0,0x370,0xa0,*(0,)*28)+(0,)*216
def tail_case(**changes):
    assert not changes.keys()-set(TAIL_FIELDS)
    return tuple((dict(zip(TAIL_FIELDS,TAIL_DEFAULT))|changes).values())
def tail_members(row):return 2+sum(k!=0xffff for k in row[20:36])
def tail_representable(row,member):
    j=84+12*member;return not row[j] and not row[j+4] and not row[j+5]
def tail_expected_native_rejection(row):
    """First failure in native pop order; None when the whole tail commits."""
    for member in range(tail_members(row)):
        if row[0]<=member:return 1
        if not tail_representable(row,member):return 2
    return None
KINDS=(0,5,6,13,14,0x7fff,0x8000,0xd3ff,0xfffe,0x1fd,0x205,0x20d,0x204,0x2aaa)
def tail_corpus():
    rows=[]
    slot_sets=((55,54,53,52,*range(51,37,-1)),tuple(range(18)),tuple(range(67,49,-1)),(0,67,33,12,40,7,55,21,60,3,48,29,1,66,2,65,4,64))
    for count in range(69):
        for slots in slot_sets:rows.append(tail_case(count=count,**{f's{m}':s for m,s in enumerate(slots)}))
    # Every table shape: n pickups at chosen entries, each frame family, count 2
    # cadence, Y + 16 wrap; positions are consumed densely.
    rng=random.Random(0x68a468bc)
    for n in range(17):
        for variant in range(6):
            entries=sorted(rng.sample(range(16),n));r={f'kind_{k}':0xffff for k in range(16)}
            for i,k in enumerate(entries):
                r[f'kind_{k}']=KINDS[(i+variant)%len(KINDS)];r[f'qty_{k}']=(2,0,1,0xffff,7)[(i+variant)%5]
            for k in range(16):r[f'px_{k}']=(k*0x40+variant)&65535;r[f'py_{k}']=(0xffe8+k*3+variant)&65535
            rows.append(tail_case(**r,**{f's{m}':s for m,s in enumerate(range(67,49,-1))}))
    # Exhaustion after every pop for every pickup count (0..16 pickups + 2 links).
    for n in range(17):
        tables={f'kind_{k}':(k%14 if k<n else 0xffff) for k in range(16)}
        for count in range(n+3):rows.append(tail_case(count=count,**tables,**{f's{m}':s for m,s in enumerate(range(67,49,-1))}))
    # Every inherited represented field per member.
    for fill in (0,0x5a,0xff):
        for target,words,cadence,pos in ((912,(912,915),(1,1),(150,262)),(65535,(65535,0),(255,0),(65535,65535)),(1234,(0x8000,0x7fff),(0x80,0x7f),(0x8000,0x7fff))):
            for link in (0,0xffff0690,0xffffffff):
                r={}
                for m in range(4):
                    r|={f'target_{m}':target^m,f'countdown_{m}':(target+m)&65535,f'link_{m}':link^m,f'w08_{m}':words[0]^(m<<4),f'w0a_{m}':words[1]^m,
                        f'c0c_{m}':cadence[0]^m,f'r0d_{m}':cadence[1]^(m<<1),f'x_{m}':pos[0]^(m<<8),f'y_{m}':pos[1]^(m<<2)}
                rows.append(tail_case(fill=fill,**r))
    # Unrepresented inherited bytes: the original keeps them; native rejects.
    for member in range(4):
        j=84+12*member
        for k,value in ((0,1),(4,0xfaa4),(5,1)):
            r=list(tail_case());r[j+k]=value;rows.append(tuple(r))
            r[0]=member;rows.append(tuple(r))
            r[0]=member+1;rows.append(tuple(r))
    for _ in range(8192):
        slots=rng.sample(range(68),18);kinds=[0xffff if rng.random()<0.6 else rng.choice((rng.choice(KINDS),rng.randrange(65535))) for _k in range(16)]
        members=2+sum(k!=0xffff for k in kinds)
        r=[rng.choice((rng.randrange(69),rng.randrange(members,69),rng.randrange(members,69),members,rng.randrange(members))),rng.randrange(256),*slots,*kinds,
           *(rng.choice((2,rng.randrange(65536))) for _k in range(16)),*(rng.randrange(65536) for _k in range(32))]
        for _member in range(18):
            clean=rng.random()<0.97
            r+=[0 if clean else rng.randrange(256),rng.randrange(65536),rng.randrange(65536),rng.randrange(2**32),
                0 if clean else rng.randrange(2**32),0 if clean else rng.randrange(256),
                rng.randrange(65536),rng.randrange(65536),rng.randrange(256),rng.randrange(256),rng.randrange(65536),rng.randrange(65536)]
        rows.append(tuple(r))
    return rows


# [68BC,68C4): 7DB8 message selection with CB72's priority gate, then 6EF0's gate.
MESSAGE_FIELDS=('two_player','fruit_returned','pair_request','tilemap','priority','row',*(f'kind_{k}' for k in range(16)))
MESSAGE_DEFAULT=(0,0,0,0xffffe000,0,3,5,6,*(0xffff,)*14)
def message_case(**changes):
    assert not changes.keys()-set(MESSAGE_FIELDS)
    return tuple((dict(zip(MESSAGE_FIELDS,MESSAGE_DEFAULT))|changes).values())
def message_corpus():
    rows=[]
    # Every priority byte against both messages, and every kind count.
    for priority in range(256):
        rows.append(message_case(priority=priority))
        rows.append(message_case(priority=priority,fruit_returned=1))
    for n in range(17):
        rows.append(message_case(**{f'kind_{k}':(k if k<n else 0xffff) for k in range(16)}))
    # Gates: FF33E2/FF31AA/FF316C words, including high-bit and odd values.
    for two in (0,1,0x8000,0xffff):
        for returned in (0,1,0x8000,0xffff):
            for pair in (0,1,0x8000,0xffff):rows.append(message_case(two_player=two,fruit_returned=returned,pair_request=pair))
    # Rows and tilemap bases that wrap the VRAM destination word.
    for row in (0,1,0x1ff,0x200,0x7fff,0x8000,0xffff):
        for base in (0,0xffffe000,0x1234fff0,0xfffffff2):rows.append(message_case(row=row,tilemap=base))
    rng=random.Random(0x7db86ef0)
    for _ in range(4096):
        rows.append((rng.choice((0,0,0,rng.randrange(65536))),rng.choice((0,0,rng.randrange(65536))),rng.choice((0,0,0,rng.randrange(65536))),rng.randrange(2**32),
                     rng.randrange(256),rng.randrange(65536),*(rng.choice((0xffff,0xffff,rng.randrange(65536))) for _k in range(16))))
    return rows


# [68C4,68D4): 7FBE, 7154, 735E and 7568, each two pops behind its gate word
# (FF3172..FF3178). Per member as for 783A; positions are always written.
PAIRS_FIELDS=('count','fill','a5',*(f'gate_{i}' for i in range(4)),'p2x','p2y',*(f's{m}' for m in range(8)),*(f'{n}_{m}' for m in range(8) for n in MEMBER))
PAIRS_DEFAULT=(68,0xa5,0xffff0690,1,1,1,1,0x2d0,0xa0,*range(51,43,-1))+(0,)*80
def pairs_case(**changes):
    assert not changes.keys()-set(PAIRS_FIELDS)
    return tuple((dict(zip(PAIRS_FIELDS,PAIRS_DEFAULT))|changes).values())
def pairs_members(row):return 2*sum(g!=0 for g in row[3:7])
def pairs_representable(row,member):
    j=17+10*member;return not row[j] and not row[j+4] and not row[j+5]
def pairs_expected_native_rejection(row):
    """First failure in native pop order; None when every open pair commits."""
    for member in range(pairs_members(row)):
        if row[0]<=member:return 1
        if not pairs_representable(row,member):return 2
    return None
def pairs_shape(row,b):
    """Open-gate mask, then each pair's pops ordered by address (partner, lead)."""
    mask=sum(1<<i for i in range(4) if row[3+i]);pops=row[9:9+pairs_members(row)]
    return b[1]==mask and list(b[2:2+len(pops)])==[s for k in range(0,len(pops),2) for s in sorted(pops[k:k+2])]
def pairs_corpus():
    rows=[]
    slot_sets=(tuple(range(51,43,-1)),tuple(range(8)),(0,67,33,12,40,7,55,21),(12,40,7,55,21,60,3,48))
    # Every free-stack depth with all four gates open (exhaustion after each pop).
    for count in range(69):
        for slots in slot_sets:rows.append(pairs_case(count=count,**{f's{m}':s for m,s in enumerate(slots)}))
    # Every gate combination, both pop orders, gate word shapes and caller A5.
    for mask in range(16):
        for words in ((1,1,1,1),(0x8000,0xffff,2,0x7fff)):
            for slots in slot_sets:
                for a5 in (0xffff0690,0xffff0838):
                    rows.append(pairs_case(a5=a5,**{f'gate_{i}':(words[i] if mask>>i&1 else 0) for i in range(4)},**{f's{m}':s for m,s in enumerate(slots)}))
    for a5 in (0,0xffff1ab4,0xffffffff):rows.append(pairs_case(a5=a5))
    # 7FBE's lead position from the P2 control's +3C/+3E, with word wrap.
    for x,y in ((0,0),(7,0xffe7),(8,0xffe8),(0xffff,0xffff),(0x8000,0x7fff),(0x2d0,0xa0)):
        rows.append(pairs_case(p2x=x,p2y=y,gate_1=0,gate_2=0,gate_3=0))
    # Every inherited represented field per member, independently varied.
    for fill in (0,0x5a,0xa5,0xff):
        for target,words,cadence in ((0,(0,0),(0,0)),(912,(912,915),(1,1)),(65535,(65535,0),(255,0)),(1234,(0x8000,0x7fff),(0x80,0x7f))):
            for link in (0,0xffff0690,0xffff0838,0xffffffff):
                r={}
                for m in range(8):
                    r|={f'target_{m}':target^m,f'countdown_{m}':(target+m)&65535,f'link_{m}':link^m,f'w08_{m}':words[0]^(m<<4),
                        f'w0a_{m}':words[1]^m,f'c0c_{m}':cadence[0]^m,f'r0d_{m}':cadence[1]^(m<<1)}
                rows.append(pairs_case(fill=fill,**r))
    # Unrepresented inherited bytes: the original keeps them; native rejects.
    for member in range(8):
        j=17+10*member
        for k,value in ((0,1),(0,255),(4,0x8040),(4,0x12646),(5,1),(5,0xa5)):
            r=list(pairs_case());r[j+k]=value;rows.append(tuple(r))
            r[0]=member;rows.append(tuple(r))
            r[0]=member+1;rows.append(tuple(r))
    rng=random.Random(0x68c468d4)
    for _ in range(8192):
        slots=rng.sample(range(68),8);gates=[rng.choice((0,0,1,rng.randrange(65536))) for _i in range(4)]
        members=2*sum(g!=0 for g in gates)
        r=[rng.choice((rng.randrange(69),rng.randrange(members,69),rng.randrange(members,69),members,rng.randrange(members+1))),rng.randrange(256),
           rng.choice((0xffff0690,0xffff0838,rng.randrange(2**32))),*gates,rng.randrange(65536),rng.randrange(65536),*slots]
        for _member in range(8):
            clean=rng.random()<0.95
            r+=[0 if clean else rng.randrange(256),rng.randrange(65536),rng.randrange(65536),rng.randrange(2**32),
                0 if clean else rng.randrange(2**32),0 if clean else rng.randrange(256),
                rng.randrange(65536),rng.randrange(65536),rng.randrange(256),rng.randrange(256)]
        rows.append(tuple(r))
    return rows
