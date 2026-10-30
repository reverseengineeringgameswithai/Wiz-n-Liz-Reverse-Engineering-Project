"""Authored airborne states and hand-worked goldens; no proprietary bytes."""
from movement_cases import fixture


def case(op=0,x=200,y=109,speed=0,vertical=0,delay=65535,flags=0,update=1,
         positive=192,negative=0xff40,damping=3,acceleration=12,contact_damping=11,gravity=4,
         boost=0,left=0,right=0,gate=0,sx=9,sy=10,repeats=1):
    return (op,x,y,speed,vertical,delay,flags,update,positive,negative,damping,acceleration,contact_damping,
            gravity,boost,left,right,gate,sx,sy,repeats)


def expected(c,**changes):
    # Copy initial values, then apply only the explicitly hand-worked outputs.
    fields=dict(x=c[1],y=c[2],speed=c[3],vertical=c[4],delay=c[5],update=c[7],mode=0xa5,
                first=0xa5a5,begin=0xa5a5,end=0xa5a5,counter=0xa5,reload=0xa5,sx=c[18],sy=c[19],flags=c[6],
                horizontal=0,settles=0,landings=0,calls=1,immediate=0,contact=0)
    if not changes.keys()<=fields.keys():raise ValueError('unknown expected field')
    fields.update(changes);return tuple(fields.values())


def goldens():
    idle=dict(vertical=65532,delay=65534,update=8,mode=128,first=2,begin=0,end=5,reload=4,sx=84,sy=4,settles=1,landings=1,immediate=1)
    ground=dict(mode=129,first=0,begin=0,end=5,landings=1)
    rows=[
        (case(),idle),
        (case(y=108),idle|dict(y=109,settles=2)),
        (case(y=107),dict(y=109,vertical=65532,delay=65534,update=2,sx=84,sy=3,settles=2)),
        (case(vertical=12),dict(y=107,vertical=8,delay=65534,update=2,sx=84,sy=4,settles=1)),
        (case(vertical=12,delay=1,boost=1),dict(y=107,vertical=13,delay=0,sx=84,sy=4,settles=1)),
        (case(delay=32768,boost=255),dict(y=108,vertical=1,delay=32767,sx=84,sy=4,settles=1)),
        (case(delay=0,boost=1),idle|dict(delay=65535)),
        (case(vertical=0xffd0),idle|dict(vertical=0xffcc)),
        (case(y=0xf000,vertical=0xffcf),dict(y=0xf008,delay=65534,update=2,settles=8)),
        (case(y=0xf000,vertical=0x8000),dict(y=1,delay=65534,update=2,settles=4097)),
        (case(left=1,right=1,flags=0xffff),ground|dict(x=199,speed=0xfff4,vertical=65532,delay=65534,update=4,reload=4,sx=83,sy=4,flags=0xf7ff,horizontal=1,settles=1)),
        (case(right=128,flags=0x47),ground|dict(x=201,speed=12,vertical=65532,delay=65534,update=3,reload=4,sx=85,sy=4,flags=0x847,horizontal=1,settles=1)),
        (case(left=1,right=1,gate=1),idle),
        (case(flags=0xffff,gate=65535,left=255),idle|dict(update=7)),
        (case(op=1,speed=32,y=110),dict(x=202,y=109,speed=20,sx=86,sy=3,horizontal=2)),
        (case(op=1,speed=1,y=110),dict(x=201,y=109,speed=0,sx=85,sy=4,horizontal=1)),
        (case(op=1),dict(sx=84,sy=4,settles=1,contact=1)),
        (case(op=1,speed=32,y=110,contact_damping=65535),dict(x=202,y=109,speed=0,sx=86,sy=3,horizontal=2)),
        (case(op=1,speed=32768),dict(x=1223,sx=1107,sy=3,horizontal=64513)),
        (case(op=2,speed=65535,y=110),dict(x=199,y=109,speed=0,sx=83,sy=4,horizontal=1)),
        (case(op=3,x=65535),dict(x=0,sx=65420,sy=3,horizontal=1)),
        (case(op=4,speed=192,flags=0x800),ground|dict(update=3,reload=1)),
        (case(op=4,speed=193,flags=0x800),dict(update=5,mode=129,first=6,begin=12,end=17,counter=2,reload=2,landings=1)),
        (case(op=4,speed=0xff40),ground|dict(update=4,reload=1)),
        (case(op=4,speed=0xff3f),dict(update=6,mode=129,first=6,begin=12,end=17,counter=2,reload=2,landings=1)),
        (case(op=4,speed=20,flags=8),ground|dict(update=4,reload=4)),
        (case(op=4,flags=0xffff,vertical=0x1234),ground|dict(update=7,mode=128,first=2,reload=4,immediate=1)),
        (case(op=5,speed=31),dict(reload=4)),(case(op=5,speed=32),dict(reload=3)),
        (case(op=5,speed=64),dict(reload=2)),(case(op=5,speed=96),dict(reload=1)),
        (case(op=5,speed=32768),dict(reload=4)),(case(op=6,speed=0xffe0),dict(reload=3)),
        (case(op=6,speed=0xffc0),dict(reload=2)),(case(op=6,speed=0xffa0),dict(reload=1)),
        (case(update=2,y=107,repeats=16),idle|dict(y=109,vertical=65528,delay=65535,calls=2,settles=3)),
    ]
    return [(c,expected(c,**changes)) for c,changes in rows]


def decode_results(data,count):
    rows=[tuple(map(int,line.split())) for line in data.splitlines()]
    if len(rows)!=count or any(len(r)!=21 for r in rows):raise ValueError('airborne output shape/count mismatch')
    return rows
