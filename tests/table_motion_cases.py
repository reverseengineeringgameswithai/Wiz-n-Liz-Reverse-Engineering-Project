"""Authored 7A88 word arithmetic, cycle, DBRA and presentation boundary cases."""
import random
FIELDS='x y flags mode first begin end counter reload target countdown control cursor delta toggle loops repeats budget'.split()
DEFAULT=(99,0,0xbeef,0x81,7,3,11,2,2,100,14,1,0,65535,0,0,1,4096)
def case(**changes):
    assert not changes.keys()-set(FIELDS)
    return tuple((dict(zip(FIELDS,DEFAULT))|changes).values())
def corpus():
    rows=[case(countdown=i,x=i,y=65535,cursor=4) for i in range(65536)]
    rows += [case(toggle=i,countdown=0,cursor=23) for i in range(65536)]
    rows += [case(delta=i,x=65535,countdown=0) for i in range(65536)]
    for cursor in range(24):
        for loops in (0,1,2,3,23,24,47,48,255):
            for toggle in (0,1,2,65535):
                for delta in (1,65535,32768):rows.append(case(cursor=cursor,loops=loops,toggle=toggle,delta=delta,repeats=3))
    for loops in (4095,4096,32767,32768,65534,65535):
        for toggle in (0,1,2):rows.append(case(loops=loops,toggle=toggle,budget=65536,cursor=23,countdown=32768))
    rng=random.Random(0x7a88)
    for _ in range(2048):
        rows.append(case(x=rng.randrange(65536),y=rng.randrange(65536),flags=rng.randrange(65536),countdown=rng.randrange(65536),
            control=rng.getrandbits(32),cursor=rng.randrange(24),delta=rng.randrange(65536),toggle=rng.randrange(65536),loops=rng.randrange(32)))
    rows += [case(loops=0,repeats=256),case(loops=1,repeats=256),case(toggle=2,loops=2,repeats=256)]
    return rows

def presentations():
    return [case(mode=m,counter=c,first=f,loops=1) for m in range(256) for c in (0,1,2,255) for f in (0,3,11,65535)]
