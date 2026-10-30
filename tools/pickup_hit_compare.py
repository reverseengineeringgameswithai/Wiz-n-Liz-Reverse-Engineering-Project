"""Restricted original 6BD6/6C00 pickup walks (hits with dormant and carrying links, vanish/release, swap and re-dress callbacks) versus native MixedPool::walk_pickup."""
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
from movement_probe import validate, transfer
from rnc_loader_probe import parse_disassembly
from reset_probe import word
from terrain_cases import encode_cases
sys.path.insert(0, str(ROOT / 'tests'))
from pickup_hit_cases import corpus

STEP = 're/pickup_hit_step.json'
# Previously mapped scope the walks execute: the walk body, F76C, the RTS
# selectors, 6BD6, AC5E, 6B44/6BB2, the FAA4 release and the FCB32 mismatch return.
EXECUTED = ((0x69aa, 0x69c2, 7), (0xf76c, 0xf850, 59), (0x12646, 0x12648, 1), (0x6bd6, 0x6c00, 9), (0xac5e, 0xac9c, 19), (0x6b44, 0x6bd6, 36),
            (0xfaa4, 0xfabc, 7), (0xfcb32, 0xfcb42, 4), (0xfcb7a, 0xfcb7e, 2))
# Stops: after the service, the three family branches, the seeded collectable
# callback and FCB32's selector-match path (never taken here).
EXITS = {0x69c2, 0x6e32, 0x6e5e, 0x6e8a, 0xcaf0, 0xfcb42}
# F84E's JMP (A0) reaches the callbacks; 69BA/69C0 the handler and service.
INDIRECT = {0xf84e: [0xfaa4, 0x6cda, 0x6cf4, 0xcaf0], 0x69ba: [0x12646], 0x69c0: [0x6bd6, 0x12646]}
GNU = ((0x6c48, 4, 'tstb'), (0x6c4c, 4, 'beqw'), (0x6c54, 4, 'movew'), (0x6c58, 4, 'movew'), (0x6c90, 4, 'moveb'), (0x6cb8, 2, 'movel'), (0x6cba, 2, 'movel'),
       (0x6cfe, 4, 'moveal'), (0x6d02, 2, 'movew'), (0x6d2c, 2, 'movel'), (0x6d3e, 4, 'clrw'), (0xfb0e, 2, 'moveb'), (0xfb10, 4, 'dbf'), (0xfb14, 2, 'moveal'))


def target(data, pc):
    """transfer() plus JSR (xxx).W, which 6CC0/6CDA/6D86 use for 59BC and 5964."""
    if word(data, pc) == 0x4eb8: return word(data, pc + 2) | (0xffff0000 if word(data, pc + 2) & 0x8000 else 0)
    return transfer(data, pc)


