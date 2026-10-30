"""The retained level world joined to the native player from its first object
loop. Fresh replays of frames [START, END) capture P1 (genesis_session_capture's
early-session evidence with the 1345A timer active: timer, banner, input
conversion and the wrapper returning at 6986) and the world (the pair capture's
walk recipe, frame boundaries and write records); the referenced setup capture
(genesis_pair_initializer: the [6886,68D4) setup and the world to 1066) supplies
the setup and must agree at START. P1 and the world are cross-checked frame by
frame; then one native wiznliz-session --world-session run builds the setup
from its entry stack and, from START, runs the level-start fade timer, P1 from
one seed and physical held sets, and every object loop consuming P1's own
tracking and position. The only other inputs are the world's E918 counts and
message-producer updates. The world's own writes of P1's state (13294 and 1324E
from the spell anchor; 7082 entering the door) are checked separately and split
P1's session evidence, which accepts P1's exit handlers from the entry on."""
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
import genesis_pair_initializer as g
from genesis_world_pool import world_rows
from terrain_cases import encode_cases

# The world's first object loop; the fade timer (FF0B90 = FFFF) runs from START
# to 668. END stops after 1532, when P1's 7126 ends the level (FF33E0 = 7).
START, END = 634, 1533
# The world's writers of P1's session state: 13294 (from 7B42) and 1324E (from
# 7B58's completion) write the transition block; 7082 (entering the door) P1's
# actor and +1A6. Native write PCs report the next PC.
WORLD_WRITERS = {'13294': (0x13294, 0x132d2), '7B58': (0x1324e, 0x13294), '7082': (0x7082, 0x710e)}
CURVE = 0x135ea
CURVES = {0x1356a: 1, 0x135aa: 2, 0x135ea: 3}
SOURCES = ('tools/genesis_world_session.py', 'tools/genesis_world_pool.py', 'tools/genesis_session_capture.py', 'tools/genesis_dispatch_capture.py',
           'tools/genesis_movie_actor_capture.py', 'tools/genesis_actions_capture.py', 'tools/genesis_pair_initializer.py', 'tools/genesis_reversal_capture.py')


def setup_evidence(path):
    """The referenced pair capture, revalidated with the current tool: its
    recipes and recorded sources must equal the current ones."""
    parent = json.loads(path.read_text())
    require(parent['recipes'] == dict(early=g.recipe(False), walk=g.recipe(True)), 'setup capture recipe differs')
    require(parent['sources'] == {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in g.SOURCES}, 'setup capture sources differ from the current tool')
    require(not parent.get('reference_report') and parent['end'] == g.END, 'setup capture is not a fresh capture')
    read = fixture_reader(parent, path.parent)
    routines, writes, boundaries, hooked, unhooked, end_ram = g.load(read)
    _pairs, _retained, _phases, _obs, prefixes, tails, messages, gated, _walks, _probes = g.validate(routines, writes, boundaries, end_ram)
    return dict(parent=parent, frames={r['frame']: r['events'] for r in routines}, boundaries=boundaries, writes=writes, runs=(prefixes[0], tails[0], messages[0], gated[0]))


def world_evidence(setup, read):
    """Expected world rows: the setup from the setup capture, every loop to END
    from this pass's world replay."""
    def lines(name): return [json.loads(l) for l in gzip.decompress(read(name)).decode().splitlines() if l]
    routines = lines('world-routines.jsonl.gz'); writes = lines('world-writes.jsonl.gz'); boundaries = json.loads(gzip.decompress(read('world-boundaries.json.gz')))
    require([w['frame'] for w in writes] == list(range(START, END)) and all(START <= r['frame'] < END for r in routines), 'world replay extent differs')
    seed, rows, world_row, phases, lines_, summary = world_rows(setup['frames'], setup['boundaries'], setup['writes'], *setup['runs'],
        loop_evidence=({r['frame']: r['events'] for r in routines}, boundaries, writes), end_frame=END)
    return dict(seed=seed, rows=rows, world_row=world_row, phases=phases, lines=lines_, summary=summary)


