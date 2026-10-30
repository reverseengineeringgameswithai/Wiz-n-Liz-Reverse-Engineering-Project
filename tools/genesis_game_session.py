"""The first level and the scene after it as one native run. Fresh replays
capture the level (genesis_world_session: P1 and the world over [634, 1533)),
the scene change (every call 0x42A..5EDC returns to, with the state the native
session carries, and the RAM at every frame boundary of [1532, 1563)) and the
hub (genesis_hub_session: [1562, 1759)). Across the scene change the carried
state may change only inside the routines enter_hub_scene reconstructs. One
native wiznliz-session --game-session run then builds the level's setup, runs
its 899 loops, applies the scene change (P1 is not reseeded: 9880 rebuilds its
actor at the level's FF4446/48), switches to the hub's terrain and runs the
hub's 196 loops; the level's and the hub's lines are checked as their own tools
check them, and the scene change's line against the hub's first P1 call, its
timer, banner request and 60E6's pool.

After the hub a fourth replay captures the change into the second level
(every return of 0x4A4, the hint screen 1959E, E2A and 754's head with the
state the native session carries, E918's draws by caller, and the RAM at
every frame boundary of [1758, 2107)) and a fifth P1 in the second level's
loop from 2107. The native run continues: the hint screen's loops on the
carried timer, the second level's entry (enter_second_level), then P1 alone on
the second level's terrain. P1's evidence holds through SECOND_END - 1: from
SECOND_END the level's objects query the terrain through the scratch P1's
session owns, and the capture must reject that frame."""
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
from genesis_movie_actor_capture import snapshot_fields, MOVIE_SHA256, INPUT_SHA256
from genesis_dispatch_capture import tracking_fields
import genesis_session_capture as sc
import genesis_world_session as ws
import genesis_hub_session as hs
from terrain_cases import encode_cases

# The scene change: from the level's last loop (6A92 returns at 1532) to the
# hub's first (1563).
SCENE_START, SCENE_END = ws.END - 1, hs.START
# Every return in the scene change's call sequence, in order (0x42A..0x49E the
# top-level loop, 16ED0..16F12 inside 16EA4, F854..F85E inside F850, 98AE/98DC
# inside 9880, then 5D30's own), with 1345A to show the timer stays still.
CALLS = (0x6a92, 0x42a, 0x470, 0x476, 0x488, 0x49e, 0x5d30, 0x16ed0, 0x16ed6, 0x16edc, 0x16ee2, 0x16ee8, 0x16eee, 0xf854, 0xf858, 0xf85e, 0x16ef2,
         0x16ef8, 0x16efe, 0x16f12, 0x5d36, 0x98ae, 0x98dc, 0x5d4e, 0x5d54, 0x5d58, 0x5d6a, 0x5d74, 0x5d7e, 0x5d94, 0x5d9a, 0x5da4, 0x5db2, 0x5dc4,
         0x5dca, 0x5de4, 0x5e30, 0x5e36, 0x5e42, 0x5e52, 0x5e62, 0x5e72, 0x5e80, 0x5e8a, 0x5e8e, 0x5e9e, 0x5ea8, 0x5eba, 0x5ed4, 0x5edc)
TIMER_PCS = (0x1345a, 0x134b0, 0x134d4, 0xebf2)
BANNER_PCS = (0x63e2, 0x17532, 0x175d0)
# The carried state, by name: P1's actor; FF0690's +A2/+A4 (the anchor 9880
# reads), +42/+44 and +1A6 (tracking), +5A..+6D (parameters); the terrain
# scratch, FF4446/48, the timer, FF0EDE, the action globals and FF0F16.
CARRIED = dict(actor=(0x1ab4, 78), anchor=(0x0732, 4), tracking=(0x06d2, 4), selector=(0x0836, 2), parameters=(0x06ea, 20), scratch=(0x4442, 4),
               requested=(0x4446, 4), timer=(0x0b90, 20), scope=(0x0ede, 2), globals=(0x33d8, 4), mode=(0x33e0, 2), gate=(0x0f16, 2))
# Which carried state each call interval may change (by its closing return).
ALLOWED = {0x49e: {'anchor'}, 0x16ee8: {'actor'}, 0x16eee: {'actor'}, 0xf854: {'actor'}, 0xf858: {'actor'}, 0x5d36: {'timer', 'scope', 'gate'},
           0x98ae: {'actor', 'selector', 'parameters'}, 0x5e9e: {'scratch'}, 0x5edc: {'timer'}}
