"""Authored return-only dispatch and retained presentation input corpus."""
import random
FIELDS='x y flags mode first begin end counter reload target countdown control repeats'.split()
DEFAULT=(164,270,0x800,0x81,921,916,921,3,5,0,17,0,1)
def case(**changes):
    assert not changes.keys()-set(FIELDS)
    return tuple((dict(zip(FIELDS,DEFAULT))|changes).values())
def corpus():
    rows=[case(mode=m,counter=c,first=7,begin=3,end=11,target=100) for m in range(256) for c in range(256)]
    for first in range(65536):
        rows += [case(mode=m,first=first,begin=0,end=65535,counter=1,reload=1,repeats=2) for m in (0x81,0x83)]
    rows += [case(mode=m,first=f,begin=3,end=11,counter=c,reload=r,target=100,repeats=n)
        for m in range(256) for f in (0,3,7,11,32768,65534,65535) for c in (0,1,255) for r in (0,1,2,255) for n in (1,2,17,256)]
    # Dormant callback traps must never advance or invoke anything.
    rows += [case(mode=m,first=7,counter=1,target=7,repeats=256) for m in range(128)]
    rng=random.Random(0x1264669aa)
    for _ in range(4096):
        rows.append(case(x=rng.randrange(65536),y=rng.randrange(65536),flags=rng.randrange(65536),
            mode=rng.randrange(256)&~4,first=rng.randrange(65536),begin=rng.randrange(65536),end=rng.randrange(65536),
            counter=rng.randrange(256),reload=rng.randrange(256),target=rng.randrange(65536),
            countdown=rng.randrange(65536),control=rng.randrange(2**32),repeats=rng.randrange(1,33)))
    return rows
