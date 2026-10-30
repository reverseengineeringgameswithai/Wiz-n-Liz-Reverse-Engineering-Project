"""Restricted original executions of the spell's completion: the FF31C0 anchor's 7B42/7B58/7B8A handlers with 13294, 7B58's completion (D269, 7E18 and 7ED6, the 83DA lookup, recipe 8652 with 7F08 and 6F02, 95EE, 1324E), 7F08's sparkle (7F6A) and 6F02's door and sign (6FB6, 5964, 6FCA, 4C08, 4C34, 705C) with its contact path (7082, 4CA2), versus native step_spell_countdown, MixedPool::complete_spell, step_spell_sparkle, step_exit_door and step_door_sign."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from rom import ROOT, DEFAULT_ROM, inspect_file, verify_expected
from rnc import approved_directory, atomic_write
from native_build import PRESETS, verify_executable
from build_terrain_reference import verify_executable as reference_executable, REPORT
from genesis_actor_capture import save, require
from movement_probe import validate
from rnc_loader_probe import parse_disassembly
from reset_probe import word
from terrain_cases import encode_cases
from pickup_hit_compare import target
sys.path.insert(0, str(ROOT / 'tests'))
from completion_cases import anchor_corpus, completion_corpus, sparkle_corpus, door_corpus

STEP = 're/completion_step.json'
# Session 053's door entry (7082, 4CA2) extends the door variant.
STEPS = (STEP, 're/door_entry_step.json')
# Previously mapped scope the corpora execute: the walk body, F76C, the RTS
# selectors, CB72/CB9A, 1324E, F9E2, the FCB32 mismatch return, 5964, E918,
# 5A9A, F994, the FAA4 release, AC5E, session 051's 7B42 countdown, 59BC and
# the RTS closing 7126 (7082's inactive-link return).
EXECUTED = ((0x69aa, 0x69c2, 7), (0xf76c, 0xf850, 59), (0x12646, 0x12648, 1), (0xcb72, 0xcc18, 43), (0x1324e, 0x13294, 9), (0xf9e2, 0xfa1e, 14),
            (0xfcb32, 0xfcb42, 4), (0xfcb7a, 0xfcb7e, 2), (0x5964, 0x59ae, 12), (0xe918, 0xe948, 10), (0x5a9a, 0x5ae4, 13), (0xf994, 0xf9d0, 14),
            (0xfaa4, 0xfabc, 7), (0xac5e, 0xac9c, 19), (0x7b42, 0x7b4e, 3), (0x7b56, 0x7b58, 1), (0x59bc, 0x5a06, 12), (0x7152, 0x7154, 1))
# Stops: after the service; FCB32 past its selector test (the driver); 7ED6's FF31A8 path; 9288 (no recipe); 8652's 9182;
# the two-player door position (6F44); 95EE's 9682/9614; the allocators'
# exhaustion loops; a seeded callback (CAF0); the two-player door test (7072)
# and an active +1A2 link at the entry (70FE); every other recipe's effect.
STOPS = {0x69c2, 0xfcb42, 0x7ef4, 0x9288, 0x9182, 0x6f44, 0x9682, 0x9614, 0xfa1e, 0xf9d0, 0xcaf0, 0x70fe, 0x7072}
GNU = ((0x7b5e, 2, 'bnes'), (0x7e38, 4, 'divuw'), (0x7e90, 2, 'cmpw'), (0x7e92, 2, 'bnes'), (0x6f10, 2, 'cmpal'), (0x6f12, 2, 'blts'), (0x6f14, 2, 'exg'),
       (0x7f84, 2, 'bgts'), (0x95ee, 4, 'moveml'), (0x7fb4, 2, 'beqs'), (0x7b72, 2, 'movel'), (0x7e6a, 2, 'movew'), (0x7ebe, 2, 'jsr'), (0x4c38, 2, 'movew'),
       (0x7f6e, 2, 'bpls'))


def recipes(data):
    rows = []; a = 0x83da
    while data[a] != 0xff: rows.append((data[a], data[a + 1], int.from_bytes(data[a + 2:a + 6], 'big'))); a += 6
    require(a == 0x8650, 'recipe table extent differs'); return rows


def probe(data, meta, out):
    for m in meta: validate(data, m)
    rows = []; new = []; commands = []
    effects = {e for _a, _b, e in recipes(data)}; exits = STOPS | (effects - {0x8652})
    # F84E's JMP (A0) is a presentation callback (6FCA, or the seeded CAF0);
    # 69BA/69C0 the handler and service; 7EBE the matched recipe's effect.
    indirect = {0xf84e: [0x6fca, 0xcaf0], 0x69ba: [0x12646, 0x7b42, 0x7b58, 0x7b8a, 0x7f6a, 0x6fb6, 0x4c34], 0x69c0: [0x12646, 0x705c], 0x7ebe: sorted(effects)}
    for lo, hi, n, mine in [(r['start'], r['end_exclusive'], r['instruction_count'], True) for m in meta for r in m['regions']] + [(*x, False) for x in EXECUTED]:
        cmd = ['rasm2', '-a', 'm68k', '-b', '32', '-e', '-c', '68000', '-s', hex(lo), '-D', data[lo:hi].hex()]
        p = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15)
        decoded = parse_disassembly(p.stdout, data, lo, hi); require(len(decoded) == n, 'completion decoder count differs')
        rows += decoded; new += decoded if mine else []; commands.append(dict(command=cmd, stdout=p.stdout, stderr=p.stderr))
    addresses = {r['address'] for r in rows}; edges = []
    for r in rows:
        pc = r['address']; op = word(data, pc)
        if op == 0x4e75: continue
        targets = [pc + r['size']]
        if pc in indirect:
            require(op in (0x4ed0, 0x4e90, 0x4e92), 'completion indirect opcode differs')
            if op == 0x4ed0: targets = []
            targets += indirect[pc]
        else:
            t = target(data, pc)
            if t is not None:
                if op & 0xff00 == 0x6000 or op in (0x4ef9, 0x4efa): targets = []
                targets.append(t)
            else: require(not 0x4e80 <= op <= 0x4eff, 'unmodeled completion indirect transfer')
        for t in targets:
            require(t in addresses or t in exits, f'completion graph escapes declared scope at {pc:X} -> {t:X}'); edges.append([pc, t])
    for pc, n, mnemonic in GNU:
        cmd = ['rasm2', '-a', 'm68k.gnu', '-b', '32', '-e', '-c', 'm68000', '-s', hex(pc), '-D', data[pc:pc + n].hex()]
        p = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15); row, = parse_disassembly(p.stdout, data, pc, pc + n)
        require(row['assembly'].split()[0].startswith(mnemonic), 'completion GNU corroboration differs'); commands.append(dict(command=cmd, stdout=p.stdout, stderr=p.stderr))
    for d in (d for m in meta for d in m['data']): require(hashlib.sha256(data[d['start']:d['end_exclusive']]).hexdigest() == d['sha256'], 'completion data hash differs')
    save(out / 'static.json', dict(commands=commands, edges=edges, exits=sorted(exits), instructions=len(addresses), gnu_checks=len(GNU), recipes=len(effects),
         limitation='GNU corroborates register and short forms (the waits\' BNE, DIVU.W, the recipe compares, CMPA/BLT/EXG ordering, the sparkle\'s BGT/BEQ/BPL, '
                    'MOVEM, the A6 and word stack moves, JSR (A2) and the sign table read); the absolute-address loads/stores, immediates and JSR (xxx) calls rely on the '
                    'primary decoder plus restricted execution.'))
    return addresses, {r['address'] for r in new}


def anchor_classes(row, out):
    if not row[3] & 0x80: return ['inactive']
    phase = out[0]
    if phase == 4: return ['completion_stop']
    if phase == 3: return ['revealed']
    if row[14] == 0: return ['fade_started'] if phase == 1 else ['counting']
    return ['waiting']


def completion_classes(row, out):
    if out[0] == 2:
        return [{0x7ef4: 'ff31a8_path', 0x9288: 'no_recipe_or_9288', 0x9182: 'request_9182', 0x6f44: 'two_player', 0x9682: 'gate_9682', 0x9614: 'gate_9614',
                 0xfa1e: 'exhausted', 0xcaf0: 'callback'}.get(out[1], 'other_recipe')]
    if out[0] == 0: return ['waiting']
    cleared = out[13 + 2 * 15 + 7]
    return ['completed', 'message_shown' if cleared else 'message_refused', 'p2_control' if row[11] == 0xffff0838 else 'p1_control']


def sparkle_classes(row, out):
    if out[0] == 1: return ['exhausted']
    found = ['released' if out[4] == 0 else 'counting']
    particles = out[11]
    if particles: found.append('spawned')
    if any(out[12 + 11 * k + 3] == 0x4000 for k in range(particles)): found.append('flagged')
    return found


def door_classes(row, out):
    if out[0] == 1: return [{0x70fe: 'active_link', 0x7072: 'two_player', 0xcaf0: 'callback'}[out[1]]]
    phase = out[1]; found = [('waiting', 'appearing', 'open', 'entered')[phase]]
    if phase == 3: found.append('entered_two_player' if row[26] else 'entered_camera')
    elif phase > row[13]: found.append('dressed' if phase == 2 else 'appeared')
    base = 12 if phase == 3 else 15
    if out[base]: found.append('bobbing')
    sounds = out[base + 7]
    if any(out[base + 8 + 4 * k] == 0x95 for k in range(sounds)): found.append('sound_95')
    return found


VARIANTS = {'anchor': (anchor_corpus, anchor_classes, {'inactive', 'completion_stop', 'revealed', 'fade_started', 'counting', 'waiting'}),
            'completion': (completion_corpus, completion_classes, {'ff31a8_path', 'no_recipe_or_9288', 'request_9182', 'two_player', 'gate_9682', 'gate_9614', 'exhausted',
                                                                   'other_recipe', 'waiting', 'completed', 'message_shown', 'message_refused', 'p1_control', 'p2_control'}),
            'sparkle': (sparkle_corpus, sparkle_classes, {'exhausted', 'released', 'counting', 'spawned', 'flagged'}),
            'door': (door_corpus, door_classes, {'entered', 'entered_camera', 'entered_two_player', 'active_link', 'two_player', 'callback', 'waiting', 'appearing', 'open',
                                                 'dressed', 'appeared', 'bobbing', 'sound_95'})}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--preset', choices=PRESETS, default='debug'); args = p.parse_args(argv)
    identity = inspect_file(); verify_expected(identity); meta = [json.loads((ROOT / n).read_text()) for n in STEPS]
    native = verify_executable(args.preset, 'wiznliz-collision'); reference = reference_executable()
    out = Path(tempfile.mkdtemp(prefix='run-', dir=approved_directory(ROOT, 'local/generated/completion-comparison')))
    report = dict(ok=False, preset=args.preset, scope=' '.join(m['contract'] for m in meta), rom_sha256=identity['sha256'],
        native_build=json.loads((native.parent / 'provenance.json').read_text()), reference_build=json.loads(REPORT.read_text()),
        sources={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in ('tools/completion_compare.py', 'tests/completion_cases.py', *STEPS)})
    try:
        pcs, new = probe(DEFAULT_ROM.read_bytes(), meta, out); visited = set(); report['variants'] = {}
        for name, (make, classes, want) in VARIANTS.items():
            rows = make(); data = encode_cases(rows); atomic_write(out / f'{name}.in', data)
            results = {}; processes = {}
            for kind, cmd in [('native', [str(native), '--' + name]), ('reference', [str(reference), str(DEFAULT_ROM), '--' + name])]:
                r = subprocess.run(cmd, input=data, capture_output=True, timeout=900)
                atomic_write(out / f'{name}-{kind}.stdout', r.stdout); atomic_write(out / f'{name}-{kind}.stderr', r.stderr)
                require(r.returncode == 0, f'{name} {kind} failed: ' + r.stderr.decode()[:1000])
                results[kind] = [tuple(map(int, l.split())) for l in r.stdout.splitlines()]
                require(len(results[kind]) == len(rows), f'{name} output extent differs')
                processes[kind] = dict(command=cmd, output_sha256=hashlib.sha256(r.stdout).hexdigest())
                if kind == 'reference': obs = json.loads(r.stderr)
            outcomes = Counter()
            for i, (row, a, b) in enumerate(zip(rows, results['native'], results['reference'])):
                require(a == b, f'{name} case {i}: {row} native={a} original={b}')
                outcomes.update(classes(row, b))
            require(want <= set(outcomes), f'{name} corpus lacks a class: ' + ', '.join(sorted(want - set(outcomes))))
            seen = set(obs['visited']); require(seen <= pcs, f'{name} execution escaped the declared graph'); visited |= seen
            report['variants'][name] = dict(cases=len(rows), outcomes=dict(outcomes), processes=processes, observation={k: v for k, v in obs.items() if k != 'visited'},
                                            instructions_visited=len(seen))
        require(new <= visited, 'new completion instructions not all executed: ' + ', '.join(f'{a:X}' for a in sorted(new - visited)))
        report.update(ok=True, cases=sum(v['cases'] for v in report['variants'].values()), visited_pcs=sorted(visited),
                      successful_instructions_visited=len(visited), new_instructions_visited=len(new & visited))
    except Exception as e: report['error'] = str(e)
    finally:
        verify_expected(inspect_file()); report['rom_unchanged'] = True; save(out / 'report.json', report)
    print(json.dumps({k: report.get(k) for k in ('ok', 'cases', 'new_instructions_visited', 'error')}
                     | {'outcomes': {n: v['outcomes'] for n, v in report.get('variants', {}).items()}, 'report': str(out / 'report.json')}, indent=2))
    return int(not report['ok'])


if __name__ == '__main__': raise SystemExit(main())