def probe(data, meta, out):
    validate(data, meta); rows = []; new = []; commands = []
    for lo, hi, n, mine in [(r['start'], r['end_exclusive'], r['instruction_count'], True) for r in meta['regions']] + [(*x, False) for x in EXECUTED]:
        cmd = ['rasm2', '-a', 'm68k', '-b', '32', '-e', '-c', '68000', '-s', hex(lo), '-D', data[lo:hi].hex()]
        p = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15)
        decoded = parse_disassembly(p.stdout, data, lo, hi); require(len(decoded) == n, 'pickup hit decoder count differs')
        rows += decoded; new += decoded if mine else []; commands.append(dict(command=cmd, stdout=p.stdout, stderr=p.stderr))
    addresses = {r['address'] for r in rows}; edges = []
    for r in rows:
        pc = r['address']; op = word(data, pc)
        if op == 0x4e75: continue
        targets = [pc + r['size']]
        if pc in INDIRECT:
            require(op in (0x4ed0, 0x4e90), 'pickup hit indirect opcode differs')
            if op == 0x4ed0: targets = []
            targets += INDIRECT[pc]
        else:
            t = target(data, pc)
            if t is not None:
                if op & 0xff00 == 0x6000 or op in (0x4ef9, 0x4efa): targets = []
                targets.append(t)
            else: require(not 0x4e80 <= op <= 0x4eff, 'unmodeled pickup hit indirect transfer')
        for t in targets:
            require(t in addresses or t in EXITS, f'pickup hit graph escapes declared scope at {pc:X} -> {t:X}'); edges.append([pc, t])
    for pc, n, mnemonic in GNU:
        cmd = ['rasm2', '-a', 'm68k.gnu', '-b', '32', '-e', '-c', 'm68000', '-s', hex(pc), '-D', data[pc:pc + n].hex()]
        p = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15); row, = parse_disassembly(p.stdout, data, pc, pc + n)
        require(row['assembly'].split()[0].startswith(mnemonic), 'pickup hit GNU corroboration differs'); commands.append(dict(command=cmd, stdout=p.stdout, stderr=p.stderr))
    save(out / 'static.json', dict(commands=commands, edges=edges, exits=sorted(EXITS), instructions=len(addresses), gnu_checks=len(GNU),
         limitation='GNU corroborates fourteen register-form opcodes (link test and branch, field swaps, record writes, the 6CF4 kind load, the history clear and the FB06 loop); it rejects the immediate/absolute forms, which rely on the primary decoder plus restricted execution.'))
    return addresses, {r['address'] for r in new}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--preset', choices=PRESETS, default='debug'); args = p.parse_args(argv)
    identity = inspect_file(); verify_expected(identity); meta = json.loads((ROOT / STEP).read_text())
    native = verify_executable(args.preset, 'wiznliz-collision'); reference = reference_executable()
    out = Path(tempfile.mkdtemp(prefix='run-', dir=approved_directory(ROOT, 'local/generated/pickup-hit-comparison')))
    report = dict(ok=False, preset=args.preset, scope=meta['contract'], rom_sha256=identity['sha256'],
        native_build=json.loads((native.parent / 'provenance.json').read_text()), reference_build=json.loads(REPORT.read_text()),
        sources={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in ('tools/pickup_hit_compare.py', 'tests/pickup_hit_cases.py', STEP)})
    try:
        pcs, new = probe(DEFAULT_ROM.read_bytes(), meta, out); rows = corpus(); data = encode_cases(rows); atomic_write(out / 'hit.in', data)
        results = {}; processes = {}
        for kind, cmd in [('native', [str(native), '--pickup-hit']), ('reference', [str(reference), str(DEFAULT_ROM), '--pickup-hit'])]:
            r = subprocess.run(cmd, input=data, capture_output=True, timeout=600)
            atomic_write(out / f'hit-{kind}.stdout', r.stdout); atomic_write(out / f'hit-{kind}.stderr', r.stderr)
            require(r.returncode == 0, f'pickup hit {kind} failed: ' + r.stderr.decode()[:1000])
            results[kind] = [tuple(map(int, l.split())) for l in r.stdout.splitlines()]
            require(len(results[kind]) == len(rows), 'pickup hit output extent differs')
            processes[kind] = dict(command=cmd, output_sha256=hashlib.sha256(r.stdout).hexdigest())
            if kind == 'reference': obs = json.loads(r.stderr)
        outcomes = Counter()
        for i, (row, a, b) in enumerate(zip(rows, results['native'], results['reference'])):
            require(a == b, f'case {i}: {row} native={a} original={b}')
            outcomes.update(classes(row, b))
        visited = set(obs['visited'])
        require(visited <= pcs, 'pickup hit execution escaped the declared graph')
        require(new <= visited, 'new pickup hit instructions not all executed')
        want = {'family_stop', 'callback_stop', 'released', 'kept', 'collectable', 'vanishing', 'swapped_out', 'swapped_in', 'p1_link_converted', 'p2_link_converted',
                'p1_exchange', 'p2_exchange', 'redressed', 'repeat_hit', 'no_contact'}
        require(want <= set(outcomes), 'pickup hit corpus lacks a class: ' + ', '.join(sorted(want - set(outcomes))))
        report.update(ok=True, cases=len(rows), outcomes=dict(outcomes), processes=processes, observation=obs, visited_pcs=sorted(visited),
                      successful_instructions_visited=len(visited), new_instructions_visited=len(new & visited))
    except Exception as e: report['error'] = str(e)
    finally:
        verify_expected(inspect_file()); report['rom_unchanged'] = True; save(out / 'report.json', report)
    print(json.dumps({k: report.get(k) for k in ('ok', 'cases', 'outcomes', 'new_instructions_visited', 'error')} | {'report': str(out / 'report.json')}, indent=2))
    return int(not report['ok'])


def classes(row, out):
    """Outcome classes from the original's output and the case's initial links."""
    if out[0] == 0: return ['family_stop' if out[1] == 1 else 'callback_stop']
    found = ['released' if out[1] else 'kept', ('collectable', 'vanishing', 'swapped_out', 'swapped_in')[out[17]]]
    at = 18; kinds = []
    for _k in range(2):
        kinds.append(out[at]); at += 1 + 11 + (1 + 10 + 4 if out[at] else 1)
    for n, (before, after) in enumerate(zip(row[18:20], kinds), 1):
        if not before and after: found.append(f'p{n}_link_converted')
    sounds = out[at + 32]; records = out[at:at + 32]
    if sounds == 0: found.append('no_contact')
    if sounds > 1: found.append('repeat_hit')
    # A carrying link whose record now names the pickup exchanged with it.
    for n in (1, 2):
        if row[17 + n] and sounds and records[2 * row[20 + 26 * (n - 1) + 25]] == 1: found.append(f'p{n}_exchange')
    if out[17] == 0 and sounds and any(row[18:20]): found.append('redressed')
    return found


if __name__ == '__main__': raise SystemExit(main())
