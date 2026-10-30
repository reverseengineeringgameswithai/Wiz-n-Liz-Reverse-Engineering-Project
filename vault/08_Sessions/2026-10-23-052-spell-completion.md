---
id: SESSION-2026-10-23-052
type: session
status: completed
---
# The spell's completion: the joined run to the exit door

Started clean at `8542f7ff22444ee9e8c8a8e4b4ce54e24e61163b` on
`work/airborne-update` (session 051's checkpoint), with an empty index, no stash
and no merge/rebase/cherry-pick/revert operation. The user asked to continue with
the next task. No BizHawk GUI session was running. Authorized local
implementation, validation, vault sync and a reviewed local commit; no
pushes/uploads. No subagents; no external tool changes;
[[02_Workflow/PROJECT_BOUNDARIES]] observed. The preserved recording sufficed.

Intended checkpoint: `Complete the spell natively: the joined run to the door`.

## Delivered scope

Survey (session 051's trace of 1066..2628): 13294 at 1433, 7B58's completion
at 1447 (D269, 7E18, recipe 8652: 7F08's sparkle and 6F02's sign and door,
1324E), 7B8A until the fade-in ends, the sparkle's 64 walks with particles,
the door's puff at 1478 and opening, P1 entering the door at 1515 (705C, then
710E/13208 and 7126 to 1532). Static reading named 7E18's recipe table at 83DA
(105 fruit pairs, one effect routine each) and the movie's pair, fruits 6 and 5
(8652). The joined run therefore ends at 1515.

Library: `start_spell_fade_out`; `SpellPhase` and the timer-aware
`step_spell_countdown`; `src/sim/spell.*` (recipes, `SpellSparkle`, `ExitDoor`,
`DoorSign`); `MixedPool::complete_spell`, `walk_anchor`, `walk_sparkle`, the
timer parameter of `MixedPool::step` (passed by `step_world_phase`) and the new
`PickupWorld` fields; `P1SessionResult::transition` (the timer as 1345A left it). Transport: `--anchor` (20 fields), `--completion`,
`--sparkle`, `--door` (`tools/native/completion_transport.hpp`); world objects
12 (with its phase), 13, 14, 15; the world row adds FF31A8 and FF0690's
+3C/+3E; the world state adds FF316E, FF316C, FF31A8 and FF31C4/FF31C6;
`--world-session` allows 4096 calls (session 051). Evidence:
`re/completion_step.json`, `tools/completion_compare.py`,
`tests/completion_cases.py`, reference modes 6 (extended), 7, 8, 9; the walk
recipe traces FF31A8, FF316C..FF3171, FF31C4..FF31C7 and FF0690's +3C/+3E;
`genesis_world_pool.world_rows` models the completion's births, the sparkle's
particles and E918 calls, the door raising the sign, the deactivated
ingredients and the anchor's phases; `genesis_world_session.py` validates P1 in
segments split after the world's 13294 and 1324E writes and pins FF0690's
+3C/+3E; `genesis_session_capture.py` traces and accepts 1345A's 134D4 return. `tools/spell_compare.py` no longer runs the anchor corpus (moved).

See [[03_Reverse_Engineering/findings/FIND-0049-spell-completion]].

## Validation

- Restricted original execution: `completion-compare` **14,720 cases per preset**
  (debug `run-ahnc27sh`, release `run-y7_45q90`, sanitize `run-c_a8wwo5` in
  `local/generated/completion-comparison`); all 219 new instructions execute
  (430 in all). `spell-compare` keeps 8,330 cases (the anchor corpus moved).
- Fresh setup capture `local/generated/pair-initializer-capture/run-acg9hmd7`
  (fifteen comparisons; fourteen digests equal to session 047's, the world pool
  adding the completion's world fields) and fresh joined capture
  `local/generated/world-session/run-7ob9aoj2` (634..1515; independent
  unhooked endpoint equal at 1515): native matches the setup and, with no
  supplied loops, **all 881 timer states, P1 calls and object loops**
  (cross-check: 881 tracking values, 166 owner positions; 24 palette requests on
  the fade's level steps; 9 external E918 calls and 7 message-producer updates
  as inputs). Fixtures on every preset (release `run-4t6q7fm_`, sanitize
  `run-0x3950zy`) reproduce the same digest.
- Fresh regression captures (the session validator changed): mixed
  `run-9k6nnz5d`, early `run-_n7m9xzd`, late `run-t_mdiqkw`, effect
  `run-8hc6huo1`, each rerun on release/sanitize; every digest equals
  session 050's.
- Regressions on every preset: spell, ingredient, delivery, pickup-hit,
  return-only, collision and table-motion corpora; the setup fixtures.
- **229 Python tests, zero skips; 46/46 CTests per preset**; warning-free.
- Coverage: **146 bounded plus nine partial / 164 indexed**; 31,135 classified
  bytes (+1,671); 2,434 cumulative executed instructions. Evidence:
  `re/completion_validation.json`.

## Attempts, failures and skips

Before any recorded comparison the new reference modes were corrected: the
door and completion scopes lacked the shared RTSs their branches reach (6FB4,
7B56); a callback stop (CAF0) needed its own stack depth; recipe 9288 is also
reached by JSR (A2), one level deeper than 7ED2's branch; 5964 writes the
door's +0E; the sparkle's check missed its presentation bytes and printed slots
from 24-bit addresses; `0x312e+2` lexed as one preprocessing number; one
out-of-scope read was the harness's own post-run check (now direct RAM reads);
and the door's +4A was missing from the reference line. Review before the
corpora moved native's two-player check after 6F02's allocations (the original
allocates first).

The first joined capture (`run-ip7um_0g`) stopped in P1's evidence: on 1433 and
1447 the trace's events after P1's wrapper see the world's timer write
("transition block changed outside 1345A"); those loop-time events are no
longer P1 evidence on those frames. Next, 1345A's level steps in the positive
direction return through 134D4, which the session validator did not accept
("timer phase differs"): `genesis_session_capture.py` now traces and accepts
it, so the mixed, early/late P1 and effect regressions were recaptured fresh.
Offline on that capture's artifacts the native timer print then differed at
1433: it showed the timer after the world's 13294; `P1SessionResult::transition`
now carries the timer as 1345A left it. With these all 881 frames matched and
the joined capture was rerun fresh. `tools/spell_compare.py` no longer runs the
anchor corpus, which continues through 13294 in `tools/completion_compare.py`.
Not rerun: corpora of untouched routines, whole-movie survey and SDL3.

## Reproduction and handoff

```sh
python3 -B tools/project.py build --preset debug
python3 -B tools/project.py completion-compare --preset debug
python3 -B tools/project.py pair-initializer-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py world-session local/generated/capture-qb2htq3j/recording.json --world-report local/generated/pair-initializer-capture/<run>/report.json --preset debug
python3 -B tools/project.py test --rom --preset debug
python3 -B tools/project.py check-vault
python3 -B tools/project.py check-hygiene
```

Next: **P1 enters the door at 1515** ([[01_Project/NEXT_ACTIONS]]).
TASK-0010 is **in progress**; native playability is **none**.

Preservation: the baseline was taken at pass start. ROM, BK2/recording,
worker/build manifest, 104 runtime binaries and 59 GenesisDebug sources verify;
owned workers closed. The BizHawk tree's status changed during the pass (308 →
310 entries, all newer paths under `Tools/SCHMap`, 14:45–15:29): concurrent work
outside this project; this pass writes nothing there and the GenesisDebug worker
is unchanged (recorded in `re/completion_validation.json`). Explicit staged
review precedes the local checkpoint commit. No pushes/uploads.
