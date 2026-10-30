"""Authored deferred coasting entry and input-independent update expectations."""
from transition_cases import case as transition_case, expected as transition_expected, decode


def case(**changes):return transition_case(**({'handler':23,'mode':128}|changes))


def entry_expected(c):
    # The initializer sets selector but does not run the wrapper coordinate tail.
    out=list(transition_expected(c,timer=True,handler=23,mode=128,first=541));out[-16]=65535
    return tuple(out)


def entry_goldens():
    return [(c,entry_expected(c)) for c in (
        case(handler=7,mode=0,speed=32768,vertical=65535,delay=32768,first=65535,tracking_selector=0),
        case(handler=8,mode=255,flags=65535,callback=11,counter=1,first=542,target=542,speed=32,tracking_selector=32768),
        case(handler=22,mode=128,repeats=16,tracking_selector=65535))]


def goldens():
    rows=[]
    def add(changes,**result):
        c=case(**changes);rows.append((c,transition_expected(c,**result)))
    add(dict(jump=255,drop=255,up=255,down=255,left=255,right=255,direction=0))
    add(dict(speed=1),x=201,y=108,speed=0,sx=85,sy=4,horizontal=1)
    add(dict(speed=65535),x=199,y=108,speed=0,sx=83,sy=4,horizontal=1)
    add(dict(speed=32),x=202,y=108,speed=28,sx=86,sy=3,horizontal=2)
    add(dict(speed=65504),x=198,y=108,speed=65508,sx=82,sy=3,horizontal=2)
    add(dict(speed=1,x=65535,y=0,sy=4),x=0,y=65535,speed=0,horizontal=1)
    add(dict(speed=1,tracking_selector=65535),x=201,y=108,speed=0,sx=85,sy=4,horizontal=1)
    add(dict(mode=0,service=0,speed=32768,x=65535,y=65535))
    return rows
