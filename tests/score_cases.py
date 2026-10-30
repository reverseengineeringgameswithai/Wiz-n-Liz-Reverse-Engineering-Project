"""Authored valid packed-decimal secondary tally contracts; invalid digits reject."""
from exit_tally_cases import case as exit_case, expected as exit_expected, decode as exit_decode, START
from tally_cases import SOUND
EXTRA='score threshold increment rewards score_scratch'.split()
DEFAULT=(0,0x10000,0x10000,8,0xdeadbeef)
REWARD=dict(samples=((1,230,0x20e4),),mailbox_count=230,mailbox_parameter=0x20e4,mailbox_offset=0xa5ea,mailbox_bank=30)


def packed(n):return int(str(n),16)


def case(**changes):
    extra=dict(zip(EXTRA,DEFAULT))
    for k in list(changes):
        if k in extra:extra[k]=changes.pop(k)
    return (*exit_case(**({'remaining':0,'secondary_gate':1,'secondary_remaining':2,'tally_countdown':65535}|changes)),*extra.values())


def expected(c,advances=0,**changes):
    extra=dict(zip(EXTRA,c[72:]))
    for k in list(changes):
        if k in extra:extra[k]=changes.pop(k)
    return (*exit_expected(c[:72],**changes),*extra.values(),advances)


def decode(data,count):
    rows=[tuple(map(int,l.split())) for l in data.splitlines()]
    if len(rows)!=count or any(len(r)<65 for r in rows):raise ValueError('score output extent differs')
    exit_decode(('\n'.join(' '.join(map(str,r[:-6])) for r in rows)+'\n').encode(),count)
    return rows


def goldens():
    rows=[]
    def add(changes,**result):
        c=case(**changes);rows.append((c,expected(c,**result)))
    consumed=dict(secondary_remaining=1,tally_countdown=3,score_scratch=0x10000,sounds=SOUND)
    add({},score=0x10000,**consumed) # Equality: no reward.
    add(dict(tally_countdown=0),tally_countdown=65535)
    add(dict(tally_countdown=32767),tally_countdown=32766)
    add(dict(start=255,tally_countdown=60),skip=65535,score=0x10000,**consumed)
    add(dict(start=255,skip=1,tally_countdown=0),tally_countdown=65535)
    add(dict(score=0x10000),score=0x20000,threshold=0x20000,rewards=9,advances=1,**consumed,**REWARD)
    add(dict(score=0x80000,increment=0x20000),score=0x90000,threshold=0x90000,rewards=9,secondary_remaining=1,tally_countdown=3,score_scratch=0x20000,sounds=SOUND,advances=4,**REWARD)
    for rewards,new in ((9,9),(10,11),(65535,0)):
        add(dict(score=0x10000,rewards=rewards),score=0x20000,threshold=0x20000,rewards=new,advances=1,**consumed,**REWARD)
    add(dict(score=0x99999999),score=0x9999,**consumed)
    add(dict(secondary_remaining=1),score=0x10000,secondary_remaining=0,tally_countdown=3,score_scratch=0x10000,sounds=SOUND)
    add(dict(secondary_remaining=1,start=255,repeats=2),**START,score=0x10000,secondary_remaining=0,skip=65535,tally_countdown=3,score_scratch=0x10000,sounds=SOUND)
    add(dict(secondary_gate=0))
    add(dict(secondary_remaining=0,start=255),**START)
    add(dict(remaining=1),remaining=0,credit=3,tally_countdown=60,sounds=SOUND)
    add(dict(handler=28,direction=1))
    add(dict(mode=0,service=0))
    add(dict(speed=1),x=201,y=108,speed=0,sx=85,sy=4,horizontal=1,score=0x10000,**consumed)
    add(dict(speed=65535,flags=0),x=199,y=108,speed=0,sx=83,sy=4,horizontal=1,score=0x10000,**consumed)
    return rows
