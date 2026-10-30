"""ROM-free authored terrain resources and independently specified edge cases."""
import struct


def fixture():
    # Pattern zero is an eight-byte sentinel. Remaining records cover all bytes.
    records = bytes([8] * 8) + bytes(range(256))
    base_count, extra_count = 17, 16
    bank = bytes(32) + struct.pack(">H", base_count - 1) + bytes(base_count * 32) + records[:base_count * 8]
    cells = [1 + (i % 32) | ((i // 32) % 32) << 11 for i in range(4096)]
    header = struct.pack(">8H", 0, 0, 0, 0, 0, 0, 0, extra_count - 1)
    scene = header + bytes(extra_count * 32) + struct.pack(">2H4096H",128,32,*cells) + records[base_count * 8:]
    return scene, bank


def golden_cases():
    # Tuples: mode,x,y,old scratch x/y -> x,y,new scratch x/y,byte,comparison,NZVC,map.
    # Expected values are hand-worked independently of either implementation.
    return [
        ((0,128,128,99,99), (128,128,0,0,0,0,4,0x4001)),
        ((0,135,128,99,99), (135,128,7,0,7,0,0,0x4001)),
        ((0,136,128,99,99), (136,128,8,0,8,0,0,0x4002)),
        ((0,384,128,99,99), (384,128,256,0,7,0,0,0x4801)),
        ((0,640,128,99,99), (640,128,512,0,0,0,4,0x5001)),
        ((0,896,128,99,99), (896,128,768,0,7,0,0,0x5801)),
        ((0,128,127,6,7), (128,127,6,7,8,0,0,0)),
        ((0,128,0x8080,6,7), (128,0x8080,6,7,8,0,0,0)),
        ((0,128,2176,9,9), (128,2176,0,2048,0,0,4,0x4001)),
        ((0,1152,128,9,9), (1152,128,1024,0,0,0,4,0x4001)),
        ((0,0,128,9,9), (0,128,65408,0,135,0,8,0x5811)),
        ((1,116,106,9,9), (116,106,0,0,0,1,0,0x4001)),
        ((2,117,105,9,9), (117,105,1,0,1,1,4,0x4001)),
        ((3,118,104,9,9), (118,104,2,0,2,1,9,0x4001)),
        ((2,244,105,9,9), (244,105,128,0,128,1,11,0x4011)),
        ((4,117,105,9,9), (117,105,1,0,1,1,4,0x4001)),
        ((4,118,105,9,9), (118,106,2,0,2,1,0,0x4001)),
        ((4,116,65535,6,0), (116,0,6,0,8,1,0,0)),
    ]


def encode_cases(cases):
    return "".join(" ".join(map(str,c)) + "\n" for c in cases).encode()


def decode_results(data, count):
    rows = [tuple(map(int, line.split())) for line in data.splitlines()]
    if len(rows) != count or any(len(row) != 8 for row in rows):
        raise ValueError("terrain result count/shape mismatch")
    return rows
