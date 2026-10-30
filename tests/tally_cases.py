"""Authored tally boundaries, independent word/countdown and held-input expectations."""
from transition_cases import case as transition_case,expected as transition_expected,decode as transition_decode

EXTRA='palette_gate remaining skip tally_countdown credit special_gate start'.split()
DEFAULT=(0,5,0,120,0,0,0)
SOUND=((140,6,192,1),)


def case(**changes):
    extension=dict(zip(EXTRA,DEFAULT))
    for k in list(changes):
        if k in extension:extension[k]=changes.pop(k)
    return (*transition_case(**({'handler':24,'mode':128}|changes)),*extension.values())


def expected(c,**changes):
    extension=dict(zip(EXTRA[:6],c[60:66]))
    for k in list(changes):
        if k in extension:extension[k]=changes.pop(k)
    return (*transition_expected(c[:60],**changes),*extension.values())


def decode(data,count):
    rows=[tuple(map(int,l.split())) for l in data.splitlines()]
    if len(rows)!=count or any(len(r)<54 for r in rows):raise ValueError('tally output extent differs')
    transition_decode(('\n'.join(' '.join(map(str,r[:-6])) for r in rows)+'\n').encode(),count)
    return rows


def unsupported(c):
    return bool(c[7]&128) and ((c[0]==24 and c[60]) or (c[61]==0 and not c[62] and c[66] and not c[65] and c[38]&0x70==0x10))


def goldens():
    rows=[]
    def add(changes,**result):
        c=case(**changes);rows.append((c,expected(c,**result)))
    add({},tally_countdown=119)
    add(dict(tally_countdown=0),tally_countdown=65535)
    add(dict(tally_countdown=32767),tally_countdown=32766)
    add(dict(tally_countdown=32768),remaining=4,credit=3,tally_countdown=3,sounds=SOUND)
    add(dict(tally_countdown=65535,credit=179),remaining=4,credit=180,tally_countdown=3,sounds=SOUND)
    add(dict(tally_countdown=65535,credit=65534),remaining=4,credit=1,tally_countdown=3,sounds=SOUND)
    add(dict(start=255),remaining=4,skip=65535,credit=3,tally_countdown=3,sounds=SOUND)
    add(dict(start=255,skip=1,tally_countdown=0),tally_countdown=65535)
    add(dict(remaining=0))
    add(dict(remaining=0,start=255),world_mode=3)
    add(dict(remaining=0,skip=1,raw=0x10),world_mode=3)
    add(dict(remaining=0,start=255,raw=0x10,special_gate=1),world_mode=3)
    add(dict(mode=0,palette_gate=1,remaining=0,start=255,raw=0x10,service=0,speed=32768))
    add(dict(handler=25,palette_gate=1),tally_countdown=119)
    add(dict(speed=1),x=201,y=108,speed=0,sx=85,sy=4,horizontal=1,tally_countdown=119)
    add(dict(speed=65535,flags=0),x=199,y=108,speed=0,sx=83,sy=4,horizontal=1,tally_countdown=119)
    add(dict(speed=1,x=65535,y=0,sy=4),x=0,y=65535,speed=0,horizontal=1,tally_countdown=119)
    add(dict(remaining=1,start=255,repeats=2),remaining=0,skip=65535,credit=3,tally_countdown=3,sounds=SOUND,world_mode=3)
    add(dict(remaining=1,tally_countdown=0,repeats=2),remaining=0,credit=3,tally_countdown=3,sounds=SOUND)
    return rows
