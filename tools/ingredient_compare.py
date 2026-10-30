"""Restricted original walks of a 7910 copy through callback79B6's first-ingredient path and 7AD6 (CB72/CB9A, the FF31B4 table object, the record, the release and 7A88 on the released copy) versus native MixedPool::walk_delivered."""
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
from delivery_cases import ingredient_corpus

STEP = 're/ingredient_step.json'
# Previously mapped scope the walks execute: the walk body, F76C, the RTS
# selectors, 6BB2, CB72/CB9A, FB06, the FAA4 release, 7A88 and the already
# classified [7A46,7A58) FF31BC/FF31BE tail.
EXECUTED = ((0x69aa, 0x69c2, 7), (0xf76c, 0xf850, 59), (0x12646, 0x12648, 1), (0x6bb2, 0x6bd6, 8), (0xcb72, 0xcc18, 43), (0xfb06, 0xfb1a, 8),
            (0xfaa4, 0xfabc, 7), (0x7a88, 0x7ad6, 19), (0x7a46, 0x7a58, 3))
# Stops: after the service and 79B6's second-ingredient branch (7A00); 7AE6,
# 7AD6's FF31AC-nonzero path, cannot follow a zero FF31AC at 79F2.
EXITS = {0x69c2, 0x7a00, 0x7ae6}
# F84E's JMP (A0) reaches 79B6; 69BA/69C0 the handler (RTS, or 7A88 once
# called back) and service.
INDIRECT = {0xf84e: [0x79b6], 0x69ba: [0x12646, 0x7a88], 0x69c0: [0x12646]}
GNU = ((0x79b6, 4, 'addqw'), (0x79ba, 4, 'addqw'), (0x79d6, 4, 'jsr'), (0x79ea, 4, 'clrw'), (0x79ee, 4, 'moveal'), (0x79fe, 2, 'beqs'), (0x7ae2, 4, 'beqw'),
       (0x7b34, 4, 'moveal'), (0x7b38, 2, 'movel'), (0x7b40, 2, 'rts'))


def probe(data, meta, out):
    validate(data, meta); rows = []; new = []; commands = []
    for lo, hi, n, mine in [(r['start'], r['end_exclusive'], r['instruction_count'], not r.get('previously_classified')) for r in meta['regions']] + [(*x, False) for x in EXECUTED]:
        cmd = ['rasm2', '-a', 'm68k', '-b', '32', '-e', '-c', '68000', '-s', hex(lo), '-D', data[lo:hi].hex()]
        p = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15)
        decoded = parse_disassembly(p.stdout, data, lo, hi); require(len(decoded) == n, 'ingredient decoder count differs')
        rows += decoded; new += decoded if mine else []; commands.append(dict(command=cmd, stdout=p.stdout, stderr=p.stderr))
    addresses = {r['address'] for r in rows}; edges = []
    for r in rows:
        pc = r['address']; op = word(data, pc)
        if op == 0x4e75: continue
        targets = [pc + r['size']]
        if pc in INDIRECT:
            require(op in (0x4ed0, 0x4e90), 'ingredient indirect opcode differs')
            if op == 0x4ed0: targets = []
            targets += INDIRECT[pc]
        else:
            t = target(data, pc)
            if t is not None:
                if op & 0xff00 == 0x6000 or op in (0x4ef9, 0x4efa): targets = []
                targets.append(t)
            else: require(not 0x4e80 <= op <= 0x4eff, 'unmodeled ingredient indirect transfer')
        for t in targets:
            require(t in addresses or t in EXITS, f'ingredient graph escapes declared scope at {pc:X} -> {t:X}'); edges.append([pc, t])
    for pc, n, mnemonic in GNU:
        cmd = ['rasm2', '-a', 'm68k.gnu', '-b', '32', '-e', '-c', 'm68000', '-s', hex(pc), '-D', data[pc:pc + n].hex()]
        p = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15); row, = parse_disassembly(p.stdout, data, pc, pc + n)
        require(row['assembly'].split()[0].startswith(mnemonic), 'ingredient GNU corroboration differs'); commands.append(dict(command=cmd, stdout=p.stdout, stderr=p.stderr))
    save(out / 'static.json', dict(commands=commands, edges=edges, exits=sorted(EXITS), instructions=len(addresses), gnu_checks=len(GNU),
         limitation='GNU corroborates ten register/displacement forms (both position adds, JSR 6BB2.W, the +36 clear, the +4A load, both FF31AC branches, the record store and the RTS); it rejects the immediate/absolute and memory-to-memory forms (frame restores, mode, handler/cursor stores, FF31AC/FF31B4 loads, the message, +32/+10 stores and the JSR (xxx).L calls), which rely on the primary decoder plus restricted execution.'))
    return addresses, {r['address'] for r in new}


def ingredient_classes(row, out):
    """Outcome classes from the original's output and the case."""
    if out[0] == 0: return ['second_ingredient_stop']
    if not out[1]: return ['not_called']
    found = ['first_ingredient', 'p2_control' if row[11] == 0xffff0838 else 'p1_control']
    cleared = out[3 + 30 + 6]
    found.append('message_shown' if cleared else 'message_refused')
    if row[10] == 2: found.append('fast_cadence')
    return found


VARIANTS = {'ingredient': (ingredient_corpus, ingredient_classes, {'second_ingredient_stop', 'not_called', 'first_ingredient', 'p1_control', 'p2_control', 'message_shown',
                                                                   'message_refused', 'fast_cadence'})}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--preset', choices=PRESETS, default='debug'); args = p.parse_args(argv)
    identity = inspect_file(); verify_expected(identity); meta = json.loads((ROOT / STEP).read_text())
    native = verify_executable(args.preset, 'wiznliz-collision'); reference = reference_executable()
    out = Path(tempfile.mkdtemp(prefix='run-', dir=approved_directory(ROOT, 'local/generated/ingredient-comparison')))
    report = dict(ok=False, preset=args.preset, scope=meta['contract'], rom_sha256=identity['sha256'],
        native_build=json.loads((native.parent / 'provenance.json').read_text()), reference_build=json.loads(REPORT.read_text()),
        sources={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in ('tools/ingredient_compare.py', 'tests/delivery_cases.py', 'tests/pickup_hit_cases.py', STEP)})
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
        require(new <= visited, 'new ingredient instructions not all executed')
        report.update(ok=True, cases=sum(v['cases'] for v in report['variants'].values()), visited_pcs=sorted(visited),
                      successful_instructions_visited=len(visited), new_instructions_visited=len(new & visited))
    except Exception as e: report['error'] = str(e)
    finally:
        verify_expected(inspect_file()); report['rom_unchanged'] = True; save(out / 'report.json', report)
    print(json.dumps({k: report.get(k) for k in ('ok', 'cases', 'new_instructions_visited', 'error')}
                     | {'outcomes': {n: v['outcomes'] for n, v in report.get('variants', {}).items()}, 'report': str(out / 'report.json')}, indent=2))
    return int(not report['ok'])


if __name__ == '__main__': raise SystemExit(main())
