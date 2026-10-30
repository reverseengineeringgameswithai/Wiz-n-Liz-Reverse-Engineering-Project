"""Independent synthetic checks for F9E2/7B9C evidence, write audit and continuity."""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import genesis_pair_initializer as g
from genesis_mixed_session import validate_anchor
from pair_initializer_cases import case, corpus, expected_native_rejection, representable, quad_case, quad_corpus, quad_expected_native_rejection

CALLER_A6 = 0xffc00000
SP = 0xffff00f4
REGS = {f'M68K D{i}': 0x100 + i for i in range(8)} | {f'M68K A{i}': 0x200 + i for i in range(6)}


def free_block(slots):
    b = bytearray(280)
    for i, s in enumerate(slots): b[4 + 4 * i:8 + 4 * i] = g.address(s).to_bytes(4, 'big')
    b[276:280] = (0xffff300c + 4 * len(slots)).to_bytes(4, 'big'); return bytes(b)


def pop_head(free):
    """F9E2 moves only the head; the popped entry's bytes stay in place."""
    b = bytearray(free); b[276:280] = (int.from_bytes(free[276:280], 'big') - 4).to_bytes(4, 'big'); return bytes(b)


def residue(target=0, countdown=0, link=0):
    b = bytearray(78); b[0x16:0x1a] = b[0x46:0x4a] = (0x12646).to_bytes(4, 'big')
    b[0x0e:0x10] = target.to_bytes(2, 'big'); b[0x10:0x12] = countdown.to_bytes(2, 'big'); b[0x4a:0x4e] = link.to_bytes(4, 'big')
    return bytes(b)


class Stream:
    def __init__(self, frame=629): self.events = []; self.frame = frame; self.base = dict(REGS); self.dormant = bytes(8); self.links = bytes(8)

    def add(self, pc, a6, sp, obj, free, stack, anchor, a0=None):
        regs = dict(self.base, **{'M68K A6': a6, 'M68K A7': sp}, **getattr(self, 'override', {}))
        if a0 is not None: regs['M68K A0'] = a0
        ranges = [dict(label='object', hex=obj.hex()), dict(label='anchor', hex=anchor.to_bytes(4, 'big').hex()), dict(label='stack', hex=stack.hex()),
                  dict(label='dormant', hex=self.dormant.hex()), dict(label='link0', hex=self.links[:4].hex()), dict(label='link1', hex=self.links[4:].hex())]
        if free is not None: ranges.append(dict(label='free', hex=free.hex()))
        self.events.append(dict(frame=self.frame, sequence=len(self.events), pc=pc, registers=regs, ranges=ranges))

    def f9e2(self, caller_a6, caller_obj, sp, ret, free, res, anchor, a0_saved=0x200):
        """One successful allocation popping the top entry; returns (target, final bytes, stack after)."""
        after = pop_head(free); head = int.from_bytes(free[276:280], 'big'); target = int.from_bytes(free[(head & 65535) - 0x3008 - 4:][:4], 'big')
        stack = ret.to_bytes(4, 'big') + bytes(12); inner = a0_saved.to_bytes(4, 'big') + stack[:12]
        final = g.apply(res, g.F9E2_FIELDS)
        for pc in g.F9E2_PCS:
            popped = pc >= 0xf9f4; loaded = pc >= 0xf9f6
            a0 = a0_saved if pc in (0xf9e2, 0xfa1c) else head - 4 if pc >= 0xf9ea else head
            obj = final if pc == 0xfa1c else res if loaded else caller_obj
            self.add(pc, target if loaded else caller_a6, sp if pc in (0xf9e2, 0xfa1c) else sp - 4, obj,
                     after if popped else free, stack if pc in (0xf9e2, 0xfa1c) else inner, anchor, a0)
        return target, final, after

    def group(self, slots, residues=(), anchor=0x13572468, name='return_only', free=None):
        """One initializer run of any member count; returns [(target, final bytes)]."""
        v = g.VARIANTS[name]; n = len(v['member_pcs']); residues = [r or residue() for r in residues] + [residue()] * (n - len(residues))
        entry_stack = (0x68a0).to_bytes(4, 'big') + bytes(12); obj = bytes(78); a6 = CALLER_A6
        free = free or free_block(slots); out = []
        self.add(v['entry'], CALLER_A6, SP, obj, free, entry_stack, anchor)
        stores = g.members(v, self.base['M68K A5'])
        for k, pcs in enumerate(v['member_pcs']):
            t, f, free = self.f9e2(a6, obj, SP - 4, v['pushes'][k], free, residues[k], anchor)
            f = g.apply(f, stores[k])
            for pc in pcs:
                # Identity stores take effect at their next-PC event.
                for spc, at, _w, value in stores[k]:
                    if at >= 0x100 and spc == pc and at in g.LINKS_AT:
                        d = bytearray(self.links); o = 4 * g.LINKS_AT.index(at); d[o:o + 4] = t.to_bytes(4, 'big'); self.links = bytes(d)
                    elif at >= 0x100 and spc == pc:
                        d = bytearray(self.dormant); o = at - g.DORMANT; d[o:o + 4] = t.to_bytes(4, 'big'); self.dormant = bytes(d)
                self.add(pc, t, SP, f, free, entry_stack, t if pc == 0x7c24 else anchor)
                if v.get('clobbers') and k == 0 and pc == pcs[-2]: self.override = {'M68K ' + v['clobbers']: t}
            out.append((t, f)); a6, obj = t, f
        self.rest = free; self.override = {}
        return out

    def pair(self, slots, first_res=None, second_res=None, anchor=0x13572468, name='return_only', free=None):
        (t1, f1), (t2, f2) = self.group(slots, [first_res, second_res], anchor, name, free)
        return t1, t2, f1, f2


def runs(stream): return g.split_invocations([e for e in stream.events if e['pc'] in g.F9E2_PCS], 0xf9e2, g.F9E2_PCS)


def pair_writes(stream, first, second, name='return_only'):
    p = g.validate_pair(stream.events, runs(stream), name)[0]; want = g.pair_writes(p); split = 1 + 9 + len(g.VARIANTS[name]['members'][0])
    events = [dict(pc=pc, address=a, width=w, value=v, registers={'M68K A6': first if i < split else second, 'M68K A0': 0x200}) for i, (pc, a, w, v) in enumerate(want)]
    return p, events


def prefix_stream():
    """One synthetic [6886,68A4): LEA, then six runs between BSR/return marks."""
    s = Stream(); s.base['M68K A5'] = 0xffff0690; slots = list(range(3, 6)) + list(range(56, 68))
    free = free_block(slots); entry_stack = (0x68a4).to_bytes(4, 'big') + bytes(12)
    s.add(g.PREFIX[0], CALLER_A6, SP + 4, bytes(78), free, entry_stack, 0x13572468); s.add(g.PREFIX[1], CALLER_A6, SP + 4, bytes(78), free, entry_stack, 0x13572468)
    anchor = 0x13572468; out = {}
    for name, mark in zip(g.PREFIX_ORDER, g.PREFIX[2:]):
        out[name] = s.group([], name=name, anchor=anchor, free=free); free = s.rest
        if name == 'return_only': anchor = out[name][-1][0]
        s.add(mark, CALLER_A6, SP + 4, bytes(78), free, entry_stack, anchor)
    for k, e in enumerate(s.events): e['sequence'] = k
    return s, out


def pickup_run(s, kinds, counts, positions, free, anchor=0x13572468):
    """One synthetic 6A94 run at SP: per created pickup, the 6AF0 entry with its
    register inputs, F9E2, the post-allocation mark and the 6AF0 return."""
    tables = [dict(label='kinds', hex=b''.join(k.to_bytes(2, 'big') for k in kinds).hex()), dict(label='counts', hex=b''.join(c.to_bytes(2, 'big') for c in counts).hex()),
              dict(label='positions', hex=b''.join(x.to_bytes(2, 'big') + y.to_bytes(2, 'big') for x, y in positions).hex())]
    def mark(pc, a6, sp, obj, free, records):
        s.add(pc, a6, sp, obj, free, bytes(16), anchor)
        s.events[-1]['ranges'] += tables + [dict(label='records', hex=bytes(records).hex()), dict(label='activation', hex=('00' * 8) if pc == 0x6aee else '1122334455667788')]
    records = bytearray(b'\x5a' * 192); mark(0x6a94, CALLER_A6, SP, bytes(78), free, records); records = bytearray(192); made = []
    for m, k in enumerate(k for k in range(16) if kinds[k] != 0xffff):
        regs = {'M68K D0': positions[m][0], 'M68K D1': positions[m][1] + 16 & 65535, 'M68K D2': kinds[k], 'M68K D3': counts[k], 'M68K A0': 0xffff312c + 2 * k,
                'M68K A1': 0xffff314c + 2 * k, 'M68K A3': 0xffff447a + 12 * m, 'M68K A5': s.base['M68K A5'], 'M68K A6': CALLER_A6}
        s.override = dict(regs); s.override.pop('M68K A6')
        mark(0x6af0, CALLER_A6, SP - 4, bytes(78), free, records)
        t, f, free = s.f9e2(CALLER_A6, bytes(78), SP - 16, 0x6afa, free, residue(), anchor, a0_saved=regs['M68K A0'])
        mark(0x6afa, t, SP - 12, f, free, records)
        final = g.apply(f, [x for part in g.pickup_stores(regs, kinds[k], counts[k]) for x in part])
        records[12 * m:12 * m + 12] = t.to_bytes(4, 'big') + regs['M68K A0'].to_bytes(4, 'big') + regs['M68K A1'].to_bytes(4, 'big')
        s.override['M68K A3'] = regs['M68K A3'] + 12
        if (kinds[k] ^ 0x8000) - 0x8000 < 14: s.override['M68K D2'] = (kinds[k] * 6 >> 16) << 16 | kinds[k]
        mark(0x6b3e, t, SP - 12, final, free, records); made.append((t, final))
    s.override = {}; mark(0x6aee, CALLER_A6, SP, bytes(78), free, records); s.rest = free
    return made