def p1_recipe():
    """The session recipe plus 7126's FF4446/48 (requested) and FF0732/34 (saved) positions."""
    r = sc.recipe(True)
    r['ranges'] += [dict(label='requested_position', domain='68K RAM', offset=0x4446, length=4), dict(label='saved_position', domain='68K RAM', offset=0x0732, length=4)]
    return r


def curve_codes(transition):
    """FF0B98/9C/A0 as native's curve resources (0 retained, else the known three)."""
    return tuple(CURVES.get(be(transition, i, 4), 0) for i in (8, 12, 16))


def capture(source, out, ext, inputs):
    """Fresh P1 session trace of [START, END) and an independent unhooked endpoint."""
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
    # The world replay: the pair capture's walk recipe, write records and boundaries.
    routines = []; records = []
    with WorkerClient([str(ext / 'run-worker.sh'), '--storage', str(out / 'world-worker')]) as w:
        s = ReplaySession.from_recording(w, source); check_worker(w, s, ext); require(s.opened['identity'] == identity, 'world replay identity differs')
        s.seek(START); boundaries = {str(START): g.boundary(w)}
        w.request('trace.configure', g.recipe(True)); w.request('debug.trace.configure', {'mask': 4})
        for frame in range(START, END):
            s.seek(frame + 1); t = w.request('trace.drain'); wr = w.request('debug.trace.drain')
            require(t['dropped'] == 0 and t['overflow'] is False and t['error'] is None and t['identity'] == identity and wr['identity'] == identity, f'world trace loss at {frame}')
            require(all(e['frame'] == frame for e in t['events']), 'world drain frame differs')
            if t['events']: routines.append(dict(frame=frame, events=t['events']))
            records.append(g.write_record(frame, wr)); boundaries[str(frame + 1)] = g.boundary(w)
        save(out / 'world-hooked.json', w.request('snapshot'))
    storage = (out / 'world-worker').resolve(); require(storage.parent == out.resolve(), 'unexpected worker storage'); shutil.rmtree(storage)
    for name, value in (('world-routines.jsonl.gz', routines), ('world-writes.jsonl.gz', records)):
        atomic_write(out / name, gzip.compress(('\n'.join(json.dumps(r) for r in value) + '\n').encode(), mtime=0))
    atomic_write(out / 'world-boundaries.json.gz', gzip.compress(json.dumps(boundaries).encode(), mtime=0))
    with WorkerClient([str(ext / 'run-worker.sh'), '--storage', str(out / 'unhooked-worker')]) as w:
        s = ReplaySession.from_recording(w, source); check_worker(w, s, ext); s.seek(END); save(out / 'unhooked.json', w.request('snapshot'))
    for name, value in (('trace.json.gz', dict(trace, events=events)), ('writes.json.gz', writes)):
        atomic_write(out / name, gzip.compress(json.dumps(value).encode(), mtime=0))
    save(out / 'inputs.json', inputs)
    return identity


def world_frames(world):
    """Frames whose object loop wrote P1's session state: 13294 from 7B42 and
    1324E from 7B58's completion (the timer), 7082 entering the door (P1's actor
    and tracking selector)."""
    return {c['frame']: c['cause'] for c in world['summary']['conversions'] if c['cause'] in WORLD_WRITERS}


