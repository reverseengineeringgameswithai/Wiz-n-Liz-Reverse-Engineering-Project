"""Authored private-object arithmetic, gate-width and presentation boundaries."""
import random
FIELDS='kind x y flags mode first begin end counter reload target countdown control rise flags_gate hide repeats'.split()
DEFAULT=(0,99,262,0xbeef,0x81,7,3,11,2,2,100,8,1,1,0,0,1)
def case(**changes):
    assert not changes.keys()-set(FIELDS)
    return tuple((dict(zip(FIELDS,DEFAULT))|changes).values())
def corpus():
    rows=[case(countdown=i,y=0,rise=0x10000,control=(i*65537)&0xffffffff) for i in range(65536)]
    # Both word gates: high bits are nonzero, not signed/byte/bit tests.
    rows += [case(kind=1,flags_gate=i,hide=65535-i,x=i,y=65535-i) for i in range(65536)]
    for rise in (0,1,65536,0x80000000,0xffffffff):
        for y in (0,245,246,247,262,32767,32768,65535):
            for countdown in (0,1,8,32767,32768,32769,65535):
                for n in (1,2,9,144,256):rows.append(case(rise=rise,y=y,countdown=countdown,repeats=n))
    rng=random.Random(0x78087ca4)
    for _ in range(2048):
        rows.append(case(kind=rng.randrange(2),x=rng.randrange(65536),y=rng.randrange(65536),flags=rng.randrange(65536),
          countdown=rng.randrange(65536),control=rng.getrandbits(32),rise=rng.getrandbits(32),flags_gate=rng.randrange(65536),hide=rng.randrange(65536)))
    return rows

def presentations():
    rows=[]
    for kind in (0,1):
        for mode in range(256):
            for counter in (0,1,2,255):
                for first in (0,3,11,65535):
                    rows.append(case(kind=kind,mode=mode,counter=counter,first=first,flags_gate=1,hide=1))
    return rows