def message_stream(two=0, returned=0, priority=0x10, kinds=(5, 6), lock=0xa55a, vram=True):
    """One synthetic [68BC,68C4): marks, the model's 7DB8/CB72/CB9A/6EF0 PCs and its writes."""
    k = list(kinds) + [0xffff] * (16 - len(kinds)); events = []; regs = dict(REGS, **{'M68K A5': 0xffff0690})
    def ranges(msg, pr, ret):
        m = bytearray(18); m[0:4] = msg.to_bytes(4, 'big'); m[0x53 - 0x46] = pr; m[0x56 - 0x46:0x58 - 0x46] = (3).to_bytes(2, 'big')
        return [dict(label='message', hex=bytes(m).hex()), dict(label='two_player', hex=two.to_bytes(2, 'big').hex()), dict(label='returned', hex=ret.to_bytes(2, 'big').hex()),
                dict(label='pair_request', hex='0000'), dict(label='tilemap', hex='ffffe000'), dict(label='lock', hex=lock.to_bytes(2, 'big').hex()),
                dict(label='kinds', hex=b''.join(x.to_bytes(2, 'big') for x in k).hex())]
    def add(pc, sp, msg, pr, ret): events.append(dict(frame=629, sequence=len(events), pc=pc, registers=dict(regs, **{'M68K A7': sp}), ranges=ranges(msg, pr, ret)))
    selected, code, final_pr, final_ret, shown = 0, None, priority, returned, False
    add(0x68bc, SP, 0x12345678, priority, returned); add(0x7db8, SP - 4, 0x12345678, priority, returned)
    writes = []
    if not two and (returned or len(kinds) >= 2):
        selected = 2 if returned else 1; msg = 0xd2a2 if returned else 0xd28c
        add(0x7e08 if returned else 0x7dec, SP - 4, 0x12345678, priority, returned)
        if returned: writes.append((0x7e02, 0xff31aa, 2, 0)); final_ret = 0
        writes.append((0x7e10 if returned else 0x7df4, 0xff06d6, 4, msg)); add(0xcb72, SP - 8, msg, priority, final_ret)
        writes.append((0x7dfa if not returned else 0x7e16, SP - 4 & 0xffffff, 4, 0x7dfa))  # JSR CB72's push: stack, not message state.
        shown = 0x64 >= (priority ^ 0x80) - 0x80
        if shown:
            writes += [(0xcb86, 0xff06e3, 1, 0x64), (0xcbb0, 0xff010c, 2, 1)]; add(0xcb9a, SP - 12, msg, 0x64, final_ret)
            if vram: writes += [(0xcbb8, 0xc00004, 2, 0x8004), (0xcbf0, 0xc00004, 4, 0x61ce0003), *[(0xcbfc, 0xc00000, 2, 1)] * 26, (0xcc0e, 0xc00004, 2, 0x8014)]
            writes.append((0xcc06, 0xff010c, 2, lock)); add(0xcc16, SP - 12, msg, 0x64, final_ret); code, final_pr = selected, 0x64
        else: writes.append((0xcb94, 0xff06d6, 4, 0xffffffff)); add(0xcb8c, SP - 8, msg, priority, final_ret); code = 0; msg = 0xffffffff
        add(0xcb98, SP - 8, msg, final_pr, final_ret); add(0x7dfa if not returned else 0x7e16, SP - 4, msg, final_pr, final_ret)
    else: msg = 0x12345678; add(0x7e16, SP - 4, msg, priority, returned)
    add(0x68c0, SP, msg, final_pr, final_ret); add(0x6ef0, SP - 4, msg, final_pr, final_ret); add(0x6f00, SP - 4, msg, final_pr, final_ret); add(0x68c4, SP, msg, final_pr, final_ret)
    record = dict(frame=629, count=len(writes), dropped=0, events=[dict(pc=pc, address=a, width=w, value=v, registers={}) for pc, a, w, v in writes])
    return events, [record]


def gated_stream(gates=(0, 0, 0, 0), path_gates=None, extra=(), opened=False, interrupt=False):
    """One synthetic [68C4,68D4): BSR marks at SP, each initializer's entry and
    closed RTS at SP - 4 with RAM gate words `gates`, and the four pushes."""
    free = free_block([3, 7, 9]); events = []; gate_hex = b''.join(x.to_bytes(2, 'big') for x in gates).hex()
    def add(pc, sp): events.append(dict(frame=629, sequence=len(events), pc=pc, registers=dict(REGS, **{'M68K A5': 0xffff0690, 'M68K A7': sp}),
                                        ranges=[dict(label='free', hex=free.hex()), dict(label='pair_gates', hex=gate_hex), dict(label='p2_origin', hex='02d000a0')]))
    for mark, (entry, ret, open_pc) in zip(g.GATED, g.GATED_PCS):
        add(mark, SP); add(entry, SP - 4); add(open_pc if opened and entry == 0x7154 else ret, SP - 4)
    add(g.GATED[-1], SP)
    writes = [(pc, SP - 4 & 0xffffff, 4, pc) for pc in g.GATED[1:]] + list(extra)
    events_w = [dict(pc=pc, address=a, width=w, value=v, registers={}) for pc, a, w, v in writes]
    if interrupt:  # A VBlank frame taken at 7156: PC long then SR word, mask raised.
        events_w[1:1] = [dict(pc=0x7156, address=SP - 12 & 0xffffff, width=4, value=0x7156, registers={'M68K SR': 0x2600}),
                         dict(pc=0x7156, address=SP - 14 & 0xffffff, width=2, value=0x2000, registers={'M68K SR': 0x2600})]
    return events, [dict(frame=629, count=len(events_w), dropped=0, events=events_w)]


def obj_bytes(mode=0x81, x=0x370, y=0xb0, words=(0x284, 0x284, 0x289), cadence=(5, 5), target=900, count=0, handler=0x12646, service=0x6bd6, callback=0,
              ext=(0x10, 0x10), record=1, control=0xffff0690, cd36=None, history=None):
    b = bytearray(78); b[0] = mode
    for o, v in ((2, x), (4, y), (6, words[0]), (8, words[1]), (10, words[2]), (14, target), (16, count), (0x1e, ext[0]), (0x20, ext[1])): b[o:o + 2] = v.to_bytes(2, 'big')
    b[12], b[13] = cadence
    for o, v in ((0x16, handler), (0x1a, callback), (0x42, 0xffff447a + 12 * record), (0x46, service), (0x4a, control)): b[o:o + 4] = v.to_bytes(4, 'big')
    if cd36 is not None: b[0x36:0x38] = cd36.to_bytes(2, 'big')
    for h, v in enumerate(history or ()): b[0x22 + 2 * h:0x24 + 2 * h] = v.to_bytes(2, 'big')
    return bytes(b)


def records_block(holders):
    """holders: {record: (object address, entry)}."""
    b = bytearray(192)
    for r, (obj, entry) in holders.items(): b[12 * r:12 * r + 12] = obj.to_bytes(4, 'big') + (0xffff312c + 2 * entry).to_bytes(4, 'big') + (0xffff314c + 2 * entry).to_bytes(4, 'big')
    return bytes(b)


def pickup_hit_frames(tamper=False):
    """Pickup 54 hit at frame 700 by P1 (dormant link 53 becomes the emitter),
    then two vanishing walks, the second releasing it (FAA4)."""
    pickup, link, other = g.address(54), g.address(53), g.address(52)
    dormant = obj_bytes(mode=0, words=(0x21d, 0, 0), handler=0x12646, service=0x12646, control=0xffff0690, record=0)
    hit = obj_bytes(); vanish = obj_bytes(mode=0x85, x=0x368, words=(0x21e, 0x21e, 0x227), cadence=(3, 3), target=0x227, service=0x12646, callback=0xfaa4)
    emitter = obj_bytes(handler=0x6d8c, service=0x12646, cd36=0, history=(0xff80,) * 10)
    before = records_block({0: (g.address(55), 0), 1: (pickup, 1)}); after = records_block({0: (g.address(55), 0), 1: (link, 1)})
    kinds = b''.join(k.to_bytes(2, 'big') for k in (5, 6, *(0xffff,) * 14))
    frames = {}; boundaries = {}
    def ev(frame, events, pc, a6, obj, records, a4=0, linked=bytes(78), a5=0xffff0690):
        events.append(dict(frame=frame, sequence=len(events), pc=pc, registers=dict(REGS, **{'M68K A6': a6, 'M68K A5': a5, 'M68K A4': a4}),
                           ranges=[dict(label='object', hex=obj.hex()), dict(label='link0', hex=link.to_bytes(4, 'big').hex()), dict(label='link1', hex=other.to_bytes(4, 'big').hex()),
                                   dict(label='records', hex=records.hex()), dict(label='kinds', hex=kinds.hex()), dict(label='tracking', hex='037000b0'),
                                   dict(label='collision_mask', hex='03ff'), dict(label='multiplayer', hex='0000'), dict(label='tracking2', hex='00000000'),
                                   dict(label='mailbox', hex='0089000600c00001'), dict(label='linked', hex=linked.hex())]))
    states = [(hit, vanish, True, False), (vanish, vanish, False, False), (vanish, bytes([0]) + vanish[1:], False, True)]
    for n, (entry, exit_, is_hit, released) in enumerate(states):
        frame = 700 + n; es = []
        ev(frame, es, 0x69a4, g.BASE, entry, before if is_hit else after)
        ev(frame, es, 0x69aa, pickup, entry if not (tamper and n == 1) else hit, before if is_hit else after)
        if is_hit:
            ev(frame, es, 0x6c00, pickup, entry, before); ev(frame, es, 0x6c48, pickup, entry, before, a4=link, linked=dormant)
            ev(frame, es, 0xfcb32, pickup, entry, before); ev(frame, es, 0x6d8a, pickup, exit_, after, a4=link, linked=emitter)
        if released: ev(frame, es, 0xfaa4, pickup, exit_, after)
        ev(frame, es, 0x69c2, pickup, exit_, after); ev(frame, es, 0x69ce, g.LIMIT, exit_, after)
        frames[frame] = es
        boundaries[str(frame)] = dict(slots={'53': (dormant if n == 0 else emitter).hex(), '52': dormant.hex()})
        boundaries[str(frame + 1)] = dict(slots={'53': emitter.hex(), '52': dormant.hex()})
    return frames, boundaries