POOL = (0x1b50, 0x3120 - 0x1b50)
# Frames whose boundary-to-boundary pool may change: 17024 and 170E2 (1535),
# F850 (1536) and 60E6 (1562).
POOL_FRAMES = (1535, 1536, 1562)
LABELS = (0x647c, 0x64e8, 0x6497, 0x6503, 0x64b2, 0x651e, 0x64cd, 0x6539)
SOURCES = ('tools/genesis_game_session.py', *ws.SOURCES, 'tools/genesis_hub_session.py')
# After the hub: from its last loop (603E returns in 1758) to P1's first call in
# the second level's loop (0x792) at SECOND_START. From SECOND_END 2512's ten
# objects (slots 58..67) query the terrain through FF4442/44.
AFTER_START, SECOND_START, SECOND_END = hs.END - 1, 2107, 2136
# Every return the change's native counterpart follows, in order: 0x4A4..0x4C4,
# 1959E (its 16EA4 returns at 195B0, FF0F10 = 00F0 before 19668), E2A (16EA4,
# 9880 on both controls), 754's head (118C: 54BA, [11A6,11EE), 9952 at
# [1356,1364), the rest), 0x774/0x77C and 14A4's return (0x780). The loops'
# tops (19676, 0x792) wait for the frame and are not traced.
AFTER_CALLS = (0x603e, 0x4a4, 0x4a8, 0x4ac, 0x4c4, 0x1959e, 0x195b0, 0x19668, 0x4ca, 0xe30, 0xe8a, 0x98ae, 0x98dc, 0xe90, 0x4ce, 0x4ea, 0x770,
               0x1192, 0x11a6, 0x11ee, 0x1356, 0x1364, 0x1384, 0x774, 0x77c, 0x780)
# The hint loop: its test (19718), the paths after the pad (1972E, 1974A,
# 19756) and its return (19764); a loop's end shows at the next frame's 1345A.
HINT_PCS = (0x19718, 0x1972e, 0x1974a, 0x19756, 0x19764)
AFTER_CARRIED = dict(actor=(0x1ab4, 78), tracking=(0x06d2, 4), selector=(0x0836, 2), parameters=(0x06ea, 20), saved=(0x0732, 4), scratch=(0x4442, 4),
                     requested=(0x4446, 4), timer=(0x0b90, 20), scope=(0x0ede, 2), actions=(0x33d8, 4), mode=(0x33e0, 2), gate=(0x0f16, 2), hint=(0x0f0e, 4),
                     random=(0x0bac, 8), range=(0x3402, 2))
# Which carried state each interval may change, by its closing event: 1959E's
# and E2A's 16EA4 (the actor zeroed, the fade-in, FF0F0E cleared), FF0F10 =
# 00F0, the hint loop's body (its countdown shows at the next frame's 1345A)
# and 13208, E2A's +A2/+A4, 9880 on P1, 118C's +1A6 (119A), FF33D8 (and its
# draw), 9952, FF33E0; a draw of E918 shows at the event after it; 1345A's
# own steps.
AFTER_ALLOWED = {0x195b0: {'actor', 'timer', 'scope', 'gate', 'hint'}, 0x19668: {'hint'}, 0x1345a: {'hint'}, 0x1974a: {'hint'}, 0x19756: {'hint', 'timer', 'scope'},
                 0xe30: {'actor', 'timer', 'scope', 'gate', 'hint'}, 0xe8a: {'saved'}, 0x98ae: {'actor', 'selector', 'parameters'}, 0x1192: {'random'},
                 0x11a6: {'selector'}, 0x11ee: {'actions', 'random'}, 0x1356: {'random'}, 0x1364: {'actor', 'parameters'}, 0x77c: {'mode'}, 0xe918: {'random'},
                 0x134b0: {'timer'}, 0x134d4: {'timer'}}


def scene_recipe():
    return dict(pcs=[*CALLS, *TIMER_PCS, *BANNER_PCS], registers=True, returns=False, maxEvents=20000,
                ranges=[dict(label=k, domain='68K RAM', offset=o, length=n) for k, (o, n) in CARRIED.items()])


def scene_capture(source, out, ext):
    """The scene change's call returns with the carried state, and the RAM at
    every frame boundary, with an independent unhooked endpoint at SCENE_END."""
    sys.path.insert(0, str(ext / 'python'))
    from genesis_debug import WorkerClient, ReplaySession
    events = []; boundaries = {}
    with WorkerClient([str(ext / 'run-worker.sh'), '--storage', str(out / 'scene-worker')]) as w:
        s = ReplaySession.from_recording(w, source); identity = s.opened['identity']; check_worker(w, s, ext)
        s.seek(SCENE_START); boundaries[str(SCENE_START)] = w.read_bytes('68K RAM', 0, 65536).hex()
        w.request('trace.configure', scene_recipe())
        for frame in range(SCENE_START, SCENE_END):
            s.seek(frame + 1); t = w.request('trace.drain')
            require(t['identity'] == identity and t['dropped'] == 0 and t['overflow'] is False and t['error'] is None, f'scene trace loss at {frame}')
            require(all(e['frame'] == frame for e in t['events']), 'scene drain frame differs'); events.extend(t['events'])
            boundaries[str(frame + 1)] = w.read_bytes('68K RAM', 0, 65536).hex()
        save(out / 'scene-hooked.json', w.request('snapshot'))
    storage = (out / 'scene-worker').resolve(); require(storage.parent == out.resolve(), 'unexpected worker storage'); shutil.rmtree(storage)
    with WorkerClient([str(ext / 'run-worker.sh'), '--storage', str(out / 'scene-unhooked-worker')]) as w:
        s = ReplaySession.from_recording(w, source); check_worker(w, s, ext); s.seek(SCENE_END); save(out / 'scene-unhooked.json', w.request('snapshot'))
    for name, value in (('scene-events.json.gz', events), ('scene-boundaries.json.gz', boundaries)):
        atomic_write(out / name, gzip.compress(json.dumps(value).encode(), mtime=0))
    return identity


