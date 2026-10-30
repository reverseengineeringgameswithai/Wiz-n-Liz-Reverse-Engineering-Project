"""Synthetic checks for the hub session evidence: pool decoding, free stack, writers and the validator's hub variant."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import genesis_hub_session as h
import genesis_session_capture as sc


def boundary(slots=None, free=None):
    """A pool range: `slots` maps slot -> 78 bytes; `free` lists slots bottom first."""
    pool = bytearray(0x3120 - 0x1b50)
    for i in range(68):
        o = bytearray(78); o[0x16:0x1a] = o[0x46:0x4a] = (0x12646).to_bytes(4, 'big'); pool[78 * i:78 * (i + 1)] = o
    for i, b in (slots or {}).items(): pool[78 * i:78 * (i + 1)] = b
    free = list(range(68)) if free is None else free
    for k, i in enumerate(free): pool[0x300c - 0x1b50 + 4 * k:0x3010 - 0x1b50 + 4 * k] = (0xffff1b50 + 78 * i).to_bytes(4, 'big')
    pool[0x311c - 0x1b50:0x3120 - 0x1b50] = (0xffff300c + 4 * len(free)).to_bytes(4, 'big')
    return dict(pool=pool.hex())


def door(handler=0x61f6, service=0x12646, **bytes_):
    o = bytearray(78); o[0] = 0x81; o[2:4] = (0x1b0).to_bytes(2, 'big'); o[4:6] = (0xa4).to_bytes(2, 'big'); o[6:8] = (0xb0).to_bytes(2, 'big')
    o[0x10:0x12] = (0x3c).to_bytes(2, 'big'); o[0x16:0x1a] = handler.to_bytes(4, 'big'); o[0x46:0x4a] = service.to_bytes(4, 'big')
    o[0x26:0x2a] = (0xffff1b50 + 78 * 66).to_bytes(4, 'big'); o[0x2a:0x2e] = (0xffff1b50 + 78 * 65).to_bytes(4, 'big')
    for k, v in bytes_.items(): o[int(k[1:], 16)] = v
    return bytes(o)


class HubSessionTests(unittest.TestCase):
    def test_slot_pointers_are_24_bit_pool_slots(self):
        self.assertEqual(h.slot_of(0xffff1b50 + 78 * 67), 67)
        self.assertEqual(h.slot_of(0x00ff1b50), 0)
        for bad in (0xffff1b51, 0xffff3008, 0xffff1b00):
            with self.assertRaises(ValueError): h.slot_of(bad)

    def test_free_stack_reads_bottom_first_and_checks_its_shape(self):
        self.assertEqual(h.free_stack(boundary(free=[3, 1, 2])), [3, 1, 2])
        b = bytearray(bytes.fromhex(boundary(free=[3])['pool'])); b[0x3008 - 0x1b50] = 1
        with self.assertRaises(ValueError): h.free_stack(dict(pool=b.hex()))

    def test_pool_image_prints_occupied_slots_with_their_pointers(self):
        image = h.pool_image(boundary({67: door()}, free=list(range(67))))
        self.assertEqual(image[0], 67)
        self.assertEqual(image[68:], [67, 0x81, 0x1b0, 0xa4, 0xb0, 0, 0, 0, 0, 0, 0x3c, 0, 0x61f6, 0x12646, 0, 0, 0, 0, 0xffff1b50 + 78 * 66, 0xffff1b50 + 78 * 65])

    def test_pool_image_rejects_unmodeled_objects_and_bytes(self):
        for bad in (door(o2f=1), door(o14=1), door(handler=0x7b42), door(service=0x705c), door(o0=0x01)):
            with self.assertRaises(ValueError): h.pool_image(boundary({67: bad}, free=list(range(67))))

    def test_writers_use_next_pc_ranges(self):
        e = dict(cpu='M68K', pc=0x61f7, address=0xff1b50, width=2)
        self.assertTrue(h.within(e, h.LOOP_WRITERS)); self.assertFalse(h.within(dict(e, pc=0x61f6), ((0x61f6, 0x630a),)))
        self.assertFalse(h.within(dict(e, cpu='Z80'), h.LOOP_WRITERS))
        self.assertTrue(h.overlaps(dict(address=0xff0835, width=2), 0xff0836, 2)); self.assertFalse(h.overlaps(dict(address=0xff0834, width=2), 0xff0836, 2))

    def test_hub_variant_requires_the_early_checks(self):
        with self.assertRaises(ValueError): sc.validate_session(dict(events=[]), [], [], 0, 1, None, False, True, hub=True)
        self.assertEqual(sc.HUB_CONVERSIONS[-1], (0xffff0690, 0x5f34))


if __name__ == '__main__': unittest.main()
