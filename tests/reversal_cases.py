"""Hand-calculated reversal/effect boundaries and strict comparison transports."""
from actor_cases import case,expected


def actor_goldens():
    rows=[]
    for handler,speed,left,right,result_handler,result_speed,x,flags,callback,ex,ey,side,sx in (
        (5,160,1,0,14,148,205,2048,7,222,124,0,89),
        (6,65376,0,1,15,65388,195,0,8,194,125,1,79)):
        c=case(handler=handler,speed=speed,left=left,right=right)
        e=expected(c,handler=result_handler,x=x,speed=result_speed,flags=flags,callback=callback,mode=133,
                   first=52,begin=52,end=57,counter=3,reload=3,target=57,sx=sx,sy=4,horizontal=5)
        rows.append((c,(*e,1,1,side,ex,ey,flags,133,215,215,220,2,2,220)))
    return rows


EFFECT_FIELDS='owner side x y flags mode first begin end counter reload target supplied_owner owner_x owner_y repeats'.split()
EFFECT_DEFAULT=(1,0,200,100,2048,133,215,215,220,2,2,220,1,300,999,1)


def effect_case(**changes):
    if changes.keys()-set(EFFECT_FIELDS):raise ValueError('unknown effect field')
    d=dict(zip(EFFECT_FIELDS,EFFECT_DEFAULT));d.update(changes);return tuple(d.values())


def effect_goldens():
    rows=[]
    for changes,result in (
        ({},(1,0,322,100,2048,133,215,215,220,1,2,220,0,1)),
        ({'side':1,'owner_x':2,'flags':0},(1,1,65532,100,0,133,215,215,220,1,2,220,0,1)),
        ({'first':220,'counter':1},(1,0,322,100,2048,0,215,215,220,2,2,220,1,1)),
        ({'repeats':12},(1,0,322,100,2048,0,215,215,220,2,2,220,1,12)),
        ({'repeats':16},(1,0,322,100,2048,0,215,215,220,2,2,220,1,16)),
        ({'mode':5},(1,0,200,100,2048,5,215,215,220,2,2,220,0,1)),
        ({'counter':0},(1,0,322,100,2048,133,215,215,220,255,2,220,0,1)),
        ({'mode':129,'first':65535,'end':65535,'counter':1},(1,0,322,100,2048,129,215,215,65535,2,2,220,0,1)),
    ):rows.append((effect_case(**changes),result))
    return rows


def decode_actor_rows(data,count):
    rows=[tuple(map(int,l.split())) for l in data.splitlines()]
    if len(rows)!=count:raise ValueError('reversal output count mismatch')
    for r in rows:
        if len(r)<24:raise ValueError('reversal output truncated')
        split=23+4*r[21]
        if split>=len(r) or len(r)!=split+1+12*r[split]:raise ValueError('reversal output shape mismatch')
    return rows


def split_actor(row):
    split=23+4*row[21]
    return row[:split],tuple(row[i:i+12] for i in range(split+1,len(row),12))
