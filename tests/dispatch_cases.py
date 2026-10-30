"""Authored whole-wrapper cases; tracking outputs are not fed back into actor motion."""
from actions_cases import case as action_case, expected as action_expected, decode as action_decode


def case(*,service=1,tracking_selector=0,tracking_x=0x1234,tracking_y=0x5678,**changes):
    return (*action_case(**changes),service,tracking_selector,tracking_x,tracking_y)


def expected(c,**changes):
    result=action_expected(c[:43],**changes)
    x,y=(0xff80,0xff80) if c[44]==65535 else ((result[1]+4)&65535,(result[2]+6)&65535)
    return (*result,c[43],c[44],x,y)


def decode(data,count):
    rows=[tuple(map(int,l.split())) for l in data.splitlines()]
    if len(rows)!=count or any(len(r)<35 for r in rows):raise ValueError('dispatch output extent differs')
    action_decode(('\n'.join(' '.join(map(str,r[:-4])) for r in rows)+'\n').encode(),count)
    return rows


def goldens():
    rows=[]
    def add(changes,**result):
        c=case(**changes);rows.append((c,expected(c,**result)))
    # Return-only is an observed handler, not a fallback for unknown identities.
    add(dict(handler=20,mode=128,speed=0x8000,jump=1,drop=1,up=1,down=1,left=1,right=1))
    add(dict(handler=20,mode=128,x=65535,y=65535))
    add(dict(handler=20,mode=128,tracking_selector=65535))
    # Inactive bypasses even unsupported service/callback/handler, but runs the tail.
    add(dict(handler=20,mode=5,callback=0,first=2,target=2,counter=1,service=0,x=65533,y=65531))
    add(dict(handler=20,mode=0,service=0,tracking_selector=65535))
    # AA50 only initializes, then the wrapper executes the selected airborne handler once.
    # Flat contact equals the foot probe at Y109: the airborne pass lands
    # immediately and consumes idle, without descending a pixel.
    for flags in (0,0x800):
        add(dict(handler=20,flags=flags,mode=135,first=542,begin=542,end=551,counter=1,reload=3,target=542,callback=11),
            handler=7 if flags else 8,vertical=65532,delay=65534,mode=128,first=2,begin=0,end=5,counter=6,reload=4,sx=84,sy=4,settles=2,landings=1)
    # Action's contextual callback still runs two handlers before the later service.
    add(dict(handler=17,mode=135,first=31,begin=30,end=35,counter=1,reload=2,target=31,callback=10),
        handler=7,mode=128,first=2,counter=2,sx=84,sy=4,settles=2)
    add(dict(handler=16,mode=128,up=1,raw=0xbf),cooldown=2,interval=15,
        mailbox_count=200,mailbox_parameter=0xf14,mailbox_offset=0x8000,mailbox_bank=30,samples=((0,200,0xf14),))
    return rows
