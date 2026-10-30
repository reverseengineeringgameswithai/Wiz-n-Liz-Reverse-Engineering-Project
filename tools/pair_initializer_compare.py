"""Restricted original F9E2 group initializers (7B9C, 7C26, 7772 pairs; 783A quad; the [6886,68A4) setup prefix, [68A4,68BC) tail and [68C4,68D4) gated pairs) and the [68BC,68C4) message step versus native."""
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
from movement_probe import validate, closed_graph
from rnc_loader_probe import parse_disassembly
from terrain_cases import encode_cases
sys.path.insert(0, str(ROOT / 'tests'))
from pair_initializer_cases import corpus, expected_native_rejection, quad_corpus, quad_expected_native_rejection, prefix_corpus, prefix_expected_native_rejection, tail_corpus, tail_expected_native_rejection, tail_members, message_corpus, \
    pairs_corpus, pairs_expected_native_rejection, pairs_members, pairs_shape

EXHAUSTION = 0xfa1e
# The installed GNU plugin rejects every immediate/absolute extension form here
# (4EB9, 1D7C, 2D7C, 3D7C, 23C8, 23CE, 33FC); corroborate the register forms.
VARIANTS = {
    'return-only': dict(step='re/pair_initializer_step.json', region='return_only_pair_initializer', native=('wiznliz-return-only', '--pair'),
                        reference='--pair-initializer', returns=[0x7c24, 0xfa1c], anchored=True, new=None, output='pair-initializer-comparison'),
    'visibility': dict(step='re/visibility_pair_step.json', region='visibility_pair_initializer', native=('wiznliz-private', '--pair'),
                       reference='--visibility-pair', returns=[0x7ca2, 0xfa1c], anchored=False, new=(0x7c26, 0x7ca4), output='visibility-pair-comparison'),
    'rising': dict(step='re/rising_pair_step.json', region='rising_pair_initializer', native=('wiznliz-private', '--rising-pair'),
                   reference='--rising-pair', returns=[0x7806, 0xfa1c], anchored=False, new=(0x7772, 0x7808), output='rising-pair-comparison',
                   # GNU rejects MOVE.W d16(An),d16(An) and ADDI.W here; corroborate the link/clear/LEA forms.
                   gnu=((0x777e, 4, 'movel'), (0x77b4, 4, 'clrw'), (0x77b8, 2, 'lea'), (0x77c0, 4, 'movel'))),
    # Four pops: probe (with extents), then three return-only members.
    'collision-quad': dict(step='re/collision_quad_step.json', region='collision_quad_initializer', native=('wiznliz-collision', '--quad'),
                           reference='--collision-quad', returns=[0x78ec, 0xfa1c], anchored=False, new=(0x783a, 0x78ee), output='collision-quad-comparison',
                           members=4, extra=2, corpus=quad_corpus, rejection=quad_expected_native_rejection,
                           # GNU rejects the immediate/A4-relative MOVE and ADDI.W forms here; corroborate the link store and LEA.
                           gnu=((0x7846, 4, 'movel'), (0x7878, 2, 'lea'))),
    # The whole fragment with every callee: twelve pops, then FF31B4/FF31B8/FF31C0.
    'setup-prefix': dict(step='re/setup_prefix_step.json', regions=('setup_prefix_fragment', 'dormant_first_initializer', 'dormant_second_initializer',
                                                                    'rising_pair_initializer', 'collision_quad_initializer', 'return_only_pair_initializer',
                                                                    'visibility_pair_initializer'),
                         native=('wiznliz-return-only', '--prefix'), reference='--setup-prefix', returns=[0x6eda, 0x6eee, 0x7806, 0x78ec, 0x7c24, 0x7ca2, 0xfa1c],
                         continuations=[[0x68a0, 0x68a4]], anchored=False, new=((0x6886, 0x68a4), (0x6ec8, 0x6ef0)), output='setup-prefix-comparison',
                         members=12, extra=2, count_offset=2, corpus=prefix_corpus, rejection=prefix_expected_native_rejection,
                         ids=lambda row: (*row[2:14], row[2], row[3], row[11]),
                         # GNU rejects LEA/MOVE absolute and MOVE #imm forms here; corroborate the six BSRs and the dormant RTS.
                         gnu=tuple((pc, 4, 'bsrw') for pc in range(0x688c, 0x68a4, 4)) + ((0x6eee, 2, 'rts'),)),
    # Variable member count (pickups + two links): the harness checks records,
    # links and clears itself; here the slots, count and exact equality are checked.
    'setup-tail': dict(step='re/setup_tail_step.json', regions=('setup_tail_fragment', 'pickup_table_pass', 'pickup_initializer', 'pickup_frames',
                                                                'pickup_cadence', 'control_link_initializer'),
                       native=('wiznliz-return-only', '--tail'), reference='--setup-tail', returns=[0x6aee, 0x6b42, 0x6b66, 0x6b88, 0x6b9c, 0x6bb0, 0x6bc6, 0x6bd4, 0x6ec6, 0xfa1c],
                       continuations=[[0x68b8, 0x68bc]], anchored=False, new=((0x68a4, 0x68bc), (0x6a94, 0x6bd6), (0x6eb6, 0x6ec8)), output='setup-tail-comparison',
                       members=18, limit=tail_members, corpus=tail_corpus, rejection=tail_expected_native_rejection,
                       shape=lambda row, b: b[1] == tail_members(row) - 2 and list(b[2:2 + tail_members(row)]) == list(row[2:2 + tail_members(row)]),
                       # GNU corroborates the register and BSR forms; it rejects absolute LEA/CLR, MOVE #imm and MULU here.
                       gnu=((0x68a4, 4, 'bsrw'), (0x68ae, 4, 'bsrw'), (0x6a9a, 2, 'movel'), (0x6aa0, 2, 'clrl'), (0x6aa6, 4, 'dbf'),
                            (0x6af0, 2, 'movel'), (0x6b02, 2, 'movel'), (0x6ebc, 4, 'movel'))),
    # No allocation: outputs are compared exactly and classified by path.
    'setup-message': dict(step='re/setup_message_step.json', regions=('setup_message_fragment', 'message_selection', 'message_request', 'message_row_clear', 'pair_gate'),
                          native=('wiznliz-return-only', '--message'), reference='--setup-message', returns=[0x6f00, 0x7dfa, 0x7e16, 0xcb98, 0xcc16],
                          continuations=[[0x68c0, 0x68c4], [0x6ef6, 0x6f02], [0x6efe, 0x6f02]], anchored=False, output='setup-message-comparison',
                          new=((0x68bc, 0x68c4), (0x7db8, 0x7e18), (0xcb72, 0xcc18), (0x6ef0, 0x6f02)), exact=True, corpus=message_corpus, allocates=False,
                          # GNU corroborates the BSR, loop, compare and register forms here.
                          gnu=((0x68bc, 4, 'bsrw'), (0x7dd2, 2, 'movew'), (0x7ddc, 4, 'dbf'), (0xcb7a, 2, 'moveb'), (0xcbfc, 4, 'dbf'), (0x6f00, 2, 'rts'))),
    # Two pops per open gate. The harness checks registers, selectors, handlers,
    # links and every byte; here the gate mask, address order and equality.
    'setup-pairs': dict(step='re/setup_pairs_step.json', regions=('setup_pairs_fragment', 'p2_placed_pair_initializer', 'first_fixed_pair_initializer',
                                                                  'second_fixed_pair_initializer', 'third_fixed_pair_initializer'),
                        native=('wiznliz-return-only', '--pairs'), reference='--setup-pairs', returns=[0x715c, 0x71cc, 0x7366, 0x73d6, 0x7570, 0x75e0, 0x7fc6, 0x803e, 0xfa1c],
                        continuations=[[0x68d0, 0x68d4]], anchored=False, new=((0x68c4, 0x68d4), (0x7154, 0x71ce), (0x735e, 0x73d8), (0x7568, 0x75e2), (0x7fbe, 0x8040)),
                        output='setup-pairs-comparison', members=8, limit=pairs_members, corpus=pairs_corpus, rejection=pairs_expected_native_rejection, shape=pairs_shape,
                        # GNU corroborates the BSR, MOVEM, ordering (CMPA.L/BLT/EXG) and register-store forms; it rejects the immediate forms here.
                        gnu=((0x68c4, 4, 'bsrw'), (0x7fc8, 4, 'moveml'), (0x7fcc, 4, 'bsrw'), (0x7fd0, 2, 'lea'), (0x7fd6, 2, 'cmpal'), (0x7fd8, 2, 'blts'),
                             (0x7fda, 2, 'exg'), (0x7fdc, 4, 'movel'), (0x801a, 4, 'movel'), (0x803a, 4, 'moveml'), (0x718a, 4, 'clrw'), (0x71a4, 4, 'subqw'),
                             (0x7364, 2, 'bnes')))}
