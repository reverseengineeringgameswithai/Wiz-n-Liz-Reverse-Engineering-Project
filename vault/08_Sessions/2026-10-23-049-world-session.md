---
id: SESSION-2026-10-23-049
type: session
status: completed
---
# The native player joined to the retained level world

Started clean at `369e2f4cb4e9e2b6dcd312c375170f43eacd74b5` on
`work/airborne-update` (session 048's checkpoint, made earlier in this
conversation), with an empty index, no stash and no merge/rebase/cherry-pick/
revert operation. The user asked to continue with the next task after the stack
decision. No BizHawk GUI session was running. Authorized local implementation,
validation, vault sync and a reviewed local commit; no pushes/uploads. No
subagents; no external tool changes. Following
[[02_Workflow/PROJECT_BOUNDARIES]], no other home-directory project was read or
queried, and the baseline/preservation scripts no longer record one.

Intended checkpoint: `Join the native player to the retained level world`.

## Delivered scope

Library: `MixedSessionState::world`, `establish_world`, `WorldUpdates`,
`WorldPhaseResult`, `step_world_phase`; `step_mixed_session` gains `WorldUpdates`
and runs its object loop through `step_world_phase`, returning the world's sound
requests and row clears. Transports: `--world-pool` now uses the library
functions (byte-identical output on all presets); new `wiznliz-session
--world-session`. Tool: `tools/genesis_world_session.py`
(`project.py world-session`) pairs a fresh P1 capture with the world capture,
cross-checks them and compares the joined run. Tests: carried-world unit tests in
`tests/unit/mixed_pool_test.cpp`, a `--world-session` transport test in
`tests/native_mixed_pool.py` and a cross-check test in `tests/test_world_pool.py`.

See [[03_Reverse_Engineering/findings/FIND-0046-world-session]] and
`re/world_session_validation.json`.

## Validation

- Fresh P1 capture of 669..1066 with independent unhooked endpoint (equal to the
  world capture's): `local/generated/world-session/run-m5oexgkg/report.json`
  (debug), with the world capture `run-m589atg2`. Native matches the setup, the
  35 supplied loops, all 397 P1 calls and all 397 joined loops; the cross-check
  holds for 397 tracking values and 128 owner positions. Release
  (`run-uzd8hcpj`) and sanitize (`run-j974l_j5`) reuse it with the same digest.
  Toggling a held button at 700 or 775 breaks the comparison there.
- Regressions per preset: the world capture fixture (fifteen comparisons, world
  digest unchanged), the mixed session `[1066,1100)` (digest unchanged), pickup
  hit 6,576, delivery 8,557 and ingredient 4,172 cases, and the context probe.
- **225 Python tests, zero skips; 46/46 CTests per preset**; warning-free.
- Coverage unchanged (composition): 133 bounded plus six partial / 148 indexed.

## Attempts, failures and skips

- Survey first: the early P1 session evidence over 634..1066 rejected at 634
  because the level-start fade timer (FF0B90 = FFFF, 1345A writers) runs until
  668; the same trace from 669 matched natively for all 397 calls. The join
  starts at 669; loops 634..668 keep supplied tracking.
- The first joined capture (`run-pvyvbwin`) validated fully but its comparison
  hit a tool bug (a shadowed variable); the fixed comparison on its artifacts
  matched; it was superseded because the tool changed.
- A unit test first placed the pickup below its link, which correctly rejected
  (the converted emitter walked without an owner); it now uses the ordinary
  layout.

Not rerun: restricted corpora that do not drive pool hits, a fresh world capture
(tool unchanged; fixtures rerun with the new transports), a fresh mixed capture,
whole-movie survey and SDL3.

## Reproduction and handoff

```sh
python3 -B tools/project.py build --preset debug
python3 -B tools/project.py pair-initializer-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py world-session local/generated/capture-qb2htq3j/recording.json --world-report local/generated/pair-initializer-capture/<run>/report.json --preset debug
python3 -B tools/project.py test --rom --preset debug
python3 -B tools/project.py check-vault
python3 -B tools/project.py check-hygiene
```

Next: **schedule the level-start fade timer in the session so P1 joins the world
from 634** ([[01_Project/NEXT_ACTIONS]]). TASK-0010 is **in progress**; native
playability is **none**.

Preservation: the baseline was taken at pass start. ROM, BK2/recording,
worker/build manifest, 104 runtime binaries and 59 GenesisDebug sources verify;
the BizHawk tree status is unchanged; owned workers closed. Explicit staged
review precedes the local checkpoint commit. No pushes/uploads.
