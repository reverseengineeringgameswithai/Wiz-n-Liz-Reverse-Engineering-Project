"""Restricted original executions of callback79B6's second-ingredient path with 7AD6's FF31B8/FF31B0/FF31C0 path and the per-frame 7CC8 producer, versus native MixedPool::walk_delivered and MixedPool::mix_spell. The FF31C0 anchor's 7B42 corpus moved to tools/completion_compare.py (session 052)."""
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
from spell_cases import second_corpus, mix_corpus

STEP = 're/spell_step.json'
# 7B42's regions run in tools/completion_compare.py's anchor corpus, which now
# continues through 13294.
MOVED = {0x7b42, 0x7b56}
# Previously mapped scope the corpora execute: the walk body, F76C, the RTS
# selectors, 79B6's shared prefix, 6BB2, CB72/CB9A, 7AD6's gate, FB06, the FAA4
# release and 7A88.
EXECUTED = ((0x69aa, 0x69c2, 7), (0xf76c, 0xf850, 59), (0x12646, 0x12648, 1), (0x79b6, 0x7a00, 14), (0x6bb2, 0x6bd6, 8), (0xcb72, 0xcc18, 43),
            (0x7ad6, 0x7ae6, 3), (0xfb06, 0xfb1a, 8), (0xfaa4, 0xfabc, 7), (0x7a88, 0x7ad6, 19))
# Stops: after the service; 13294 (the spell's completion) and the 7B4E store
# after it; the first-ingredient paths (7A26 at 79FE, 7B22 at 7AE2) need FF31AC zero.
EXITS = {0x69c2, 0x13294, 0x7b4e, 0x7a26, 0x7b22}
# F84E's JMP (A0) reaches 79B6; 69BA/69C0 the handler (RTS, 7A88 once called
# back, or the anchor's 7B42) and service.
INDIRECT = {0xf84e: [0x79b6], 0x69ba: [0x12646, 0x7a88, 0x7b42], 0x69c0: [0x12646]}
GNU = ((0x7a12, 2, 'negw'), (0x7a24, 2, 'rts'), (0x7afc, 2, 'movel'), (0x7b04, 2, 'movel'), (0x7b1e, 2, 'moveal'), (0x7b42, 4, 'subqw'), (0x7b46, 2, 'bpls'),
       (0x7d10, 2, 'cmpal'), (0x7d12, 2, 'bhis'), (0x7d18, 2, 'bcss'), (0x7d1c, 4, 'movew'), (0x7db6, 2, 'rts'))


def probe(data, meta, out):
    validate(data, meta); rows = []; new = []; commands = []
    for lo, hi, n, mine in [(r['start'], r['end_exclusive'], r['instruction_count'], not r.get('previously_classified')) for r in meta['regions']] + [(*x, False) for x in EXECUTED]:
        cmd = ['rasm2', '-a', 'm68k', '-b', '32', '-e', '-c', '68000', '-s', hex(lo), '-D', data[lo:hi].hex()]
        p = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15)
        decoded = parse_disassembly(p.stdout, data, lo, hi); require(len(decoded) == n, 'spell decoder count differs')
        rows += decoded; new += decoded if mine and lo not in MOVED else []; commands.append(dict(command=cmd, stdout=p.stdout, stderr=p.stderr))
    addresses = {r['address'] for r in rows}; edges = []
    for r in rows:
        pc = r['address']; op = word(data, pc)
        if op == 0x4e75: continue
        targets = [pc + r['size']]
        if pc in INDIRECT:
            require(op in (0x4ed0, 0x4e90), 'spell indirect opcode differs')
            if op == 0x4ed0: targets = []
            targets += INDIRECT[pc]
        else:
            t = target(data, pc)
            if t is not None:
                if op & 0xff00 == 0x6000 or op in (0x4ef9, 0x4efa): targets = []
                targets.append(t)
            else: require(not 0x4e80 <= op <= 0x4eff, 'unmodeled spell indirect transfer')
        for t in targets:
            require(t in addresses or t in EXITS, f'spell graph escapes declared scope at {pc:X} -> {t:X}'); edges.append([pc, t])
    for pc, n, mnemonic in GNU:
        cmd = ['rasm2', '-a', 'm68k.gnu', '-b', '32', '-e', '-c', 'm68000', '-s', hex(pc), '-D', data[pc:pc + n].hex()]
        p = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15); row, = parse_disassembly(p.stdout, data, pc, pc + n)
        require(row['assembly'].split()[0].startswith(mnemonic), 'spell GNU corroboration differs'); commands.append(dict(command=cmd, stdout=p.stdout, stderr=p.stderr))
    save(out / 'static.json', dict(commands=commands, edges=edges, exits=sorted(EXITS), instructions=len(addresses), gnu_checks=len(GNU),
         limitation='GNU corroborates register and short forms (the NEG.W, RTSs, the record and stack moves, the SUBQ.W/BPL countdown, CMPA/BHI/BCS and a register swap move); the absolute-address loads/stores, immediates and JSR (xxx).L calls rely on the primary decoder plus restricted execution.'))
    return addresses, {r['address'] for r in new}


