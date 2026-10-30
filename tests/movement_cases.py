"""Authored motion fixtures/goldens; no game bytes or implementation oracle."""
import struct


def fixture(flat=False):
    records=[bytes([5]*8),bytes(range(1,9)),bytes(range(8,0,-1)),bytes(8)]
    bank=bytes(32)+struct.pack(">H",1)+bytes(64)+b"".join(records[:2])
    cells=[0 if flat else ((i%4)|(((i//4)%32)<<11)) for i in range(4096)]
    scene=struct.pack(">8H",0,0,0,0,0,0,0,1)+bytes(64)+struct.pack(">2H4096H",128,32,*cells)+b"".join(records[2:])
    return scene,bank


def case(op=0,x=200,y=109,speed=0,positive=192,negative=0xff40,damping=3,sx=9,sy=10,repeats=1):
    return (op,x,y,speed,positive,negative,damping,sx,sy,repeats)


def retained(x,y,speed,sx,sy,steps=0):
    return (x,y,speed,0x1357,0x2468,0,0xa5,0xa5a5,0xa5a5,0xa5a5,0xa5,0xa5,sx,sy,steps,0)


def airborne(x,y,speed,sx,sy,steps=0,transitions=1):
    return (x,y,speed,0,0xffff,1,0x81,0x3a,0x3c,0x3d,6,6,sx,sy,steps,transitions)


def goldens():
    # All for the uniform contact-level-five fixture, worked by hand.
    return [
        (case(),retained(200,109,0,84,4)),
        (case(y=108),retained(200,109,0,84,3)),
        (case(speed=1),retained(201,109,1,85,4,1)),
        (case(speed=31),retained(201,109,31,85,4,1)),
        (case(speed=32),retained(202,109,32,86,4,2)),
        (case(speed=0xffff),retained(199,109,0xffff,83,4,1)),
        (case(op=2,y=110,speed=20),retained(201,109,20,85,4,1)),
        (case(op=2,y=108,speed=20),retained(201,109,20,85,4,1)),
        (case(op=2,y=105,speed=20),airborne(201,106,24,85,1,1)),
        (case(op=1,y=105,speed=0xffff),airborne(199,106,0xfffb,83,1,1)),
        (case(y=105,speed=32,positive=1),airborne(202,107,1,86,2,2,2)),
        (case(y=105,speed=31),airborne(201,106,35,85,1,1)),
        (case(speed=0x8000),retained(1223,109,0x8000,1107,4,64513)),
        (case(speed=0x7fff),retained(1224,109,0x7fff,1108,4,1024)),
        (case(op=3,speed=0x8000,damping=0),retained(200,109,0x8001,9,10)),
        (case(op=3,speed=0x8000,damping=65535),retained(200,109,0,9,10)),
        (case(op=3,speed=5),retained(200,109,1,9,10)),
        (case(op=3,speed=0xfffd),retained(200,109,0,9,10)),
        (case(op=4,speed=0xffff),retained(200,109,0,9,10)),
        (case(op=5,speed=193),retained(200,109,192,9,10)),
        (case(op=5,speed=0x8000),retained(200,109,0x8000,9,10)),
        (case(op=6,speed=0xff3f),retained(200,109,0xff40,9,10)),
        (case(op=6,speed=32767),retained(200,109,32767,9,10)),
        (case(op=7),airborne(200,109,0,9,10)),
        (case(op=2,x=65535),retained(0,109,0,65420,4,1)),
        (case(speed=32,repeats=16),retained(232,109,32,116,4,32)),
    ]


def decode_results(data,count):
    rows=[tuple(map(int,line.split())) for line in data.splitlines()]
    if len(rows)!=count or any(len(r)!=16 for r in rows):raise ValueError("movement output shape/count mismatch")
    return rows