def p1_evidence(trace, writes, inputs, terrain, frames):
    """P1's session evidence with the world's own writes of its state set aside.
    Each is checked here by its routine (13294/1324E: the transition block or
    FF0EDE; 7082: FF0836 = FFFF among its writes); the session is validated in
    segments split after them, P1's state must carry across each split exactly
    as the world wrote it, and from the entry on P1's exit handlers may restart
    the timer (13208) and end the level (FF33E0 = 7). On those frames the
    trace's events after P1's wrapper returns (6986) belong to the object loop
    and are not P1 evidence. FF0690's +3C/+3E, a world input, must have no
    writer."""
    def overlaps(e, lo, n): return e['address'] < lo + n and lo < e['address'] + e['width']
    filtered = []
    for frame, t in zip(range(START, END), writes):
        lo, hi = WORLD_WRITERS[frames[frame]] if frame in frames else (0, 0)
        mine = [e for e in t['events'] if e['type'] == 4 and lo < e['pc'] <= hi]
        if frame in frames and frames[frame] == '7082':
            require(any((e['address'], e['width'], e['value']) == (0xff0836, 2, 0xffff) for e in mine), f'door entry writes differ at {frame}')
        elif frame in frames:
            require(all(e['cpu'] == 'M68K' and (overlaps(e, 0xff0b90, 20) or overlaps(e, 0xff0ede, 2)) for e in mine) and len(mine) >= 4, f'world transition writes differ at {frame}')
        require(not any(e['type'] == 4 and overlaps(e, 0xff06cc, 4) for e in t['events']), f'FF0690 +3C/+3E written at {frame}')
        filtered.append(dict(t, events=[e for e in t['events'] if e not in mine]))
    loop_start = {}
    for e in trace['events']:
        if e['frame'] in frames and e['pc'] == 0x6986: loop_start[e['frame']] = e['sequence']
    require(sorted(loop_start) == sorted(frames), 'P1 wrapper return missing on a world frame')
    events = [e for e in trace['events'] if e['frame'] not in loop_start or e['sequence'] <= loop_start[e['frame']]]
    entry = min((f for f, c in frames.items() if c == '7082'), default=None)
    cuts = [START, *sorted(f + 1 for f in frames), END]; pairs = []; scratch = 0
    for lo, hi in zip(cuts, cuts[1:]):
        seg = dict(trace, events=[e for e in events if lo <= e['frame'] < hi])
        p, n = sc.validate_session(seg, filtered[lo - START:hi - START], inputs[lo - START:hi - START], lo, hi, terrain, True, True,
                                   exit_transition=entry is not None and lo > entry)
        if pairs:
            last, first = pairs[-1], p[0]; cause = frames[lo - 1]
            before, after = block(last['return'], 'actor'), block(first['wrapper'], 'actor')
            carried = last.get('transition_out', last['transition'])
            if cause == '7082':
                # 70D2..70F4: +4A = the control, mode 80, frame 021D, handler 710E; +1A6 = FFFF.
                want = bytearray(before); want[0] = 0x80; want[6:8] = (0x21d).to_bytes(2, 'big'); want[0x16:0x1a] = (0x710e).to_bytes(4, 'big'); want[0x4a:0x4e] = (0xffff0690).to_bytes(4, 'big')
                require(after == bytes(want) and tracking_fields(first['wrapper']) == (1, 0xffff, *tracking_fields(last['return'])[2:])
                        and first['transition_before'] == carried, f'door entry state differs at {lo}')
            else:
                words = (1, 6, 0, be(last['transition'], 6)) if cause == '13294' else (0xffff, 6, 0, 0)
                want = b''.join(v.to_bytes(2, 'big') for v in words) + CURVE.to_bytes(4, 'big') * 3
                require(after == before and tracking_fields(last['return']) == tracking_fields(first['wrapper']), f'P1 state changed across the split at {lo}')
                require(first['transition_before'] == want, f'world transition state differs at {lo}')
            require(block(last['return'], 'scratch') == block(first['banner_before'], 'scratch'), f'P1 scratch changed across the split at {lo}')
        pairs += p; scratch += n
    return pairs, scratch


def cross_check(world, pairs):
    """The two captures describe one replay: from START, every world loop's 78EE
    tracking is P1's after its wrapper, and an emitter's owner position is P1's
    actor position."""
    first = world['summary']['first_loop']; owners = 0
    for i, p in enumerate(pairs):
        row = world['phases'][START + i - first]; event = p['return']; actor = block(event, 'actor')
        require(tuple(row[:2]) == tracking_fields(event)[2:], f'world tracking differs from P1 at {START + i}')
        if row[7]: require(tuple(row[8:10]) == (be(actor, 2), be(actor, 4)), f'emitter owner differs from P1 at {START + i}'); owners += 1
    return dict(frames=len(pairs), tracking=len(pairs), owner_positions=owners)


