---
id: SESSION-2026-10-23-047
type: session
status: completed
---
# The retained level world: every object loop natively from the setup to 1066

Started clean at `3ac6c70033f373d539656827503471702c98f9e2` on
`work/airborne-update` (session 046's checkpoint), with an empty index, no stash
and no merge/rebase/cherry-pick/revert operation. No BizHawk/EmuHawk session was
running at pass start. The user asked to continue the previous work and to leave
Git and Obsidian clean. Authorized local implementation, validation, vault sync
and a reviewed local commit; no pushes/uploads. No subagents; no external tool
changes.

Intended checkpoint: `Run the retained level world natively through its hits`.

## Delivered scope

The next task asked to run the retained setup pool natively past its hits.
Rather than giving each per-group continuity its own partial world, one
comparison now runs the **whole** retained world: `wiznliz-collision
--world-pool` builds the complete `[6886,68D4)` setup natively from the
6886-entry stack (all 68 slots are free there) and steps every object loop of
frames 634..1065 in that one `MixedPool`, carrying one `PickupWorld`, the private
globals and the E918 state from the setup's own outputs. Per-loop inputs are
only the explicit external ones: 78EE tracking, the resolved emitter owner
position, the count of E918 calls by non-pool code, and message-field updates by
the non-native message producer. No `src/` change was required: the library
already composed every path; what was missing was a carried world and the
emitter's inputs.

Tools: the walk recipe now also traces FF0690's +00 link, the owner actor's
X/Y (FF1AB4), the E918 state (FF0BAC..FF0BB3) and the 5A9A/E918 call sites; the
write record keeps FF0BAC..FF0BB3 and FF31BC..FF31BF writes; `validate_message`
records the pre-7DB8 +46 code. New `tools/genesis_world_pool.py` derives every
input row and expected line from the original alone (slot kinds and generations
followed through the trace), checks that pool bytes change only inside walks,
attributes every E918 call and audits the kept writes; `compare_world` joins the
capture's comparisons. Tests: `tests/world_cases.py`, a carried-world golden in
`tests/native_collision.py` and `tests/test_world_pool.py`.

See [[03_Reverse_Engineering/findings/FIND-0045-retained-world]] and
`re/world_pool_validation.json`.

## Validation

- Fresh hooked replay of frames 0..1066 with an independent unhooked endpoint:
  `local/generated/pair-initializer-capture/run-m589atg2/report.json` (debug).
  The world matches the setup line and **all 432 loops**: 5,732 walk updates (31
  releases), 33 births, 128 emitter walks, both 6C00 hits, all nine 7910 hits
  (one delivery), the 853 first-ingredient path, three sound requests and the
  E60E row clear, with the free stack, generations, records, identities,
  messages, globals and E918 state after every loop. All fourteen earlier
  comparisons reproduce with their bounds; release (`run-mhj7onwl`) and sanitize
  (`run-ihrwz6ca`) reuse the capture.
- Impacted regressions per debug/release/sanitize (every corpus driving
  `wiznliz-collision`): collision 478,345, pickup service 136,848, pickup hit
  6,576, delivery 8,557, ingredient 4,172 and 783A quad 8,746 cases match.
- **224 Python tests, zero skips; 46/46 CTests per preset**; warning-free builds.
- Coverage unchanged (composition only): 133 bounded plus six partial / 148
  indexed plus four fragments; 29,146 classified / 1,019,430 unclassified bytes;
  2,142 cumulative executed instructions.

## Attempts, failures and skips

Before any recorded result, on an exploration capture with the same recipe
(`run-hltyxepl`, which matched all fourteen earlier comparisons):

- The first world run rejected `foreign E918 call at 634`: code at 109E4 and
  10A00 for the object at FFFF32C2 (outside the pool) calls E918 after the
  object loops of 634, 797, 850, 1000 and 1053. Re-seeding the state was
  rejected as an approach; the calls became an explicit count that native
  advances with its own recurrence.
- The second run differed only in the setup line (7DB8's row clear is printed
  with its selection, not as a world request); all 432 loops already matched.
- A stricter between-loop check first compared next-loop entries with frame
  ends and failed at slot 67 (changed at 853 by the copy's walk before its own);
  it now exempts slots another walk of the same loop changed first.
- Sabotage (rerun identically on the final capture): omitting the 798
  external E918 call, the 754 message update or shifting the owner at 790 each
  first differs at that loop; withholding the owner or moving P1 at 780 makes
  native reject.

The exploration capture was superseded because the tool sources changed after
it. The first definitive capture (`run-h4f_f2wy`, fixtures `run-c2scn8lc` and
`run-1u5woe6z`) matched all fifteen comparisons with the same world output; it
was superseded only to correct three docstrings of the world module, whose hash
the capture records. Not rerun: return-only/table-motion/private/trail/reversal/effect
regressions and the other pair/setup variants (their targets are unchanged),
the input through score corpora, mixed-session comparisons and a fresh mixed
capture, other captures, whole-movie survey and SDL3.

## ADR-0001 trigger

The proposed [[06_Decisions/ADR-0001-presentation-shell]] names as its trigger
the first native frame loop over the retained mixed pool that replays a window of
the user's recording. The pool part is now met (432 consecutive object loops),
with the P1 actor still an input. Acceptance remains the user's decision; no
shell work, download or toolchain change was made.

## Reproduction and handoff

```sh
python3 -B tools/build_terrain_reference.py
python3 -B tools/project.py build --preset debug
python3 -B tools/project.py pair-initializer-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py collision-compare --preset debug
python3 -B tools/project.py test --rom --preset debug
python3 -B tools/project.py check-vault
python3 -B tools/project.py check-hygiene
```

Next: **join the native P1 session to the retained world** (see
[[01_Project/NEXT_ACTIONS]]). TASK-0010 is **in progress**; native playability
is **none**.

Preservation: the baseline was taken at pass start. ROM, BK2/recording,
worker/build manifest, 104 runtime binaries and 59 GenesisDebug sources verify;
owned workers closed. WL3PC's owner committed during the pass (`c0c973e` →
`9c892b8`); it was only read. Explicit staged review precedes the local
checkpoint commit. No pushes/uploads.
