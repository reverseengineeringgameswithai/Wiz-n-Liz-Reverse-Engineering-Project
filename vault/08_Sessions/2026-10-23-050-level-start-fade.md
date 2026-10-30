---
id: SESSION-2026-10-23-050
type: session
status: completed
---
# The level-start fade in the session: the world native from its first loop

Started clean at `880497b7de576e0ebeee034a59238bb641b5353c` on
`work/airborne-update` (session 049's checkpoint), with an empty index, no stash
and no merge/rebase/cherry-pick/revert operation. The user asked whether work can
continue without SDL3 or Godot; it can (all current work is headless and
verified against the original), so the pass continued with the next task. No
BizHawk GUI session was running. Authorized local implementation, validation,
vault sync and a reviewed local commit; no pushes/uploads. No subagents; no
external tool changes; [[02_Workflow/PROJECT_BOUNDARIES]] observed.

Intended checkpoint: `Run the level-start fade in the native session`.

## Delivered scope

Library: `P1SessionState::transition`; `step_p1_session` and `step_mixed_session`
run `step_transition_timer` before the banner. Transport: `--world-session` takes
the timer row and prints the timer after each frame's banner. Evidence:
`genesis_session_capture.validate_session`/`validate_writes` gain `active_timer`
(default unchanged); `tools/genesis_world_session.py` now joins P1 from 634 and
checks the fade's dirty requests (`fade`). Tests: a session unit test for the
timer and its rollback, the timer in the `--world-session` transport test and a
`fade` test.

See [[03_Reverse_Engineering/findings/FIND-0047-level-start-fade]] and
`re/fade_session_validation.json`.

## Validation

- Fresh P1 capture of 634..1066 (independent unhooked endpoint equal to the world
  capture's): `local/generated/world-session/run-z6v12tnt/report.json` (debug),
  with the world capture `run-m589atg2`. Native matches the setup and, with no
  supplied loops, all 432 timer states, **all 432 P1 calls** and **all 432
  object loops**; the cross-check holds for 432 tracking values and 128 owner
  positions; the eight dirty requests match the level steps. Release
  (`run-u8n22j5m`) and sanitize (`run-vbpuecyb`) reuse it with the same digest.
- The validator's hash changed, so the session regressions were recaptured fresh
  (debug) and rerun as fixtures (release/sanitize): the mixed session
  `[1066,1100)`, the early and late P1 sessions `[700,1067)` and
  `[3100,3200)`, and the effect session `[700,1090)`; every digest equals the
  one recorded before this pass.
- **226 Python tests, zero skips; 46/46 CTests per preset**; warning-free.
- Coverage unchanged (composition).

## Attempts, failures and skips

The trace already captured in session 049 (634..1066) showed the plan was sound
before any new capture: with the timer's block and writes set aside P1 matched
natively for all 432 calls, and every transition-block writer was the timer. The
first validator edit named its parameter `timer`, which a loop variable of that
function reassigns; it was renamed before any run. Not rerun: restricted corpora
(no routine changed), a fresh world capture (tool unchanged), whole-movie survey
and SDL3.

## Reproduction and handoff

```sh
python3 -B tools/project.py build --preset debug
python3 -B tools/project.py pair-initializer-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py world-session local/generated/capture-qb2htq3j/recording.json --world-report local/generated/pair-initializer-capture/<run>/report.json --preset debug
python3 -B tools/project.py test --rom --preset debug
python3 -B tools/project.py check-vault
python3 -B tools/project.py check-hygiene
```

Next: **extend the joined run past 1066** ([[01_Project/NEXT_ACTIONS]]).
TASK-0010 is **in progress**; native playability is **none**.

Preservation: the baseline was taken at pass start. ROM, BK2/recording,
worker/build manifest, 104 runtime binaries and 59 GenesisDebug sources verify;
the BizHawk tree status is unchanged; owned workers closed. Explicit staged
review precedes the local checkpoint commit. No pushes/uploads.