def probe_hit_frames(tamper=None):
    """The slot-63 probe hit at frame 800 by P1 carrying in link 53: the
    delivery pops the sparkle (48) then the copy (47); at 801 both walk and the
    dormant link returns at 7A56; at 802 the copy's walk enters 79B6's
    first-ingredient path (D20E shown at VRAM E00E, 7AD6 copies it into the
    FF31B4 object, slot 67, which then walks as a table object) and the sparkle
    releases (an artificial cadence, for the evidence logic only); 6C00 next
    loads link 53 at 803. Returns frames, boundaries and the write records."""
    probe_a, link, other, copy_a, sparkle_a = g.address(63), g.address(53), g.address(52), g.address(47), g.address(48)
    probe = bytearray(obj_bytes(mode=0x80, x=0x96, y=0x106, words=(0x390, 0, 0), cadence=(0, 0), target=0, service=0x78ee, ext=(0x38, 8))); probe[0x42:0x46] = bytes(4)
    probe = bytes(probe); dormant = obj_bytes(mode=0, words=(0x21d, 0, 0), service=0x12646, record=0)
    emitter = obj_bytes(x=0x2d0, words=(0x27e, 0x27e, 0x283), cadence=(2, 5), target=911, handler=0x6d8c, service=0x12646, record=0, cd36=1, history=tuple(0xff80 + i for i in range(10)))
    done = bytearray(obj_bytes(mode=0, x=0xa4, y=0xf6, words=(0x227, 0x21e, 0x227), cadence=(3, 3), target=0x21e, service=0x12646, callback=0x79b6, record=0, cd36=1,
                               history=(0x27e, 0xff81, 0x283, *(0xff80 + i for i in range(3, 10)))))
    done = bytes(done); copy = bytes([0x87]) + done[1:]
    sparkle = bytearray(obj_bytes(mode=0x85, x=0x2c8, y=0xa8, words=(0x21e, 0x21e, 0x227), cadence=(3, 3), target=0x227, service=0x12646, callback=0xfaa4, count=0x1234, control=0xdeadbeef))
    sparkle = bytes(sparkle); walked = lambda b, counter, frame=None: bytes(b[:6]) + (frame or b[6:8]) + bytes(b[8:12]) + bytes([counter]) + bytes(b[13:])
    copy1, sparkle1 = walked(copy, 2), walked(sparkle, 2)
    sparkle2 = bytes([0]) + walked(sparkle1, 1)[1:]
    frames = {}; boundaries = {str(800): dict(slots={'53': emitter.hex(), '52': dormant.hex()})}
    for f in (801, 802, 803): boundaries[str(f)] = dict(slots={'53': done.hex(), '52': dormant.hex()})
    table_a = g.address(67); ff31 = lambda ac, bc, be_: (ac.to_bytes(4, 'big') + bytes(4) + table_a.to_bytes(4, 'big') + g.address(66).to_bytes(4, 'big')
                                                      + bc.to_bytes(2, 'big') + be_.to_bytes(2, 'big'))
    message = lambda text, priority: text.to_bytes(4, 'big') + bytes(9) + bytes([priority]) + bytes(4)
    def table_bytes(b, mode, x, y, countdown, cursor, toggle):
        b = bytearray(b); b[0] = mode
        for o, v in ((2, x), (4, y), (6, 0x27e), (8, 0x27e), (10, 0x283), (0x10, countdown), (0x32, 0xffff), (0x36, toggle)): b[o:o + 2] = v.to_bytes(2, 'big')
        b[12] = b[13] = 5; b[0x16:0x1a] = (0x7a88).to_bytes(4, 'big'); b[0x2e:0x32] = (0x7a58 + 2 * cursor).to_bytes(4, 'big'); return bytes(b)
    table = table_bytes(copy1, 0x81, 0xac, 0xfa, 0x0e, 0, 0); residue = table_bytes(copy1, 0, 0xab, 0xfb, 0x0d, 1, 1); table1 = table_bytes(copy1, 0x81, 0xab, 0xfb, 0x0d, 1, 1)
    def ev(es, pc, a6, obj, free, a4=0, linked=bytes(78), mailbox='1111222233334444', globals_=ff31(0, 2, 0), text=message(0xd28c, 0), records=records_block({0: (link, 0)})):
        es.append(dict(frame=0, sequence=len(es), pc=pc, registers=dict(REGS, **{'M68K A6': a6, 'M68K A5': 0xffff0690, 'M68K A4': a4}),
                       ranges=[dict(label='object', hex=obj.hex()), dict(label='link0', hex=link.to_bytes(4, 'big').hex()), dict(label='link1', hex=other.to_bytes(4, 'big').hex()),
                               dict(label='tracking', hex='04a00106'), dict(label='collision_mask', hex='03ff'), dict(label='multiplayer', hex='0000'), dict(label='tracking2', hex='00000000'),
                               dict(label='rise', hex='00000000'), dict(label='mailbox', hex=mailbox), dict(label='linked', hex=linked.hex()), dict(label='free', hex=free.hex()),
                               dict(label='ingredient', hex=globals_.hex()), dict(label='message', hex=text.hex()), dict(label='message2', hex=bytes(18).hex()),
                               dict(label='tilemap', hex='0000e000'), dict(label='records', hex=records.hex())]))
    stack = free_block([5, 47, 48] if tamper != 'pops' else [5, 48, 47]); rest = free_block([5])
    es = []; ev(es, 0x69a4, g.BASE, probe, stack); ev(es, 0x69aa, probe_a, probe, stack); ev(es, 0x7910, probe_a, probe, stack); ev(es, 0x7922, probe_a, probe, stack, a4=link, linked=emitter)
    ev(es, 0xfcb32, probe_a, probe, stack, mailbox='008c000600c00001'); ev(es, 0x7976, sparkle_a, sparkle, rest); ev(es, 0x79b2, link, done, rest, a4=copy_a, linked=copy)
    ev(es, 0x79b4, probe_a, probe, rest); ev(es, 0x69c2, probe_a, probe, rest); ev(es, 0x69ce, g.LIMIT, probe, rest); frames[800] = es
    es = []; ev(es, 0x69a4, g.BASE, probe, rest)
    ev(es, 0x69aa, copy_a, copy if tamper != 'chain' else done, rest); ev(es, 0x69c2, copy_a, copy1, rest); ev(es, 0x69aa, sparkle_a, sparkle, rest); ev(es, 0x69c2, sparkle_a, sparkle1, rest)
    ev(es, 0x69aa, probe_a, probe, rest); ev(es, 0x7910, probe_a, probe, rest); ev(es, 0x7922, probe_a, probe, rest, a4=link, linked=done); ev(es, 0x7a56, probe_a, probe, rest)
    ev(es, 0x69c2, probe_a, probe, rest); ev(es, 0x69ce, g.LIMIT, probe, rest); frames[801] = es
    shown = dict(globals_=ff31(table_a, 0, 0x50), text=message(0xd20e, 1), records=records_block({0: (table_a, 0)}))
    es = []; ev(es, 0x69a4, g.BASE, probe, rest)
    ev(es, 0x69aa, copy_a, copy1, rest); ev(es, 0x79b6, copy_a, copy1, rest); ev(es, 0xcb9a, copy_a, copy1, rest)
    ev(es, 0xfaa4, copy_a, copy1, rest, a4=table_a, linked=table if tamper != 'copied' else residue); ev(es, 0x69c2, copy_a, residue, free_block([5, 47]), **shown)
    ev(es, 0x69aa, sparkle_a, sparkle1, free_block([5, 47]), **shown); ev(es, 0xfaa4, sparkle_a, sparkle2, free_block([5, 47]), **shown)
    ev(es, 0x69c2, sparkle_a, sparkle2, free_block([5, 47, 48]), **shown)
    ev(es, 0x69aa, table_a, table, free_block([5, 47, 48]), **shown); ev(es, 0x69c2, table_a, table1, free_block([5, 47, 48]), **shown)
    ev(es, 0x69ce, g.LIMIT, probe, free_block([5, 47, 48]), **shown); frames[802] = es
    if tamper == 'touched': boundaries['802'] = dict(slots={'53': emitter.hex(), '52': dormant.hex()})
    es = []; ev(es, 0x6c48, g.address(54), probe, rest, a4=link); frames[803] = es
    vdp = [(0xcbb8, 0xc00004, 2, 0x8004), (0xcbf0, 0xc00004, 4, 0x600e0003), *[(0xcbfc, 0xc00000, 2, 1)] * 26, (0xcc0e, 0xc00004, 2, 0x8014)]
    writes = [dict(frame=802, count=len(vdp), dropped=0, events=[dict(pc=pc, address=a, width=w, value=v, registers={}) for pc, a, w, v in vdp])]
    return frames, boundaries, writes


