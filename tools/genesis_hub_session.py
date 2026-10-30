"""The scene between levels (5D30) natively from its door setup to its end.
Fresh replays of the preserved movie capture the setup frame (60E6's doors at
SETUP) and every hub loop [START, END): P1 (genesis_session_capture's hub
evidence: the 1345A timer, input conversion and the wrapper returning at 5F3A)
and the world (the pool, its free stack and the hub's words at every frame
boundary, each loop's walk calls and every write). One native wiznliz-session
--hub-session run then builds the doors from the setup's records and free
stack and, from START, runs the timer, P1 from one seed and physical held sets
and every hub loop: the doors' countdowns, P1 touching door 0 (623C: 17298,
FF4446/FF4448, FF3398, the puff, the number objects released, 630A on both
controls, 13208), P1 coasting through the exit fade and 6024 ending the scene.
P1's evidence is split after the loop whose 623C wrote its state."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from rom import ROOT, inspect_file, verify_expected
from rnc import approved_directory, atomic_write
from native_build import PRESETS, verify_executable
from genesis_actor_capture import save, require, block, be, terrain_fixture
from genesis_actions_capture import check_worker
from genesis_effect_session import fixture_reader
from genesis_movie_actor_capture import snapshot_fields, MOVIE_SHA256, INPUT_SHA256
from genesis_dispatch_capture import tracking_fields
import genesis_session_capture as sc
from genesis_world_session import p1_recipe, curve_codes
from terrain_cases import encode_cases

# 60E6 builds the doors in SETUP; the hub's loops run from START until 6024
# returns (603E) in END - 1, 1758, after P1 entered door 0 at 1742.
SETUP, START, END = 1562, 1563, 1759
POOL, STRIDE, SLOTS = 0xff1b50, 78, 68
# Boundary ranges: the pool with its free stack and head; the door records and
# FF3398; FF4446..FF4449; FF33C4/FF33E0/FF33E2; both controls; both actors;
# the timer block with FF0EDE; FF13AE.
RANGES = dict(pool=(0x1b50, 0x3120 - 0x1b50), records=(0x330c, 0x3398 + 4 - 0x330c), requested=(0x4446, 4), stage=(0x33c4, 2), mode=(0x33e0, 2),
              multiplayer=(0x33e2, 2), control=(0x0690, 0x1a8), control2=(0x0838, 0x1a8), actors=(0x1ab4, 2 * STRIDE), timer=(0x0b90, 20), scope=(0x0ede, 2),
              mask=(0x13ae, 2))
# The hub's walk calls, 623C and its callees, 6024's two outcomes and 60E6.
WORLD_PCS = (0x5f3a, 0x5f6e, 0x5f74, 0x5f82, 0x603a, 0x603e, 0x60e6, 0x611e, 0x63a4, 0x623c, 0x17298, 0xfa8c, 0x630a, 0x13208)
# Writers by routine (native write PCs report the next PC: lo < pc <= hi).
SETUP_WRITERS = ((0x60e6, 0x61f6), (0x6334, 0x639a), (0x63a4, 0x63e2), (0xf9e2, 0xfa1e), (0xf994, 0xf9d0))
LOOP_WRITERS = ((0xf76c, 0xf850), (0x61f6, 0x630a), (0xfac4, 0xfae4), (0xfaa4, 0xfabc), (0xfa8c, 0xfaa4))
ENTRY_WRITERS = ((0x623c, 0x630a), (0x630a, 0x632a), (0x13208, 0x1324e), (0x17298, 0x172be), (0xfa8c, 0xfaa4))
# B0C8's sprite pass (after the loop) clears each visible object's +14, which
# the hub never sets: a zero written over zero, the only other pool writer.
RENDER_CLEAR = (0xb12a, 0x14, 2, 0)
HANDLERS = {0x12646, 0x61f6, 0x6218, 0xfac4, 0xfae2}
SOURCES = ('tools/genesis_hub_session.py', 'tools/genesis_world_session.py', 'tools/genesis_session_capture.py', 'tools/genesis_dispatch_capture.py',
           'tools/genesis_movie_actor_capture.py', 'tools/genesis_actions_capture.py')


def boundary(w):
    return {k: w.read_bytes('68K RAM', o, n).hex() for k, (o, n) in RANGES.items()}


def world_recipe():
    return dict(pcs=list(WORLD_PCS), registers=True, returns=False, maxEvents=20000,
                ranges=[dict(label='object', domain='68K RAM', register='M68K A6', offset=0, length=STRIDE)])


def capture(source, out, ext):
    """Fresh P1 trace of [START, END), a world replay of [SETUP, END) with
    boundaries, walk calls and writes, and an independent unhooked endpoint."""
    sys.path.insert(0, str(ext / 'python'))
    from genesis_debug import WorkerClient, ReplaySession
    writes = []; events = []
    with WorkerClient([str(ext / 'run-worker.sh'), '--storage', str(out / 'hooked-worker')]) as w:
        s = ReplaySession.from_recording(w, source); identity = s.opened['identity']; save(out / 'capabilities.json', check_worker(w, s, ext))
        require(identity == source['start']['worker_open']['identity'], 'session loaded identity differs')
        s.seek(START); atomic_write(out / 'before.ram', w.read_bytes('68K RAM', 0, 65536))
        w.request('trace.configure', p1_recipe()); w.request('debug.trace.configure', {'mask': 4 | 65536})
        for frame in range(START, END):
            s.seek(frame + 1); t = w.request('debug.trace.drain'); require(t['identity'] == identity, 'write trace identity differs'); writes.append(t)
            trace = w.request('trace.drain')
            require(trace['identity'] == identity and trace['dropped'] == 0 and trace['overflow'] is False and trace['error'] is None, 'incomplete routine trace')
            require(all(e['frame'] == frame for e in trace['events']), 'routine drain frame differs'); events.extend(trace['events'])
        save(out / 'hooked.json', w.request('snapshot')); atomic_write(out / 'after.ram', w.read_bytes('68K RAM', 0, 65536))
    storage = (out / 'hooked-worker').resolve(); require(storage.parent == out.resolve(), 'unexpected worker storage'); shutil.rmtree(storage)
    routines = []; records = []; boundaries = {}
    with WorkerClient([str(ext / 'run-worker.sh'), '--storage', str(out / 'world-worker')]) as w:
        s = ReplaySession.from_recording(w, source); check_worker(w, s, ext); require(s.opened['identity'] == identity, 'world replay identity differs')
        s.seek(SETUP); boundaries[str(SETUP)] = boundary(w)
        w.request('trace.configure', world_recipe()); w.request('debug.trace.configure', {'mask': 4})
        for frame in range(SETUP, END):
            s.seek(frame + 1); t = w.request('trace.drain'); wr = w.request('debug.trace.drain')
            require(t['dropped'] == 0 and t['overflow'] is False and t['error'] is None and t['identity'] == identity and wr['identity'] == identity, f'world trace loss at {frame}')
            require(wr['dropped'] == 0 and all(e['frame'] == frame for e in t['events'] + wr['events']), f'world drain differs at {frame}')
            routines.append(dict(frame=frame, events=t['events'])); records.append(dict(frame=frame, events=[e for e in wr['events'] if e['type'] == 4]))
            boundaries[str(frame + 1)] = boundary(w)
        save(out / 'world-hooked.json', w.request('snapshot'))
    storage = (out / 'world-worker').resolve(); require(storage.parent == out.resolve(), 'unexpected worker storage'); shutil.rmtree(storage)
    with WorkerClient([str(ext / 'run-worker.sh'), '--storage', str(out / 'unhooked-worker')]) as w:
        s = ReplaySession.from_recording(w, source); check_worker(w, s, ext); s.seek(END); save(out / 'unhooked.json', w.request('snapshot'))
    for name, value in (('trace.json.gz', dict(trace, events=events)), ('writes.json.gz', writes), ('world-routines.json.gz', routines),
                        ('world-writes.json.gz', records), ('world-boundaries.json.gz', boundaries)):
        atomic_write(out / name, gzip.compress(json.dumps(value).encode(), mtime=0))
    return identity


def ram(b, label): return bytes.fromhex(b[label])


def slot_of(pointer):
    pointer &= 0xffffff
    require(POOL <= pointer < POOL + STRIDE * SLOTS and (pointer - POOL) % STRIDE == 0, 'hub pointer outside pool'); return (pointer - POOL) // STRIDE


def free_stack(b):
    pool = ram(b, 'pool'); head = be(pool, 0x311c - 0x1b50, 4); depth = (head - 0xffff300c) // 4
    require(0xffff300c <= head <= 0xffff300c + 4 * SLOTS and (head - 0xffff300c) % 4 == 0 and be(pool, 0x3008 - 0x1b50, 4) == 0, 'hub free stack shape differs')
    return [slot_of(be(pool, 0x300c - 0x1b50 + 4 * i, 4)) for i in range(depth)]


# Bytes of an occupied slot the hub never writes; they stay as the reset left them (zero).
UNMODELED = (1, 0x14, 0x15, 0x24, 0x25, *range(0x2e, 0x46), *range(0x4a, 0x4e))


def pool_image(b):
    """The pool as print_hub_pool prints it, from a boundary."""
    pool = ram(b, 'pool'); free = free_stack(b); image = [len(free), *free]
    for i in range(SLOTS):
        if i in free: continue
        o = bytes(pool[STRIDE * i:STRIDE * (i + 1)])
        require(not any(o[k] for k in UNMODELED), f'unmodeled hub object bytes in slot {i}')
        require(o[0] & 0x80 and be(o, 0x16, 4) in HANDLERS and be(o, 0x46, 4) in (0x12646, 0x621a, 0x6218), f'unmodeled hub object in slot {i}')
        image += [i, o[0], be(o, 2), be(o, 4), be(o, 6), be(o, 8), be(o, 10), o[12], o[13], be(o, 14), be(o, 16), be(o, 18), be(o, 0x16, 4), be(o, 0x46, 4),
                  be(o, 0x1a, 4), be(o, 0x1e), be(o, 0x20), be(o, 0x22), be(o, 0x26, 4), be(o, 0x2a, 4)]
    return image


def records(b):
    r = ram(b, 'records'); return [be(r, 14 * i + 2 * k) for i in range(9) for k in range(7)], be(r, 0x3398 - 0x330c, 4)


def overlaps(e, lo, n): return e['address'] < lo + n and lo < e['address'] + e['width']


def within(e, ranges): return e['cpu'] == 'M68K' and any(lo < e['pc'] <= hi for lo, hi in ranges)


def world_evidence(read):
    """The setup precondition and writers, every loop's writers and calls, the
    entry and the exit, from the world replay."""
    routines = json.loads(gzip.decompress(read('world-routines.json.gz'))); writes = json.loads(gzip.decompress(read('world-writes.json.gz')))
    boundaries = json.loads(gzip.decompress(read('world-boundaries.json.gz')))
    require([r['frame'] for r in routines] == [w['frame'] for w in writes] == list(range(SETUP, END)) and sorted(map(int, boundaries)) == list(range(SETUP, END + 1)), 'world replay extent differs')
    first = boundaries[str(SETUP)]; pool = ram(first, 'pool')
    # 1535..1536's reset left every slot free and zero but its 12646 handlers.
    require(len(free_stack(first)) == SLOTS, 'hub setup pool is not empty')
    for i in range(SLOTS):
        o = pool[STRIDE * i:STRIDE * (i + 1)]
        require(be(o, 0x16, 4) == be(o, 0x46, 4) == 0x12646 and not any(o[k] for k in range(STRIDE) if not 0x16 <= k < 0x1a and not 0x46 <= k < 0x4a), f'hub setup slot {i} is not reset')
    # The controls' message fields (+46..+59) also have the message producer as a
    # writer; only 17298's entry writes are checked (below).
    world_ranges = [(POOL, 0x3120 - 0x1b50), (0xff330c, 0x90), (0xff4446, 4), (0xff0836, 2), (0xff09de, 2), (0xff1b02, STRIDE)]
    # The setup frame: only 60E6's chain (63A4 rewrites the records) writes the world.
    setup = [e for e in writes[0]['events'] if any(overlaps(e, lo, n) for lo, n in world_ranges)]
    require(all(within(e, SETUP_WRITERS) for e in setup), 'hub setup world writer differs')
    calls = routines[0]['events']; require([e['pc'] for e in calls if e['pc'] in (0x63a4, 0x60e6)] == [0x63a4, 0x60e6], 'hub setup calls differ')
    entries = []; summary = dict(walk_handlers={}, setup_writes=len(setup), loop_writes=0)
    for r, wr in zip(routines[1:], writes[1:]):
        frame = r['frame']; es = r['events']
        exits = [e['pc'] for e in es if e['pc'] in (0x603a, 0x603e)]
        require(exits == ([0x603e] if frame == END - 1 else [0x603a]), f'hub loop exit differs at {frame}')
        enters = [e for e in es if e['pc'] == 0x623c]
        for e in enters: entries.append((frame, e['registers']['M68K A5'], be(block(e, 'object'), 0x22)))
        for e in es:
            if e['pc'] in (0x5f6e, 0x5f74):
                key = hex(e['registers']['M68K A0']); summary['walk_handlers'][key] = summary['walk_handlers'].get(key, 0) + 1
        mine = [e for e in wr['events'] if any(overlaps(e, lo, n) for lo, n in world_ranges)]
        renders = [e for e in mine if POOL <= e['address'] < 0xff3008 and (e['pc'], (e['address'] - POOL) % STRIDE, e['width'], e['value']) == RENDER_CLEAR]
        mine = [e for e in mine if e not in renders]; summary['render_clears'] = summary.get('render_clears', 0) + len(renders)
        allowed = LOOP_WRITERS + (ENTRY_WRITERS if enters else ())
        for e in mine:
            require(within(e, allowed), f'hub loop world writer differs at {frame}: {e["pc"]:X} {e["address"]:X}')
            if not overlaps(e, POOL, 0x3120 - 0x1b50): require(enters, f'hub world word written outside an entry at {frame}')
        summary['loop_writes'] += len(mine)
    require(len(entries) == 1, 'hub door entries differ')
    frame, control, number = entries[0]
    require(control in (0xffff0690, 0xffff0838), 'hub entry control differs')
    # 17298 on the touching control and 630A on FF0838 (P2's, not native here).
    entry_writes = [e for e in writes[frame - SETUP]['events'] if within(e, ENTRY_WRITERS)]
    c = control & 0xffff
    cleared = {(e['address'], e['width'], e['value']) for e in entry_writes if 0x17298 < e['pc'] <= 0x172be}
    require(cleared == {(0xff0000 | c + 0x46, 4, 0xffffffff), (0xff0000 | c + 0x4e, 4, 0xffffffff), (0xff0000 | c + 0x52, 1, 0), (0xff0000 | c + 0x53, 1, 0),
                        (0xff0000 | c + 0x54, 2, 0), (0xff0000 | c + 0x56, 2, 0), (0xff0000 | c + 0x58, 2, 0)}, 'hub entry 17298 writes differ')
    after = boundaries[str(frame + 1)]; c2 = ram(after, 'control2'); a2 = ram(after, 'actors')[STRIDE:]
    require(be(c2, 0x1a6) == 0xffff and a2[0] == 0x80 and be(a2, 6) == 0x21d and be(a2, 0x16, 4) == 0x632a, 'hub entry P2 630A differs')
    summary.update(entry=dict(frame=frame, control=control, number=number), end=END - 1)
    return dict(boundaries=boundaries, entry=(frame, 0 if control == 0xffff0690 else 1, number), summary=summary)


def p1_evidence(trace, writes, inputs, terrain, entry):
    """P1's hub evidence with 623C's writes of its state set aside on the entry
    frame (630A: FF0836 = FFFF; 13208: the timer); validated in two segments,
    joined by exactly what 630A and 13208 wrote. On the entry frame the trace's
    events after P1's wrapper returns (5F3A) belong to the loop."""
    frame = entry[0]; filtered = []
    for f, t in zip(range(START, END), writes):
        mine = [e for e in t['events'] if e['type'] == 4 and within(e, ENTRY_WRITERS)] if f == frame else []
        if f == frame:
            require(any((e['address'], e['width'], e['value']) == (0xff0836, 2, 0xffff) for e in mine), 'hub entry 630A writes differ')
            require(any(overlaps(e, 0xff0b90, 20) and 0x13208 < e['pc'] <= 0x1324e for e in mine), 'hub entry 13208 writes differ')
        filtered.append(dict(t, events=[e for e in t['events'] if e not in mine]))
    cut = next(e['sequence'] for e in trace['events'] if e['frame'] == frame and e['pc'] == 0x5f3a)
    events = [e for e in trace['events'] if e['frame'] != frame or e['sequence'] <= cut]
    pairs = []; scratch = 0
    for lo, hi in ((START, frame + 1), (frame + 1, END)):
        seg = dict(trace, events=[e for e in events if lo <= e['frame'] < hi])
        p, n = sc.validate_session(seg, filtered[lo - START:hi - START], inputs[lo - START:hi - START], lo, hi, terrain, True, True, hub=True)
        if pairs:
            last, first = pairs[-1], p[0]
            before, after = block(last['return'], 'actor'), block(first['wrapper'], 'actor')
            # 630A: mode 80, frame 021D, handler 632A; +1A6 = FFFF. 13208: the exit fade.
            want = bytearray(before); want[0] = 0x80; want[6:8] = (0x21d).to_bytes(2, 'big'); want[0x16:0x1a] = (0x632a).to_bytes(4, 'big')
            require(after == bytes(want) and tracking_fields(first['wrapper']) == (1, 0xffff, *tracking_fields(last['return'])[2:]), f'hub entry P1 state differs at {lo}')
            require(first['transition_before'] == sc.EXIT_FADE, f'hub entry timer differs at {lo}')
            require(block(last['return'], 'scratch') == block(first['wrapper'], 'scratch'), f'P1 scratch changed across the split at {lo}')
        pairs += p; scratch += n
    return pairs, scratch


