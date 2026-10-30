"""Authored 5132/5188 boundaries, with independent last-unit/deferred expectations."""
from tally_cases import case as tally_case,expected as tally_expected,decode as tally_decode,SOUND
EXTRA='secondary_gate secondary_remaining marker selection target_selection'.split()
DEFAULT=(0,0,7,2,3)
START=dict(handler=28,direction=1,countdown=1,transition_reload=1,level=14,curve_r=1,curve_g=1,curve_b=2,palette_scope=0)


def case(**changes):
    extra=dict(zip(EXTRA,DEFAULT))
    for k in list(changes):
        if k in extra:extra[k]=changes.pop(k)
    return (*tally_case(**({'handler':27}|changes)),*extra.values())


def expected(c,**changes):
    extra=dict(zip(EXTRA,c[67:]))
    for k in list(changes):
        if k in extra:extra[k]=changes.pop(k)
    return (*tally_expected(c[:67],**changes),*extra.values())


def decode(data,count):
    rows=[tuple(map(int,l.split())) for l in data.splitlines()]
    if len(rows)!=count or any(len(r)<59 for r in rows):raise ValueError('exit tally output extent differs')
    tally_decode(('\n'.join(' '.join(map(str,r[:-5])) for r in rows)+'\n').encode(),count)
    return rows


def goldens():
    rows=[]
    def add(changes,**result):
        c=case(**changes);rows.append((c,expected(c,**result)))
    add({},tally_countdown=119)
    add(dict(tally_countdown=0),tally_countdown=65535)
    add(dict(tally_countdown=32768),remaining=4,credit=3,tally_countdown=3,sounds=SOUND)
    add(dict(remaining=1,tally_countdown=65535,credit=65534),remaining=0,credit=1,tally_countdown=60,sounds=SOUND)
    add(dict(remaining=1,start=255),remaining=0,skip=65535,credit=3,tally_countdown=60,sounds=SOUND)
    add(dict(remaining=1,start=255,repeats=2),**START,remaining=0,skip=65535,credit=3,tally_countdown=60,sounds=SOUND)
    add(dict(remaining=1,tally_countdown=0,repeats=2),remaining=0,credit=3,tally_countdown=60,sounds=SOUND)
    add(dict(remaining=0))
    add(dict(remaining=0,start=255),**START)
    add(dict(remaining=0,skip=1),**START)
    add(dict(remaining=0,secondary_gate=1))
    add(dict(remaining=0,secondary_remaining=65535))
    add(dict(remaining=1,secondary_gate=1,secondary_remaining=1,tally_countdown=0),tally_countdown=65535)
    add(dict(handler=28,direction=1))
    add(dict(handler=28,direction=65535))
    add(dict(handler=28),world_mode=1,saved_x=0x789a,saved_y=0xbcde)
    add(dict(handler=28,selection=65535,target_selection=65535),marker=0,world_mode=1,saved_x=0x789a,saved_y=0xbcde)
    add(dict(handler=28,secondary_gate=1,secondary_remaining=1),world_mode=1,saved_x=0x789a,saved_y=0xbcde)
    add(dict(mode=0,service=0,remaining=0,secondary_gate=1,secondary_remaining=1))
    add(dict(speed=1),x=201,y=108,speed=0,sx=85,sy=4,horizontal=1,tally_countdown=119)
    add(dict(speed=65535,flags=0),x=199,y=108,speed=0,sx=83,sy=4,horizontal=1,tally_countdown=119)
    add(dict(handler=28,speed=1,x=65535,y=0,sy=4),x=0,y=65535,speed=0,horizontal=1,world_mode=1,saved_x=0x789a,saved_y=0xbcde)
    return rows
