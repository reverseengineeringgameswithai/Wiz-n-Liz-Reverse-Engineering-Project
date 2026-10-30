"""ROM-independent checks for bounded static evidence and consumer-derived layout."""
import hashlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from rnc_loader_probe import (decoder_cfg, descriptor_address, direct_target,
                              inspect_pattern_bank, parse_disassembly, u32)


class RncLoaderTests(unittest.TestCase):
    def test_body_first_zero_count_has_one_pattern_and_record(self):
        data = bytes(range(32)) + b"\0\0" + b"P" * 32 + b"R" * 8
        result = inspect_pattern_bank(data)
        self.assertEqual(result["record_count"], 1)
        self.assertEqual(result["regions"]["patterns"]["range"], [34, 66])
        self.assertEqual(result["regions"]["opaque_records"]["range"], [66, 74])
        self.assertEqual(result["regions"]["patterns"]["sha256"], hashlib.sha256(b"P" * 32).hexdigest())
        self.assertIsNone(result["opaque_record_meaning"])

    def test_multiple_records_partition_exactly(self):
        data = bytes(32) + b"\0\2" + bytes(range(96)) + bytes(range(24))
        result = inspect_pattern_bank(data)
        self.assertEqual(result["record_count"], 3)
        self.assertEqual(result["regions"]["patterns"]["range"], [34, 130])
        self.assertEqual(result["regions"]["opaque_records"]["range"], [130, 154])
        self.assertEqual(sum(row["size_bytes"] for row in result["regions"].values()), len(data))

    def test_malformed_layout_does_not_allocate_declared_lengths(self):
        valid = bytes(74)
        for data in (bytes(33), valid[:-1], valid + b"X", bytes(32) + b"\xff\xff"):
            with self.subTest(size=len(data)), self.assertRaises(ValueError):
                inspect_pattern_bank(data)
        with self.assertRaisesRegex(ValueError, "configured limit"):
            inspect_pattern_bank(bytes(32) + b"\xff\xff", max_records=100)

    def test_descriptor_uses_unsigned_multiply_then_signed_word_index(self):
        self.assertEqual(descriptor_address(0x10000, 3, 34), 0x10066)
        self.assertEqual(descriptor_address(0x10000, 0xFFFF, 34), 0xFFDE)
        self.assertEqual(descriptor_address(0x10000, 0x4000, 34), 0x8000)
        self.assertEqual(descriptor_address(0x10000, 0x10000, 34), 0x10000)
        self.assertEqual(descriptor_address(0, 0xFFFF, 34), 0xFFFFFFDE)

    def test_direct_calls_use_extension_address_and_signed_offsets(self):
        self.assertEqual(direct_target(bytes.fromhex("4eb900123456"), 0), 0x123456)
        self.assertEqual(direct_target(bytes.fromhex("4e714ebafffe"), 2), 2)
        self.assertEqual(direct_target(bytes.fromhex("6100fffe"), 0), 0)
        self.assertEqual(direct_target(bytes.fromhex("61ff"), 0), 1)  # 68000 byte -1
        self.assertIsNone(direct_target(bytes.fromhex("4e75"), 0))

    def test_truncated_fields_reject(self):
        for offset in (-1, 1, 4):
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                u32(bytes(4), offset)
        for data in (b"", b"\x4e", bytes.fromhex("4eb90000"), bytes.fromhex("4eba")):
            with self.subTest(data=data), self.assertRaises(ValueError):
                direct_target(data, 0)

    def test_disassembly_must_match_bytes_boundaries_and_valid_instructions(self):
        data = bytes.fromhex("70024e75")
        text = "0x00000000 2 7002 moveq 2, d0\n0x00000002 2 4e75 rts\n"
        rows = parse_disassembly(text, data, 0, 4)
        self.assertEqual([row["address"] for row in rows], [0, 2])
        for broken in (text.replace("7002", "7003"), text.replace("02 2", "03 2"),
                       text.replace("rts", "invalid"), text.replace("2 4e75", "6 4e75"),
                       text.splitlines()[0], "nonsense"):
            with self.subTest(text=broken), self.assertRaises(ValueError):
                parse_disassembly(broken, data, 0, 4)

    def test_closed_cfg_with_body_first_loop(self):
        data = bytes.fromhex("70024e7151c8fffc4e75")
        rows = [{"address": pc, "size": size} for pc, size in ((0, 2), (2, 2), (4, 4), (8, 2))]
        graph = decoder_cfg(data, rows)
        self.assertEqual(graph["reachable_instructions"], 4)
        self.assertEqual(graph["return_addresses"], [8])
        self.assertIn([4, 2], graph["edges"])

    def test_cfg_rejects_mid_instruction_targets_calls_and_unexplained_bytes(self):
        with self.assertRaises(ValueError):
            decoder_cfg(b"", [])
        for data, rows in (
            (bytes.fromhex("600000034e75"), [(0, 4), (4, 2)]),
            (bytes.fromhex("600000104e75"), [(0, 4), (4, 2)]),
            (bytes.fromhex("61004e75"), [(0, 2), (2, 2)]),
            (bytes.fromhex("60024e714e75"), [(0, 2), (2, 2), (4, 2)]),
            (bytes.fromhex("4e904e75"), [(0, 2), (2, 2)]),
        ):
            with self.subTest(data=data), self.assertRaises(ValueError):
                decoder_cfg(data, [{"address": pc, "size": size} for pc, size in rows])
