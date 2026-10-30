"""Authored allocator-client boundaries and deterministic arithmetic corpora."""
import random

FIELDS='x y countdown h0x h0y h1x h1y h2x h2y h3x h3y h4x h4y mode first begin end counter reload target flags owner available_owner owner_x owner_y capacity random mirror repeats'.split()
DEFAULT=(100,200,0,10,20,30,40,50,60,70,80,90,100,0x81,638,638,643,5,5,0,0x800,1,1,65534,7,16,0x12345678,0xabcdef01,1)
def case(**changes):
    assert not changes.keys()-set(FIELDS)
    return tuple((dict(zip(FIELDS,DEFAULT))|changes).values())

def corpus():
    rows=[case(),case(countdown=1),case(h1x=10,h1y=20),case(h1x=10),case(countdown=0x8000),case(countdown=0x8001)]
    # Every countdown word and low RNG word; high word follows a different cycle.
    for value in range(65536):
        rows.append(case(countdown=value,random=((value*40503)&65535)<<16|value,x=value,y=65535-value))
    rng=random.Random(0x6d8c)
    for i in range(4096):
        f=[rng.randrange(65536) for _ in range(21)]+[1,1,rng.randrange(65536),rng.randrange(65536),16,rng.getrandbits(32),rng.getrandbits(32),rng.randrange(1,33)]
        f[13]=0x81;f[17]=rng.randrange(256);f[18]=rng.randrange(256)
        rows.append(tuple(f))
    return rows

def particle_cases():
    rows=[(0,65535,0xdead,0x85,227,227,234,2,2,234,n) for n in (1,2,15,16,17,32)]
    for mode in range(256):
        for count in (0,1,2,255):
            for first in (0,227,234,65535):rows.append((99,101,0xbeef,mode,first,227,234,count,2,234,1))
    return rows

def rng_cases():
    return [(i<<16|((i*40503)&65535),0xdeadbeef,1) for i in range(65536)]+[(v,0x12345678,n) for v in (0,1,0xffffffff,0x80000000,0x12345678) for n in (2,3,32)]