GNU = ((0xf9e2, 2, 'movel'), (0xf9ea, 2, 'tstl'), (0xf9ec, 2, 'beqs'), (0xf9f4, 2, 'moveal'),
       (0xfa10, 4, 'clrw'), (0xfa1a, 2, 'moveal'), (0xfa1c, 2, 'rts'), (0xfa2e, 2, 'bras'))


def probe(data, meta, out, variant):
    validate(data, meta); rows = {}; commands = []
    for r in meta['regions']:
        lo, hi = r['start'], r['end_exclusive']
        cmd = ['rasm2', '-a', 'm68k', '-b', '32', '-e', '-c', '68000', '-s', hex(lo), '-D', data[lo:hi].hex()]
        p = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15)
        decoded = parse_disassembly(p.stdout, data, lo, hi); require(len(decoded) == r['instruction_count'], 'pair decoder count differs')
        rows[r['id']] = decoded; commands.append(dict(command=cmd, stdout=p.stdout, stderr=p.stderr))
    allocates = variant.get('allocates', True)
    success = [row for region in variant.get('regions', (variant.get('region'),)) for row in rows[region]] + (rows['allocate_a6_success'] if allocates else [])
    loop = rows['allocate_a6_exhaustion_loop'] if allocates else []
    exits = variant.get('continuations', [])
    graph = closed_graph(data, success + loop, tuple(b for _a, b in exits))
    require(sorted(graph['returns']) == variant['returns'] and graph['continuations'] == exits, 'pair graph returns/exits differ')
    require(all(r['address'] < EXHAUSTION or r['address'] < 0x10000 for r in success), 'success graph overlaps exhaustion loop')
    for pc, n, mnemonic in GNU + ((variant['returns'][0], 2, 'rts'),) + variant.get('gnu', ()):
        cmd = ['rasm2', '-a', 'm68k.gnu', '-b', '32', '-e', '-c', 'm68000', '-s', hex(pc), '-D', data[pc:pc + n].hex()]
        p = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15); row, = parse_disassembly(p.stdout, data, pc, pc + n)
        require(row['assembly'].split()[0].startswith(mnemonic), 'pair GNU corroboration differs'); commands.append(dict(command=cmd, stdout=p.stdout, stderr=p.stderr))
    save(out / 'static.json', dict(commands=commands, graph=graph, gnu_checks=len(GNU) + 1 + len(variant.get('gnu', ())),
         limitation='GNU corroborates eight register-form opcodes (push/test/branch/pop/clear/restore/return/loop). Its plugin rejects the immediate and absolute forms (JSR.L, MOVE #imm to d16(An), absolute MOVE.L/MOVE.W), which rely on the primary decoder plus restricted and full-machine execution. FA1E..FA30 is decoded and graph-closed but never executed.'))
    return {r['address'] for r in success}, {r['address'] for r in loop}