def fade(pairs, writes):
    """The timer's dirty request (FF0EDC = FFFF) is written exactly on the frames
    whose 1345A call stepped the level or ended the fade; 13432's clears are the
    palette consumer, which is not native."""
    steps = [START + i for i, p in enumerate(pairs) if be(p['transition_before'], 0) and be(p['transition_before'], 2) == 0]
    sets, clears = [], []
    for frame, t in zip(range(START, END), writes):
        for e in t['events']:
            if e['type'] == 4 and e['address'] < 0xff0ede and 0xff0edc < e['address'] + e['width']:
                timer = sc.TIMER_CODE[0] < e['pc'] <= sc.TIMER_CODE[1]
                require((e['width'], e['value']) == (2, 0xffff) if timer else (e['pc'], e['width'], e['value']) == (0x1344c, 2, 0), 'unmodeled FF0EDC writer')
                (sets if timer else clears).append(frame)
    require(sets == steps, 'fade dirty requests differ from its level steps')
    active = [START + i for i, p in enumerate(pairs) if be(p['transition_before'], 0)]
    return dict(active_frames=[active[0], active[-1]] if active else [], level_steps=steps, consumer_clears=len(clears))


def level_rows(world, pairs, inputs):
    """The native --world-session input before the per-frame rows (seed, timer,
    setup, collision and the supplied loops), the per-frame rows and the
    retained curve pointers check_level needs."""
    first = world['summary']['first_loop']; supplied = START - first; phases = world['phases']
    seed = sc.session_seed(pairs[0]['wrapper']); before = pairs[0]['banner_before']
    seed = (*seed[:26], be(block(before, 'scratch'), 0), be(block(before, 'scratch'), 2), *seed[28:], be(block(before, 'difficulty'), 0), be(block(before, 'stage'), 0),
            before['registers']['M68K D1'] & 65535)
    configs = {(r[2], r[3], r[4], r[5], r[6]) for r in phases}; require(len(configs) == 1, 'collision configuration changes'); collision, = configs
    frames = [(sc.physical_fields(row)[0], *phase[10:]) for row, phase in zip(inputs, phases[supplied:])]
    w0 = pairs[0]['wrapper']; actions = block(w0, 'action_globals')
    timer = (*(be(pairs[0]['transition_before'], 2 * k) for k in range(4)), *curve_codes(pairs[0]['transition_before']),
             *(be(block(w0, l), i) for l in ('requested_position', 'saved_position') for i in (0, 2)), be(actions, 0), be(actions, 2), be(actions, 8))
    retained = {i: be(pairs[0]['transition_before'], 8 + 4 * i, 4) for i, c in enumerate(curve_codes(pairs[0]['transition_before'])) if not c}
    head = [seed, timer, world['seed'][0], *world['seed'][1:], *world['rows'], world['world_row'], collision, (supplied,), *phases[:supplied]]
    return head, frames, retained


