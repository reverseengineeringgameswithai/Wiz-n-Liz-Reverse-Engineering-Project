"""Authored actor-handler inputs and independently calculated flat-terrain outputs."""
from movement_cases import fixture

FIELDS = 'handler x y speed vertical delay flags mode first begin end counter reload target cycles callback positive negative damping air_acc contact gravity ground_acc impulse jump_delay jump drop up down left right gate sx sy repeats'.split()
DEFAULT = (7,200,109,0,0,65535,0x800,165,42405,42405,42405,165,165,0x1234,0x5678,0,
           192,0xff40,3,12,11,4,8,28,10,0,0,0,0,0,0,0,9,10,1)
HANDLERS = [0xcafe,0xaaea,0xab04,0xa408,0xa546,0xa6c8,0xa88e,0xa1be,0xa246,0xa2ec,0xa384,0xa4ec,0xa634,0xa27e,0xa7ec,0xa9b2,0x9c90,0x9d26,0x9d88,0x9dcc,0x12646,0x710e,0x7126,0x632a,0x51c8,0x5222,0x5204,0x5132,0x5188]
CALLBACKS = [0xcafe,0xa2e8,0xa380,0xa50e,0xa654,0xa774,0xa93a,0xa814,0xa9da,0xf938,0xa196,0xaa50]


def case(**changes):
    if changes.keys()-set(FIELDS): raise ValueError('unknown actor field')
    d=dict(zip(FIELDS,DEFAULT));d.update(changes);return tuple(int(v) for v in d.values())


def expected(c,*,horizontal=0,settles=0,landings=0,sounds=(),**changes):
    d=dict(zip(FIELDS[:16],c[:16]));d.update(sx=c[32],sy=c[33])
    if changes.keys()-d.keys(): raise ValueError('unknown actor output')
    d.update(changes)
    return (*d.values(),horizontal,settles,landings,len(sounds),c[34],*(v for r in sounds for v in r))


def goldens():
    sounds=((60,1,192,1),(107,1,192,2))
    rows=[]
    def add(changes,**result):
        c=case(**changes);rows.append((c,expected(c,**result)))
    add({},sx=84,sy=4,settles=1)
    add({'handler':8,'flags':0},sx=84,sy=4,settles=1)
    add({'right':1,'jump':1},handler=3,mode=129,first=2,begin=0,end=5,counter=4,reload=4)
    add({'handler':8,'flags':0,'left':255},handler=4,mode=129,first=2,begin=0,end=5,counter=4,reload=4)
    add({'left':1},handler=10,flags=0,mode=135,first=47,begin=42,end=47,target=42,counter=3,reload=3,callback=2)
    add({'handler':8,'flags':0,'right':1},handler=9,flags=2048,mode=135,first=47,begin=42,end=47,target=42,counter=3,reload=3,callback=1)
    add({'jump':255},handler=1,vertical=29,delay=9,y=105,mode=129,first=58,begin=60,end=61,counter=6,reload=6,sounds=sounds,sx=84,sy=4,settles=1)
    add({'handler':3,'speed':64,'right':255},x=203,speed=68,reload=2,horizontal=3,sx=87,sy=4)
    add({'handler':4,'flags':0,'speed':65472,'left':255},x=197,speed=65468,reload=2,horizontal=3,sx=81,sy=4)
    add({'handler':3,'speed':149,'right':1},handler=5,x=205,speed=145,first=6,begin=12,end=17,counter=2,reload=2,horizontal=5,sx=89,sy=4)
    add({'handler':5,'speed':148},handler=3,x=205,speed=144,first=0,begin=0,end=5,counter=1,reload=1,horizontal=5,sx=89,sy=4)
    add({'handler':3,'speed':4},handler=7,speed=0,mode=128,first=2,reload=4,sx=84,sy=4,settles=1)
    # Airborne lands then idle executes in the SAME call, adding a settle query.
    add({'handler':2,'flags':0},handler=8,vertical=65532,mode=128,first=2,begin=0,end=5,reload=4,sx=84,sy=4,settles=2,landings=1)
    # A1FA removes the idle return; +2 y, delayed entry decrements to FFFE,
    # falling vertical -4 and two more settling calls. Idle must not run again.
    add({'drop':255},handler=2,y=113,vertical=65532,delay=65534,mode=129,first=58,begin=60,end=61,counter=6,reload=6,sx=84,sy=7,settles=2)
    add({'handler':11,'speed':64,'left':1},x=202,speed=52,sx=86,sy=4,horizontal=2)
    add({'handler':12,'speed':64,'jump':1,'gate':1},x=203,sx=87,sy=4,horizontal=3)
    add({'handler':5,'speed':160,'jump':1},handler=1,x=205,y=105,speed=156,vertical=29,delay=9,mode=133,
        first=62,begin=62,end=63,counter=2,reload=2,target=63,cycles=2,callback=5,horizontal=5,sx=89,sy=3,sounds=sounds)
    return rows


def decode_results(data,count):
    rows=[tuple(map(int,line.split())) for line in data.splitlines()]
    if len(rows)!=count or any(len(r)<23 or len(r)!=23+4*r[21] for r in rows):
        raise ValueError('actor output shape/count mismatch')
    return rows
