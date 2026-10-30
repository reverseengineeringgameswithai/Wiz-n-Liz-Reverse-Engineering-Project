"""Restricted original 78EE/7910 probe walks (deliveries from carrying links, dormant-link returns, the FF31B0 gate) and later walks of the 59AE sparkle and FB06 copy versus native MixedPool::walk_probe and MixedPool::step."""
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
from delivery_cases import probe_corpus, delivered_corpus

STEP = 're/delivery_step.json'
# Previously mapped scope the walks execute: the walk body, F76C, the RTS
# selectors, 78EE, AC5E, the FCB32 mismatch return, 59BC, 5964, both
# allocators, FB06 and the FAA4 release.
EXECUTED = ((0x69aa, 0x69c2, 7), (0xf76c, 0xf850, 59), (0x12646, 0x12648, 1), (0x78ee, 0x7910, 9), (0xac5e, 0xac9c, 19), (0xfcb32, 0xfcb42, 4),
            (0xfcb7a, 0xfcb7e, 2), (0x59bc, 0x5a06, 12), (0x5964, 0x59ae, 12), (0xf9e2, 0xfa1e, 14), (0xf994, 0xf9d0, 14), (0xfb06, 0xfb1a, 8),
            (0xfaa4, 0xfabc, 7))
# Stops: after the service, the allocators' exhaustion loops, the seeded probe
# callback, the copy's 79B6 callback and FCB32's selector-match path (never taken).
EXITS = {0x69c2, 0xfa1e, 0xf9d0, 0xcaf0, 0x79b6, 0xfcb42}
# F84E's JMP (A0) reaches the callbacks; 69BA/69C0 the handler and service.
INDIRECT = {0xf84e: [0xfaa4, 0xcaf0, 0x79b6], 0x69ba: [0x12646], 0x69c0: [0x78ee, 0x12646]}
GNU = ((0x791a, 4, 'bnew'), (0x791e, 4, 'moveal'), (0x7922, 4, 'tstb'), (0x7926, 4, 'beqw'), (0x792a, 2, 'movel'), (0x7952, 2, 'lea'), (0x7954, 4, 'movel'),
       (0x7964, 4, 'movew'), (0x7968, 4, 'movew'), (0x796c, 2, 'subqw'), (0x796e, 2, 'subqw'), (0x7970, 2, 'movel'), (0x7972, 4, 'jsr'), (0x7976, 2, 'moveal'),
       (0x7978, 4, 'subqw'), (0x799c, 2, 'lea'), (0x799e, 2, 'moveal'), (0x79a6, 4, 'moveal'), (0x79aa, 4, 'movel'), (0x79ae, 4, 'clrb'), (0x79b2, 2, 'moveal'),
       (0x79b4, 2, 'rts'), (0x7a56, 2, 'rts'), (0x59b4, 4, 'movew'), (0x59b8, 4, 'movew'))


def probe(data, meta, out):
    validate(data, meta); rows = []; new = []; commands = []
    # 7A56 (callback79B6's closing RTS) was classified and executed with the [7A46,7A58) writer fragment.
    for lo, hi, n, mine in [(r['start'], r['end_exclusive'], r['instruction_count'], not r.get('previously_classified')) for r in meta['regions']] + [(*x, False) for x in EXECUTED]:
        cmd = ['rasm2', '-a', 'm68k', '-b', '32', '-e', '-c', '68000', '-s', hex(lo), '-D', data[lo:hi].hex()]
        p = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15)
        decoded = parse_disassembly(p.stdout, data, lo, hi); require(len(decoded) == n, 'delivery decoder count differs')
        rows += decoded; new += decoded if mine else []; commands.append(dict(command=cmd, stdout=p.stdout, stderr=p.stderr))
    addresses = {r['address'] for r in rows}; edges = []
    for r in rows:
        pc = r['address']; op = word(data, pc)
        if op == 0x4e75: continue
        targets = [pc + r['size']]
        if pc in INDIRECT:
            require(op in (0x4ed0, 0x4e90), 'delivery indirect opcode differs')
            if op == 0x4ed0: targets = []
            targets += INDIRECT[pc]
        else:
            t = target(data, pc)
            if t is not None:
                if op & 0xff00 == 0x6000 or op in (0x4ef9, 0x4efa): targets = []
                targets.append(t)
            else: require(not 0x4e80 <= op <= 0x4eff, 'unmodeled delivery indirect transfer')
        for t in targets:
            require(t in addresses or t in EXITS, f'delivery graph escapes declared scope at {pc:X} -> {t:X}'); edges.append([pc, t])
    for pc, n, mnemonic in GNU:
        cmd = ['rasm2', '-a', 'm68k.gnu', '-b', '32', '-e', '-c', 'm68000', '-s', hex(pc), '-D', data[pc:pc + n].hex()]
        p = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15); row, = parse_disassembly(p.stdout, data, pc, pc + n)
        require(row['assembly'].split()[0].startswith(mnemonic), 'delivery GNU corroboration differs'); commands.append(dict(command=cmd, stdout=p.stdout, stderr=p.stderr))
    save(out / 'static.json', dict(commands=commands, edges=edges, exits=sorted(EXITS), instructions=len(addresses), gnu_checks=len(GNU),
         limitation='GNU corroborates twenty-five register/displacement forms (the gate branch, the link load and mode test, the A6/A5 saves and restores, the position and Y arithmetic, both JSR (xxx).W and the copy\'s +42/mode stores, both RTS and 59AE\'s position stores); it rejects the immediate/absolute forms (the FF31B0 compare, the mailbox and position/callback stores, the JSR (xxx).L calls), which rely on the primary decoder plus restricted execution.'))
    return addresses, {r['address'] for r in new}