def check_level(got, world, pairs, retained):
    """The level's native lines against the world's setup and loop lines, every
    P1 call, the timer after each frame's 1345A call (with its curves; a
    retained curve must keep its original pointer) and FF33E0 after the frame.
    FF0732/34 is the camera position, which non-native code rewrites every
    frame; native models only 7126's final write, compared on the frame FF33E0
    becomes 7."""
    first = world['summary']['first_loop']; supplied = START - first; lines = world['lines']
    require(len(got) == len(lines) == 1 + supplied + len(pairs), 'native world session output extent differs')
    require(got[0] == lines[0], 'native world session setup differs')
    for k in range(supplied): require(got[1 + k] == lines[1 + k], f'native supplied loop differs at {first + k}')
    for i, p in enumerate(pairs):
        r = got[1 + supplied + i]; frame = START + i; event = p['return']; n = r[39]; cut = 40 + 4 * n + 15
        require(r[0] == i + 1 and r[1:19] == snapshot_fields(event, be(block(p['wrapper'], 'actor'), 0x1a, 4)), f'native P1 differs at {frame}')
        require(r[19:23] == tracking_fields(event) and r[23:35] == sc.control_fields(event), f'native P1 tracking/input differs at {frame}')
        require(tuple(tuple(r[j:j + 4]) for j in range(40, 40 + 4 * n, 4)) == p['sounds'] and not p['samples'] and r[cut - 15:cut - 10] == p['banner_request'], f'native P1 requests differ at {frame}')
        codes = curve_codes(p['transition'])
        require(all(be(p['transition'], 8 + 4 * k, 4) == retained.get(k) for k in range(3) if not codes[k]), f'retained curve changed at {frame}')
        require(r[cut - 10:cut - 3] == (*(be(p['transition'], 2 * k) for k in range(4)), *codes), f'native fade timer differs at {frame}')
        mode = be(block(event, 'action_globals'), 8); ended = mode == 7 and be(block(p['wrapper'], 'action_globals'), 8) != 7
        require(r[cut - 1] == mode and (not ended or r[cut - 3:cut - 1] == (be(block(event, 'saved_position'), 0), be(block(event, 'saved_position'), 2))),
                f'native FF33E0 or 7126\'s saved position differs at {frame}')
        require(r[cut:] == lines[1 + supplied + i], f'native world differs at {frame}')


