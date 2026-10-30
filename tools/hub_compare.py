"""Restricted original executions of the scene between levels: the setup's [5E86,5E8E) (63A4, then 60E6's door records through 611E, 6334, F9E2 and F994), door walks through the loop's walk body (F76C, 61F6, 621A with AC5E, 623C with 17298, FA8C, 630A and 13208, FAC4/FAE2 and the FAA4 release) and 6024's exit test, versus native update_hub_door_states, MixedPool::initialize_hub_doors, step_hub_door, MixedPool::enter_hub_door and hub_loop_ends; the scene changes into it (enter_hub_scene's pieces) and after it (the hint screen's loop test with 14E3C; the second level's entry: 16EA4's pieces, E2A's anchor clear, 9880, 118C's FF33D8 with E918, 9952 again and FF33E0)."""
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
from hub_cases import hub_doors_corpus, hub_door_corpus, hub_exit_corpus, scene_change_corpus, second_level_corpus, hint_screen_corpus

STEP = 're/hub_step.json'
# Session 055's scene change into the hub (16EA4's resets, 9880, 131C2 ...);
# session 056's hint screen and second-level entry.
STEPS = (STEP, 're/scene_change_step.json', 're/second_level_step.json')
# Previously mapped scope the corpora execute: F76C, the 12646 RTS, F9E2 and
# F994 (their exhaustion loops stop), the FAA4 release, AC5E, 630A, 13208 and
# 5964 (9952's appearance) and E918.
EXECUTED = ((0xf76c, 0xf850, 59), (0x12646, 0x12648, 1), (0xf9e2, 0xfa1e, 14), (0xf994, 0xf9d0, 14), (0xfaa4, 0xfabc, 7), (0xac5e, 0xac9c, 19),
            (0x630a, 0x632a, 6), (0x13208, 0x1324e, 9), (0x5964, 0x59ae, 12), (0xe918, 0xe948, 10))
# Stops: the setup continuing at 5E8E; after the walk's service (5F76); the
# allocators' exhaustion loops; a seeded callback (CAF0); 6024's BRA to the
# loop's top (5EEA); the scene change's fragments continuing (049E, 17004,
# 5D7E, 5EDC) and FF0F16's clear (16FBA); the second level's fragments
# continuing (E52, 11EE, 1364, 77C) and the hint loop continuing (19676).
STOPS = {0x5e8e, 0x5f76, 0xfa1e, 0xf9d0, 0xcaf0, 0x5eea, 0x49e, 0x16fba, 0x17004, 0x5d7e, 0x5edc, 0xe52, 0x11ee, 0x1364, 0x77c, 0x19676}
GNU = ((0x60f6, 2, 'beqs'), (0x6118, 4, 'dbf'), (0x6152, 2, 'bmis'), (0x638a, 4, 'addb'), (0x6388, 2, 'extw'), (0x627c, 4, 'muluw'), (0x63c4, 2, 'lsrw'),
       (0xfac8, 2, 'bpls'), (0x6030, 2, 'bnes'), (0x6038, 2, 'beqs'), (0x633a, 2, 'lea'), (0x6280, 4, 'lea'), (0x5f6e, 2, 'jsr'), (0xfa8e, 4, 'clrb'),
       (0x172a8, 4, 'clrb'), (0x11c0, 2, 'bgts'), (0x11c8, 2, 'bnes'), (0x11d0, 2, 'bras'), (0x11e4, 2, 'swap'), (0x11e6, 2, 'addqw'), (0xe4a, 4, 'clrw'),
       (0x14e40, 4, 'orb'), (0x14e48, 4, 'moveb'), (0x1973e, 2, 'beqs'), (0x19746, 4, 'bplw'), (0x19752, 4, 'jsr'), (0x19756, 4, 'braw'))