def compare_rows(rows, native, original, anchored=True, members=2, extra=0, rejection=expected_native_rejection, ids_of=None, shape=None, limit_of=None):
    """`members` ordered pops (`limit_of` when the count depends on the row);
    `extra` fields follow the probe (783A extents). `ids_of` names the printed
    slots and identities when they are not the leading member fields of the row."""
    outcomes = Counter()
    for i, (row, a, b) in enumerate(zip(rows, native, original)):
        want = rejection(row)
        if b[0] == 0:
            limit = limit_of(row) if limit_of else members
            require(len(b) == 2 and b[1] == min(row[0], limit) < limit and want is not None, f'case {i}: unexpected original exhaustion {row} {b}')
            outcomes['original_exhausted_after_%d' % b[1]] += 1
        elif shape:
            require(shape(row, b), f'case {i}: original group shape differs {row} {b}'); outcomes['original_created'] += 1
        else:
            ids = ids_of(row) if ids_of else (*row[1:1 + members], row[members]) if anchored else tuple(row[1:1 + members])
            require(row[0] >= members and len(b) == 2 + 12 * members + extra + len(ids) and b[1:1 + len(ids)] == ids and b[1 + len(ids)] == row[0] - members,
                    f'case {i}: original group identity differs {row} {b}')
            outcomes['original_created'] += 1
        if want is None:
            require(a == b, f'case {i}: {row} native={a} original={b}'); outcomes['native_created'] += 1
        else:
            require(a == (0, want), f'case {i}: {row} native={a} expected rejection {want}')
            outcomes['native_exhausted' if want == 1 else 'native_unknown_inheritance'] += 1
    return dict(outcomes)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--preset', choices=PRESETS, default='debug')
    p.add_argument('--variant', choices=VARIANTS, default='return-only'); args = p.parse_args(argv); variant = VARIANTS[args.variant]
    identity = inspect_file(); verify_expected(identity); meta = json.loads((ROOT / variant['step']).read_text())
    native = verify_executable(args.preset, variant['native'][0]); reference = reference_executable()
    out = Path(tempfile.mkdtemp(prefix='run-', dir=approved_directory(ROOT, 'local/generated/' + variant['output'])))
    report = dict(ok=False, preset=args.preset, variant=args.variant, scope=meta['contract'], rom_sha256=identity['sha256'],
        native_build=json.loads((native.parent / 'provenance.json').read_text()), reference_build=json.loads(REPORT.read_text()),
        sources={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in ('tools/pair_initializer_compare.py', 'tests/pair_initializer_cases.py', variant['step'])})
    try:
        pcs, loop = probe(DEFAULT_ROM.read_bytes(), meta, out, variant); rows = variant.get('corpus', corpus)(); data = encode_cases(rows); atomic_write(out / 'pair.in', data)
        results = {}; processes = {}
        for kind, cmd in [('native', [str(native), variant['native'][1]]), ('reference', [str(reference), str(DEFAULT_ROM), variant['reference']])]:
            r = subprocess.run(cmd, input=data, capture_output=True, timeout=300)
            atomic_write(out / f'pair-{kind}.stdout', r.stdout); atomic_write(out / f'pair-{kind}.stderr', r.stderr)
            require(r.returncode == 0, f'pair {kind} failed: ' + r.stderr.decode()[:1000])
            results[kind] = [tuple(map(int, l.split())) for l in r.stdout.splitlines()]
            require(len(results[kind]) == len(rows), 'pair output extent differs')
            processes[kind] = dict(command=cmd, output_sha256=hashlib.sha256(r.stdout).hexdigest())
            if kind == 'reference': obs = json.loads(r.stderr)
        if variant.get('exact'):
            outcomes = Counter()
            for i, (row, a, b) in enumerate(zip(rows, results['native'], results['reference'])):
                require(a == b, f'case {i}: {row} native={a} original={b}')
                outcomes['open_6ef0_rejected' if b[0] == 0 else ('none', 'mix', 'returned')[b[1]] + ('_shown' if b[5] else '_refused' if b[1] else '')] += 1
            outcomes = dict(outcomes)
        else:
            outcomes = compare_rows(rows, results['native'], results['reference'], variant['anchored'], variant.get('members', 2), variant.get('extra', 0),
                                    variant.get('rejection', expected_native_rejection), variant.get('ids'), variant.get('shape'), variant.get('limit'))
        visited = set(obs['visited'])
        require(visited == pcs, 'pair successful instruction coverage differs from declared graph')
        require(not visited & loop, 'restricted execution entered the exhaustion loop')
        if variant.get('exact'): require({'none', 'mix_shown', 'mix_refused', 'returned_shown', 'returned_refused', 'open_6ef0_rejected'} <= set(outcomes), 'message corpus lacks a path class')
        else: require(all(outcomes.get(f'original_exhausted_after_{k}') for k in range(variant.get('members', 2))) and outcomes.get('native_unknown_inheritance'), 'pair corpus lacks a boundary class')
        report.update(ok=True, cases=len(rows), outcomes=outcomes, processes=processes, observation=obs, visited_pcs=sorted(visited),
            successful_instructions_visited=len(visited), exhaustion_loop_instructions_static=len(loop),
            new_instructions_visited=len(visited) if variant['new'] is None else sum(any(lo <= pc < hi for lo, hi in (variant['new'] if isinstance(variant['new'][0], tuple) else (variant['new'],))) for pc in visited))
    except Exception as e: report['error'] = str(e)
    finally:
        verify_expected(inspect_file()); report['rom_unchanged'] = True; save(out / 'report.json', report)
    print(json.dumps({k: report.get(k) for k in ('ok', 'cases', 'outcomes', 'new_instructions_visited', 'error')} | {'report': str(out / 'report.json')}, indent=2))
    return int(not report['ok'])


if __name__ == '__main__': raise SystemExit(main())