def hub_inputs(world):
    """The hub world's setup inputs from the SETUP boundary: FF33E2, FF33C4,
    FF3398, the records, the free stack and the collision row."""
    setup = world['boundaries'][str(SETUP)]
    table, record = records(setup); free = free_stack(setup)
    collision = (be(ram(setup, 'mask'), 0), be(ram(setup, 'multiplayer'), 0), 0, 0, 0)
    require(not collision[1], 'hub session expects one player')
    return dict(two_player=be(ram(setup, 'multiplayer'), 0), stage=be(ram(setup, 'stage'), 0), record=record, table=table, free=free, collision=collision)


def hub_timer(pairs):
    """The 14-field timer row from the first P1 call (the timer, FF4446/48, FF0732/34, FF33D8/DA/E0)."""
    w0 = pairs[0]['wrapper']; actions = block(w0, 'action_globals'); t0 = pairs[0]['transition_before']
    require(all(curve_codes(t0)), 'hub timer retains an unknown curve')
    return (*(be(t0, 2 * k) for k in range(4)), *curve_codes(t0), *(be(block(w0, l), i) for l in ('requested_position', 'saved_position') for i in (0, 2)),
            be(actions, 0), be(actions, 2), be(actions, 8))


def hub_setup_line(world):
    """The pool image and record states 60E6 leaves (the START boundary)."""
    start = world['boundaries'][str(START)]
    return (*pool_image(start), *(be(ram(start, 'records'), 14 * i + 8) for i in range(9)))


