"""Authored bonus table boundaries and selected assignment order."""
from tally_cases import case as tally_case,expected as tally_expected,decode as tally_decode
ASSIGNED=(0,0,0,0,0,65535,0,0,0,0,0)
CHOICES=(11,12,13,14,15,0,0,0,0,0,0)
SAMPLE=dict(special_gate=65535,world_mode=3,mailbox_count=200,mailbox_parameter=0xf14,mailbox_offset=0x8000,mailbox_bank=30,samples=((0,200,0xf14),))


def case(*,assigned=ASSIGNED,choices=CHOICES,count=6,cursor=1,**changes):
    return (*tally_case(**({'remaining':0,'start':255,'raw':0x10}|changes)),count,cursor,*assigned,*choices)


def expected(c,*,assigned=None,cursor=None,probes=0,assignments=(),**changes):
    return (*tally_expected(c[:67],**changes),c[67],c[68] if cursor is None else cursor,*(c[69:80] if assigned is None else assigned),*c[80:91],probes,len(assignments),*(v for a in assignments for v in a))


def split(row):
    n=23+4*row[21];k=n+8+3*row[n+7]+23
    if len(row)<k+26 or len(row)!=k+26+2*row[k+25]:raise ValueError('bonus output extent differs')
    return row[:k],row[k:k+24],row[k+24],tuple(tuple(row[i:i+2]) for i in range(k+26,len(row),2))


def decode(data,count):
    rows=[tuple(map(int,l.split())) for l in data.splitlines()]
    if len(rows)!=count or any(len(r)<80 for r in rows):raise ValueError('bonus output count/extent differs')
    tally_decode(('\n'.join(' '.join(map(str,split(r)[0])) for r in rows)+'\n').encode(),count)
    return rows


def goldens():
    rows=[]
    def add(changes,**result):
        c=case(**changes);rows.append((c,expected(c,**result)))
    filled=(*CHOICES[:5],*ASSIGNED[5:]);order=((4,15),(3,14),(2,13),(1,12),(0,11))
    add({},**SAMPLE,assigned=filled,cursor=6,probes=10,assignments=order)
    add(dict(cursor=0),**SAMPLE,assigned=filled,cursor=6,probes=11,assignments=order)
    add(dict(cursor=6),**SAMPLE,assigned=filled,cursor=6,probes=12,assignments=order)
    add(dict(assigned=filled),**SAMPLE,probes=6)
    add(dict(assigned=(65535,)*11,count=0),**SAMPLE,probes=1) # No division when scan terminates.
    add(dict(assigned=(*filled[:3],0,0,*ASSIGNED[5:])),**SAMPLE,assigned=filled,cursor=3,probes=16,assignments=order[:2])
    add(dict(count=1,assigned=ASSIGNED,choices=(0,)*11,cursor=0),**SAMPLE,cursor=1,probes=14,assignments=((0,0),)*5)
    add(dict(count=1,cursor=65535,choices=(65535,*CHOICES[1:])),**SAMPLE,assigned=(65535,*ASSIGNED[1:]),cursor=0,probes=3,assignments=((0,65535),))
    add(dict(start=0))
    add(dict(raw=0x50),world_mode=3)
    add(dict(skip=1),world_mode=3)
    add(dict(special_gate=1),world_mode=3)
    add(dict(mode=0,service=0))
    add(dict(repeats=2),**SAMPLE,assigned=filled,cursor=6,probes=10,assignments=order)
    add(dict(handler=25,speed=1),**SAMPLE,assigned=filled,cursor=6,probes=10,assignments=order,x=201,y=108,speed=0,sx=85,sy=4,horizontal=1)
    add(dict(speed=65535,flags=0),**SAMPLE,assigned=filled,cursor=6,probes=10,assignments=order,x=199,y=108,speed=0,sx=83,sy=4,horizontal=1)
    return rows
