"""Synthetic checks for the retained-world evidence: object fields, identities and the write audit."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import genesis_pair_initializer as g
import genesis_world_pool as w


def obj(mode=0x81, handler=0x12646, service=0x12646, callback=0, control=0xffff0690, **words):
    b = bytearray(78); b[0] = mode; b[2:4] = (0x100).to_bytes(2, 'big'); b[4:6] = (0x80).to_bytes(2, 'big')
    b[0x16:0x1a] = handler.to_bytes(4, 'big'); b[0x46:0x4a] = service.to_bytes(4, 'big'); b[0x1a:0x1e] = callback.to_bytes(4, 'big'); b[0x4a:0x4e] = control.to_bytes(4, 'big')
    for offset, value in words.items(): b[int(offset[1:], 16):int(offset[1:], 16) + 2] = value.to_bytes(2, 'big')
    return bytes(b)


class WorldPoolTests(unittest.TestCase):
    def test_particle_fields_accept_both_allocators_only(self):
        for handler in (0x5ae2, 0x12646):
            self.assertEqual(w.world_fields(w.PARTICLE, obj(mode=0x85, handler=handler, callback=0xfaa4, o0e=234)), (0x100, 0x80, 0, 0x85, 0, 0, 0, 0, 0, 234))
        for bad in (obj(mode=0x85, handler=0x5ae2), obj(mode=0x85, handler=0x6d8c, callback=0xfaa4)):
            with self.assertRaises(ValueError): w.world_fields(w.PARTICLE, bad)

    def test_return_only_fields_dormant_residue_but_active_zero(self):
        dormant = bytearray(obj(mode=0, callback=0xfaa4)); dormant[0x22:0x24] = b'\x12\x34'
        self.assertEqual(w.world_fields(w.RETURN_ONLY, bytes(dormant)), (0x100, 0x80, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1))
        active = bytearray(dormant); active[0] = 0x81
        with self.assertRaises(ValueError): w.world_fields(w.RETURN_ONLY, bytes(active))
        with self.assertRaises(ValueError): w.world_fields(w.RETURN_ONLY, obj(mode=0, control=0x1234))

    def test_reversal_fields_follow_the_effect_session_with_the_owner(self):
        b = bytearray(obj(mode=0x85, handler=0xaa40, callback=0xfaa4, o12=3, o0e=7)); b[0x22:0x26] = (0xffff1ab4).to_bytes(4, 'big')
        self.assertEqual(w.world_fields(w.REVERSAL, bytes(b)), (1, 0x100, 0x80, 3, 0x85, 0, 0, 0, 0, 0, 7, 1))
        b[0x22:0x26] = (0xffff0690).to_bytes(4, 'big')
        with self.assertRaises(ValueError): w.world_fields(w.REVERSAL, bytes(b))

    def test_spell_anchor_fields_name_the_phase_by_handler(self):
        for phase, handler in enumerate((0x7b42, 0x7b58, 0x7b8a)):
            self.assertEqual(w.world_fields(w.SPELL, obj(handler=handler, o10=0x12c)), (0x100, 0x80, 0, 0x81, 0, 0, 0, 0, 0, 0, 0x12c, 1, phase))
        for bad in (obj(o10=0x12c), obj(handler=0x7b42, service=0x7b58)):
            with self.assertRaises(ValueError): w.world_fields(w.SPELL, bad)

    def test_completion_objects_print_only_what_they_write(self):
        # The sparkle and a waiting door hide F9E2's leftover +08..+0E; an open
        # door adds its extents; a raised sign its 4C52 cursor.
        residue = dict(o08=0x1111, o0a=0x2222, o0e=0x3333)
        self.assertEqual(w.world_fields(w.SPARKLE, obj(mode=0x80, handler=0x7f6a, o06=0x21d, o10=0x40, o1e=16, o20=16, **residue)),
                         (0x100, 0x80, 0, 0x80, 0x21d, 0, 0, 0, 0, 0, 0x40, 16, 16))
        door = bytearray(obj(mode=0x80, handler=0x6fb6, o06=0x21d, o10=0x1e, **residue)); door[0x36:0x3a] = g.address(5).to_bytes(4, 'big')
        self.assertEqual(w.world_fields(w.DOOR, bytes(door)), (0, 0x100, 0x80, 0, 0x80, 0x21d, 0, 0, 0, 0, 0, 0x1e, 0, 0, 1, 5))
        door[0x16:0x1a] = (0x12646).to_bytes(4, 'big'); door[0x46:0x4a] = (0x705c).to_bytes(4, 'big'); door[0x1e:0x22] = bytes((0, 16, 0, 32))
        self.assertEqual(w.world_fields(w.DOOR, bytes(door))[:1] + w.world_fields(w.DOOR, bytes(door))[6:], (2, 0x1111, 0x2222, 0, 0, 0x3333, 0x1e, 16, 32, 1, 5))
        door[0x46:0x4a] = (0x12646).to_bytes(4, 'big')
        with self.assertRaises(ValueError): w.world_fields(w.DOOR, bytes(door))   # The puff needs its 6FCA callback.
        sign = bytearray(obj(mode=0x80, handler=0x4c34, o06=0xd2)); sign[0x22:0x26] = (0x4c52 + 2 * 13).to_bytes(4, 'big')
        self.assertEqual(w.world_fields(w.SIGN, bytes(sign)), (1, 0x100, 0x80, 0, 0x80, 0xd2, 13))
        sign[0x22:0x26] = (0x4c6e).to_bytes(4, 'big')
        with self.assertRaises(ValueError): w.world_fields(w.SIGN, bytes(sign))

    def test_emitter_maps_owner_and_keeps_history_order(self):
        b = bytearray(obj(handler=0x6d8c, o10=2, o36=3, o1e=16, o20=16)); b[0x42:0x46] = (0xffff447a + 12).to_bytes(4, 'big')
        for h in range(10): b[0x22 + 2 * h:0x24 + 2 * h] = (0x40 + h).to_bytes(2, 'big')
        f = w.world_fields(w.EMITTER, bytes(b))
        self.assertEqual(f[10:12], (2, 3)); self.assertEqual(f[12:22], tuple(range(0x40, 0x4a))); self.assertEqual(f[22:], (1, 16, 16, 1))
        with self.assertRaises(ValueError): w.world_fields(w.EMITTER, obj(mode=0))

    def test_identities_follow_births_and_releases(self):
        world = w.World(); self.assertEqual(world.ref(0), (0, 0, 0))
        with self.assertRaises(ValueError): world.ref(g.address(3))
        world.born(3, w.PARTICLE); self.assertEqual(world.ref(g.address(3)), (1, 3, 1))
        with self.assertRaises(ValueError): world.born(3, w.COPY)
        world.kinds[3] = None; world.born(3, w.COPY); self.assertEqual(world.ref(g.address(3)), (1, 3, 2))

    def test_message_codes(self):
        m = bytearray(18); m[0:4] = (0xd20e).to_bytes(4, 'big'); m[0x0d] = 1; m[0x10:0x12] = (12).to_bytes(2, 'big')
        self.assertEqual(w.message_fields(bytes(m)), (3, 1, 12))
        m[0:4] = (0xd300).to_bytes(4, 'big')
        with self.assertRaises(ValueError): w.message_fields(bytes(m))

    def test_write_audit_attributes_random_and_ingredient_state(self):
        def record(frame, *events, dropped=0): return dict(frame=frame, dropped=dropped, events=[dict(pc=pc, address=a, width=n) for pc, a, n in events])
        ok = [record(700, (0xe92a, 0xff0bac, 2), (0xe946, 0xff0bb0, 4)), record(701, (0x7a4e, 0xff31be, 2)), record(702, dropped=3), record(600, (0x1234, 0xff0bac, 2))]
        audit = w.audit_world_writes(ok, [700, 701, 702])
        self.assertEqual((audit['complete_frames'], audit['incomplete_frames'], audit['writes']), (2, [702], dict(random=2, ingredient_tail=1)))
        for bad in ((0x1234, 0xff0bae, 2), (0xe92a, 0xff31bc, 2), (0x7a4e, 0xff0bb2, 1), (0x7cc8, 0xff31be, 2), (0x7cf0, 0xff31bc, 2)):
            with self.assertRaises(ValueError): w.audit_world_writes([record(700, bad)], [700])
        # 7CC8 counts FF31BE down and, on reload, advances FF31BC; writes after
        # the last loop are not audited.
        audit = w.audit_world_writes([record(1200, (0x7cda, 0xff31be, 2), (0x7ce2, 0xff31bc, 2)), record(1201, (0x1234, 0xff31bc, 2))], [1199, 1200])
        self.assertEqual(audit['writes'], dict(producer=2))


class WorldSessionTests(unittest.TestCase):
    def test_cross_check_ties_world_inputs_to_p1(self):
        import genesis_world_session as ws
        def event(x, y, ax, ay):
            actor = bytearray(78); actor[2:4] = ax.to_bytes(2, 'big'); actor[4:6] = ay.to_bytes(2, 'big'); actor[0x46:0x4a] = (0x12646).to_bytes(4, 'big')
            control = bytearray(112); control[0x42:0x44] = x.to_bytes(2, 'big'); control[0x44:0x46] = y.to_bytes(2, 'big')
            return dict(ranges=[dict(label='actor', hex=actor.hex()), dict(label='control', hex=control.hex()), dict(label='tracking_selector', hex='0000')])
        pairs = [{'return': event(10, 20, 6, 20)}, {'return': event(11, 20, 7, 20)}]
        row = lambda x, y, owner=None: (x, y, 1023, 0, 0, 0, 0, *((1, *owner) if owner else (0, 0, 0)), 0, *(0,) * 8)
        world = dict(summary=dict(first_loop=ws.START - 1), phases=[row(0, 0), row(10, 20), row(11, 20, (7, 20))])
        self.assertEqual(ws.cross_check(world, pairs), dict(frames=2, tracking=2, owner_positions=1))
        for bad in (row(12, 20, (7, 20)), row(11, 20, (8, 20))):
            world['phases'][2] = bad
            with self.assertRaises(ValueError): ws.cross_check(world, pairs)

    def test_curve_codes_and_the_exit_fade_block(self):
        import genesis_world_session as ws
        import genesis_session_capture as sc
        block = lambda *curves: bytes(8) + b''.join(c.to_bytes(4, 'big') for c in curves)
        self.assertEqual(ws.curve_codes(block(0x1356a, 0x135aa, 0x135ea)), (1, 2, 3))
        self.assertEqual(ws.curve_codes(block(0x12345, 0, 0x135ea)), (0, 0, 3))
        # 13208: direction 1, countdown 1, reload 1, level 14, curves 1356A/1356A/135AA.
        self.assertEqual(sc.EXIT_FADE[:8], bytes((0, 1, 0, 1, 0, 1, 0, 14))); self.assertEqual(ws.curve_codes(sc.EXIT_FADE), (1, 1, 2))

    def test_fade_dirty_requests_follow_level_steps(self):
        import genesis_world_session as ws
        block = lambda *w: b''.join(v.to_bytes(2, 'big') for v in w) + bytes(12)
        pairs = [dict(transition_before=block(0xffff, 1, 1, 12), transition=block(0xffff, 0, 1, 12)),
                 dict(transition_before=block(0xffff, 0, 1, 12), transition=block(0xffff, 1, 1, 14)),
                 dict(transition_before=block(0, 0, 1, 14), transition=block(0, 0, 1, 14))]
        write = lambda pc, value: dict(type=4, address=0xff0edc, width=2, pc=pc, value=value)
        writes = [dict(events=[]), dict(events=[write(0x13496, 0xffff)]), dict(events=[write(0x1344c, 0)])]
        self.assertEqual(ws.fade(pairs, writes), dict(active_frames=[ws.START, ws.START + 1], level_steps=[ws.START + 1], consumer_clears=1))
        for bad in ([dict(events=[write(0x13496, 0xffff)]), dict(events=[]), dict(events=[])], [dict(events=[]), dict(events=[write(0x12000, 0xffff)]), dict(events=[])]):
            with self.assertRaises(ValueError): ws.fade(pairs, bad)


if __name__ == '__main__':
    unittest.main()
