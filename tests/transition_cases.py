"""Authored transition boundary cases; pointer encodings stay in research adapters."""
from dispatch_cases import case as dispatch_case, expected as dispatch_expected, decode as dispatch_decode
from actions_cases import expected as action_expected

EXTRA='direction countdown transition_reload level curve_r curve_g curve_b dirty palette_scope requested_x requested_y saved_x saved_y'.split()
DEFAULT=(0,9,3,7,0,0,0,123,456,0x789a,0xbcde,8,9)


def case(**changes):
    extension=dict(zip(EXTRA,DEFAULT))
    for k in list(changes):
        if k in extension:extension[k]=changes.pop(k)
    return (*dispatch_case(**({'handler':21,'mode':128}|changes)),*extension.values())


def expected(c,*,timer=False,**changes):
    extension=dict(zip(EXTRA,c[47:]))
    for k in list(changes):
        if k in extension:extension[k]=changes.pop(k)
    core=(*action_expected(c[:43],**changes),*c[43:47]) if timer else dispatch_expected(c[:47],**changes)
    return (*core,*extension.values())


def decode(data,count):
    rows=[tuple(map(int,l.split())) for l in data.splitlines()]
    if len(rows)!=count or any(len(r)<48 for r in rows):raise ValueError('transition output extent differs')
    dispatch_decode(('\n'.join(' '.join(map(str,r[:-13])) for r in rows)+'\n').encode(),count)
    return rows


def goldens():
    rows=[]
    def add(changes,**result):
        c=case(**changes);rows.append((c,expected(c,**result)))
    start=dict(handler=22,direction=1,countdown=1,transition_reload=1,level=14,curve_r=1,curve_g=1,curve_b=2,palette_scope=0)
    add({},**start)
    add(dict(speed=1),**start,x=201,y=108,speed=0,sx=85,sy=4,horizontal=1)
    add(dict(speed=65535),**start,x=199,y=108,speed=0,sx=83,sy=4,horizontal=1)
    add(dict(handler=22,direction=1))
    add(dict(handler=22,direction=65535,up=1,down=1,jump=1))
    add(dict(handler=22,direction=0),world_mode=7,saved_x=0x789a,saved_y=0xbcde)
    add(dict(handler=22,direction=0,speed=1),world_mode=7,saved_x=0x789a,saved_y=0xbcde,x=201,y=108,speed=0,sx=85,sy=4,horizontal=1)
    add(dict(handler=21,mode=0,service=0))
    return rows


def timer_goldens():
    rows=[]
    def add(changes,**result):
        c=case(**changes);rows.append((c,expected(c,timer=True,**result)))
    add(dict(direction=0))
    add(dict(direction=1,countdown=1),countdown=0)
    add(dict(direction=65535,countdown=32768),countdown=32767)
    add(dict(direction=1,countdown=0,level=0),direction=0,dirty=65535)
    add(dict(direction=65535,countdown=0,level=14),direction=0,dirty=65535)
    add(dict(direction=1,countdown=0,level=1),level=65535,countdown=3,dirty=65535)
    add(dict(direction=32768,countdown=0,level=65535),level=1,countdown=3,dirty=65535)
    add(dict(direction=1,countdown=1,level=14,transition_reload=1,repeats=16),direction=0,countdown=0,level=0,dirty=65535)
    return rows