def after_recipe():
    return dict(pcs=[*AFTER_CALLS, *HINT_PCS, *TIMER_PCS, 0xe918], registers=True, returns=False, maxEvents=20000,
                ranges=[dict(label=k, domain='68K RAM', offset=o, length=n) for k, (o, n) in AFTER_CARRIED.items()]
                + [dict(label='stack', domain='68K RAM', register='M68K A7', offset=0, length=4)])


def second_recipe():
    """P1's session recipe outside the early window, with FF4446/48 and FF0732/34."""
    r = sc.recipe(False)
    r['ranges'] += [dict(label='requested_position', domain='68K RAM', offset=0x4446, length=4), dict(label='saved_position', domain='68K RAM', offset=0x0732, length=4)]
    return r


def after_capture(source, out, ext):
    """The change's returns with the carried state and the RAM at every frame
    boundary of [AFTER_START, SECOND_START], with an independent unhooked endpoint."""
    sys.path.insert(0, str(ext / 'python'))
    from genesis_debug import WorkerClient, ReplaySession
    events = []; boundaries = {}
    with WorkerClient([str(ext / 'run-worker.sh'), '--storage', str(out / 'after-worker')]) as w:
        s = ReplaySession.from_recording(w, source); identity = s.opened['identity']; check_worker(w, s, ext)
        s.seek(AFTER_START); boundaries[str(AFTER_START)] = w.read_bytes('68K RAM', 0, 65536).hex()
        w.request('trace.configure', after_recipe())
        for frame in range(AFTER_START, SECOND_START):
            s.seek(frame + 1); t = w.request('trace.drain')
            require(t['identity'] == identity and t['dropped'] == 0 and t['overflow'] is False and t['error'] is None, f'after trace loss at {frame}')
            require(all(e['frame'] == frame for e in t['events']), 'after drain frame differs'); events.extend(t['events'])
            boundaries[str(frame + 1)] = w.read_bytes('68K RAM', 0, 65536).hex()
        save(out / 'after-hooked.json', w.request('snapshot'))
    storage = (out / 'after-worker').resolve(); require(storage.parent == out.resolve(), 'unexpected worker storage'); shutil.rmtree(storage)
    with WorkerClient([str(ext / 'run-worker.sh'), '--storage', str(out / 'after-unhooked-worker')]) as w:
        s = ReplaySession.from_recording(w, source); check_worker(w, s, ext); s.seek(SECOND_START); save(out / 'after-unhooked.json', w.request('snapshot'))
    storage = (out / 'after-unhooked-worker').resolve(); require(storage.parent == out.resolve(), 'unexpected worker storage'); shutil.rmtree(storage)
    for name, value in (('after-events.json.gz', events), ('after-boundaries.json.gz', boundaries)):
        atomic_write(out / name, gzip.compress(json.dumps(value).encode(), mtime=0))
    return identity


def second_capture(source, out, ext):
    """P1's trace and native writes over [SECOND_START, SECOND_END + 1) (the last
    frame is the one that must reject), with an independent unhooked endpoint."""
    sys.path.insert(0, str(ext / 'python'))
    from genesis_debug import WorkerClient, ReplaySession
    events = []; writes = []
    with WorkerClient([str(ext / 'run-worker.sh'), '--storage', str(out / 'second-worker')]) as w:
        s = ReplaySession.from_recording(w, source); identity = s.opened['identity']; check_worker(w, s, ext)
        s.seek(SECOND_START); atomic_write(out / 'before.ram', w.read_bytes('68K RAM', 0, 65536))
        w.request('trace.configure', second_recipe()); w.request('debug.trace.configure', {'mask': 4 | 65536})
        for frame in range(SECOND_START, SECOND_END + 1):
            s.seek(frame + 1); t = w.request('debug.trace.drain'); require(t['identity'] == identity, 'write trace identity differs'); writes.append(t)
            trace = w.request('trace.drain')
            require(trace['identity'] == identity and trace['dropped'] == 0 and trace['overflow'] is False and trace['error'] is None, 'incomplete routine trace')
            require(all(e['frame'] == frame for e in trace['events']), 'routine drain frame differs'); events.extend(trace['events'])
        save(out / 'second-hooked.json', w.request('snapshot')); atomic_write(out / 'after.ram', w.read_bytes('68K RAM', 0, 65536))
    storage = (out / 'second-worker').resolve(); require(storage.parent == out.resolve(), 'unexpected worker storage'); shutil.rmtree(storage)
    with WorkerClient([str(ext / 'run-worker.sh'), '--storage', str(out / 'second-unhooked-worker')]) as w:
        s = ReplaySession.from_recording(w, source); check_worker(w, s, ext); s.seek(SECOND_END + 1); save(out / 'second-unhooked.json', w.request('snapshot'))
    storage = (out / 'second-unhooked-worker').resolve(); require(storage.parent == out.resolve(), 'unexpected worker storage'); shutil.rmtree(storage)
    for name, value in (('trace.json.gz', dict(trace, events=events)), ('writes.json.gz', writes)):
        atomic_write(out / name, gzip.compress(json.dumps(value).encode(), mtime=0))
    return identity