def second_classes(row, out):
    if not out[1]: return ['not_called']
    found = ['second_ingredient', 'p2_control' if row[11] == 0xffff0838 else 'p1_control']
    cleared = out[3 + 15 + 15 + 12 + 7]
    found.append('message_shown' if cleared else 'message_refused')
    found.append('negative_drift' if out[3 + 15 + 13] & 0x8000 else 'non_negative_drift')
    return found


def mix_classes(row, out):
    found = ['spell' if row[0] else 'no_spell']
    if row[0]: found.append('reload' if row[2] == 0 else 'countdown')
    exchanged = row[0] and row[1] and out[2:17] != row[6:21]
    if row[0] and row[1]: found.append('exchange' if exchanged else 'kept')
    return found


VARIANTS = {'second-ingredient': (second_corpus, second_classes, {'not_called', 'second_ingredient', 'p1_control', 'p2_control', 'message_shown', 'message_refused',
                                                                 'negative_drift', 'non_negative_drift'}),
            'spell-mix': (mix_corpus, mix_classes, {'spell', 'no_spell', 'reload', 'countdown', 'exchange', 'kept'})}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--preset', choices=PRESETS, default='debug'); args = p.parse_args(argv)
    identity = inspect_file(); verify_expected(identity); meta = json.loads((ROOT / STEP).read_text())
    native = verify_executable(args.preset, 'wiznliz-collision'); reference = reference_executable()
    out = Path(tempfile.mkdtemp(prefix='run-', dir=approved_directory(ROOT, 'local/generated/spell-comparison')))
    report = dict(ok=False, preset=args.preset, scope=meta['contract'], rom_sha256=identity['sha256'],
        native_build=json.loads((native.parent / 'provenance.json').read_text()), reference_build=json.loads(REPORT.read_text()),
        sources={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in ('tools/spell_compare.py', 'tests/spell_cases.py', STEP)})
    try:
        pcs, new = probe(DEFAULT_ROM.read_bytes(), meta, out); visited = set(); report['variants'] = {}
        for name, (make, classes, want) in VARIANTS.items():
            rows = make(); data = encode_cases(rows); atomic_write(out / f'{name}.in', data)
            results = {}; processes = {}
            for kind, cmd in [('native', [str(native), '--' + name]), ('reference', [str(reference), str(DEFAULT_ROM), '--' + name])]:
                r = subprocess.run(cmd, input=data, capture_output=True, timeout=600)
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
        require(new <= visited, 'new spell instructions not all executed: ' + ', '.join(f'{a:X}' for a in sorted(new - visited)))
        report.update(ok=True, cases=sum(v['cases'] for v in report['variants'].values()), visited_pcs=sorted(visited),
                      successful_instructions_visited=len(visited), new_instructions_visited=len(new & visited))
    except Exception as e: report['error'] = str(e)
    finally:
        verify_expected(inspect_file()); report['rom_unchanged'] = True; save(out / 'report.json', report)
    print(json.dumps({k: report.get(k) for k in ('ok', 'cases', 'new_instructions_visited', 'error')}
                     | {'outcomes': {n: v['outcomes'] for n, v in report.get('variants', {}).items()}, 'report': str(out / 'report.json')}, indent=2))
    return int(not report['ok'])


if __name__ == '__main__': raise SystemExit(main())
