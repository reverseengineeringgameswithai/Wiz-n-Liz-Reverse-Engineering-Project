---
id: SESSION-2026-10-03-020
type: session
status: completed
---
# Bounded tally path from the user's recording

Started clean on `work/airborne-update` at
`b7c28375c2e87e6279759f10ddc188ed9f79c590`, with empty index and no pending Git
operation. Read actual entry points, current handoff/task/finding, durable brief,
Git rules and the Genesis hook/capability documentation. The user authorized
continuing with 51C8; no new input or recording was needed.

Intended checkpoint: `Reconstruct bounded tally actor path from recorded gameplay`.

## Implemented result

The movie's 51C8 path branches immediately to 5222, coasts, consumes five units
through 537C/AF98 and waits for Start before setting shared mode=3. It retains
51C8 throughout. The native dispatcher now implements that bounded path and the
direct 5222 selector, with typed tally context and a separate Start byte.
Mutable tally fields participate in the entire presentation/handler/wrapper
transaction, including rollback on late unsupported service or budget failure.

Preserved details: signed countdown, zero-to-FFFF delay before consumption,
one-time Start bypass through a shared skip flag, word wrap before unsigned
credit cap, deferred completion after consuming the final unit, ordered sound
requests, persistent terrain scratch and original tail/subroutine boundaries.
Research `--tally-sequence` retains actor/service/tracking and all four mutable
tally counters, rejecting incoming drift rather than reseeding state.

**51C8 and 5222 remain partial handlers.** Nonzero gate 51D0 and special bonus
allocation 5266 reject transactionally. No palette, allocation or world effects
are silently omitted from a successful invocation. The two partial mappings and
three bounded helpers add **210 disjoint bytes / 48 instructions**, reaching
**83 bounded simulation mappings plus two partial tally handlers / 94 indexed
functions** and **23,763 classified bytes**. The function index records bounded
entry fragments and leaves overall function ends unknown; only exact metadata
regions contribute bytes.
See [[03_Reverse_Engineering/findings/FIND-0020-tally-handler]].

## Verification performed here

- Exact ROM ranges, primary original-68000 decode/sentinels, closed graph and
  four new GNU checks pass. Inherited BCHG corroboration limitation remains;
  no new secondary-decoder limitation. Unsupported targets are explicit exits.
- **231,475 original/native cases per debug/release/sanitize preset**, identical
  output hashes, nineteen goldens and all 48 new instructions visited. Groups:
  216,115 flat/state, 4,608 authored terrain, 10,752 cataloged terrain. Separate
  countdown/credit/remaining word sweeps; no exhaustive Cartesian claim.
- **154 Python tests, zero skips; 24/24 CTest targets in all three presets pass.**
  Tests exercise held Start, ordering, deferred completion, arithmetic, inactive
  wrappers, missing context, work budgets, late rollback, transport drift,
  missing trace boundaries, wrong stacks, uncontracted writes and overflow.
- **175 continuous ordinary P1 wrappers at 3403–3577**, 142 counter-helper calls,
  five sound/credit events and completion at 3577. No actor/counter reseeding;
  controls/scratch/world feeds explicit. Full wrapper return is 7EC; same-call
  branches preserve F906, A148 returns to 522C, credit to 53AE, sound to 53D4.
  Independent unhooked replay matches the declared covered-state endpoint.
- Fresh sanitized regressions: **87,571 coasting, 306,528 transition, 138,149
  wrapper, 146,638 actions, 347,320 presentation, 152,093 actor, 203,586 reversal,
  415,940 airborne, 282,233 movement, 614,436 terrain**. Eleven fresh corpora
  visit **1,076 scoped instructions**, including six reference-only sound guards.
- Fresh movie regressions: one coasting initializer / 16 updates, 17 transition
  actor / 17 timer calls and 191 ordinary / 72 input-branch wrappers. Every
  declared endpoint matches independent unhooked replay. Older 507/92/24 movie
  contracts and the full survey were not rerun. Contracts overlap; do not sum.

No original/native semantic mismatch, final failing check or skipped test.
Initial broad discovery slices started inside adjacent instructions; only the
six exact ranges were promoted. An intermediate edit script stopped at an
unmatched print-statement spelling; the remaining edits were applied explicitly
before the reference build and comparisons. No input/ROM/reference-runtime
change was used to make a comparison pass.

Exact reports, source/output identities, logs and preservation audit are indexed
in `re/tally_validation.json`. Final movie:
`local/generated/tally-movie/run-0x1impxc/report.json`. Regression movies:
`local/generated/coasting-movie/run-h_ur4nxv/report.json`,
`local/generated/transition-movie/run-5bl5s6yh/report.json`,
`local/generated/dispatch-movie/run-yc1mh17u/report.json`.
Discovery, disassembly and logs remain ignored under
`local/generated/recovery-research/`; that provisional name assigns no gameplay
meaning to the observed counters or world mode.

## Reproduction

```sh
python3 -B tools/build_terrain_reference.py
python3 -B tools/project.py tally-probe --disassemble
python3 -B tools/project.py build --preset debug
python3 -B tools/project.py test --rom --preset debug
python3 -B tools/project.py tally-compare --rom --preset debug
python3 -B tools/project.py tally-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py coasting-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py transition-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py dispatch-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py check-vault
python3 -B tools/project.py check-hygiene
```

Build/test/tally-compare repeated for release/sanitize. All ten previous
simulation `*-compare --rom --preset sanitize` corpora ran after their help and
existing recipes were reviewed. Only the local research Musashi harness was
rebuilt. Shared trace validators now accept an explicit completion-mode allowlist,
empty by default; the tally contract permits only mode 3 and compares outputs.
The prior movie contracts were rerun after this change.

## Review and preservation

Reviewed all **34 explicitly staged owned paths**, covering native arithmetic,
context transactions, typed selectors, restricted original allowlists, continuous
transports, exact trace boundaries, authored tests, metadata and vault. Nineteen
pinned reports/audits and current source/build identities verify. Staged whitespace
checks pass; vault validation checks **72 notes** and hygiene checks **255 indexed
files**, both without errors. Review keeps the two partial handlers separate from
bounded helpers and leaves overall original function ends unknown.

ROM: 1,048,576 bytes, SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
Original BK2: 2,597 bytes, SHA-256
`c1db675318d4e8b1527f8161fa4b782fe96f1ce4e47f173b66ae782a01b327fd`.
All 104 frozen runtime binaries and the worker retain their original hashes.
The independent owned worker contexts close normally. User GUI, BizHawk source/
runtime, Sonic19420 and read-only WL3PC were untouched. No subagent, package
installation, external rebuild, push or upload. Bulk artifacts remain ignored.

## Exact next task

Reconstruct **51D0's nonzero-gate path and deferred handler 5204**, including
137CE/1372C palette preparation and 1324E initialization, using a clearly labeled
controlled-state movie experiment. Ordinary captured 51C8 calls take the zero
branch. Keep 5266's allocation path separately unsupported; 5132/5188 remain
later recorded targets. TASK-0010 stays **in progress**. **Native playability:
none.** World/P2 scheduling, shared allocation/ownership, palette consumers,
rendering and audio playback remain incomplete. No additional user input needed.