def capture(source, out, ext):
    for name in ('level', 'hub', 'scene', 'after', 'second'): (out / name).mkdir()
    identity = ws.capture(source, out / 'level', ext, source['inputs'][ws.START:ws.END])
    require(hs.capture(source, out / 'hub', ext) == identity and scene_capture(source, out / 'scene', ext) == identity, 'game session identities differ')
    require(after_capture(source, out / 'after', ext) == identity and second_capture(source, out / 'second', ext) == identity, 'game session identities differ')
    return identity


def nested_reader(parent, directory):
    """fixture_reader for artifacts in the run's level/hub/scene directories."""
    require(parent['ok'] is True and parent['rom_unchanged'] is True, 'reference capture did not pass')
    root = directory.resolve()
    for name, digest in parent['artifacts'].items():
        path = (directory / name).resolve()
        require(path.is_relative_to(root) and hashlib.sha256(path.read_bytes()).hexdigest() == digest, 'fixture artifact changed')
    def read(name):
        require(name in parent['artifacts'], 'unhashed fixture input: ' + name)
        return (directory / name).read_bytes()
    return read


def range_of(e, label): return bytes.fromhex(next(r['hex'] for r in e['ranges'] if r['label'] == label))


def scene_evidence(read):
    """The scene change: its call sequence, the timer still, every change of
    the carried state inside an allowed interval, the pool changing only in
    POOL_FRAMES and reset as reset_object_pool makes it, and the inputs and
    expectations of the native scene change."""
    events = json.loads(gzip.decompress(read('scene-events.json.gz'))); bs = json.loads(gzip.decompress(read('scene-boundaries.json.gz')))
    require(sorted(map(int, bs)) == list(range(SCENE_START, SCENE_END + 1)), 'scene boundary extent differs')
    calls = [e for e in events if e['pc'] in CALLS]
    require([e['pc'] for e in calls] == list(CALLS) and calls[0]['frame'] == SCENE_START, 'scene call sequence differs')
    timers = [e for e in events if e['pc'] in TIMER_PCS]
    require(all(e['sequence'] < calls[0]['sequence'] for e in timers), 'the timer runs during the scene change')
    changes = {}
    for a, b in zip(calls, calls[1:]):
        changed = {k for k in CARRIED if range_of(a, k) != range_of(b, k)}
        require(changed <= ALLOWED.get(b['pc'], set()), f'carried state {sorted(changed)} changes before {b["pc"]:X}')
        if changed: changes[hex(b['pc'])] = sorted(changed)
    ram = lambda f: bytes.fromhex(bs[str(f)])
    pool = lambda f: ram(f)[POOL[0]:POOL[0] + POOL[1]]
    moved = [f for f in range(SCENE_START + 1, SCENE_END) if pool(f) != pool(f + 1)]
    require(set(moved) <= set(POOL_FRAMES), f'scene pool changes in {moved}')
    reset = pool(1537)
    for i in range(hs.SLOTS):
        o = reset[hs.STRIDE * i:hs.STRIDE * (i + 1)]
        require(be(o, 0x16, 4) == be(o, 0x46, 4) == 0x12646 and not any(o[k] for k in range(hs.STRIDE) if not 0x16 <= k < 0x1a and not 0x46 <= k < 0x4a), f'reset slot {i} differs')
    require([be(reset, 0x300c - 0x1b50 + 4 * i, 4) for i in range(hs.SLOTS)] == [0xffff1b50 + hs.STRIDE * i for i in range(hs.SLOTS)]
            and be(reset, 0x3008 - 0x1b50, 4) == 0 and be(reset, 0x311c - 0x1b50, 4) == 0xffff311c, 'reset free stack differs')
    # 0x488's anchor (FF0690's +A2/+A4 at FF0732) is FF4446/48.
    after = next(e for e in calls if e['pc'] == 0x49e); require(range_of(after, 'anchor') == range_of(after, 'requested'), '0x488 anchor differs')
    # 63E2 with D1 = 000D: its text request (17532: A0 the label, A1 the
    # destination) and an optional number request (175D0: D0, A1).
    banner = [e for e in events if e['pc'] in BANNER_PCS and e['frame'] == 1562]  # 1532's are the level's own banner.
    require([e['pc'] for e in banner] in (list(BANNER_PCS), list(BANNER_PCS[:2])) and banner[0]['frame'] == 1562 and banner[0]['registers']['M68K D1'] & 65535 == 0x0d,
            'scene banner calls differ')
    text = banner[1]; require(text['registers']['M68K A0'] in LABELS, 'scene banner label differs')
    number = (1, banner[2]['registers']['M68K D0'] & 65535, banner[2]['registers']['M68K A1'] & 65535) if len(banner) == 3 else (0, 0, 0)
    request = (LABELS.index(text['registers']['M68K A0']), text['registers']['M68K A1'] & 65535, *number)
    end = ram(SCENE_END - 1)  # 1562's boundary: what 63A4, 60E6 and 63E2 read.
    level_end = ram(SCENE_START + 1)
    inputs = dict(two_player=be(end, 0x33e2), slow=int(be(level_end, 0x06c0) != 0), stage=be(end, 0x33c4), difficulty=be(end, 0x13e2), record=be(end, 0x3398, 4),
                  table=[be(end, 0x330c + 14 * i + 2 * k) for i in range(9) for k in range(7)])
    require(not inputs['two_player'] and inputs['difficulty'] <= 3, 'scene change inputs outside native scope')
    return dict(inputs=inputs, banner=request, summary=dict(calls=len(calls), carried_changes=changes, pool_frames=moved, timer_events_before=len(timers)))