def probe(data, meta, out):
    for m in meta: validate(data, m)
    rows = []; new = []; commands = []
    # F84E's JMP (A0) is a presentation callback (the puff's FAA4, or the seeded
    # CAF0); 5F6E/5F74 the walk's handler and service.
    indirect = {0xf84e: [0xfaa4, 0xcaf0], 0x5f6e: [0x12646, 0x61f6, 0x6218, 0xfac4, 0xfae2], 0x5f74: [0x12646, 0x621a, 0x6218]}
    for lo, hi, n, mine in [(r['start'], r['end_exclusive'], r['instruction_count'], True) for m in meta for r in m['regions']] + [(*x, False) for x in EXECUTED]:
        cmd = ['rasm2', '-a', 'm68k', '-b', '32', '-e', '-c', '68000', '-s', hex(lo), '-D', data[lo:hi].hex()]
        p = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15)
        decoded = parse_disassembly(p.stdout, data, lo, hi); require(len(decoded) == n, 'hub decoder count differs')
        rows += decoded; new += decoded if mine else []; commands.append(dict(command=cmd, stdout=p.stdout, stderr=p.stderr))
    addresses = {r['address'] for r in rows}; edges = []
    for r in rows:
        pc = r['address']; op = word(data, pc)
        if op == 0x4e75: continue
        targets = [pc + r['size']]
        if pc in indirect:
            require(op in (0x4ed0, 0x4e90), 'hub indirect opcode differs')
            if op == 0x4ed0: targets = []
            targets += indirect[pc]
        else:
            t = target(data, pc)
            if t is not None:
                if op & 0xff00 == 0x6000 or op in (0x4ef9, 0x4efa): targets = []
                targets.append(t)
            else: require(not 0x4e80 <= op <= 0x4eff, 'unmodeled hub indirect transfer')
        for t in targets:
            require(t in addresses or t in STOPS, f'hub graph escapes declared scope at {pc:X} -> {t:X}'); edges.append([pc, t])
    for pc, n, mnemonic in GNU:
        cmd = ['rasm2', '-a', 'm68k.gnu', '-b', '32', '-e', '-c', 'm68000', '-s', hex(pc), '-D', data[pc:pc + n].hex()]
        p = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15); row, = parse_disassembly(p.stdout, data, pc, pc + n)
        require(row['assembly'].split()[0].startswith(mnemonic), 'hub GNU corroboration differs'); commands.append(dict(command=cmd, stdout=p.stdout, stderr=p.stderr))
    for d in (d for m in meta for d in m['data']): require(hashlib.sha256(data[d['start']:d['end_exclusive']]).hexdigest() == d['sha256'], 'hub data hash differs')
    save(out / 'static.json', dict(commands=commands, edges=edges, exits=sorted(STOPS), instructions=len(addresses), gnu_checks=len(GNU),
         limitation='GNU corroborates the short and register forms (the record loop\'s BEQ/DBF, the closed test\'s BMI, EXT.W and the PC-relative ADD.B of the '
                    'number table, MULU.W and the indexed LEA of FF3398, 63A4\'s LSR, FAC4\'s BPL, the exit test\'s BNE/BEQ, LEA (A5),A4, the walk\'s JSR (A0), '
                    'FA8C\'s and 17298\'s CLR.B; 118C\'s BGT/BNE/BRA, SWAP and ADDQ.W, E2A\'s CLR.W, 14E3C\'s OR.B/MOVE.B, the hint loop\'s BEQ/BPL/BRA and '
                    'JSR (PC)); the absolute-address loads/stores, EORI.W, ANDI.L, DIVU.W, BTST, SUBQ.W to memory and JSR (xxx) calls rely on the primary decoder plus '
                    'restricted execution.'))
    return addresses, {r['address'] for r in new}


def doors_classes(row, out):
    if out[0] == 1: return [{0xfa1e: 'exhausted_door', 0xf9d0: 'exhausted_number'}[out[1]]]
    found = ['rewrote' if out[1] == 0 and row[2] else 'kept', 'two_player' if row[0] else 'single_player']
    i = 3; kinds = Counter(); frames = set()
    for _ in range(out[2]):
        kind = out[i + 1]; kinds[kind] += 1; frames.add(out[i + 5]); i += 8 + (3 if kind < 2 else 0) + (5 if kind == 1 else 0)
    if kinds[0]: found.append('closed')
    if kinds[1]: found.append('open')
    if 0xcd in frames: found.append('lock')
    if frames & {0x217, 0x218}: found.append('partner')
    return found


