"""Authored overlap boundaries and bounded service/presentation input cases."""
import random
FIELDS='x y flags mode first begin end counter reload target countdown control x_extent y_extent primary_x primary_y mask secondary_gate secondary_present secondary_x secondary_y repeats'.split()
DEFAULT=(150,262,0xbeef,0x80,912,0,0,0,0,100,0,1,56,8,0,0,1023,0,0,0,0,1)
def case(**changes):
    assert not changes.keys()-set(FIELDS)
    return tuple((dict(zip(FIELDS,DEFAULT))|changes).values())
def overlap_corpus():
    # Each operand domain matters independently: unsigned distances, addition
    # overflow in both thresholds, and arbitrary bit masks (not only 2^n-1).
    rows=[]
    for i in range(65536):
        rows.extend(((i,0,56,8,0,0,65535),(0,i,56,8,0,0,65535),
            (0,0,i,8,0,0,65535),(0,0,56,i,0,0,65535),(65535,0,0,0,0,0,i)))
    edge=(0,1,11,12,13,15,16,17,32767,32768,65519,65520,65523,65524,65535)
    for width in edge:
        for height in edge:
            for dx in (0,1,(width+16)&65535,(width+17)&65535,65535):
                for dy in (0,1,(height+12)&65535,(height+13)&65535,65535):
                    rows.append((123,321,width,height,(123+width-dx)&65535,(321+height-dy)&65535,65535))
    rng=random.Random(0xac5e78ee)
    rows += [tuple(rng.randrange(65536) for _ in range(7)) for _ in range(8192)]
    return rows

def service_corpus():
    rows=[case(secondary_gate=i,secondary_present=1,secondary_x=30000,secondary_y=30000) for i in range(65536)]
    # X misses and Y-only misses, including masks and wrapped thresholds.
    for mask in (0,1,0x5555,1023,32767,32768,65535):
        for width in (0,56,32768,65519,65520,65535):
            for height in (0,8,32768,65523,65524,65535):
                for n in (1,2,16,256):
                    # x distance=0, y distance is one beyond the wrapped limit;
                    # a threshold of FFFF has no miss, so exclude that height.
                    if height==65523:continue
                    y=123;target_y=(y+height-(((height+12)&65535)+1))&65535
                    rows.append(case(x=321,y=y,x_extent=width,y_extent=height,primary_x=(321+width)&65535,primary_y=target_y,mask=mask,repeats=n))
    return rows

def presentations():
    return [case(mode=m,first=f,begin=3,end=11,counter=c,reload=2) for m in range(256) for c in (0,1,2,255) for f in (0,3,11,65535)]