def after_evidence(read):
    """The change after the hub: its call sequence; the carried state changing
    only as AFTER_ALLOWED says from the hub's 603E on; the pool reset by E2A's
    16EA4; E918's draws by caller (54BA's before 11A6, FF33D8's in [11A6,11EE),
    the rest after); one hint loop per frame (after the frame's 1345A), with
    the timer, FF0F10 and FF0F0E after the loop and whether it returned; and the
    native change's inputs and E918's state at SECOND_START."""
    events = json.loads(gzip.decompress(read('after-events.json.gz'))); bs = json.loads(gzip.decompress(read('after-boundaries.json.gz')))
    require(sorted(map(int, bs)) == list(range(AFTER_START, SECOND_START + 1)), 'after boundary extent differs')
    calls = [e for e in events if e['pc'] in AFTER_CALLS]
    require([e['pc'] for e in calls] == list(AFTER_CALLS) and calls[0]['frame'] == AFTER_START and calls[-1]['frame'] == SECOND_START - 1, 'after call sequence differs')
    at = {e['pc']: e for e in calls}; tail = events[events.index(calls[0]):]
    changes = {}
    for a, b in zip(tail, tail[1:]):
        changed = {k for k in AFTER_CARRIED if range_of(a, k) != range_of(b, k)}
        require(changed <= AFTER_ALLOWED.get(b['pc'], set()), f'carried state {sorted(changed)} changes before {b["pc"]:X} at {b["frame"]}')
        for k in changed: changes.setdefault(hex(b['pc']), set()).add(k)
    ram = lambda f: bytes.fromhex(bs[str(f)])
    reset = ram(at[0xe30]['frame'] + 1)[POOL[0]:POOL[0] + POOL[1]]
    for i in range(hs.SLOTS):
        o = reset[hs.STRIDE * i:hs.STRIDE * (i + 1)]
        require(be(o, 0x16, 4) == be(o, 0x46, 4) == 0x12646 and not any(o[k] for k in range(hs.STRIDE) if not 0x16 <= k < 0x1a and not 0x46 <= k < 0x4a), f'E2A reset slot {i} differs')
    draws = [e for e in events if e['pc'] == 0xe918]; callers = [be(range_of(e, 'stack'), 0, 4) for e in draws]
    require(all(at[0x770]['sequence'] < e['sequence'] < at[0x780]['sequence'] for e in draws), 'E918 draws outside 118C')
    require(all((c == 0x54c0) == (e['sequence'] < at[0x11a6]['sequence']) for e, c in zip(draws, callers)), '54BA\'s draws differ')
    require(all((c == 0x11d8) == (at[0x11a6]['sequence'] < e['sequence'] < at[0x11ee]['sequence']) for e, c in zip(draws, callers)), 'FF33D8\'s draw differs')
    tests = [e for e in events if e['pc'] == 0x19718]; frames = [e['frame'] for e in tests]
    require(frames == list(range(frames[0], frames[0] + len(frames))) and at[0x19668]['sequence'] < tests[0]['sequence'] and tests[-1]['sequence'] < at[0x4ca]['sequence'],
            'hint loop cadence differs')
    hint = []
    for t in tests:
        timer, = [e for e in events if e['frame'] == t['frame'] and e['pc'] == 0xebf2 and e['sequence'] < t['sequence']]
        end = next(e for e in events if e['sequence'] > t['sequence'] and e['pc'] in (0x1345a, 0x19764))
        after = range_of(end, 'timer'); h = range_of(end, 'hint')
        hint.append((*(be(after, 2 * k) for k in range(4)), be(h, 2), int(be(h, 0) != 0), int(end['pc'] == 0x19764)))
    require([r[-1] for r in hint] == [0] * (len(hint) - 1) + [1], 'hint screen return differs')
    end = ram(SECOND_START)
    inputs = dict(hint=1, two_player=be(end, 0x33e2), slow=int(be(end, 0x06c0) != 0), range=be(range_of(at[0x11a6], 'range'), 0),
                  random_before=callers.count(0x54c0), random_after=sum(c not in (0x54c0, 0x11d8) for c in callers))
    require(not inputs['two_player'], 'second level inputs outside native scope')
    return dict(inputs=inputs, hint=hint, frames=frames, random=(be(end, 0x0bac, 4), be(end, 0x0bb0, 4)),
                summary=dict(calls=len(calls), carried_changes={k: sorted(v) for k, v in changes.items()}, hint_loops=len(hint), hint_frames=[frames[0], frames[-1]],
                             draws=dict(before=inputs['random_before'], cooldown=callers.count(0x11d8), after=inputs['random_after'])))


