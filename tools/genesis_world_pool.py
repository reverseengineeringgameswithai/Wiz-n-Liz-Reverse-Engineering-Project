"""The retained level world from the [6886,68D4) setup to frame 1066: native
wiznliz-collision --world-pool builds the whole setup from its 6886-entry stack
and then runs every object walk of the whole pool with one carried PickupWorld,
private globals and E918 state. The original trace supplies only explicit
external inputs (78EE tracking, the emitter owner's position, the count of E918
calls by code outside the pool and message-field updates by the non-native
message producer between object loops) and, derived independently of the
native output, every expected walk event and the world state after each object
loop."""
import hashlib
import subprocess
from collections import Counter
import genesis_pair_initializer as g
from genesis_actor_capture import require, block, be
from genesis_return_only_evidence import return_only_fields
from genesis_mixed_session import private_fields
from genesis_collision_evidence import collision_fields
from genesis_reversal_capture import effect_fields
from terrain_cases import encode_cases

# Logical controls: 1 is FF0690 (P1), 2 FF0838; native types are the PoolObject
# variant indices.
LINKS = {0: 0, 0xffff0690: 1, 0xffff0838: 2}
REVERSAL, PARTICLE, EMITTER, PRIVATE, TABLE, PROBE, RETURN_ONLY, PICKUP, COPY, SPELL, SPARKLE, DOOR, SIGN = 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15
CODES = {0xffffffff: 0, 0xd28c: 1, 0xd2a2: 2, 0xd20e: 3, 0xd22f: 4, 0xd269: 5}
# E918's own RAM writers (next PCs) and its range; 79B6's tail (the [7A46,7A58)
# FF31BC writer fragment) and 7CC8's countdown are the world's FF31BC/FF31BE writers.
RANDOM_CODE, INGREDIENT_TAIL, PRODUCER = (0xe918, 0xe948), (0x7a46, 0x7a58), (0x7cc8, 0x7cea)
# The bytes 7CC8 exchanges between the two table objects.
EXCHANGED = (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 0x10, 0x11, 0x2e, 0x2f, 0x30, 0x31, 0x32, 0x33, 0x36, 0x37)
PARTICLE_RETURN = 0x5aa0
# P1's reversal effects: F994 called from A818/A9DE with A6 = the P1 actor.
P1_ACTOR, REVERSAL_CALLERS = 0xffff1ab4, (0xa81c, 0xa9e2)
# The anchor's handlers by phase (7B42, 7B58, 7B8A); the door's handler and
# service by phase (6FB6 waiting, the 5964 puff, 705C open).
SPELL_HANDLERS = (0x7b42, 0x7b58, 0x7b8a)
DOOR_PHASES = {(0x6fb6, 0x12646): 0, (0x12646, 0x12646): 1, (0x12646, 0x705c): 2}


def control(v):
    require(v in LINKS, 'unmapped world control identity'); return LINKS[v]


def common(b): return (be(b, 2), be(b, 4), be(b, 0x12), b[0], be(b, 6), be(b, 8), be(b, 10), b[12], b[13], be(b, 14), be(b, 16))


