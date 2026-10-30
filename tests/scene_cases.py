"""Original authored scene/bank fixtures, never proprietary game bytes."""
import struct


def scene_fixture():
    # One coordinate, two state starts, one additional pattern, complete map.
    header = struct.pack(">8H", 0, 0xffff, 0xffb0, 0xff80, 0xfff0, 10, 20, 0)
    pattern = bytearray(32)
    pattern[0], pattern[3], pattern[28], pattern[31] = 0x10, 0x02, 0x30, 0x04
    cells = [1, 0x0801, 0x1001, 0x9801] + [0] * 4092
    scene = header + pattern + struct.pack(">2H4096H", 128, 32, *cells) + bytes(range(160,168))
    palette = bytes.fromhex("0000 0E00 00E0 000E 0EE0") + bytes(22)
    bank = palette + bytes(2 + 32 + 8)
    return bytes(scene), bank