def overlaps(obj, ext, ctl, mask):
    """AC5E (for outcome classes only; the comparison is the native one)."""
    return ((obj[0] + ext[0] - ctl[0]) & mask) <= ext[0] + 16 and ((obj[1] + ext[1] - ctl[1]) & 0xffff) <= ext[1] + 12


def probe_classes(row, out):
    """Outcome classes from the original's output and the case's first walk."""
    if out[0] == 0: return ['exhausted' if out[1] == 1 else 'probe_callback']
    at = 15; kinds = []
    for _k in range(2):
        kinds.append(out[at]); at += 1 + 11 + (1 + 10 + 4 if out[at] else 1)
    created = out[at]; found = []
    for n, (before, after) in enumerate(zip(row[17:19], kinds), 1):
        if before and not after: found.append(f'p{n}_delivered')
    if created == 4: found.append('two_deliveries')
    rise = row[71] << 16 | row[72]; p1 = overlaps(row[0:2], row[12:14], row[73:75], row[75])
    p2 = row[76] and overlaps(row[0:2], row[12:14], row[78:80], row[75])
    if p1 and rise: found.append('gate_closed')
    if p1 and not rise and not row[17]: found.append('dormant_return')
    if not p1 and not p2: found.append('no_first_contact')
    if created and row[83] > 1 and (row[84] == 0 or row[84] > 1): found.append('repeat_after_delivery')
    return found or ['other']


def delivered_classes(row, out):
    if out[0] == 0: return ['copy_callback']
    return [('copy' if row[0] else 'sparkle') + ('_released' if out[1] else '_kept')]


VARIANTS = {'probe-hit': (probe_corpus, probe_classes, {'p1_delivered', 'p2_delivered', 'two_deliveries', 'gate_closed', 'dormant_return', 'no_first_contact',
                                                         'repeat_after_delivery', 'exhausted', 'probe_callback'}),
            'delivered': (delivered_corpus, delivered_classes, {'sparkle_released', 'sparkle_kept', 'copy_kept', 'copy_callback'})}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--preset', choices=PRESETS, default='debug'); args = p.parse_args(argv)
    identity = inspect_file(); verify_expected(identity); meta = json.loads((ROOT / STEP).read_text())
    native = verify_executable(args.preset, 'wiznliz-collision'); reference = reference_executable()
    out = Path(tempfile.mkdtemp(prefix='run-', dir=approved_directory(ROOT, 'local/generated/delivery-comparison')))
    report = dict(ok=False, preset=args.preset, scope=meta['contract'], rom_sha256=identity['sha256'],
        native_build=json.loads((native.parent / 'provenance.json').read_text()), reference_build=json.loads(REPORT.read_text()),
        sources={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in ('tools/delivery_compare.py', 'tests/delivery_cases.py', 'tests/pickup_hit_cases.py', STEP)})
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
        require(new <= visited, 'new delivery instructions not all executed')
        report.update(ok=True, cases=sum(v['cases'] for v in report['variants'].values()), visited_pcs=sorted(visited),
                      successful_instructions_visited=len(visited), new_instructions_visited=len(new & visited))
    except Exception as e: report['error'] = str(e)
    finally:
        verify_expected(inspect_file()); report['rom_unchanged'] = True; save(out / 'report.json', report)
    print(json.dumps({k: report.get(k) for k in ('ok', 'cases', 'new_instructions_visited', 'error')}
                     | {'outcomes': {n: v['outcomes'] for n, v in report.get('variants', {}).items()}, 'report': str(out / 'report.json')}, indent=2))
    return int(not report['ok'])


if __name__ == '__main__': raise SystemExit(main())