def check_hub(got, world, pairs):
    """The hub's per-loop native lines: every P1 call, the timer after each
    frame's 1345A, FF4446/FF4448, FF3398, the entry, 6024's outcome and the
    pool image after the loop. Returns the occupied-slot range."""
    bs = world['boundaries']; entry = world['entry']; occupied = []
    require(len(got) == len(pairs), 'native hub output extent differs')
    for i, p in enumerate(pairs):
        r = got[i]; frame = START + i; event = p['return']; n = r[39]; base = 40 + 4 * n
        require(r[1:19] == snapshot_fields(event, be(block(p['wrapper'], 'actor'), 0x1a, 4)), f'native P1 differs at {frame}')
        require(r[19:23] == tracking_fields(event) and r[23:35] == sc.control_fields(event), f'native P1 tracking/input differs at {frame}')
        require(tuple(tuple(r[j:j + 4]) for j in range(40, base, 4)) == p['sounds'] and not p['samples'], f'native P1 requests differ at {frame}')
        require(r[base:base + 7] == (*(be(p['transition'], 2 * k) for k in range(4)), *curve_codes(p['transition'])), f'native timer differs at {frame}')
        after = bs[str(frame + 1)]; requested = ram(after, 'requested'); _t, record = records(after)
        require(r[base + 7:base + 10] == (be(requested, 0), be(requested, 2), record), f'native FF4446/FF3398 differ at {frame}')
        k = base + 10
        if frame == entry[0]: require(r[k:k + 3] == (1, entry[1], entry[2]), f'native hub entry differs at {frame}'); k += 3
        else: require(r[k] == 0, f'native hub entry differs at {frame}'); k += 1
        require(r[k] == int(frame == END - 1), f'native hub end differs at {frame}')
        image = pool_image(after); require(r[k + 1:] == tuple(image), f'native hub pool differs at {frame}'); occupied.append(SLOTS - image[0])
    return [min(occupied), max(occupied)]


