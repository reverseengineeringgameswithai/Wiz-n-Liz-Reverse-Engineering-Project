"""Independent action inputs/goldens; global mailbox is a research adapter only."""
from actor_cases import case as actor_case, expected as actor_expected

EXTRA = 'world_mode cooldown interval raw mailbox_count mailbox_parameter mailbox_offset mailbox_bank'.split()
DEFAULT = (19,65535,12,255,0x1111,0x2222,0x3333,0x4444)


def case(**changes):
    extension=dict(zip(EXTRA,DEFAULT))
    for k in list(changes):
        if k in extension:extension[k]=changes.pop(k)
    return (*actor_case(**changes),*extension.values())


def expected(c,*,samples=(),**changes):
    extension=dict(zip(EXTRA[:3]+EXTRA[4:],c[35:38]+c[39:43]))
    for k in list(changes):
        if k in extension:extension[k]=changes.pop(k)
    return (*actor_expected(c[:35],**changes),*extension.values(),len(samples),*(v for r in samples for v in r))


def split(row):
    if len(row)<31:raise ValueError('incomplete action output')
    n=23+4*row[21]
    if len(row)<n+8 or len(row)!=n+8+3*row[n+7]:raise ValueError('action request extent differs')
    return row[:n],row[n:n+7],tuple(tuple(row[i:i+3]) for i in range(n+8,len(row),3))


def decode(data,count):
    rows=[tuple(map(int,l.split())) for l in data.splitlines()]
    if len(rows)!=count:raise ValueError('action output count differs')
    for row in rows:split(row)
    return rows


def goldens():
    rows=[]
    def add(changes,**result):
        c=case(**changes);rows.append((c,expected(c,**result)))
    add({'up':255},handler=16,mode=133,first=30,begin=30,end=35,target=34,counter=3,reload=3,callback=9)
    add({'handler':8,'flags':0,'down':255},handler=18,mode=133,first=36,begin=36,end=41,target=40,counter=3,reload=3,callback=9)
    add({'up':1,'down':1,'speed':4},handler=16,speed=0,mode=133,first=30,begin=30,end=35,target=34,counter=3,reload=3,callback=9)
    add({'handler':16,'up':1,'raw':0xbf},cooldown=2,interval=15,mailbox_count=200,mailbox_parameter=0xf14,mailbox_offset=0x8000,mailbox_bank=30,samples=((0,200,0xf14),))
    # Wrapped SUBI's N flag, not a signed subtraction with overflow correction.
    add({'handler':16,'raw':0,'interval':0x8000,'up':1},cooldown=0x7ff6,interval=0x8003,mailbox_count=200,mailbox_parameter=0xf14,mailbox_offset=0x8000,mailbox_bank=30,samples=((0,200,0xf14),))
    add({'handler':16,'raw':0,'interval':65535,'up':1},cooldown=0,interval=2,mailbox_count=200,mailbox_parameter=0xf14,mailbox_offset=0x8000,mailbox_bank=30,samples=((0,200,0xf14),))
    # Both hold paths defer jump without changing animation or executing motion.
    add({'handler':16,'jump':1,'raw':0},handler=13)
    add({'handler':18,'jump':255,'down':1,'gate':65535},handler=13)
    add({'handler':16,'begin':65535,'down':1},handler=17,mode=135,target=0,counter=2,reload=2,callback=10)
    add({'handler':18,'begin':36,'right':1},handler=19,mode=135,target=37,counter=2,reload=2,callback=10)
    add({'handler':17,'jump':1,'up':1,'right':1})
    add({'handler':19,'jump':1,'down':1,'drop':1})
    return rows


def presentation_goldens():
    rows=[]
    # Hold callback sees already-advanced frame, freezes only mode.
    c=case(handler=16,mode=133,first=34,begin=30,end=35,counter=1,reload=3,target=34,callback=9,up=1)
    rows.append((c,expected(c,first=35,counter=3,mode=128)))
    # Release callback executes idle/up with the presentation return pending.
    c=case(handler=19,mode=135,first=37,begin=36,end=41,counter=1,reload=2,target=37,callback=10,up=1)
    rows.append((c,expected(c,handler=16,mode=133,first=30,begin=30,end=35,target=34,counter=3,reload=3,callback=9)))
    for flags,handler in ((0,8),(0x800,7)):
        c=case(handler=17,flags=flags,mode=135,first=31,begin=30,end=35,counter=1,reload=2,target=31,callback=10)
        rows.append((c,expected(c,handler=handler,mode=128,first=2,counter=2,sx=84,sy=4,settles=1)))
    return rows


def scheduled_goldens():
    rows=[]
    # Callback enters idle then the scheduled handler enters idle again: two queries.
    c=case(handler=17,mode=135,first=31,begin=30,end=35,counter=1,reload=2,target=31,callback=10)
    rows.append((c,expected(c,handler=7,mode=128,first=2,counter=2,sx=84,sy=4,settles=2)))
    # Jump during release completion: callback integrates once, wrapper again.
    # Both zero-speed airborne passes settle: 109 -> 105, then the flat
    # record (contact 5 versus local Y 0) adds one before 106 - 4 = 102.
    c=case(handler=19,mode=135,first=37,begin=36,end=41,counter=1,reload=2,target=37,callback=10,jump=1)
    rows.append((c,expected(c,handler=1,y=102,vertical=30,delay=8,mode=129,first=58,begin=60,end=61,counter=6,reload=6,
                          sx=84,sy=0,settles=2,sounds=((60,1,192,1),(107,1,192,2)))))
    return rows
