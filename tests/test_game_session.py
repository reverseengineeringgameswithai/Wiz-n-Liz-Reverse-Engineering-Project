"""Synthetic checks for the joined game session evidence: the nested fixture reader and the carried-state maps of the scene change and of the change after the hub."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import genesis_game_session as g


class GameSessionTests(unittest.TestCase):
    def test_nested_reader_hashes_every_artifact_inside_the_run(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); (root / 'level').mkdir(); (root / 'level' / 'a.bin').write_bytes(b'abc')
            parent = dict(ok=True, rom_unchanged=True, artifacts={'level/a.bin': hashlib.sha256(b'abc').hexdigest()})
            self.assertEqual(g.nested_reader(parent, root)('level/a.bin'), b'abc')
            with self.assertRaises(ValueError): g.nested_reader(parent, root)('level/b.bin')
            (root / 'level' / 'a.bin').write_bytes(b'abd')
            with self.assertRaises(ValueError): g.nested_reader(parent, root)
            outside = dict(parent, artifacts={'../x': hashlib.sha256(b'').hexdigest()})
            with self.assertRaises(ValueError): g.nested_reader(outside, root)

    def test_carried_state_names_the_control_fields_the_session_reads(self):
        self.assertEqual(g.CARRIED['anchor'][0], 0x0690 + 0xa2)
        self.assertEqual(g.CARRIED['tracking'][0], 0x0690 + 0x42)
        self.assertEqual(g.CARRIED['selector'][0], 0x0690 + 0x1a6)
        self.assertEqual(g.CARRIED['parameters'], (0x0690 + 0x5a, 0x6e - 0x5a))

    def test_every_allowed_interval_closes_at_a_traced_return(self):
        self.assertTrue(set(g.ALLOWED) <= set(g.CALLS))
        self.assertTrue(all(names <= set(g.CARRIED) for names in g.ALLOWED.values()))
        self.assertEqual(len(set(g.CALLS)), len(g.CALLS))

    def test_after_hub_changes_close_at_traced_events(self):
        traced = set(g.AFTER_CALLS) | set(g.HINT_PCS) | set(g.TIMER_PCS) | {0xe918}
        self.assertTrue(set(g.AFTER_ALLOWED) <= traced)
        self.assertTrue(all(names <= set(g.AFTER_CARRIED) for names in g.AFTER_ALLOWED.values()))
        self.assertEqual(len(set(g.AFTER_CALLS)), len(g.AFTER_CALLS))
        self.assertEqual(set(g.after_recipe()['pcs']), traced)
        # 118C clears +1A6 at 119A, before [11A6,11EE) sets FF33D8; E2A clears the saved position (FF0732).
        self.assertEqual(g.AFTER_ALLOWED[0x11a6], {'selector'})
        self.assertEqual(g.AFTER_CARRIED['saved'][0], 0x0690 + 0xa2)
        self.assertEqual(g.AFTER_CARRIED['selector'][0], 0x0690 + 0x1a6)

    def test_second_level_window_follows_the_hub(self):
        self.assertEqual(g.AFTER_START, g.hs.END - 1)
        self.assertTrue(g.AFTER_START < g.SECOND_START < g.SECOND_END)
        labels = [r['label'] for r in g.second_recipe()['ranges']]
        self.assertIn('requested_position', labels); self.assertIn('saved_position', labels); self.assertIn('transition', labels)


if __name__ == '__main__': unittest.main()