def compare(native, world, pairs, inputs, out, scene, bank):
    """Native --hub-session against the setup's pool and records (hub_setup_line)
    and every loop (check_hub)."""
    for n, b in (('scene.bin', scene), ('bank.bin', bank)): atomic_write(out / n, b)
    h = hub_inputs(world)
    hub = (h['two_player'], h['stage'], h['record'], *h['table'])
    order = (len(h['free']), *h['free'], *(i for i in range(SLOTS) if i not in h['free']))
    rows = [sc.session_seed(pairs[0]['wrapper']), hub_timer(pairs), hub, order, h['collision'], *[(sc.physical_fields(row)[0],) for row in inputs]]
    data = encode_cases(rows); atomic_write(out / 'hub-session.in', data)
    command = [str(native), 'movie.scene', str(out / 'scene.bin'), 'movie.bank', str(out / 'bank.bin'), '--hub-session']
    proc = subprocess.run(command, input=data, capture_output=True, timeout=120); atomic_write(out / 'native.stdout', proc.stdout); atomic_write(out / 'native.stderr', proc.stderr)
    require(proc.returncode == 0, 'native hub session failed: ' + proc.stderr.decode())
    got = [tuple(map(int, l.split())) for l in proc.stdout.splitlines()]
    require(len(got) == 1 + len(pairs), 'native hub session output extent differs')
    require(got[0] == hub_setup_line(world), 'native hub setup differs')
    require(all(r[0] == i + 1 for i, r in enumerate(got[1:])), 'native hub invocation count differs')
    occupied = check_hub(got[1:], world, pairs)
    start = world['boundaries'][str(START)]
    return dict(command=command, seed_sha256=hashlib.sha256(data).hexdigest(), output_sha256=hashlib.sha256(proc.stdout).hexdigest(), outcome='matched',
                p1_calls=len(pairs), hub_loops=len(pairs), held_rows=len(inputs), p1_sounds=sum(len(p['sounds']) for p in pairs), setup_objects=SLOTS - len(free_stack(start)),
                occupied=occupied, record_states=[be(ram(start, 'records'), 14 * i + 8) for i in range(9)])


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('recording', type=Path)
    p.add_argument('--preset', choices=PRESETS, default='debug'); p.add_argument('--fixture', type=Path); args = p.parse_args(argv)
    ext = ROOT.parent / 'BizHawkOpenSource/Tools/GenesisDebug'; sys.path.insert(0, str(ext / 'python'))
    from genesis_debug.replay import load_recording
    source = load_recording(args.recording); rom = inspect_file(); verify_expected(rom); native = verify_executable(args.preset, 'wiznliz-session')
    require(source['rom']['sha256'] == rom['sha256'] and source['input_sha256'] == INPUT_SHA256 and len(source['inputs']) == 5298 and not source['experimental_edits'] and not source['instrumentation'], 'hub session recording differs')
    require(source['start']['imported_movie']['source']['sha256'] == MOVIE_SHA256, 'hub session movie identity differs')
    out = Path(tempfile.mkdtemp(prefix='run-', dir=approved_directory(ROOT, 'local/generated/hub-session')))
    inputs = source['inputs'][START:END]
    report = dict(ok=False, preset=args.preset, setup=SETUP, start=START, end=END, recipe=p1_recipe(), world_recipe=world_recipe(), ranges=RANGES,
        sources={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in SOURCES}, movie_sha256=MOVIE_SHA256, input_sha256=INPUT_SHA256,
        recording_sha256=hashlib.sha256(args.recording.read_bytes()).hexdigest(), native_build=json.loads((native.parent / 'provenance.json').read_text()),
        classification='fresh native comparison of captured ordinary movie' if args.fixture else f'fresh ordinary unchanged movie frames {SETUP}..{END}; no edits; owned workers',
        scope='The scene between levels from its door setup (63A4 and 60E6 at 1562, over the reset pool) through its last loop (6024 returning at 1758): '
              'the 1345A timer, P1 from one seed and physical held sets (Up/Down reaching only its actor), the eight doors and their number objects, '
              'P1 touching door 0 (623C with 17298, FF4446/FF4448, FF3398, the puff, FA8C, 630A, 13208), P1 coasting through the exit fade and 6024. '
              'The level\'s end and the scene change before 1562 (the reset, P1\'s actor initialization, the map), the message producer, renderer, audio '
              'and the next scene are outside scope.')
    try:
        if args.fixture:
            parent = json.loads(args.fixture.read_text())
            require(parent['recipe'] == report['recipe'] and parent['world_recipe'] == report['world_recipe'] and parent['sources'] == report['sources']
                    and parent['recording_sha256'] == report['recording_sha256'], 'hub session fixture contract changed')
            read = fixture_reader(parent, args.fixture.parent); report['identity'] = parent['identity']
            report['reference_report'] = str(args.fixture); report['reference_report_sha256'] = hashlib.sha256(args.fixture.read_bytes()).hexdigest()
        else:
            report['identity'] = capture(source, out, ext); read = lambda name: (out / name).read_bytes()
        trace = json.loads(gzip.decompress(read('trace.json.gz'))); writes = json.loads(gzip.decompress(read('writes.json.gz')))
        hooked, unhooked, whooked = (json.loads(read(n)) for n in ('hooked.json', 'unhooked.json', 'world-hooked.json'))
        require(all(s['identity'] == report['identity'] and s['frame'] == END and not s['experimentalEdits'] for s in (hooked, unhooked, whooked)), 'hub session endpoint provenance differs')
        require(hooked['canonicalSha256'] == unhooked['canonicalSha256'] == whooked['canonicalSha256'], 'session and world replay endpoints differ')
        report['endpoint'] = dict(hooked=hooked['canonicalSha256'], unhooked=unhooked['canonicalSha256'], world=whooked['canonicalSha256'], scope=hooked['hashScope'])
        world = world_evidence(read)
        scene, bank, terrain = terrain_fixture(read('before.ram')); require(terrain_fixture(read('after.ram'))[:2] == (scene, bank), 'terrain endpoints differ')
        pairs, scratch = p1_evidence(trace, writes, inputs, terrain, world['entry'])
        report['observation'] = dict(p1_calls=len(pairs), scratch_writes=scratch, world=world['summary'])
        report['comparison'] = compare(native, world, pairs, inputs, out, scene, bank)
        report['ok'] = True
    except Exception as e: report['error'] = str(e)
    finally:
        verify_expected(inspect_file()); report['rom_unchanged'] = True
        report['artifacts'] = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.is_file()}; save(out / 'report.json', report)
    print(json.dumps({k: report.get(k) for k in ('ok', 'observation', 'comparison', 'error')} | {'report': str(out / 'report.json')}, indent=2, default=str))
    return int(not report['ok'])


if __name__ == '__main__': raise SystemExit(main())
