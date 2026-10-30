---
id: SESSION-2026-10-02-019
type: session
status: completed
---
# Deferred coasting initializer and the 632A handler

Started clean on `work/airborne-update` at
`390c109e312df072186a3459ed9a40bbd215e792`. Read actual entry points, current
handoff/task/finding, durable brief, Git rules and Genesis capabilities/hook
semantics. No pre-existing index/worktree changes or pending Git operation.
The user authorized continuing with 632A; no clarification was needed.

Intended checkpoint: `Reconstruct deferred coasting initializer and handler`.

## Implemented result

632A is two instructions: reload associated control from actor+4A, then tail
JMP A148. It reuses the native coasting implementation and retains itself.
Buttons and shared transition completion do not redirect it; it needs no
`ActionGlobals` or `TransitionState`. Late service failure preserves actor,
terrain scratch, tracking and other contexts through the existing transaction.

The preceding 630A initializer is also implemented as `begin_coasting`. It binds
the actor associated with the given control context (original A4, not the caller's
A6), sets tracking selector FFFF, mode 80, first word 21D and handler 632A.
Other fields and tracking coordinates are retained. Movement and FF80/FF80
tracking outputs are deferred to the next wrapper invocation. The surrounding
world routine and its later shared transition initialization are not included.

Two mappings add **42 bytes / eight instructions**, reaching **80 bounded
simulation mappings / 89 indexed functions** and **23,553 classified ROM bytes**.
A148 contributes no duplicate coverage. Native targets contain no emulator.
Details: [[03_Reverse_Engineering/findings/FIND-0019-coasting-handler]].

## Verification performed here

- Exact ROM range hashes, original-68000 decoding/sentinels and closed graph
  pass. Three new GNU checks corroborate pointer loads/RTS; absolute-long JMP
  remains an explicit installed secondary-decoder limitation.
- **87,571 original/native cases per debug/release/sanitize preset**, identical
  output hashes, eleven authored goldens and all eight new instructions visited.
  Groups: 13,680 actor-flat, 66,211 initializer, 2,304 authored terrain, 5,376
  cataloged terrain. Word entry sweeps are correlated, not a Cartesian proof.
- **149 Python tests, zero skips; 22/22 CTest targets in all presets pass.**
  Tests check retained fields and deferred work, no shared-context dependency,
  zero-speed no-op, budget exhaustion, late-service rollback, transport continuity,
  missing/misordered trace boundaries, owner mismatches and uncontracted writes.
- **One ordinary P1 initializer at 1742 followed by sixteen continuous wrapper
  calls at 1743–1758**, with no actor reseeding. Initializer returns to 62F8;
  wrapper returns to 5F3A; coasting tail retains F906. Independent unhooked replay
  matches the covered-state endpoint. No input/RAM/register/ROM edits.
- Prior movie regressions pass freshly: **17 transition actor / 17 timer calls**,
  and **191 ordinary / 72 input-branch wrappers**, including intermediate
  presentation/handler checks. All their endpoints match independent unhooked
  runs. The initializer's P2 hit is observed but not compared natively.
- Fresh sanitized regressions: **306,528 transition, 138,149 wrapper, 146,638
  actions, 347,320 presentation, 152,093 actor, 203,586 reversal, 415,940 airborne,
  282,233 movement, 614,436 terrain**. Ten fresh corpora visit **1,028 scoped
  instructions**, including six reference-only sound guards.

No original/native semantic mismatch, final failing check or skipped test.
The initial larger disassembly slice began inside an instruction and included
later tables; only exact 630A–6334 boundaries were promoted. Discovery showed
initialization occurs in frame 1742, before the surveyed 632A calls. Capture
was widened backward by one frame and tests deliberately preserve the deferred
boundary. GNU limitations are inherited and explicitly retained, not suppressed.
Older 507 actor/presentation and 92 actor / 24 effect movie contracts, and the
full recording survey, were not rerun here.

Exact reports/hashes/logs: `re/coasting_validation.json`.
Final movie: `local/generated/coasting-movie/run-g7vzhcyq/report.json`.
Regressions: `local/generated/transition-movie/run-son5h9w7/report.json` and
`local/generated/dispatch-movie/run-v23xeorr/report.json`.
Discovery, disassembly and build/test logs remain ignored under
`local/generated/arrival-research/`; this directory's provisional name is not
a claim about the gameplay meaning of the transition.

## Reproduction

```sh
python3 -B tools/build_terrain_reference.py
python3 -B tools/project.py coasting-probe --disassemble
python3 -B tools/project.py build --preset debug
python3 -B tools/project.py coasting-compare --rom --preset debug
python3 -B tools/project.py test --rom --preset debug
python3 -B tools/project.py coasting-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py transition-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py dispatch-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py check-vault
python3 -B tools/project.py check-hygiene
```

Build/coasting-compare/test were repeated for release and sanitize. All nine
prior simulation `*-compare --rom --preset sanitize` tools ran after reviewing
their help and preceding session recipes. Only the local research Musashi
harness was rebuilt; the external Genesis runtime/source stayed read-only.
The reusable movie runner now accepts explicit recipes, comparators and windows;
its original transition contract was rerun after that change.

## Review and preservation

Reviewed all **32 explicitly staged owned paths**: native initialization/tail
behavior, transactions, restricted original allowlists, transport modes, authored
tests, exact metadata and vault. The evidence index verifies seventeen pinned
report/audit hashes, source identities, matching comparison outputs and all
preservation hashes. Staged whitespace checks pass; vault validation checks
**70 notes** and hygiene checks **244 indexed files**, both without errors.
Bulk captures, states, disassembly, ROM/movie and binaries remain ignored.

ROM stays 1,048,576 bytes, SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
The 2,597-byte original BK2 stays
`c1db675318d4e8b1527f8161fa4b782fe96f1ce4e47f173b66ae782a01b327fd`.
All 104 runtime binaries and the separate worker match the frozen hashes;
audit: `local/generated/arrival-research/preservation.json`. Owned worker contexts
close normally. User GUI, Sonic19420, BizHawk source/runtime and read-only WL3PC
were untouched. No subagent, package install, external rebuild, push or upload.

## Exact next task

TASK-0010 remains **in progress**. **Native playability: none.** Next reconstruct
**51C8 at movie frames 3403–3577**, using narrow captures and exact static/called
boundaries before adding native behavior. Other surveyed unknown selectors:
5132 and 5188. World allocation/ownership, broader scheduling, palette consumers,
rendering and audio playback remain open. No additional recording or user input
is required.