def compare(native, world, pairs, inputs, out, scene, bank):
    """Native --world-session (level_rows) checked by check_level."""
    for n, b in (('scene.bin', scene), ('bank.bin', bank)): atomic_write(out / n, b)
    head, frames, retained = level_rows(world, pairs, inputs)
    data = encode_cases([*head, *frames]); atomic_write(out / 'world-session.in', data)
    command = [str(native), 'movie.scene', str(out / 'scene.bin'), 'movie.bank', str(out / 'bank.bin'), '--world-session']
    proc = subprocess.run(command, input=data, capture_output=True, timeout=120); atomic_write(out / 'native.stdout', proc.stdout); atomic_write(out / 'native.stderr', proc.stderr)
    require(proc.returncode == 0, 'native world session failed: ' + proc.stderr.decode())
    got = [tuple(map(int, l.split())) for l in proc.stdout.splitlines()]
    check_level(got, world, pairs, retained)
    supplied = START - world['summary']['first_loop']
    return dict(command=command, seed_sha256=hashlib.sha256(data).hexdigest(), output_sha256=hashlib.sha256(proc.stdout).hexdigest(), outcome='matched',
                supplied_loops=supplied, p1_calls=len(pairs), world_loops=len(world['lines']) - 1, held_rows=len(frames), p1_sounds=sum(len(p['sounds']) for p in pairs))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('recording', type=Path); p.add_argument('--world-report', type=Path, required=True)
    p.add_argument('--preset', choices=PRESETS, default='debug'); p.add_argument('--fixture', type=Path); args = p.parse_args(argv)
    ext = ROOT.parent / 'BizHawkOpenSource/Tools/GenesisDebug'; sys.path.insert(0, str(ext / 'python'))
    from genesis_debug.replay import load_recording
    source = load_recording(args.recording); rom = inspect_file(); verify_expected(rom); native = verify_executable(args.preset, 'wiznliz-session')
    require(source['rom']['sha256'] == rom['sha256'] and source['input_sha256'] == INPUT_SHA256 and len(source['inputs']) == 5298 and not source['experimental_edits'] and not source['instrumentation'], 'world session recording differs')
    require(source['start']['imported_movie']['source']['sha256'] == MOVIE_SHA256, 'world session movie identity differs')
    out = Path(tempfile.mkdtemp(prefix='run-', dir=approved_directory(ROOT, 'local/generated/world-session')))
    inputs = source['inputs'][START:END]
    report = dict(ok=False, preset=args.preset, start=START, end=END, recipe=sc.recipe(True), sources={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in SOURCES},
        movie_sha256=MOVIE_SHA256, input_sha256=INPUT_SHA256, recording_sha256=hashlib.sha256(args.recording.read_bytes()).hexdigest(),
        native_build=json.loads((native.parent / 'provenance.json').read_text()), world_report=str(args.world_report), world_report_sha256=hashlib.sha256(args.world_report.read_bytes()).hexdigest(),
        classification='fresh native comparison of captured ordinary movie' if args.fixture else f'fresh ordinary unchanged movie frames {START}..{END}; no edits; owned workers',
        scope='The setup capture\'s [6886,68D4) setup and every object loop 634..1532 (this pass\'s world replay) with the native player joined from the first loop: the level-start fade timer (1345A, FF0B90..FF0B97), P1 from one seed and physical held sets, every loop consuming P1\'s tracking and position, the second delivery and ingredient, the spell countdown and 7CC8, the spell\'s completion (13294, 7B58 with recipe 8652, 1324E, 7B8A, the sparkle, the door and sign), P1 entering the door (705C\'s 7082 with 4CA2, handing P1 to 710E) and P1\'s exit fade (710E, 13208, 7126) to the level\'s end (FF33E0 = 7 at 1532). Per-frame inputs besides held buttons: E918 calls by non-pool code (counts) and message-producer updates. The next scene, the fade\'s palette consumers, renderer, audio and whole-machine parity are outside scope.')
    try:
        setup = setup_evidence(args.world_report)
        require(setup['parent']['recording_sha256'] == report['recording_sha256'] and setup['parent']['identity'] == source['start']['worker_open']['identity'], 'setup capture recording/identity differs')
        if args.fixture:
            parent = json.loads(args.fixture.read_text())
            require(parent['recipe'] == report['recipe'] and parent['sources'] == report['sources'] and parent['recording_sha256'] == report['recording_sha256'], 'world session fixture contract changed')
            read = fixture_reader(parent, args.fixture.parent); report['identity'] = parent['identity']
            report['reference_report'] = str(args.fixture); report['reference_report_sha256'] = hashlib.sha256(args.fixture.read_bytes()).hexdigest()
        else:
            report['identity'] = capture(source, out, ext, inputs); read = lambda name: (out / name).read_bytes()
        trace = json.loads(gzip.decompress(read('trace.json.gz'))); writes = json.loads(gzip.decompress(read('writes.json.gz')))
        require(json.loads(read('inputs.json')) == inputs, 'world session input rows differ')
        hooked, unhooked, whooked = (json.loads(read(n)) for n in ('hooked.json', 'unhooked.json', 'world-hooked.json'))
        require(all(s['identity'] == report['identity'] and s['frame'] == END and not s['experimentalEdits'] for s in (hooked, unhooked, whooked)), 'world session endpoint provenance differs')
        require(hooked['canonicalSha256'] == unhooked['canonicalSha256'] == whooked['canonicalSha256'], 'session and world replay endpoints differ')
        report['endpoint'] = dict(hooked=hooked['canonicalSha256'], unhooked=unhooked['canonicalSha256'], world=whooked['canonicalSha256'], scope=hooked['hashScope'])
        world = world_evidence(setup, read)
        scene, bank, terrain = terrain_fixture(read('before.ram')); require(terrain_fixture(read('after.ram'))[:2] == (scene, bank), 'terrain endpoints differ')
        pairs, scratch = p1_evidence(trace, writes, inputs, terrain, world_frames(world))
        report['observation'] = dict(p1_calls=len(pairs), scratch_writes=scratch, world=world['summary'] | dict(external_random_calls=len(world['summary']['external_random_calls']),
                                     external_message_updates=len(world['summary']['external_message_updates'])), cross_check=cross_check(world, pairs), fade=fade(pairs, writes))
        report['comparison'] = compare(native, world, pairs, inputs, out, scene, bank)
        report['ok'] = True
    except Exception as e: report['error'] = str(e)
    finally:
        verify_expected(inspect_file()); report['rom_unchanged'] = True
        report['artifacts'] = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.is_file()}; save(out / 'report.json', report)
    print(json.dumps({k: report.get(k) for k in ('ok', 'observation', 'comparison', 'error')} | {'report': str(out / 'report.json')}, indent=2, default=str))
    return int(not report['ok'])


if __name__ == '__main__': raise SystemExit(main())
