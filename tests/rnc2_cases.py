"""Authored RNC2 token sequences; expected bytes never come from a decoder.

Control strings are MSB-first and raw bytes share the byte cursor. This small
wire writer has no match selection, compression search, or decode logic.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from rnc import crc16


class Wire:
    def __init__(self, flags="00"):
        self.data = bytearray()
        self.slot = 0
        self.remaining = 0
        self.bits(flags)

    def bits(self, value):
        for bit in value:
            assert bit in "01"
            if not self.remaining:
                self.slot = len(self.data)
                self.data.append(0)
                self.remaining = 8
            self.remaining -= 1
            self.data[self.slot] |= int(bit) << self.remaining
        return self

    def raw(self, data):
        self.data.extend(data)
        return self

    def literals(self, data):
        for byte in data:
            self.bits("0").raw(bytes([byte]))
        return self

    def marker(self, more=False):
        return self.bits("1111").raw(b"\0").bits("1" if more else "0")

    def block(self, expected):
        return block(bytes(self.data), expected)


def block(payload, expected):
    return (b"RNC\2" + len(expected).to_bytes(4, "big")
            + len(payload).to_bytes(4, "big")
            + crc16(expected).to_bytes(2, "big") + crc16(payload).to_bytes(2, "big")
            + b"\0\1" + payload)


# Explicit format examples, independently checked against the pinned reference.
UPPER_DISTANCE_CODES = (
    "0", "110", "1000", "1001", "10101", "10111", "11101", "11111",
    "101000", "101001", "101100", "101101", "111000", "111001", "111100", "111101",
)


def valid_cases():
    cases = {}
    for flags in ("00", "01", "10", "11"):
        wire = Wire(flags).literals(b"A").marker()
        cases[f"literal-flags-{flags}"] = (wire.block(b"A"), b"A")
    seed = bytes(range(32))
    wire = Wire().literals(seed).marker()
    cases["literal-control-refills"] = (wire.block(seed), seed)
    for length, code in ((2, "110"), (3, "1110"), (4, "1000"), (5, "1010"),
                         (6, "10010"), (7, "10011"), (8, "10110")):
        wire = Wire().literals(b"AB").bits(code)
        if length != 2:
            wire.bits("0")  # high distance zero
        wire.raw(b"\1").marker()  # distance 2; forward overlapping copy
        expected = (b"AB" * 5)[:length + 2]
        cases[f"match-{length}"] = (wire.block(expected), expected)
    for length in (9, 263):
        expected = b"Q" * (length + 1)
        wire = Wire().literals(b"Q").bits("1111").raw(bytes([length - 8]))
        wire.bits("0").raw(b"\0").marker()
        cases[f"long-match-{length}"] = (wire.block(expected), expected)
    for count in (12, 72):
        expected = bytes(range(count))
        wire = Wire().bits("10111" + f"{count // 4 - 3:04b}").raw(expected).marker()
        cases[f"literal-run-{count}"] = (wire.block(expected), expected)
    # Each high-distance prefix, with both low-byte extremes; 4096 is the largest
    # encoded distance. Pattern isn't periodic at 256, so high-byte errors show.
    seed = bytes((i * 13 + i // 251) % 256 for i in range(4096))
    for high, code in enumerate(UPPER_DISTANCE_CODES):
        for low in (0, 255):
            distance = high * 256 + low + 1
            expected = bytearray(seed)
            # A recurrence states the LZ overlap contract independently of token
            # decoding; literals are authored above, no native output is used.
            for _ in range(3):
                expected.append(expected[-distance])
            wire = Wire().literals(seed).bits("1110" + code).raw(bytes([low])).marker()
            cases[f"distance-{distance}"] = (wire.block(expected), bytes(expected))
    wire = Wire().literals(b"before")
    for _ in range(17):
        wire.marker(more=True)
    wire.literals(b"after").marker()
    expected = b"beforeafter"
    cases["continuation-markers"] = (wire.block(expected), expected)
    return cases