def door_classes(row, out):
    if out[0] == 1: return [{0xcaf0: 'callback', 0xfac4: 'revived'}[out[1]]]
    phase = out[1]; found = [('closed', 'waiting', 'open', 'vanishing', 'puffing')[phase]]
    if phase > row[14] and phase == 2: found.append('opened')
    if phase == 4 and row[14] == 3: found.append('puffed')
    if phase >= 3 and not out[5] & 0x80: found.append('released')
    if out[19]: found.append('entered_p2' if out[20] else 'entered_p1')
    return found


def exit_classes(row, out): return ['ends' if out[0] else 'continues']


def scene_classes(row, out):
    found = ['p1_slow' if row[4] else 'p1_fast', 'p2_slow' if row[5] else 'p2_fast']
    if (row[0] + 0x114) > 0xffff or (row[1] + 0xb0) > 0xffff: found.append('wrapped')
    if row[6]: found.append('two_player_paths')
    return found


def second_classes(row, out):
    found = ['p1_slow' if row[2] else 'p1_fast']
    r = row[6]
    found.append('kept' if r < 0x8000 and r > 0x0a else 'cleared' if not r else 'drawn')
    if r >= 0x8000: found.append('negative_range')
    if row[4]: found.append('two_player_paths')
    return found


def hint_classes(row, out):
    if row[6]: return ['returned' if out[0] else 'fading_out']
    if row[0]: return ['fading']
    # 1974A ran when FF0F0E (out[9]) became FFFF.
    return ['ended_start' if not row[7] & 0x80 else 'expired' if out[9] == 0xffff else 'counting']


VARIANTS = {'hub-doors': (hub_doors_corpus, doors_classes, {'exhausted_door', 'exhausted_number', 'rewrote', 'kept', 'two_player', 'single_player', 'closed', 'open', 'lock', 'partner'}),
            'hub-door': (hub_door_corpus, door_classes, {'callback', 'revived', 'closed', 'waiting', 'open', 'vanishing', 'puffing', 'opened', 'puffed', 'released',
                                                        'entered_p1', 'entered_p2'}),
            'hub-exit': (hub_exit_corpus, exit_classes, {'ends', 'continues'}),
            'scene-change': (scene_change_corpus, scene_classes, {'p1_slow', 'p1_fast', 'p2_slow', 'p2_fast', 'wrapped', 'two_player_paths'}),
            'second-level': (second_level_corpus, second_classes, {'p1_slow', 'p1_fast', 'kept', 'cleared', 'drawn', 'negative_range', 'two_player_paths'}),
            'hint-screen': (hint_screen_corpus, hint_classes, {'returned', 'fading_out', 'fading', 'ended_start', 'expired', 'counting'})}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--preset', choices=PRESETS, default='debug'); args = p.parse_args(argv)
    identity = inspect_file(); verify_expected(identity); meta = [json.loads((ROOT / n).read_text()) for n in STEPS]
    native = verify_executable(args.preset, 'wiznliz-collision'); reference = reference_executable()
    out = Path(tempfile.mkdtemp(prefix='run-', dir=approved_directory(ROOT, 'local/generated/hub-comparison')))
    report = dict(ok=False, preset=args.preset, scope=' '.join(m['contract'] for m in meta), rom_sha256=identity['sha256'],
        native_build=json.loads((native.parent / 'provenance.json').read_text()), reference_build=json.loads(REPORT.read_text()),
        sources={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in ('tools/hub_compare.py', 'tests/hub_cases.py', *STEPS)})
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
        require(new <= visited, 'new hub instructions not all executed: ' + ', '.join(f'{a:X}' for a in sorted(new - visited)))
        report.update(ok=True, cases=sum(v['cases'] for v in report['variants'].values()), visited_pcs=sorted(visited),
                      successful_instructions_visited=len(visited), new_instructions_visited=len(new & visited))
    except Exception as e: report['error'] = str(e)
    finally:
        verify_expected(inspect_file()); report['rom_unchanged'] = True; save(out / 'report.json', report)
    print(json.dumps({k: report.get(k) for k in ('ok', 'cases', 'new_instructions_visited', 'error')}
                     | {'outcomes': {n: v['outcomes'] for n, v in report.get('variants', {}).items()}, 'report': str(out / 'report.json')}, indent=2))
    return int(not report['ok'])


if __name__ == '__main__': raise SystemExit(main())