def world_fields(kind, b):
    """The native print order of a world object of `kind` from original bytes."""
    # effect_fields requires +22 = FFFF1AB4, the session's logical owner 1.
    if kind == REVERSAL: return (*effect_fields(b)[1:], 1)
    if kind == PARTICLE:
        # 5A9A particles keep the 5AE2 RTS handler; the 59AE sparkle F9E2's 12646.
        require(be(b, 0x16, 4) in (0x5ae2, 0x12646) and be(b, 0x1a, 4) == 0xfaa4 and be(b, 0x46, 4) == 0x12646 and be(b, 0x14) == 0, 'unmodeled particle bytes')
        return common(b)[:10]
    if kind == EMITTER:
        k, f = g.link_state(b); require(k == 1, 'emitter is not a carrying 6D8C link'); return (*f[:22], control(f[22]), *f[23:])
    if kind == PRIVATE: return private_fields(b)
    if kind == TABLE: f = g.table_state(b, live=bool(b[0] & 0x80)); return (*f[:11], control(f[11]), *f[12:])
    if kind == PROBE: return collision_fields(b)
    if kind == RETURN_ONLY:
        if b[0] & 0x80: return return_only_fields(b)
        # A dormant object is never walked: residue a delivery left (5964's
        # callback, history, record) is unread until 6D22's FB06 overwrites it.
        require(be(b, 0x16, 4) == be(b, 0x46, 4) == 0x12646 and b[1] == 0 and be(b, 0x14) == 0, 'unmodeled dormant object bytes')
        return (*common(b), control(be(b, 0x4a, 4)))
    if kind == PICKUP: f = g.pickup_state(b); return (*f[:11], control(f[11]), *f[12:])
    if kind == COPY: f = g.delivered_state(b); return (*f[:11], control(f[11]), *f[12:])
    if kind == SPELL:
        require(be(b, 0x16, 4) in SPELL_HANDLERS and be(b, 0x46, 4) == 0x12646 and b[1] == 0 and be(b, 0x14) == 0, 'unmodeled spell anchor bytes')
        return (*common(b), control(be(b, 0x4a, 4)), SPELL_HANDLERS.index(be(b, 0x16, 4)))
    # F9E2's objects keep +08..+0E from the previous occupant until written; a
    # mode-80 object never reads them, so they print as zero (as native holds them).
    if kind == SPARKLE:
        require(be(b, 0x16, 4) == 0x7f6a and be(b, 0x46, 4) == 0x12646 and be(b, 0x14) == 0, 'unmodeled sparkle bytes')
        return (be(b, 2), be(b, 4), be(b, 0x12), b[0], be(b, 6), 0, 0, 0, 0, 0, be(b, 0x10), be(b, 0x1e), be(b, 0x20))
    if kind == DOOR:
        phase = DOOR_PHASES.get((be(b, 0x16, 4), be(b, 0x46, 4)))
        require(phase is not None and be(b, 0x14) == 0 and (phase != 1 or be(b, 0x1a, 4) == 0x6fca), 'unmodeled door bytes')
        frames = (be(b, 8), be(b, 10), b[12], b[13], be(b, 14)) if phase else (0, 0, 0, 0, 0)
        return (phase, be(b, 2), be(b, 4), be(b, 0x12), b[0], be(b, 6), *frames, be(b, 0x10), *((be(b, 0x1e), be(b, 0x20)) if phase == 2 else (0, 0)),
                control(be(b, 0x4a, 4)), g.slot(be(b, 0x36, 4)))
    if kind == SIGN:
        handler = be(b, 0x16, 4); cursor = be(b, 0x22, 4)
        require(handler in (0x12646, 0x4c34) and be(b, 0x46, 4) == 0x12646 and be(b, 0x14) == 0 and (handler != 0x4c34 or (0x4c52 <= cursor < 0x4c6e and not cursor & 1)), 'unmodeled sign bytes')
        return (int(handler == 0x4c34), be(b, 2), be(b, 4), be(b, 0x12), b[0], be(b, 6), (cursor - 0x4c52) // 2 if handler == 0x4c34 else 0)
    raise AssertionError(f'unexpected world kind {kind}')


def mark(es, pc, sp):
    found = [e for e in es if e['pc'] == pc and e['registers']['M68K A7'] == sp]; require(len(found) == 1, f'setup mark {pc:X} differs'); return found[0]


def message_fields(m):
    require(be(m, 0, 4) in CODES, 'unmapped control message'); return (CODES[be(m, 0, 4)], m[0x53 - 0x46], be(m, 0x56 - 0x46))


def collision_context(e):
    return (block(e, 'tracking'), block(e, 'collision_mask'), block(e, 'multiplayer'), block(e, 'tracking2'))


class World:
    """The original's world as the trace shows it: each slot's object kind
    (None when free) and allocation generation, followed through the walks."""

    def __init__(self):
        self.kinds = {}; self.generations = Counter()

    def ref(self, address):
        """(present, slot, generation) of an object identity; 0 is none."""
        if not address: return (0, 0, 0)
        s = g.slot(address); require(self.kinds.get(s) is not None, 'identity names a free slot'); return (1, s, self.generations[s])

    def born(self, s, kind):
        require(self.kinds.get(s) is None, 'allocation of an occupied slot'); self.kinds[s] = kind; self.generations[s] += 1


def setup_rows(frames, prefix, tail, message, gated, world):
    """The seed rows (header without the phase count), the table, 7DB8 and gated
    rows, the setup members as (slot, kind, final bytes) and the 68D4 mark."""
    require(tail['free_before'] == prefix['free_before'][:-len(prefix['slots'])] and gated['free_before'] == tail['free_before'][:-len(tail['slots'])], 'setup pops are not consecutive')
    require(prefix['frame'] == tail['frame'] == message['frame'] == gated['frame'] == gated['return_frame'], 'setup spans frames')
    require(gated['a5'] in LINKS and not any(gated['gates']) and message['inputs']['code_before'] is not None, 'unsupported setup inputs')
    runs = [*prefix['runs'], *tail['runs']]; free = prefix['free_before']
    inherited = {a['slot']: g.residue_row(bytes.fromhex(a['residue'])) for run in runs for a in run['members']}
    seed = [(g.SLOTS, len(free)), tuple(free), *(inherited.get(i, (0,) if i in free else (1,)) for i in range(g.SLOTS))]
    t = tail['runs'][0]['tables']; x = message['inputs']
    rows = [(*t['kinds'], *t['counts'], *(v for xy in t['positions'] for v in xy)),
            (x['two_player'], x['returned'], x['pair_request'], x['tilemap'], x['code_before'], x['priority'], x['row']),
            (*gated['gates'], 0, 0, 0, LINKS[gated['a5']])]
    members = []
    for run in runs:
        v = g.VARIANTS[run['variant']]
        for k, (a, final) in enumerate(zip(run['members'], run['finals'])):
            kind = PICKUP if v.get('custom') == 'pickups' else v['kinds'][k]; world.born(a['slot'], kind); members.append((a['slot'], kind, bytes.fromhex(final)))
    end = mark(frames[gated['frame']], g.GATED[-1], gated['sp'])
    return seed, rows, members, end


def world_state(world, end, links, messages, timer, globals_, sounds, clears):
    """Expected print_world_state fields from the original after an object loop."""
    records = []
    for obj, entry in g.record_entries(block(end, 'records')):
        records += (*world.ref(obj), entry) if obj else (0, 0, 0, 0)
    out = (len(free := g.free_fields(block(end, 'free'))), *free, *globals_['random'], *records, *world.ref(be(block(end, globals_['activation']), 0, 4)))
    for k in (0, 1): out += world.ref(be(block(end, f'link{k}'), 0, 4))
    for k in (0, 1): out += world.ref(be(block(end, 'dormant'), 4 * k, 4))
    out += (*world.ref(be(block(end, 'anchor'), 0, 4)), *world.ref(globals_['spell']), *world.ref(globals_.get('door', 0)))
    for m in messages: out += m
    out += (timer, *globals_['private'], *globals_['loop'], *globals_['completion'], *globals_.get('exit', (0, 0, 0, 0)), len(sounds), *(w for q in sounds for w in q), len(clears), *clears)
    for s, b in links: out += (world.kinds[s], *world_fields(world.kinds[s], b))
    return out


def world_rows(frames, boundaries, writes, prefix, tail, message, gated, loop_evidence=None, end_frame=None, sound_label='mailbox'):
    """Every --world-pool input row and expected output line, plus a summary.
    The world's phases are the object loops after the setup frame, to
    `end_frame` (the setup capture's end by default). `loop_evidence`, a later
    capture's (frames, boundaries, writes) of the same replay, may supply the
    loops; it must agree with the setup capture at the first loop. Pool bytes
    change only inside walks and through 7CC8's exchange; between loops only
    the message producer and E918 calls by code outside the pool otherwise
    change world state, both explicit inputs."""
    world = World(); seed, rows, members, end = setup_rows(frames, prefix, tail, message, gated, world)
    setup = prefix['frame']; last = end_frame or g.END
    lframes, lboundaries, lwrites = loop_evidence or (frames, boundaries, writes)
    walks = {f: w for f in range(setup + 1, last) if (w := g.walk_windows(f, lframes.get(f, [])))}; loops = sorted(walks)
    require(loops and loops == list(range(loops[0], last)), 'object loop cadence differs')
    first = [e for e in lframes[loops[0]] if e['pc'] == 0x69a4][0]
    # Pool bytes may not change between the setup and the first object loop.
    finals = {s: b for s, _k, b in members}
    for f in range(setup + 1, loops[0] + 1):
        slots = boundaries[str(f)]['slots']
        require(all(bytes.fromhex(slots[str(s)]) == b for s, b in finals.items()), 'world changed before its first object loop')
    if loop_evidence:
        a, b = boundaries[str(loops[0])], lboundaries[str(loops[0])]
        require(all(a[k] == b[k] for k in ('slots', 'anchor', 'dormant', 'links', 'head')), 'loop capture differs from the setup capture at the first loop')
    random = (be(block(first, 'random'), 0, 4), be(block(first, 'random'), 4, 4)); gates = block(first, 'gates')
    p2 = message_fields(block(first, 'message2')); timer = be(block(first, 'ingredient'), 0x12)
    before = mark(frames[setup], g.PREFIX[0], prefix['sp'])
    origin = (be(block(first, 'origin'), 0), be(block(first, 'origin'), 2)); spell_flags = be(block(first, 'spell_flags'), 0)
    world_row = (*p2, be(block(before, 'activation'), 4, 4), be(gates, 2), be(gates, 0), timer, *random, spell_flags, *origin)
    # FF316C and FF33E2 come from the setup's 7DB8 row.
    two_player, pair_request = rows[1][0], rows[1][2]
    kinds = tuple(tail['runs'][0]['tables']['kinds'])
    # Setup line: identities, 7DB8, mask, state at 68D4 and the members.
    ids = [s for run in [*prefix['runs'], *tail['runs']] for s in (a['slot'] for a in run['members'])]
    p1 = message_fields(block(end, 'message'))
    # 7DB8's row clear is printed with its selection, not as a world request.
    require(not message['shown'] or message['vram'] is not None, 'setup row clear not reported')
    link_slots = [g.slot(be(block(end, f'link{k}'), 0, 4)) for k in (0, 1)]
    state = world_state(world, end, [(s, finals[s]) for s in link_slots], (p1, p2), timer,
                        dict(random=random, activation='activation', spell=be(block(end, 'activation'), 4, 4),
                             private=(int(bool(be(block(end, 'activation'), 4, 4))), be(gates, 2), be(gates, 0)), loop=(0, 0),
                             completion=(pair_request, spell_flags, 0, 0, 0)), [], [])
    lines = [(*(x for s in ids for x in (s, 1)), message['selected'], int(message['shown']), message['vram'] or 0, 0, *state,
              *(x for s, kind, b in members for x in (kind, *world_fields(kind, b))))]
    phases = []; carried = [p1, p2]; loop = None; summary = Counter(); external = []; spawns = Counter(); conversions = []; pending = 0; foreign = []
    identities = (0, 0); exchanges = []; recipe = (0, 0, 0); door = 0; completion = None; exit_state = (0, 0, 0, 0)
    for frame in loops:
        # Slots a walk changes before (early) or after (touched) their own walk.
        es = lframes[frame]; windows = walks[frame]; early = set(); touched = set(); exchanged = None
        # 7CC8 runs before the loop: with FF31AC and FF31B0 set (as the previous
        # loop left them) it exchanges the two table objects when the FF31AC
        # object's +32 is non-negative and the FF31B0 object is lower, or
        # negative and higher.
        if all(identities):
            a0, a1 = (g.slot(v) for v in identities); b0 = bytes.fromhex(lboundaries[str(frame)]['slots'][str(a0)])
            if (a1 > a0) if be(b0, 0x32) & 0x8000 else (a1 < a0): early |= {a0, a1}; exchanged = (a0, a1); exchanges.append(frame)
        require([g.slot(b['registers']['M68K A6']) for b, _d, _w in windows] == list(range(g.SLOTS)), f'object loop order differs at {frame}')
        start = [e for e in es if e['pc'] == 0x69a4][0]; stop = [e for e in es if e['pc'] == 0x69ce][0]
        loop_events = [e for e in es if start['sequence'] < e['sequence'] < stop['sequence']]
        require(all(collision_context(e) == collision_context(start) for e in loop_events if e['pc'] == 0x69aa), f'78EE inputs change inside the loop at {frame}')
        require(tuple(be(block(start, 'kinds'), 2 * k) for k in range(16)) == kinds and block(start, 'gates') == gates, f'FF312C kinds or private gates changed at {frame}')
        require((be(block(start, 'origin'), 0), be(block(start, 'origin'), 2)) == origin and be(block(start, 'multiplayer'), 0) == two_player, f'FF0690 +3C/+3E or FF33E2 changed at {frame}')
        require(be(block(start, 'door_state'), 0) == pair_request and be(block(start, 'spell_flags'), 0) == spell_flags, f'FF316C or FF31A8 changed outside the completion at {frame}')
        row = list(g.collision_inputs(start)); owner = None; events = []
        # P1's wrapper, before the loop, pops the shared stack for its reversal
        # effects (printed first, as native spawns them); each enters its walk as born.
        p1_calls = [e for e in es if e['sequence'] < start['sequence'] and e['registers']['M68K A6'] == P1_ACTOR and e['pc'] in (0xf994, 0xf9a8)]
        require(all(be(block(e, 'stack'), 0, 4) in REVERSAL_CALLERS for e in p1_calls if e['pc'] == 0xf994), f'P1 allocation caller differs at {frame}')
        p1_births = [g.slot(e['registers']['M68K A5']) for e in p1_calls if e['pc'] == 0xf9a8]
        require(2 * len(p1_births) == len(p1_calls), f'P1 allocation differs at {frame}')
        for j in p1_births:
            world.born(j, REVERSAL); early.add(j); spawns[REVERSAL] += 1
            events.append((0, j, world.generations[j], REVERSAL, *world_fields(REVERSAL, block(windows[j][0], 'object'))))
        # Explicit producer updates: a control's fields at loop entry differ from
        # what the previous loop (or the setup) left.
        updates = []
        for k, label in enumerate(('message', 'message2')):
            now = message_fields(block(start, label))
            if now != carried[k]: updates += [1, *now]; external.append(dict(frame=frame, control=k, before=carried[k], after=now))
            else: updates += [0, 0, 0, 0]
        for s, (begin, done, window) in enumerate(windows):
            b0, b1 = block(begin, 'object'), block(done, 'object'); kind = world.kinds.get(s)
            if kind is None:
                require(not b0[0] & 0x80 and b0 == b1, f'free slot {s} walked at {frame}'); continue
            if not b0[0] & 0x80:
                # 7ED6 leaves both ingredients as inactive table objects, never walked.
                require(kind in (RETURN_ONLY, TABLE) and b0 == b1 and (kind == RETURN_ONLY or completion), f'inactive slot {s} at {frame}')
                if kind == RETURN_ONLY: events.append((3, s, world.generations[s], kind, *world_fields(kind, b0)))
                continue
            births = []; mine = lambda pc: [e for e in window if e['pc'] == pc]
            if kind == EMITTER:
                require(be(block(begin, 'owner_link'), 0, 4) == 0xffff1ab4 and block(begin, 'owner') == block(done, 'owner'), f'emitter owner differs at {frame}')
                position = (be(block(begin, 'owner'), 2), be(block(begin, 'owner'), 4)); require(owner in (None, position), 'two emitter owners in one loop'); owner = position
                calls = [e for e in mine(g.PARTICLE) if e['registers']['M68K A6'] == begin['registers']['M68K A6']]
                pops = [e for e in mine(0xf994) if be(block(e, 'stack'), 0, 4) == PARTICLE_RETURN]
                require(len(calls) == len(pops) <= 1 and len(mine(0xf9a8)) == len(pops), f'emitter allocation differs at {frame}')
                for e in pops: births.append((g.slot([x for x in window if x['pc'] == 0xf9a8][0]['registers']['M68K A5']), PARTICLE))
                summary['emitter_walks'] += 1
            if kind == PICKUP and mine(g.PICKUP_HIT):
                linked, = mine(g.PICKUP_LINKED); link = g.slot(linked['registers']['M68K A4'])
                (touched if link < s else early).add(link)
                if [e for e in window if e['pc'] == 0x6d8a]:
                    require(world.kinds[link] == RETURN_ONLY, 'pickup hit converted a non-dormant link'); world.kinds[link] = EMITTER
                    conversions.append(dict(frame=frame, slot=link, cause='6D22', by=s))
                else: require(world.kinds[link] == EMITTER and [e for e in window if e['pc'] == 0x6cd8], 'pickup exchange differs')
                summary['pickup_hits'] += 1
            if kind == PROBE and mine(g.PROBE_DONE):
                sparkle, = mine(g.PROBE_SPARKLE); finished, = mine(g.PROBE_DONE); link = g.slot(finished['registers']['M68K A6'])
                births += [(g.slot(sparkle['registers']['M68K A6']), PARTICLE), (g.slot(finished['registers']['M68K A4']), COPY)]
                require(world.kinds[link] == EMITTER, 'delivery from a non-emitter link'); world.kinds[link] = RETURN_ONLY; (touched if link < s else early).add(link)
                conversions.append(dict(frame=frame, slot=link, cause='7910', by=s)); summary['deliveries'] += 1
            if kind == PROBE and mine(g.HIT): summary['probe_hits'] += 1
            if kind == SPARKLE:
                # 7F6A's 5A9A pops through F994 like an emitter's particle.
                pops = [e for e in mine(0xf994) if be(block(e, 'stack'), 0, 4) == PARTICLE_RETURN]
                require(len(pops) == len(mine(0xf9a8)) <= 1, f'sparkle allocation differs at {frame}')
                for e in mine(0xf9a8): births.append((g.slot(e['registers']['M68K A5']), PARTICLE))
                summary['sparkle_walks'] += 1
            entered = kind == DOOR and be(b0, 0x46, 4) == 0x705c and b1[0] == 0x85 and be(b1, 0x46, 4) == 0x12646
            if kind == DOOR and be(b0, 0x46, 4) != be(b1, 0x46, 4) and not entered:
                # 6FCA ran: its 4C08 raised the +36 sign (a lower slot, walked already).
                sign = g.slot(be(b1, 0x36, 4)); require(world.kinds.get(sign) == SIGN and sign < s, 'door sign differs')
                touched.add(sign); summary['doors_opened'] += 1
            after = kind
            if entered:
                # 7082: 4CA2's FAA4 releases the +3A sign (printed first, as native
                # releases it in the door's walk), 59BC makes the door a vanishing
                # particle; FF0F00 and (single player) the camera words follow.
                sign = g.slot(be(b0, 0x3a, 4)); require(world.kinds.get(sign) == SIGN, 'door sign differs')
                require([e for e in mine(0xfaa4) if e['registers']['M68K A6'] == g.address(sign)], 'door sign release differs')
                gone = bytes.fromhex(lboundaries[str(frame + 1)]['slots'][str(sign)]); require(not gone[0], 'door sign still active')
                events.append((2, sign, world.generations[sign], SIGN, *world_fields(SIGN, gone))); world.kinds[sign] = None; (touched if sign < s else early).add(sign)
                exit_control, camera = be(block(done, 'exit'), 0, 4), block(done, 'camera')
                exit_state = (control(exit_control), *((0, 0, 0) if two_player else (1, be(camera, 0), be(camera, 2))))
                after = PARTICLE; conversions.append(dict(frame=frame, slot=s, cause='7082', sign=sign)); summary['doors_entered'] += 1
            if kind == SPELL:
                h0, h1 = be(b0, 0x16, 4), be(b1, 0x16, 4)
                if (h0, h1) == (0x7b42, 0x7b58): conversions.append(dict(frame=frame, slot=s, cause='13294'))
                elif (h0, h1) == (0x7b8a, 0x12646): after = RETURN_ONLY; conversions.append(dict(frame=frame, slot=s, cause='7B92'))
                elif (h0, h1) == (0x7b58, 0x7b8a):
                    # 7B58's completion: 7E18 deactivates both ingredients, then
                    # 7F08 pops the sparkle and 6F02 two more (sign below door).
                    f0, f1 = g.free_fields(block(begin, 'free')), g.free_fields(block(done, 'free'))
                    require(len(f0) == len(f1) + 3 and f0[:len(f1)] == f1, f'completion allocation differs at {frame}')
                    sparkle, a, b = f0[-1], f0[-2], f0[-3]; sign_slot, door_slot = min(a, b), max(a, b)
                    births += [(sparkle, SPARKLE), *((j, SIGN if j == sign_slot else DOOR) for j in (a, b))]
                    ing = block(begin, 'ingredient'); done_ing = block(done, 'ingredient')
                    for v in (be(ing, 0, 4), be(ing, 4, 4)):
                        t = g.slot(v); require(world.kinds.get(t) == TABLE, 'completion ingredient is not a table object'); (touched if t < s else early).add(t)
                    require(be(block(done, 'door_state'), 2, 4) == g.address(door_slot) and not be(done_ing, 0, 4) and not be(done_ing, 4, 4), f'completion identities differ at {frame}')
                    recipe = (1, be(done_ing, 0x18), be(done_ing, 0x1a)); door = g.address(door_slot); completion = frame
                    conversions.append(dict(frame=frame, slot=s, cause='7B58', recipe=recipe[1:])); summary['completions'] += 1
                else: require(h0 == h1, f'spell anchor handler differs at {frame}')
            if kind == COPY and mine(g.DELIVERED_CALLBACK):
                copied, = [e for e in mine(0xfaa4) if e['registers']['M68K A6'] == begin['registers']['M68K A6']]; target = g.slot(copied['registers']['M68K A4'])
                require(world.kinds[target] == RETURN_ONLY, '7AD6 target is not dormant'); world.kinds[target] = TABLE; after = TABLE; loop = loop or frame
                (touched if target < s else early).add(target)
                if be(block(begin, 'ingredient'), 0, 4):
                    # The second ingredient: 7AE6 also gives the FF31C0 anchor 7B42.
                    require(not mine(0x7b22) and be(block(done, 'ingredient'), 4, 4) == g.address(target), 'second ingredient path differs')
                    anchor = g.slot(be(block(begin, 'anchor'), 0, 4)); require(world.kinds[anchor] == RETURN_ONLY, 'FF31C0 anchor is not return-only')
                    world.kinds[anchor] = SPELL; (touched if anchor < s else early).add(anchor)
                    conversions += [dict(frame=frame, slot=target, cause='7AE6', by=s), dict(frame=frame, slot=anchor, cause='7AE6 anchor', by=s)]
                else:
                    require(mine(0x7b22), 'first ingredient path differs'); conversions.append(dict(frame=frame, slot=target, cause='7B22', by=s))
                summary['ingredients'] += 1
            released = [e for e in mine(0xfaa4) if e['registers']['M68K A6'] == begin['registers']['M68K A6']]
            for j, born in births:
                # The new object as it stood at birth: at its own walk later in this
                # loop, else at the next loop's or, past the last, the final boundary.
                (touched if j < s else early).add(j)
                birth = (block(windows[j][0], 'object') if j > s else block(walks[frame + 1][j][0], 'object') if frame + 1 in walks
                         else bytes.fromhex(lboundaries[str(last)]['slots'][str(j)]))
                world.born(j, born); events.append((0, j, world.generations[j], born, *world_fields(born, birth))); spawns[born] += 1
            events.append((2 if released else 1, s, world.generations[s], after, *world_fields(after, b1)))
            world.kinds[s] = None if released else after; summary['releases'] += bool(released); summary['updates'] += 1
        # E918 inside the loop is an emitter's; calls by other code (outside the
        # pool) before the loop advance the shared state as an explicit count.
        calls = pending; pending = 0
        for e in es:
            if e['pc'] != g.RANDOM: continue
            if e['sequence'] < start['sequence']: calls += 1
            elif e['sequence'] > stop['sequence']: pending += 1
            else:
                a6 = e['registers']['M68K A6']; pooled = g.BASE <= a6 < g.LIMIT and (a6 - g.BASE) % g.STRIDE == 0
                # A sparkle never calls E918 on the walk that releases it.
                caller = world.kinds.get(g.slot(a6)) if pooled else None
                require(caller in (EMITTER, SPARKLE), f'non-emitter E918 call inside the loop at {frame}')
                summary['emitter_random_calls' if caller == EMITTER else 'sparkle_random_calls'] += 1
            if not start['sequence'] <= e['sequence'] <= stop['sequence']:
                foreign.append(dict(frame=frame, caller=f'{be(block(e, "stack"), 0, 4):X}', object=f'{e["registers"]["M68K A6"]:08X}'))
        if frame == loops[0]: calls = 0  # The world row's state is the first loop's entry state.
        row += [1, *owner] if owner else [0, 0, 0]; row += [calls, *updates]
        sounds = [tuple(be(block(e, sound_label), 2 * i) for i in range(4)) for e in loop_events if e['pc'] == g.SOUND]
        clears = [g.cb9a_vram(lwrites, frame)] if any(e['pc'] == 0xcb9a for e in loop_events) else []
        carried = [message_fields(block(stop, label)) for label in ('message', 'message2')]
        b = lboundaries[str(frame + 1)]['slots']; links = [g.slot(be(block(stop, f'link{k}'), 0, 4)) for k in (0, 1)]
        # Only walks change pool bytes: a slot enters its walk as the previous
        # frame left it and ends the frame as its walk left it, unless another
        # walk of this loop changed it before or after.
        for s, (begin, done, _window) in enumerate(windows):
            require(s in early or block(begin, 'object') == bytes.fromhex(lboundaries[str(frame)]['slots'][str(s)]), f'slot {s} changed before its walk at {frame}')
            require(s in touched or bytes.fromhex(b[str(s)]) == block(done, 'object'), f'slot {s} changed after its walk at {frame}')
        if exchanged:
            # Each enters its walk as the frame began, with the exchanged bytes from the other.
            pair = [bytes.fromhex(lboundaries[str(frame)]['slots'][str(x)]) for x in exchanged]
            for k, x in enumerate(exchanged):
                want = bytes(pair[1 - k][i] if i in EXCHANGED else pair[k][i] for i in range(g.STRIDE))
                require(block(windows[x][0], 'object') == want, f'7CC8 exchange differs at {frame}')
        ingredient = block(stop, 'ingredient')
        private = (int(bool(be(ingredient, 4, 4))), be(block(stop, 'gates'), 2), be(block(stop, 'gates'), 0)); identities = (be(ingredient, 0, 4), be(ingredient, 4, 4))
        state = world_state(world, stop, [(s, bytes.fromhex(b[str(s)])) for s in links], carried, be(ingredient, 0x12),
                            dict(random=(be(block(stop, 'random'), 0, 4), be(block(stop, 'random'), 4, 4)), activation='ingredient', spell=be(ingredient, 4, 4), private=private, door=door,
                                 exit=exit_state,
                                 completion=(be(block(stop, 'door_state'), 0), be(block(stop, 'spell_flags'), 0), *recipe),
                                 loop=(1, be(ingredient, 0x10)) if loop else (0, 0)), sounds, clears)
        phases.append(tuple(row)); lines.append((len(events), *(x for e in events for x in e), *state))
        summary['sounds'] += len(sounds); summary['clears'] += len(clears)
        if completion == frame:
            # 7ED6 set both ingredients' FF312C entries to FFFF; 8652 set FF316C and 7E18 cleared FF31A8.
            now = tuple(be(block(stop, 'kinds'), 2 * k) for k in range(16)); changed = [k for k in range(16) if now[k] != kinds[k]]
            pair_request, spell_flags = be(block(stop, 'door_state'), 0), be(block(stop, 'spell_flags'), 0)
            require(len(changed) <= 2 and all(now[k] == 0xffff for k in changed) and pair_request == 0xffff and not spell_flags, f'completion globals differ at {frame}')
            kinds = now
    audit = audit_world_writes(lwrites, loops)
    return seed, rows, world_row, phases, lines, dict(
        loops=len(loops), first_loop=loops[0], last_loop=loops[-1], **summary, spawns={str(k): v for k, v in spawns.items()},
        owner_positions=sum(p[7] for p in phases), external_random_calls=foreign, external_message_updates=external, conversions=conversions, first_ingredient_frame=loop,
        exchanges=exchanges, write_audit=audit)


def audit_world_writes(writes, loops):
    """From the first loop, FF0BAC..FF0BB3 is written only by E918 (whose callers
    the walks attribute) and FF31BC..FF31BF only by 79B6's tail and 7CC8. Write
    events are complete only where the native buffer did not drop."""
    complete = 0; incomplete = []; counts = Counter()
    for record in writes:
        if not loops[0] <= record['frame'] <= loops[-1]: continue
        if record['dropped']: incomplete.append(record['frame']); continue
        complete += 1
        for w in record['events']:
            a, n = w['address'], w['width']
            if a < 0xff0bb4 and 0xff0bac < a + n:
                require(RANDOM_CODE[0] < w['pc'] <= RANDOM_CODE[1], 'foreign E918 state writer'); counts['random'] += 1
            if a < 0xff31c0 and 0xff31bc < a + n:
                tail = INGREDIENT_TAIL[0] < w['pc'] <= INGREDIENT_TAIL[1]
                require(tail or PRODUCER[0] < w['pc'] <= PRODUCER[1], 'foreign FF31BC/FF31BE writer'); counts['ingredient_tail' if tail else 'producer'] += 1
    return dict(complete_frames=complete, incomplete_frames=incomplete, writes=dict(counts),
                scope='Writes the trace keeps: E918 state and FF31BC..FF31BF. Pool slots, records and identities are compared walk by walk.')


def compare_world(native, frames, boundaries, writes, prefix, tail, message, gated):
    """One native --world-pool run against every expected line."""
    seed, rows, world_row, phases, lines, summary = world_rows(frames, boundaries, writes, prefix, tail, message, gated)
    header = (*seed[0], len(phases))
    data = encode_cases([header, *seed[1:], *rows, world_row, *phases])
    p = subprocess.run([str(native), '--world-pool'], input=data, capture_output=True, timeout=120)
    identity = dict(command=[str(native), '--world-pool'], seed_sha256=hashlib.sha256(data).hexdigest())
    require(p.returncode == 0, 'native world pool failed: ' + p.stderr.decode())
    got = [tuple(map(int, l.split())) for l in p.stdout.splitlines()]; require(len(got) == len(lines), 'native world output extent differs')
    require(got[0] == lines[0], 'native world setup differs')
    for frame, a, b in zip(range(summary['first_loop'], g.END), got[1:], lines[1:]):
        require(a == b, f'native world differs at {frame}')
    return identity | dict(outcome='matched', output_sha256=hashlib.sha256(p.stdout).hexdigest(), phases=len(phases)) | summary