def second_evidence(read, inputs, terrain):
    """P1's session evidence in the second level's loop over [SECOND_START,
    SECOND_END), with the fade's input cadence; the next frame must reject
    because another object writes the terrain scratch."""
    trace = json.loads(gzip.decompress(read('trace.json.gz'))); writes = json.loads(gzip.decompress(read('writes.json.gz')))
    n = SECOND_END - SECOND_START; require(len(writes) == len(inputs) == n + 1, 'second level window extent differs')
    window = lambda end: dict(trace, events=[e for e in trace['events'] if e['frame'] < end])
    pairs, scratch = sc.validate_session(window(SECOND_END), writes[:n], inputs[:n], SECOND_START, SECOND_END, terrain, False, True)
    try: sc.validate_session(window(SECOND_END + 1), writes, inputs, SECOND_START, SECOND_END + 1, terrain, False, True); rejection = None
    except ValueError as e: rejection = str(e)
    require(rejection == 'terrain scratch has another writer', f'the second level\'s first rejection differs: {rejection}')
    return pairs, scratch, rejection


def check_second(got, pairs, first):
    """The second level's native P1 lines: every P1 call, the timer after each
    frame's 1345A, FF33D8 and FF33E0; invocations continue from `first`."""
    require(len(got) == len(pairs), 'native second level output extent differs')
    for i, p in enumerate(pairs):
        r = got[i]; frame = SECOND_START + i; event = p['return']; n = r[39]; base = 40 + 4 * n
        require(r[0] == first + i, f'native second level invocation differs at {frame}')
        require(r[1:19] == snapshot_fields(event, be(block(p['wrapper'], 'actor'), 0x1a, 4)), f'native second level P1 differs at {frame}')
        require(r[19:23] == tracking_fields(event) and r[23:35] == sc.control_fields(event), f'native second level P1 tracking/input differs at {frame}')
        require(tuple(tuple(r[j:j + 4]) for j in range(40, base, 4)) == p['sounds'] and not p['samples'], f'native second level P1 requests differ at {frame}')
        require(r[base:base + 7] == (*(be(p['transition'], 2 * k) for k in range(4)), *ws.curve_codes(p['transition'])), f'native second level timer differs at {frame}')
        g = block(event, 'action_globals'); require(r[base + 7:] == (be(g, 0), be(g, 8)), f'native second level FF33D8/FF33E0 differ at {frame}')