class PairInitializerEvidenceTests(unittest.TestCase):
    def test_probe_hit_delivery_rows_outputs_later_walks_and_dormancy(self):
        hits, later, dormant, activations = g.probe_walks(*probe_hit_frames())
        self.assertEqual([(h['frame'], h['delivered'], h['sounds'], h['created']) for h in hits], [(800, True, 1, [48, 47]), (801, False, 0, [])])
        row, want = hits[0]['row'], hits[0]['want']
        self.assertEqual(len(row), 86); self.assertEqual(row[14:19], (63, 53, 52, 1, 0)); self.assertEqual(row[71:73], (0, 0)); self.assertEqual(row[80:86], (3, 48, 47, 1, 0, 0))
        # Probe, the dormant link (0xa4, 0xf6, mode 0), the untouched link, then the sparkle and the copy.
        self.assertEqual(want[15:18], (0, 0xa4, 0xf6)); self.assertEqual(want[28], 0); self.assertEqual(want[41:44], (2, 0, 48))
        self.assertEqual(want[44:54], (0x2c8, 0xa8, 0, 0x85, 0x21e, 0x21e, 0x227, 3, 3, 0x227)); self.assertEqual(want[54:56], (1, 47))
        self.assertEqual(want[-6:], (1, 0x8c, 6, 0xc0, 1, 1)); self.assertEqual(hits[1]['want'][-3:], (0, 0, 1))
        self.assertEqual([(w['frame'], w['slot'], w['kind'], w['mode'], w['want'][:3]) for w in later],
                         [(801, 47, 1, '--delivered', (1, 0, 0xa4)), (801, 48, 0, '--delivered', (1, 0, 0x2c8)), (802, 47, 1, '--ingredient', (1, 1, 1)),
                          (802, 48, 0, '--delivered', (1, 1, 0x2c8)), (802, 67, 2, '--scheduled', (6, 0xab, 0xfb))])
        # 79B6/7AD6: the copy's 31-field row (FF31B4 = slot 67, record 0 held by link 53, MIX
        # held at priority 0, FF31BC 2) and the released residue, slot 67 and the outputs.
        ingredient = later[2]
        self.assertEqual(len(ingredient['row']), 31); self.assertEqual(ingredient['row'][16:], (0, 47, 67, 53, 0, 0, 1, 0, 0, 0, 0xe000, 2, 0, 1, 1))
        self.assertEqual(ingredient['want'][3:5], (0xab, 0xfb)); self.assertEqual(ingredient['want'][18:20], (0xac, 0xfa))
        self.assertEqual(ingredient['want'][33:], (67, 67, 0, 3, 1, 0, 1, 0xe00e, 0, 0x50, 2))
        self.assertEqual(later[4]['row'][-3:], (0, 1, 4096)); self.assertEqual(activations, [dict(frame=802, copy=47, target=67, shown=True, vram=0xe00e)])
        self.assertEqual(later[1]['row'][11:18], (0,) * 7); self.assertEqual(later[3]['want'][-1], 3)
        self.assertEqual(dormant, [dict(frame=800, slot=53, unchanged_through=803)])
        # The pops must be the stack's top two in order; a walk must start where the
        # last ended; the delivered link must not change before its next use.
        for tamper in ('pops', 'chain', 'touched', 'copied'):
            with self.assertRaises(ValueError): g.probe_walks(*probe_hit_frames(tamper))
        with self.assertRaises(ValueError): g.delivered_state(bytes([0x87]) + bytes(77))
        with self.assertRaises(ValueError): g.sparkle_state(obj_bytes(service=0x12646, callback=0x79b6))
    def test_pickup_hit_walks_rows_outputs_and_chain(self):
        frames, boundaries = pickup_hit_frames(); walks = g.pickup_walks(frames, boundaries)
        self.assertEqual([(w['frame'], w['slot'], w['hit'], w['released'], w['phase_before'], w['phase_after'], w['sounds']) for w in walks],
                         [(700, 54, True, False, 0, 1, 1), (701, 54, False, False, 1, 1, 0), (702, 54, False, True, 1, 1, 0)])
        hit = walks[0]
        self.assertEqual(len(hit['row']), 115); self.assertEqual(hit['row'][15:20], (54, 53, 52, 0, 0)); self.assertEqual(hit['row'][-1], 0)
        # The emitter takes the pickup's record; the expected output names it holder 2.
        self.assertEqual(hit['want'][:2], (1, 0)); self.assertEqual(hit['want'][17], 1)
        records = hit['want'][18 + 27 + 13:18 + 27 + 13 + 32]; self.assertEqual(records[:4], (4, 0, 2, 1))
        self.assertEqual(walks[2]['want'][-2:], (1, 54))
        # Walk 701 starts from a state other than 700's exit: the chain breaks.
        with self.assertRaises(ValueError): g.pickup_walks(*pickup_hit_frames(tamper=True))
        # Unmodeled bytes, an unknown callback or an active return-only link reject.
        with self.assertRaises(ValueError): g.pickup_state(obj_bytes()[:0x30] + b'\x01' + obj_bytes()[0x31:])
        with self.assertRaises(ValueError): g.pickup_state(obj_bytes(service=0x12646, callback=0x1234))
        with self.assertRaises(ValueError): g.link_state(obj_bytes(mode=0x80, service=0x12646))
        self.assertEqual(g.link_state(obj_bytes(handler=0x6d8c, service=0x12646, cd36=7, history=tuple(range(10))))[1][11:22], (7, *range(10)))

    def test_gated_pairs_closed_path_writes_and_rejections(self):
        x, = g.validate_gated(*gated_stream())
        self.assertEqual((x['gates'], x['writes'], x['free_before'], x['a5'], x['p2_origin'], x['interrupt_frames']), ([0] * 4, 4, [3, 7, 9], 0xffff0690, [0x2d0, 0xa0], []))
        self.assertEqual(len(g.validate_gated(*gated_stream(interrupt=True))[0]['interrupt_frames']), 1)
        # An open gate word, an open path, an extra write by these PCs or a
        # missing push is rejected; a dropped write record is incomplete.
        for kwargs in (dict(gates=(0, 1, 0, 0)), dict(opened=True), dict(extra=((0x7164, 0xff1b50, 4, 1),))):
            with self.assertRaises(ValueError): g.validate_gated(*gated_stream(**kwargs))
        e, w = gated_stream(); w[0]['events'].pop()
        with self.assertRaises(ValueError): g.validate_gated(e, w)
        e, w = gated_stream(); w[0]['dropped'] = 1
        with self.assertRaises(ValueError): g.validate_gated(e, w)
        # Writes outside the gated code (the message step's 68C4 push) are not its own.
        e, w = gated_stream(extra=((0x68c4, SP - 4 & 0xffffff, 4, 0x68c4),)); self.assertEqual(g.validate_gated(e, w)[0]['writes'], 4)

    def test_setup_message_model_paths_writes_and_vdp(self):
        events, writes = message_stream(); m, = g.validate_message(events, writes)
        self.assertEqual((m['selected'], m['code'], m['priority'], m['shown'], m['vram'], m['ram_writes'], m['device_writes']), (1, 1, 0x64, True, (0x61ce0003 >> 16 & 0x3fff) | 3 << 14, 4, 29))
        for kwargs, want in ((dict(priority=0x70), (1, 0, 0x70, False)), (dict(returned=9), (2, 2, 0x64, True)), (dict(kinds=(5,)), (0, None, 0x10, False)),
                             (dict(two=1), (0, None, 0x10, False)), (dict(priority=0x80), (1, 1, 0x64, True)), (dict(vram=False), (1, 1, 0x64, True))):
            e, w = message_stream(**kwargs); m, = g.validate_message(e, w)
            self.assertEqual((m['selected'], m['code'], m['priority'], m['shown']), want)
        self.assertIsNone(g.validate_message(*message_stream(vram=False))[0]['vram'])
        # Wrong RAM write, broken VDP sequence or a different +53 are rejected.
        e, w = message_stream(); w[0]['events'][0]['value'] = 0xd2a2
        with self.assertRaises(ValueError): g.validate_message(e, w)
        e, w = message_stream(); w[0]['events'] = [x for x in w[0]['events'] if not (x['address'] == 0xc00000)][:-1] + w[0]['events'][-1:]
        with self.assertRaises(ValueError): g.validate_message(e, w)
        e, w = message_stream(); m53 = bytearray.fromhex(e[-1]['ranges'][0]['hex']); m53[0x53 - 0x46] = 0; e[-1]['ranges'][0]['hex'] = m53.hex()
        with self.assertRaises(ValueError): g.validate_message(e, w)

    def test_pickup_pass_inputs_frames_records_and_writes(self):
        s = Stream(); s.base['M68K A5'] = 0xffff0690
        kinds = [0xffff] * 16; counts = [0] * 16; kinds[2], counts[2] = 5, 0; kinds[7], counts[7] = 0x20d, 2
        positions = [(0x2d0, 0xa0), (0x370, 0xfff8)] + [(0, 0)] * 14
        (t0, f0), (t1, f1) = pickup_run(s, kinds, counts, positions, free_block([3, 54, 55]))
        for k, e in enumerate(s.events): e['sequence'] = k
        run, = g.validate_pickups(s.events, runs(s))
        self.assertEqual(([a['slot'] for a in run['members']], run['entries']), ([55, 54], [2, 7]))
        self.assertEqual(g.pickup_fields(f0), (0x2d0, 0xb0, 0, 0x81, 0x27e, 0x27e, 0x283, 5, 5, 0, 0, 1, 16, 16, 0))
        self.assertEqual(g.pickup_fields(f1), (0x370, 8, 0, 0x81, 0x20d, 0x20d, 0x214, 1, 1, 0, 2, 1, 16, 16, 1))
        # Fixed writes plus per pickup: 11 calls/saves/F9E2, 10 stores, BSR, frames, 2 stores, BSR, cadence, handler.
        self.assertEqual(len(g.pickup_writes(run)), 2 + 48 + 2 + (9 + 6 + 10 + 1 + 5 + 2 + 1 + 2 + 1) + (9 + 6 + 10 + 1 + 3 + 2 + 1 + 2 + 1))
        # A negative kind takes the MULU path and leaves a nonzero product upper word in D2.
        wide = Stream(); wide.base['M68K A5'] = 0xffff0690; k2 = [0xd3ff] + [0xffff] * 15
        pickup_run(wide, k2, [0] * 16, positions, free_block([3, 55]))
        for k, e in enumerate(wide.events): e['sequence'] = k
        (only,) = g.validate_pickups(wide.events, runs(wide)); self.assertEqual(g.pickup_fields(bytes.fromhex(only['finals'][0]))[4], 0xd3ff * 6 + 0x260 & 65535)
        self.assertEqual(next(e for e in wide.events if e['pc'] == 0x6b3e)['registers']['M68K D2'] >> 16, 4)
        bad = Stream(); bad.base['M68K A5'] = 0xffff0690; pickup_run(bad, kinds, counts, positions, free_block([3, 54, 55]))
        tamper = copy.deepcopy(bad.events); next(e for e in tamper if e['pc'] == 0x6af0)['registers']['M68K D1'] = 0xa0
        for k, e in enumerate(tamper): e['sequence'] = k
        with self.assertRaises(ValueError): g.validate_pickups(tamper, runs(bad))
        cleared = copy.deepcopy(bad.events); cleared[-1]['ranges'][-1]['hex'] = '0000000000000001'
        for k, e in enumerate(cleared): e['sequence'] = k
        with self.assertRaises(ValueError): g.validate_pickups(cleared, runs(bad))

    def test_setup_tail_composition_writes_and_seed(self):
        s = Stream(); s.base['M68K A5'] = 0xffff0690; free = free_block([3, 52, 53, 54, 55]); stack = (0x68c0).to_bytes(4, 'big') + bytes(12)
        def mark(pc): s.add(pc, CALLER_A6, SP + 4, bytes(78), free, stack, 0x13572468)
        kinds = [0xffff] * 16; counts = [0] * 16; kinds[0] = 5; kinds[1] = 6
        mark(g.TAIL[0]); pickup_run(s, kinds, counts, [(0x2d0, 0xa0), (0x370, 0xa0)] + [(0, 0)] * 14, free); free = s.rest; mark(g.TAIL[1])
        mark(g.TAIL[2]); s.group([], name='link_p1', free=free); free = s.rest; mark(g.TAIL[3]); s.base['M68K A5'] = 0xffff0838
        mark(g.TAIL[4]); s.group([], name='link_p2', free=free); free = s.rest; mark(g.TAIL[5])
        for k, e in enumerate(s.events): e['sequence'] = k
        r = runs(s); pairs = g.validate_pickups(s.events, r) + g.validate_pair(s.events, r, 'link_p1') + g.validate_pair(s.events, r, 'link_p2')
        tail, = g.validate_tail(s.events, pairs)
        self.assertEqual((tail['slots'], s.links), ([55, 54, 53, 52], g.address(53).to_bytes(4, 'big') + g.address(52).to_bytes(4, 'big')))
        want = g.tail_writes(tail | dict(kind='tail')); self.assertEqual(len(want), 3 + len(g.pickup_writes(tail['runs'][0])) + 12 + 12)
        events = [dict(pc=pc, address=a, width=w, value=v, registers={'M68K A6': g.address(5), 'M68K A0': 0x200}) for pc, a, w, v in want]
        audit = g.audit_frame_writes(dict(frame=629, count=len(events), dropped=0, events=events), tail['runs'], [tail | dict(kind='tail')])
        self.assertEqual((audit['tail_writes'], audit['other_allocator_writes']), ([len(want)], 0))
        for bad in (events[1:], events[:60] + events[61:]):
            with self.assertRaises(ValueError): g.audit_frame_writes(dict(frame=629, count=len(bad), dropped=0, events=bad), tail['runs'], [tail | dict(kind='tail')])
        # A tail whose links were made under the wrong control is not this tail.
        with self.assertRaises(ValueError): g.validate_tail(s.events, [p for p in pairs if p['variant'] != 'link_p2'])

    def test_dormant_runs_identities_writes_and_seed(self):
        s = Stream(); kept = bytearray(residue(7, 8, 0xffff0838)); kept[2:6] = bytes.fromhex('00960106'); kept[8:14] = bytes.fromhex('000100020304')
        (t1, f1), = s.group([3, 66, 67], [bytes(kept)], name='dormant_b4')
        (t2, f2), = s.group([], name='dormant_b8', free=s.rest)
        r = runs(s); b4, = g.validate_pair(s.events, r, 'dormant_b4'); b8, = g.validate_pair(s.events, r, 'dormant_b8')
        self.assertEqual((b4['members'][0]['slot'], b8['members'][0]['slot'], s.dormant), (67, 66, g.address(67).to_bytes(4, 'big') + g.address(66).to_bytes(4, 'big')))
        # Mode cleared; F9E2's frame 021D; position, +08..+0D, target, countdown, link kept.
        self.assertEqual(g.return_only_fields(f1), (0x96, 0x106, 0, 0, 0x21d, 1, 2, 3, 4, 7, 8, 2))
        self.assertEqual((len(g.pair_writes(b4)), g.pair_writes(b4)[-2:]), (12, [(0x6ed4, g.DORMANT, 4, t1), (0x6eda, t1 & 0xffffff, 1, 0)]))
        rows = g.native_seed(b4, 2); self.assertEqual((rows[0], rows[2 + 67]), ((68, 3, 2, 0), (9, 7, 8, 2, 1, 2, 3, 4, 0x96, 0x106)))
        self.assertEqual(g.native_seed(b8, 0)[0], (68, 2, 0, 1))
        # The identity store must name the popped object; FF31B8 must be untouched by 6EC8.
        for change in (lambda e: e['ranges'][3].__setitem__('hex', bytes(8).hex()), lambda e: e['ranges'][3].__setitem__('hex', (g.address(67).to_bytes(4, 'big') * 2).hex())):
            bad = Stream(); bad.group([3, 66, 67], name='dormant_b4'); change(bad.events[-1])
            with self.assertRaises(ValueError): g.validate_pair(bad.events, runs(bad), 'dormant_b4')

    def test_setup_prefix_composition_and_writes(self):
        s, out = prefix_stream(); r = runs(s)
        pairs = [p for name, v in g.VARIANTS.items() if not v.get('custom') for p in g.validate_pair(s.events, r, name)]
        prefix, = g.validate_prefix(s.events, pairs)
        self.assertEqual(prefix['slots'], list(range(67, 55, -1))); self.assertEqual([run['variant'] for run in prefix['runs']], list(g.PREFIX_ORDER))
        want = g.prefix_writes(prefix); self.assertEqual(len(want), 6 + 12 + 12 + 43 + 65 + 40 + 38)
        events = [dict(pc=pc, address=a, width=w, value=v, registers={'M68K A6': g.address(5), 'M68K A0': 0x200}) for pc, a, w, v in want]
        audit = g.audit_frame_writes(dict(frame=629, count=len(events), dropped=0, events=events), prefix['runs'], [prefix])
        self.assertEqual((audit['prefix_writes'], audit['other_allocator_writes']), ([216], 0))
        for bad in (events[1:], events[:-1], events[:100] + events[101:]):
            with self.assertRaises(ValueError): g.audit_frame_writes(dict(frame=629, count=len(bad), dropped=0, events=bad), prefix['runs'], [prefix])
        # Order, stack and A5 are part of the composition.
        swapped = [e for e in s.events]; marks = [k for k, e in enumerate(swapped) if e['pc'] in (0x6890, 0x6894)]
        broken = copy.deepcopy(s.events); broken[marks[0]]['registers']['M68K A7'] = SP
        with self.assertRaises(ValueError): g.validate_prefix(broken, pairs)
        broken = copy.deepcopy(s.events); broken[marks[1]]['registers']['M68K A5'] = 0xffff0838
        with self.assertRaises(ValueError): g.validate_prefix(broken, pairs)
        with self.assertRaises(ValueError): g.validate_prefix(s.events, [p for p in pairs if p['variant'] != 'quad'])

    def test_dormant_conversion_bounds_continuity(self):
        s = Stream(); (t67, f67), = s.group([3, 66, 67], name='dormant_b4'); (t66, f66), = s.group([], name='dormant_b8', free=s.rest)
        r = runs(s); b4, = g.validate_pair(s.events, r, 'dormant_b4'); b8, = g.validate_pair(s.events, r, 'dormant_b8')
        identities = g.address(67).to_bytes(4, 'big') + g.address(66).to_bytes(4, 'big')
        active = bytearray(f67); active[0] = 0x81; active[0x16:0x1a] = (0x7a88).to_bytes(4, 'big'); active = bytes(active)
        end = g.END; g.END = 633
        try:
            state = {67: f67, 66: f66}; boundaries = {}; frames = {}
            def boundary(f): boundaries[str(f)] = dict(anchor='13572468', dormant=identities.hex(), slots={str(i): state[i].hex() for i in state})
            boundary(630)
            for frame in (630, 631, 632):
                w = Stream(frame); w.dormant = identities; w.add(0x69a4, 0, SP, bytes(78), None, bytes(16), 0x13572468)
                if frame == 631:
                    w.add(0x7ad6, g.address(47), SP, bytes(78), None, bytes(16), 0x13572468)
                    w.add(g.COPY, g.address(47), SP, bytes(78), None, bytes(16), 0x13572468); w.events[-1]['registers']['M68K A4'] = g.address(67)
                    state[67] = active
                for i in (66, 67):
                    w.add(0x69aa, g.address(i), SP, state[i], None, bytes(16), 0x13572468); w.add(0x69c2, g.address(i), SP, state[i], None, bytes(16), 0x13572468)
                w.add(0x69ce, 0, SP, bytes(78), None, bytes(16), 0x13572468)
                for k, e in enumerate(w.events): e['sequence'] = 1000 * frame + k
                frames[frame] = w.events; boundary(frame + 1)
            ram = bytearray(65536); ram[0x31b4:0x31bc] = identities
            for i in state: o = (g.BASE & 65535) + i * g.STRIDE; ram[o:o + 78] = state[i]
            phases, kept = g.continuity(frames, boundaries, [b4, b8], bytes(ram))
            self.assertEqual(kept['conversions'], {'67': dict(frame=631, source_slot=47, via='fb06', cause='7AD6')}); self.assertEqual(sorted(kept['end_rows']), ['66'])
            self.assertEqual([sorted(p[1]) for p in phases], [[66, 67], [66], [66]]); self.assertEqual(phases[0][5], {66: False, 67: False})
            for drop in (g.COPY, 0x7ad6):
                bad = copy.deepcopy(frames); bad[631] = [e for e in bad[631] if e['pc'] != drop]
                with self.assertRaises(ValueError): g.continuity(bad, boundaries, [b4, b8], bytes(ram))
            moved = copy.deepcopy(boundaries); moved['632']['dormant'] = bytes(8).hex()
            with self.assertRaises(ValueError): g.continuity(frames, moved, [b4, b8], bytes(ram))
            base = g.address(67) & 0xffffff
            copy_writes = [dict(pc=0xfb10, address=base + o, width=1, value=active[o], registers={}) for o in range(78)]
            later = dict(pc=0x7a98, address=base + 0x36, width=2, value=1, registers={})
            audit = g.audit_continuity_writes([dict(frame=631, count=79, dropped=0, events=copy_writes + [later]), dict(frame=632, count=1, dropped=0, events=[later])], [b4, b8], kept['conversions'])
            self.assertEqual(audit['conversion_copy_writes'], {'67': 78})
            with self.assertRaises(ValueError): g.audit_continuity_writes([dict(frame=631, count=78, dropped=0, events=copy_writes[1:] + [later])], [b4, b8], kept['conversions'])
            # Before its conversion the dormant slot accepts no handler writes.
            owned = dict(later, registers={'M68K A6': g.address(67)})
            with self.assertRaises(ValueError): g.audit_continuity_writes([dict(frame=630, count=1, dropped=0, events=[owned])], [b4, b8], kept['conversions'])
            with self.assertRaises(ValueError): g.audit_continuity_writes([dict(frame=630, count=1, dropped=0, events=[dict(later, address=g.DORMANT, width=4)])], [b4, b8])
        finally: g.END = end

    def test_collision_quad_shape_writes_seed_and_continuity(self):
        s = Stream(); s.base['M68K A5'] = 0xffff0690
        kept = bytearray(residue(5, 6, 0xffff0838)); kept[8:14] = bytes.fromhex('0390039311a5')
        (t0, f0), (t1, f1), (t2, f2), (t3, f3) = s.group([3, 60, 61, 62, 63], [bytes(kept)], name='quad')
        quad, = g.validate_pair(s.events, runs(s), 'quad')
        self.assertEqual(([a['slot'] for a in quad['members']], quad['representable']), ([63, 62, 61, 60], [True] * 4))
        # Probe: A5 link, extents, 78EE; +08..+0D, target and countdown kept.
        self.assertEqual(g.probe_fields(f0), (150, 262, 0, 0x80, 912, 0x390, 0x393, 0x11, 0xa5, 5, 6, 1, 0x38, 8))
        self.assertEqual([g.return_only_fields(f)[:5] for f in (f1, f2, f3)], [(182, 262, 0, 0x80, 913), (150, 294, 0, 0x80, 914), (182, 294, 0, 0x80, 915)])
        self.assertEqual(len(g.pair_writes(quad)), 65); self.assertEqual(g.validate_pair(s.events, runs(s), 'rising'), [])
        rows = g.native_seed(quad, [(1, 2, 1023, 0, 0, 0, 0)])
        self.assertEqual((rows[0], rows[2 + 63], rows[2 + 60], rows[-1]), ((68, 5, 1, 1), (9, 5, 6, 2, 0x390, 0x393, 0x11, 0xa5, 0, 0), (9, 0, 0, 0, 0, 0, 0, 0, 0, 0), (1, 2, 1023, 0, 0, 0, 0)))
        # A4 must stay on the probe; a wrong derived position is a different store.
        bad = Stream(); bad.base['M68K A5'] = 0xffff0690; bad.group([3, 60, 61, 62, 63], name='quad'); bad.events[-1]['registers']['M68K A4'] = g.address(60)
        with self.assertRaises(ValueError): g.validate_pair(bad.events, runs(bad), 'quad')
        bad = Stream(); bad.base['M68K A5'] = 0xffff0690; bad.group([3, 60, 61, 62, 63], name='quad')
        obj = next(r for r in bad.events[-1]['ranges'] if r['label'] == 'object'); b = bytearray.fromhex(obj['hex']); b[3] ^= 1; obj['hex'] = b.hex()
        with self.assertRaises(ValueError): g.validate_pair(bad.events, runs(bad), 'quad')
        # Retained walks: mode 80 never changes; the probe's 78EE service runs
        # once per walk and consumes the observed P1 tracking/mask/gate.
        end = g.END; g.END = 632
        try:
            state = {63: f0, 62: f1, 61: f2, 60: f3}; boundaries = {}; frames = {}
            def boundary(f): boundaries[str(f)] = dict(anchor=(0x13572468).to_bytes(4, 'big').hex(), slots={str(i): state[i].hex() for i in state})
            boundary(630)
            def add(w, pc, a6, obj, track):
                w.add(pc, a6, SP, obj, None, bytes(16), 0x13572468)
                w.events[-1]['ranges'] += [dict(label='gates', hex='00000000'), dict(label='rise', hex='00000000'), dict(label='tracking', hex=track.hex()),
                                           dict(label='collision_mask', hex='03ff'), dict(label='multiplayer', hex='0000'), dict(label='tracking2', hex='00000000')]
            for frame, track in ((630, bytes.fromhex('00100020')), (631, bytes.fromhex('00300040'))):
                w = Stream(frame); add(w, 0x69a4, 0, bytes(78), track)
                for i in (60, 61, 62, 63):
                    add(w, 0x69aa, g.address(i), state[i], track)
                    if i == 63: add(w, g.SERVICE, g.address(i), state[i], track)
                    add(w, 0x69c2, g.address(i), state[i], track)
                add(w, 0x69ce, 0, bytes(78), track)
                for k, e in enumerate(w.events): e['sequence'] = 1000 * frame + k
                frames[frame] = w.events; boundary(frame + 1)
            ram = bytearray(65536)
            for i in state: o = (g.BASE & 65535) + i * g.STRIDE; ram[o:o + 78] = state[i]
            phases, kept = g.continuity(frames, boundaries, [quad], bytes(ram))
            self.assertEqual((kept['walks'], kept['updates'], [p[3] for p in phases]), (2, 8, [(16, 32, 1023, 0, 0, 0, 0), (48, 64, 1023, 0, 0, 0, 0)]))
            self.assertEqual((kept['end_rows']['63'][0], kept['end_rows']['60'][0], kept['collision_config_inputs']), (7, 8, {str((1023, 0, 0, 0, 0)): 2}))
            # A 7910 hit inside the probe's own service is recorded (native must
            # reject there); anywhere else it is foreign work and rejects.
            service = next(k for k, e in enumerate(frames[631]) if e['pc'] == g.SERVICE)
            probe_hit = copy.deepcopy(frames); probe_hit[631].insert(service + 1, dict(probe_hit[631][service], pc=g.HIT))
            for k, e in enumerate(probe_hit[631]): e['sequence'] = 631000 + k
            phases2, kept2 = g.continuity(probe_hit, boundaries, [quad], bytes(ram))
            self.assertEqual(([p[4] for p in phases2], kept2['unsupported_hit_frames']), ([set(), {63}], [631]))
            early = copy.deepcopy(frames); early[631].insert(service, dict(early[631][service], pc=g.HIT))
            for k, e in enumerate(early[631]): e['sequence'] = 631000 + k
            hit = copy.deepcopy(frames); hit[631].insert(3, dict(hit[631][3], pc=g.HIT))
            missing = copy.deepcopy(frames); missing[631] = [e for e in missing[631] if e['pc'] != g.SERVICE]
            for f in (hit, early, missing):
                with self.assertRaises(ValueError): g.continuity(f, boundaries, [quad], bytes(ram))
            ok = dict(frame=631, count=1, dropped=0, events=[dict(pc=0xb12a, address=g.address(63) + 0x14 & 0xffffff, width=2, value=0, registers={'M68K A6': g.address(63)})])
            self.assertEqual(g.audit_continuity_writes([ok], [quad])['writes_by_slot'], {'63': 1})
            foreign = dict(ok['events'][0], pc=0x7924, address=g.address(63) + 0x1e & 0xffffff)
            with self.assertRaises(ValueError): g.audit_continuity_writes([dict(ok, events=[foreign])], [quad])
        finally: g.END = end

    def test_rising_pair_control_a4_and_derived_position(self):
        s = Stream(); t1, t2, f1, f2 = s.pair([3, 64, 65], residue(7, 99, 0xffff0838), name='rising')
        pair, = g.validate_pair(s.events, runs(s), 'rising')
        self.assertEqual((pair['members'][0]['slot'], pair['members'][1]['slot'], pair['entry_registers']['M68K A5']), (65, 64, REGS['M68K A5']))
        b1 = bytearray(f1); b1[0x4a:0x4e] = (0xffff0690).to_bytes(4, 'big'); b2 = bytearray(f2); b2[0x4a:0x4e] = (0xffff0690).to_bytes(4, 'big')
        self.assertEqual(g.private_fields(bytes(b1)), (0, 158, 262, 0, 0x81, 922, 922, 927, 5, 5, 7, 0, 1))
        self.assertEqual(g.private_fields(bytes(b2)), (0, 190, 262, 0, 0x81, 928, 928, 933, 5, 5, 0, 0, 1))
        self.assertEqual(len(g.pair_writes(pair)), 43); self.assertEqual(g.validate_pair(s.events, runs(s), 'visibility'), [])
        # A4 must be left on the first member; anything else is a changed register.
        bad = Stream(); bad.pair([3, 64, 65], name='rising'); bad.events[-1]['registers']['M68K A4'] = 0x204
        with self.assertRaises(ValueError): g.validate_pair(bad.events, runs(bad), 'rising')
        bad = Stream(); bad.pair([3, 64, 65], name='rising'); bad.events[-1]['registers']['M68K A5'] = 0x999
        with self.assertRaises(ValueError): g.validate_pair(bad.events, runs(bad), 'rising')
        # The seed carries the logical control; an unmapped caller A5 rejects.
        with self.assertRaises(ValueError): g.native_seed(pair, [])
        pair['entry_registers']['M68K A5'] = 0xffff0690
        self.assertEqual(g.native_seed(pair, [(0, 0, 0)])[0], (68, 3, 1, 1))


    def test_visibility_pair_shape_writes_and_no_anchor(self):
        s = Stream(); t1, t2, f1, f2 = s.pair([3, 56, 57], residue(5, 6, 0xffff0838), name='visibility', anchor=g.address(58))
        pair, = g.validate_pair(s.events, runs(s), 'visibility')
        self.assertEqual((pair['variant'], pair['members'][0]['slot'], pair['members'][1]['slot']), ('visibility', 57, 56))
        self.assertEqual(g.private_fields(f1), (1, 287, 152, 0, 0x81, 892, 892, 901, 5, 5, 5, 6, 2))
        self.assertEqual(g.private_fields(f2), (1, 287, 184, 0, 0x81, 902, 902, 911, 5, 5, 0, 0, 0))
        self.assertEqual(len(g.pair_writes(pair)), 38); self.assertEqual(g.validate_pair(s.events, runs(s), 'return_only'), [])
        # 7C26 must leave FF31C0 untouched.
        bad = Stream(); bad.pair([3, 56, 57], name='visibility', anchor=g.address(58)); bad.events[-1]['ranges'][1]['hex'] = g.address(56).to_bytes(4, 'big').hex()
        with self.assertRaises(ValueError): g.validate_pair(bad.events, runs(bad), 'visibility')
        rows = g.native_seed(pair, [(0, 0, 0), (0, 1, 0)])
        self.assertEqual(rows[0], (68, 3, 2)); self.assertEqual(rows[-2:], [(0, 0, 0), (0, 1, 0)]); self.assertEqual(rows[2 + 57], (9, 5, 6, 2, 0, 0, 0, 0, 0, 0))
        # Both initializers in one frame: each exact block is located, the rest
        # must be generic F9E2 forms; a 7C26 block cannot be passed off as F9E2.
        both = Stream(); a1, a2, _, _ = both.pair([3, 56, 57, 58, 59])
        b1, b2, _, _ = both.pair([], name='visibility', anchor=a2, free=both.rest)
        r = runs(both); ro, = g.validate_pair(both.events, r, 'return_only'); vis, = g.validate_pair(both.events, r, 'visibility')
        def events(p, x, y, name):
            want = g.pair_writes(p); split = 1 + 9 + len(g.VARIANTS[name]['members'][0])
            return [dict(pc=pc, address=a, width=w, value=v, registers={'M68K A6': x if i < split else y, 'M68K A0': 0x200}) for i, (pc, a, w, v) in enumerate(want)]
        record = dict(frame=629, count=78, dropped=0, events=events(ro, a1, a2, 'return_only') + events(vis, b1, b2, 'visibility'))
        self.assertEqual(g.audit_frame_writes([record], [ro, vis])['pair_writes'], [40, 38])
        with self.assertRaises(ValueError): g.audit_frame_writes([record], [ro])
        split = dict(frame=630, count=0, dropped=0, events=record['events'][60:]); head = dict(record, events=record['events'][:60])
        self.assertTrue(g.audit_frame_writes([head, split], [ro, vis])['complete'])
        with self.assertRaises(ValueError): g.audit_frame_writes([head, dict(split, dropped=1)], [ro, vis])

    def test_visibility_continuity_gates_and_writers(self):
        s = Stream(); a1, a2, f1, f2 = s.pair([3, 56, 57, 58, 59])
        b1, b2, h1, h2 = s.pair([], name='visibility', anchor=a2, free=s.rest)
        r = runs(s); ro, = g.validate_pair(s.events, r, 'return_only'); vis, = g.validate_pair(s.events, r, 'visibility')
        end = g.END; g.END = 632
        try:
            state = {59: f1, 58: f2, 57: h1, 56: h2}; boundaries = {}; frames = {}
            def boundary(f): boundaries[str(f)] = dict(anchor=a2.to_bytes(4, 'big').hex(), slots={str(i): state[i].hex() for i in state})
            boundary(630)
            def add(w, pc, a6, obj, gates=0):
                w.add(pc, a6, SP, obj, None, bytes(16), a2)
                w.events[-1]['ranges'] += [dict(label='gates', hex=gates.to_bytes(4, 'big').hex()), dict(label='rise', hex='00000000')]
            for frame, gates in ((630, 0), (631, 0x00000001)):
                w = Stream(frame); add(w, 0x69a4, 0, bytes(78))
                for i in (56, 57, 58, 59):
                    add(w, 0x69aa, g.address(i), state[i], gates)
                    b = bytearray(state[i]); b[12] = b[12] - 1 or b[13]
                    if i in (56, 57) and gates & 0xffff: b[0x12:0x14] = (0x2000).to_bytes(2, 'big')
                    state[i] = bytes(b); add(w, 0x69c2, g.address(i), state[i], gates)
                add(w, 0x69ce, 0, bytes(78))
                for k, e in enumerate(w.events): e['sequence'] = 1000 * frame + k
                frames[frame] = w.events; boundary(frame + 1)
            ram = bytearray(65536)
            for i in state: o = (g.BASE & 65535) + i * g.STRIDE; ram[o:o + 78] = state[i]
            ram[0x31c0:0x31c4] = a2.to_bytes(4, 'big')
            phases, kept = g.continuity(frames, boundaries, [ro, vis], bytes(ram))
            self.assertEqual((kept['walks'], kept['updates'], [p[2] for p in phases]), (2, 8, [(0, 0, 0), (0, 1, 0)]))
            self.assertEqual(kept['end_rows']['57'][0], 5); self.assertEqual(kept['end_rows']['57'][4], 0x2000)
            mixed = copy.deepcopy(frames); mixed[631][1]['ranges'][-2]['hex'] = '00000000'
            with self.assertRaises(ValueError): g.continuity(mixed, boundaries, [ro, vis], bytes(ram))
            ok = dict(frame=631, count=1, dropped=0, events=[dict(pc=0x7cb2, address=g.address(57) + 0x12 & 0xffffff, width=2, value=0x2000, registers={'M68K A6': g.address(57)})])
            self.assertEqual(g.audit_continuity_writes([ok], [ro, vis])['writes_by_slot'], {'57': 1})
            for bad in (dict(ok['events'][0], pc=0x7cc0), dict(ok['events'][0], registers={'M68K A6': g.address(56)}), dict(ok['events'][0], address=g.address(59) + 0x12 & 0xffffff)):
                with self.assertRaises(ValueError): g.audit_continuity_writes([dict(ok, events=[bad])], [ro, vis])
        finally: g.END = end

    def test_corpus_classes_and_native_order(self):
        rows = corpus(); classes = {expected_native_rejection(r) for r in rows}
        self.assertEqual(classes, {None, 1, 2}); self.assertEqual(len(rows[0]), 17)
        self.assertEqual(expected_native_rejection(case(count=1, b01=1)), 2)
        self.assertEqual(expected_native_rejection(case(count=1)), 1)
        self.assertEqual(expected_native_rejection(case(count=2, private_2=1)), 2)
        self.assertTrue(representable(case(target=921, link=5), 0))
        # 783A: four pops; the first failure in pop order decides the rejection.
        quads = quad_corpus(); self.assertEqual({quad_expected_native_rejection(r) for r in quads}, {None, 1, 2}); self.assertEqual(len(quads[0]), 47)
        self.assertEqual([quad_expected_native_rejection(quad_case(count=c, b01_3=1)) for c in (3, 4)], [1, 2])
        self.assertEqual(quad_expected_native_rejection(quad_case(count=2, private_1=1)), 2)
        self.assertIsNone(quad_expected_native_rejection(quad_case(w08_0=65535, c0c_3=255)))

    def test_ordinary_pair_shape_and_exact_bytes(self):
        s = Stream(); t1, t2, f1, f2 = s.pair([3, 57, 58, 59], residue(921, 7, 0xffff0690))
        runs = g.split_invocations([e for e in s.events if e['pc'] in g.F9E2_PCS], 0xf9e2, g.F9E2_PCS)
        pair, = g.validate_pair(s.events, runs)
        self.assertEqual(([a['slot'] for a in pair['members']], pair['free_before']), ([59, 58], [3, 57, 58, 59]))
        self.assertEqual(pair['entry_a6'], CALLER_A6); self.assertEqual(pair['representable'], [True, True])
        self.assertEqual(g.return_only_fields(f1), (161, 270, 0, 0x81, 916, 916, 921, 4, 4, 921, 7, 1))
        self.assertEqual(g.return_only_fields(f2), (164, 270, 0x800, 0x81, 919, 916, 921, 5, 5, 0, 0, 0))
        rows = g.native_seed(pair, 3)
        self.assertEqual(rows[:2], [(68, 4, 3), (3, 57, 58, 59)]); self.assertEqual(rows[2 + 59], (9, 921, 7, 1, 0, 0, 0, 0, 0, 0))
        self.assertEqual(rows[2 + 3], (0,)); self.assertEqual(rows[2 + 0], (1,))

    def test_pair_rejects_tampering(self):
        def mutate(f):
            s = Stream(); s.pair([57, 58, 59]); f(s.events)
            runs = g.split_invocations([e for e in s.events if e['pc'] in g.F9E2_PCS], 0xf9e2, g.F9E2_PCS)
            g.validate_pair(s.events, runs)
        def obj(i, offset, value):
            def f(es):
                r = next(x for x in es[i]['ranges'] if x['label'] == 'object'); b = bytearray.fromhex(r['hex']); b[offset] ^= value; r['hex'] = b.hex()
            return f
        def reg(i, name, value): return lambda es: es[i]['registers'].__setitem__(name, value)
        for change in (obj(50, 0x0e, 1), obj(50, 0x01, 1), obj(25, 0x12, 8), obj(14, 0x30, 1), reg(50, 'M68K A6', g.address(57)),
                       reg(50, 'M68K D3', 9), reg(14, 'M68K A0', 1), reg(50, 'M68K A7', SP - 4), lambda es: es.pop(20),
                       lambda es: es[50]['ranges'][1].__setitem__('hex', '13572468')):
            with self.assertRaises((ValueError, KeyError, IndexError)): mutate(change)
        # A different stack top is a different pop order, not the same pair.
        s = Stream(); s.pair([57, 58, 59]); r = next(x for x in s.events[0]['ranges'] if x['label'] == 'free'); r['hex'] = free_block([57, 59, 58]).hex()
        with self.assertRaises(ValueError): g.validate_pair(s.events, g.split_invocations([e for e in s.events if e['pc'] in g.F9E2_PCS], 0xf9e2, g.F9E2_PCS))

    def test_unrepresentable_residue_seeds_unknown(self):
        res = bytearray(residue()); res[1] = 1
        s = Stream(); s.pair([57, 58, 59], bytes(res))
        pair, = g.validate_pair(s.events, g.split_invocations([e for e in s.events if e['pc'] in g.F9E2_PCS], 0xf9e2, g.F9E2_PCS))
        self.assertEqual(pair['representable'], [False, True]); self.assertEqual(g.native_seed(pair, 0)[2 + 59], (0,))
        for offset in (0x1a, 0x30, 0x45):
            b = bytearray(residue()); b[offset] = 1; self.assertFalse(g.representable(bytes(b)))
        self.assertFalse(g.representable(residue(link=0xffff1ab4)))

    def test_creation_frame_write_audit(self):
        s = Stream(); t1, t2, _, _ = s.pair([57, 58, 59]); pair, writes = pair_writes(s, t1, t2)
        other = [dict(pc=0xf9e4, address=0xff00e2, width=2, value=0x312c, registers={'M68K A0': 0xffff312c, 'M68K A6': g.address(5)}),
                 dict(pc=0xf9fc, address=g.address(5) & 0xffffff, width=1, value=0x80, registers={'M68K A6': g.address(5), 'M68K A0': 0})]
        record = dict(frame=629, count=len(writes) + 2, dropped=0, events=other + writes)
        self.assertEqual(g.audit_frame_writes(record, pair)['pair_writes'], [40])
        for bad in (dict(record, dropped=1), dict(record, events=other + writes[:-1]), dict(record, events=other + writes + writes[:1]),
                    dict(record, events=other + writes[:5] + [dict(writes[5], value=1)] + writes[6:]),
                    dict(record, events=other + writes + [dict(pc=0x1234, address=t1 + 0x30 & 0xffffff, width=2, value=0, registers={})]),
                    dict(record, events=other + writes + [dict(pc=0x1234, address=g.ANCHOR + 2, width=2, value=0, registers={})]),
                    dict(record, events=[dict(other[1], value=0x81)] + writes)):
            with self.assertRaises(ValueError): g.audit_frame_writes(bad, pair)

    def test_continuity_occupancy_anchor_and_phases(self):
        s = Stream(); t1, t2, f1, f2 = s.pair([57, 58, 59])
        pair, = g.validate_pair(s.events, g.split_invocations([e for e in s.events if e['pc'] in g.F9E2_PCS], 0xf9e2, g.F9E2_PCS))
        end = g.END; g.END = 632
        try:
            state = {59: f1, 58: f2}; boundaries = {}; frames = {}
            def boundary(f): boundaries[str(f)] = dict(anchor=t2.to_bytes(4, 'big').hex(), slots={str(i): state[i].hex() for i in state})
            boundary(630)
            for frame in (630, 631):
                w = Stream(frame); w.add(0x69a4, 0, SP, bytes(78), None, bytes(16), t2)
                for i in (58, 59):
                    w.add(0x69aa, g.address(i), SP, state[i], None, bytes(16), t2)
                    b = bytearray(state[i]); b[12] = b[12] - 1 or b[13]; state[i] = bytes(b)
                    w.add(0x69c2, g.address(i), SP, state[i], None, bytes(16), t2)
                w.add(0x69ce, 0, SP, bytes(78), None, bytes(16), t2)
                for k, e in enumerate(w.events): e['sequence'] = 1000 * frame + k
                frames[frame] = w.events; boundary(frame + 1)
            ram = bytearray(65536)
            for i in state: o = (g.BASE & 65535) + i * g.STRIDE; ram[o:o + 78] = state[i]
            ram[0x31c0:0x31c4] = t2.to_bytes(4, 'big')
            phases, kept = g.continuity(frames, boundaries, pair, bytes(ram))
            self.assertEqual((kept['walks'], kept['updates'], len(phases)), (2, 4, 2))
            self.assertEqual(phases[-1][1][59][7], 2)
            bad_frames = copy.deepcopy(frames); bad_frames[631].insert(1, dict(bad_frames[631][1], pc=0xf9f6, registers=dict(bad_frames[631][1]['registers'], **{'M68K A6': g.address(59)})))
            bad_anchor = copy.deepcopy(frames); bad_anchor[630][0]['ranges'][1]['hex'] = '00000000'
            bad_reset = copy.deepcopy(frames); bad_reset[631].insert(0, dict(bad_reset[631][0], pc=0xf940))
            bad_cadence = copy.deepcopy(frames); del bad_cadence[630][2]
            for f in (bad_frames, bad_anchor, bad_reset, bad_cadence):
                with self.assertRaises(ValueError): g.continuity(f, boundaries, pair, bytes(ram))
            bad_boundary = copy.deepcopy(boundaries); bad_boundary['631']['slots']['58'] = bytes(78).hex()
            with self.assertRaises(ValueError): g.continuity(frames, bad_boundary, pair, bytes(ram))
            ram2 = bytearray(ram); ram2[0x31c3] ^= 1
            with self.assertRaises(ValueError): g.continuity(frames, boundaries, pair, bytes(ram2))
            writes = [dict(frame=630, count=1, dropped=0, events=[dict(pc=0xf778, address=g.address(58) + 12 & 0xffffff, width=1, value=0, registers={'M68K A6': g.address(58)})]),
                      dict(frame=631, count=5000, dropped=904, events=[])]
            audit = g.audit_continuity_writes(writes, pair)
            self.assertEqual((audit['complete_frames'], audit['incomplete_frames'], audit['pair_writes']), (1, [631], 1))
            for e in (dict(pc=0x1234, address=g.address(58) + 2 & 0xffffff, width=2, value=0, registers={'M68K A6': g.address(58)}),
                      dict(pc=0x1234, address=g.ANCHOR, width=4, value=0, registers={})):
                with self.assertRaises(ValueError): g.audit_continuity_writes([dict(frame=630, count=1, dropped=0, events=[e])], pair)
        finally: g.END = end

    def test_mixed_anchor_requires_retained_return_only(self):
        ram = bytearray(65536); ram[0x31c0:0x31c4] = g.address(58).to_bytes(4, 'big')
        objects = [(0,)] * 68; objects[58] = (8,); objects[59] = (5,)
        event = dict(ranges=[dict(label='anchor', hex=ram[0x31c0:0x31c4].hex())])
        self.assertEqual(validate_anchor(objects, [event], [], bytes(ram), bytes(ram)), 58)
        other = bytearray(ram); other[0x31c0:0x31c4] = g.address(59).to_bytes(4, 'big')
        for args in ((objects, [event], [], bytes(other), bytes(other)), (objects, [event], [dict(address=0xff31c2, width=2)], bytes(ram), bytes(ram)),
                     (objects, [dict(ranges=[dict(label='anchor', hex='00000000')])], [], bytes(ram), bytes(ram)), (objects, [event], [], bytes(ram), bytes(other))):
            with self.assertRaises(ValueError): validate_anchor(*args)


if __name__ == '__main__': unittest.main()