def compare(native, level, hub, scene, out, after=None, second=None):
    """One native --game-session run over the level's rows, the scene change
    and the hub's held sets."""
    lw, lp, linputs, lscene, lbank = level; hw, hp, hinputs, hscene, hbank = hub
    for n, b in (('level.scene', lscene), ('level.bank', lbank), ('hub.scene', hscene), ('hub.bank', hbank)): atomic_write(out / n, b)
    head, frames, retained = ws.level_rows(lw, lp, linputs)
    i = scene['inputs']
    rows = [*head, (len(frames),), *frames, (i['two_player'], i['slow'], i['stage'], i['difficulty'], i['record'], *i['table']),
            *[(sc.physical_fields(row)[0],) for row in hinputs]]
    command = [str(native), 'movie.scene', str(out / 'level.scene'), 'movie.bank', str(out / 'level.bank'), '--game-session', str(out / 'hub.scene'), str(out / 'hub.bank')]
    if after is not None:
        # After the hub: the change's row, the hint screen's held sets, then the second level's.
        sp, sinputs, sscene, sbank = second; a = after['inputs']
        for n, b in (('second.scene', sscene), ('second.bank', sbank)): atomic_write(out / n, b)
        rows += [(a['hint'], a['two_player'], a['slow'], a['range'], a['random_before'], a['random_after']), *[(sc.physical_fields(row)[0],) for row in after['hint_inputs']],
                 *[(sc.physical_fields(row)[0],) for row in sinputs]]
        command += [str(out / 'second.scene'), str(out / 'second.bank')]
    data = encode_cases(rows); atomic_write(out / 'game-session.in', data)
    proc = subprocess.run(command, input=data, capture_output=True, timeout=180); atomic_write(out / 'native.stdout', proc.stdout); atomic_write(out / 'native.stderr', proc.stderr)
    require(proc.returncode == 0, 'native game session failed: ' + proc.stderr.decode())
    got = [tuple(map(int, l.split())) for l in proc.stdout.splitlines()]
    n = len(lw['lines']); tail = 0 if after is None else len(after['hint']) + 1 + len(second[0])
    require(len(got) == n + 1 + len(hp) + tail, 'native game session output extent differs')
    ws.check_level(got[:n], lw, lp, retained)
    line = got[n]; seed = sc.session_seed(hp[0]['wrapper']); timer = hs.hub_timer(hp)
    require(line[:32] == seed, 'native scene change P1 differs from the hub\'s first call')
    require(line[32:46] == timer, 'native scene change timer differs')
    require(line[46:51] == scene['banner'], 'native scene change banner request differs')
    require(line[51:] == hs.hub_setup_line(hw), 'native scene change pool differs')
    hub_lines = got[n + 1:n + 1 + len(hp)]
    require(all(r[0] == len(lp) + k + 1 for k, r in enumerate(hub_lines)), 'native game invocation count differs')
    occupied = hs.check_hub(hub_lines, hw, hp)
    result = dict(command=command, seed_sha256=hashlib.sha256(data).hexdigest(), output_sha256=hashlib.sha256(proc.stdout).hexdigest(), outcome='matched',
                  level_p1_calls=len(lp), level_loops=n - 1, hub_p1_calls=len(hp), hub_loops=len(hp), p1_calls=len(lp) + len(hp), hub_occupied=occupied)
    if after is not None:
        sp = second[0]; k = n + 1 + len(hp); h = len(after['hint'])
        require(got[k:k + h] == after['hint'], 'native hint screen differs')
        entry = got[k + h]
        require(entry[:32] == sc.session_seed(sp[0]['wrapper']), 'native second level entry P1 differs from its first call')
        require(entry[32:46] == hs.hub_timer(sp), 'native second level entry timer differs')
        require(entry[46:] == after['random'], 'native second level entry E918 state differs')
        check_second(got[k + h + 1:], sp, len(lp) + len(hp) + 1)
        result.update(hint_loops=h, second_p1_calls=len(sp), p1_calls=len(lp) + len(hp) + len(sp))
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('recording', type=Path); p.add_argument('--world-report', type=Path, required=True)
    p.add_argument('--preset', choices=PRESETS, default='debug'); p.add_argument('--fixture', type=Path); args = p.parse_args(argv)
    ext = ROOT.parent / 'BizHawkOpenSource/Tools/GenesisDebug'; sys.path.insert(0, str(ext / 'python'))
    from genesis_debug.replay import load_recording
    source = load_recording(args.recording); rom = inspect_file(); verify_expected(rom); native = verify_executable(args.preset, 'wiznliz-session')
    require(source['rom']['sha256'] == rom['sha256'] and source['input_sha256'] == INPUT_SHA256 and len(source['inputs']) == 5298 and not source['experimental_edits'] and not source['instrumentation'], 'game session recording differs')
    require(source['start']['imported_movie']['source']['sha256'] == MOVIE_SHA256, 'game session movie identity differs')
    out = Path(tempfile.mkdtemp(prefix='run-', dir=approved_directory(ROOT, 'local/generated/game-session')))
    report = dict(ok=False, preset=args.preset, level=[ws.START, ws.END], scene=[SCENE_START, SCENE_END], hub=[hs.SETUP, hs.END], after=[AFTER_START, SECOND_START],
        second=[SECOND_START, SECOND_END], recipes=dict(level=ws.p1_recipe(), hub=hs.world_recipe(), scene=scene_recipe(), after=after_recipe(), second=second_recipe()),
        sources={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in dict.fromkeys(SOURCES)}, movie_sha256=MOVIE_SHA256, input_sha256=INPUT_SHA256,
        recording_sha256=hashlib.sha256(args.recording.read_bytes()).hexdigest(), native_build=json.loads((native.parent / 'provenance.json').read_text()),
        world_report=str(args.world_report), world_report_sha256=hashlib.sha256(args.world_report.read_bytes()).hexdigest(),
        classification='fresh native comparison of captured ordinary movie' if args.fixture else f'fresh ordinary unchanged movie frames {ws.START}..{SECOND_END + 1}; no edits; owned workers',
        scope='The first level from its setup (634..1532), the scene change (1533..1562: 0x488, 16EA4\'s 17024/F850/FF0F16/131C2, 9880 on P1, FF33E0, 63A4/60E6, '
              '63E2 and 5ED4), the scene after it (1563..1758), the hint screen (1959E\'s loop on the carried timer, 1767..2067), the second level\'s entry '
              '(E2A\'s 16EA4, +A2/+A4 and 9880; 118C\'s +1A6, FF33D8 and 9952; FF33E0) and P1 alone in the second level\'s loop (2107..2135) as one native run from '
              'one P1 seed: P1 is not reseeded. Other routines (VDP, map and graphics loading, the HUD, P2\'s actor, the hint\'s text and sprite, the second '
              'level\'s objects, which query the terrain from 2136) change no state P1\'s session carries before then; renderer and audio are outside scope.')
    try:
        setup = ws.setup_evidence(args.world_report)
        require(setup['parent']['recording_sha256'] == report['recording_sha256'] and setup['parent']['identity'] == source['start']['worker_open']['identity'], 'setup capture recording/identity differs')
        if args.fixture:
            parent = json.loads(args.fixture.read_text())
            require(parent['recipes'] == report['recipes'] and parent['sources'] == report['sources'] and parent['recording_sha256'] == report['recording_sha256'], 'game session fixture contract changed')
            base = nested_reader(parent, args.fixture.parent); report['identity'] = parent['identity']
            report['reference_report'] = str(args.fixture); report['reference_report_sha256'] = hashlib.sha256(args.fixture.read_bytes()).hexdigest()
        else:
            report['identity'] = capture(source, out, ext); base = lambda name: (out / name).read_bytes()
        reader = lambda d: (lambda name: base(f'{d}/{name}'))
        lread, hread, sread, aread, pread = reader('level'), reader('hub'), reader('scene'), reader('after'), reader('second')
        endpoints = {}
        for d, names, frame in (('level', ('hooked.json', 'unhooked.json', 'world-hooked.json'), ws.END), ('hub', ('hooked.json', 'unhooked.json', 'world-hooked.json'), hs.END),
                                ('scene', ('scene-hooked.json', 'scene-unhooked.json'), SCENE_END), ('after', ('after-hooked.json', 'after-unhooked.json'), SECOND_START),
                                ('second', ('second-hooked.json', 'second-unhooked.json'), SECOND_END + 1)):
            snaps = [json.loads(reader(d)(n)) for n in names]
            require(all(s['identity'] == report['identity'] and s['frame'] == frame and not s['experimentalEdits'] for s in snaps), f'{d} endpoint provenance differs')
            require(len({s['canonicalSha256'] for s in snaps}) == 1, f'{d} hooked and unhooked endpoints differ'); endpoints[d] = snaps[0]['canonicalSha256']
        report['endpoints'] = endpoints
        linputs = source['inputs'][ws.START:ws.END]; hinputs = source['inputs'][hs.START:hs.END]
        require(json.loads(lread('inputs.json')) == linputs, 'level input rows differ')
        lw = ws.world_evidence(setup, lread); lscene, lbank, lterrain = terrain_fixture(lread('before.ram'))
        lp, _ = ws.p1_evidence(json.loads(gzip.decompress(lread('trace.json.gz'))), json.loads(gzip.decompress(lread('writes.json.gz'))), linputs, lterrain, ws.world_frames(lw))
        hw = hs.world_evidence(hread); hscene, hbank, hterrain = terrain_fixture(hread('before.ram'))
        require(terrain_fixture(hread('after.ram'))[:2] == (hscene, hbank) and terrain_fixture(lread('after.ram'))[:2] == (lscene, lbank), 'terrain endpoints differ')
        hp, _ = hs.p1_evidence(json.loads(gzip.decompress(hread('trace.json.gz'))), json.loads(gzip.decompress(hread('writes.json.gz'))), hinputs, hterrain, hw['entry'])
        scene = scene_evidence(sread)
        require(hs.hub_inputs(hw)['collision'][:2] == {(r[2], r[3]) for r in lw['phases']}.pop(), 'collision configuration changes across the scene change')
        after = after_evidence(aread); after['hint_inputs'] = [source['inputs'][f] for f in after['frames']]
        sinputs = source['inputs'][SECOND_START:SECOND_END + 1]; sscene, sbank, sterrain = terrain_fixture(pread('before.ram'))
        require(terrain_fixture(pread('after.ram'))[:2] == (sscene, sbank), 'second level terrain endpoints differ')
        sp, _, rejection = second_evidence(pread, sinputs, sterrain)
        report['observation'] = dict(level_p1_calls=len(lp), hub_p1_calls=len(hp), scene=scene['summary'] | dict(inputs={k: v for k, v in scene['inputs'].items() if k != 'table'}, banner=scene['banner']),
                                     after=after['summary'] | dict(inputs=after['inputs']), second_p1_calls=len(sp), second_rejection=dict(frame=SECOND_END, reason=rejection))
        report['comparison'] = compare(native, (lw, lp, linputs, lscene, lbank), (hw, hp, hinputs, hscene, hbank), scene, out, after, (sp, sinputs[:-1], sscene, sbank))
        report['ok'] = True
    except Exception as e: report['error'] = str(e)
    finally:
        verify_expected(inspect_file()); report['rom_unchanged'] = True
        report['artifacts'] = {str(f.relative_to(out)): hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out.rglob('*')) if f.is_file()}; save(out / 'report.json', report)
    print(json.dumps({k: report.get(k) for k in ('ok', 'observation', 'comparison', 'error')} | {'report': str(out / 'report.json')}, indent=2, default=str))
    return int(not report['ok'])


if __name__ == '__main__': raise SystemExit(main())
