---
id: VALIDATION-RESULTS
type: validation
status: active
---
# Executed results

## Latest research: session 2026-10-07-038 — local Kev evidence diagnostic

36 pre-labelled claims; first option order 35/36 correct, cyclic orders 36/36
and 35/36, separate questions 35/36. No false-supported claims in this sample;
one interval-scope mistake changes with answer order. The unattended-use
criterion failed. All 16 API requests completed and 144 response rows validated;
these are repeats of 36 claims, never new game-function comparisons or coverage.
Existing synthetic tests: 208 pass, zero skips. Native/reference suites were
not rerun. ROM identity unchanged; vault/hygiene/whitespace checks pass.
Evidence: `re/kev_validation.json`, [[09_References/KEV]],
[[08_Sessions/2026-10-07-038-kev-assessment]].

## Session 2026-10-28-056 — session 055's validation completed (in progress)

- With the unchanged tools and builds: the fresh all-in-one `game-session`
  capture (`run-s49_3nc8`) matches all 1,095 P1 calls and loops from one seed
  with the offline digests (`bc8e1384…`, `8fab99e3…`); its debug, release and
  sanitize fixtures match; fresh standalone level (`run-vuef_6mv`) and hub
  (`run-s7w9oa6_`) captures reproduce session 054's digests and their fixtures
  match on every preset. `re/scene_change_validation.json` is the full record.
- Survey after the hub (research only):
  [[03_Reverse_Engineering/findings/FIND-0053-second-level-entry]].
- Second-level entry (checkpoint): 10,625 restricted cases match in debug
  (1,023 second-level, 1,019 hint-screen); offline joined run matches the level,
  hub, 301 hint loops, the entry's P1/timer and 29 second-level P1 calls, rejects
  exactly at 2136; E918's entry state is two draws behind (open). Release/
  sanitize, fresh captures and the full suite are pending; ROM identity
  unchanged.

## Latest native: session 2026-10-23-055 — the scene change: the level and the hub as one run

- Survey (research trace of 1531..1564, every return in the scene change with
  the carried state): 0x488's anchor, 16EA4 (17024, F850, FF0F16, 131C2 and
  001E), 9880 (98DE, 9952, 1737E, 5964), 17284, 446C, 63E2 and 5ED4; the timer
  does not run from the level's last loop until 1563.
- Restricted original execution (`tools/hub_compare.py` with
  `re/scene_change_step.json`, reference mode 13): **8,583 cases per
  debug/release/sanitize** match (`run-v5qc0ycz`, `run-a8vh_w5z`,
  `run-7dse2dxy`): the hub's 7,571 and 1,012 scene changes (both actors,
  parameters, the fade-in timer, FF0EDE, FF0F16 and the reset pool; declared
  camera/HUD/render words, every other byte unchanged); all 375 new
  instructions of both steps execute.
- Offline joined comparison (a fresh scene-change capture with session 054's
  fresh level and hub captures, through `tools/genesis_game_session.py`'s own
  evidence and compare): the carried state changes only inside the
  reconstructed routines, and one native `--game-session` run from one P1 seed
  matches **all 1,095 P1 calls and loops** (the level's 899, the scene change's
  P1/timer/banner/pool, the hub's 196). The tool's fresh all-in-one capture
  and its fixtures, interrupted by a restart, were completed by session 056.
- The refactored level and hub compares reproduce session 054's seed and output
  digests on its captures; the mixed, early/late P1 and effect fixtures keep
  their digests on every preset.
- Regressions on every preset: completion (14,734), spell, ingredient, delivery,
  pickup-hit, return-only, collision and table-motion corpora; the setup
  fixtures.
- **239 Python tests, zero skips; 46/46 CTests per preset**; builds warning-free.
- Coverage: **161 bounded plus 13 partial / 183 indexed**; +692 classified
  bytes (32,855; 274 more promoted from static-only); 2,838 cumulative executed
  instructions.
- Corrected: session 054's notes quoted hub-door counts from a run before the
  authored P1 rows were fixed; the recorded runs have 448 entries, 410 openings
  and 181,385 walks.
- Not rerun: corpora of untouched routines, whole-movie survey and SDL3. No
  pushes/uploads.

Evidence: `re/scene_change_validation.json` (completed by session 056),
[[03_Reverse_Engineering/findings/FIND-0052-scene-change]],
[[08_Sessions/2026-10-23-055-scene-change]]. TASK-0010 remains in progress.
**Native playability: none.**

## Historical: session 2026-10-23-054 — the scene after the level: its doors

- Survey (research traces of 1530..1800): the level loop returns at 1532; 5D30's
  setup resets the pool (1535..1536), initializes both actors (1537) and at 1562
  builds eight doors with two number objects each; its loop (no 179F8, 7CC8 or
  C086) ends at 1758 after P1 entered door 0 at 1742.
- Restricted original execution (`tools/hub_compare.py`, `re/hub_step.json`,
  reference modes 10..12): **7,571 cases per debug/release/sanitize** match: 3,122
  door setups (2,492 complete, 247 F9E2 and 383 F994 exhaustion stops), 4,163
  door walks (181,385 walks: 410 openings, 448 entries of which 69 by FF0838,
  471 puffs, 50 releases, 22 callback stops, one revival stop) and 286 exit
  tests; all 185 new instructions execute (311 in all).
- Fresh hub capture `local/generated/hub-session/run-bj1ao6x9` (1562..1759;
  independent unhooked endpoint equal at 1759): the setup's 408 world writes all
  come from 60E6's chain over a reset pool; native `--hub-session` matches the
  setup's 24 objects and, from one P1 seed and physical held sets (Up/Down on
  110 frames), **all 196 P1 calls** (two sound requests), the timer after every
  1345A, FF4446/48 and FF3398 after every loop, the entry at 1742 (17298 on
  FF0690, FF4446/48 = 0098/0008, the puff, both numbers released, 630A on both
  controls, 13208), 6024's end at 1758 and **the pool image after every loop**.
  The loops' 3,196 world writes come from the hub's routines; B0C8 writes zero
  over +14 806 times. P1's evidence is split after 1742. Release/sanitize reuse
  the capture with the same digest.
- The session validator gained its `hub` variant: the joined level capture
  (634..1533) and the mixed, early/late P1 and effect regressions were
  recaptured fresh and rerun on every preset; every digest is unchanged.
- Regressions on every preset: completion (14,734), spell, ingredient, delivery,
  pickup-hit, return-only, collision and table-motion corpora; the setup
  fixtures.
- **236 Python tests, zero skips; 46/46 CTests per preset**; builds warning-free.
- Coverage: **156 bounded plus ten partial / 175 indexed**; +876 classified
  bytes (32,163); 2,648 cumulative executed instructions.
- Failures: none in recorded comparisons; the first fresh hub capture's world
  audit stopped on B0C8's +14 clear (recognized; recaptured fresh); harness and
  corpus fixes before the first matching restricted run.
- Not rerun: corpora of untouched routines, whole-movie survey and SDL3. No
  pushes/uploads.

Evidence: `re/hub_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0051-hub-doors]],
[[08_Sessions/2026-10-23-054-hub-scene]]. TASK-0010 remains in progress.
**Native playability: none.**

## Historical: session 2026-10-23-053 — entering the door: native to the level's end

- Restricted original execution: the door variant of `tools/completion_compare.py`
  now continues through 7082 and 4CA2: **14,734 cases per debug/release/sanitize**
  match (4,150 door cases: 326 entries, 260 with camera words and 66 with two
  players; 103 active-link and 412 two-player stops); all 29 new instructions
  execute.
- A faithful P1 capture of 1514..1533 run through the shared session validator
  failed exactly at the world's FF0836 write (1515), 13208 inside P1's wrapper
  (1516) and FF33E0 (1532); the validator's new `exit_transition` accepts the
  last two, and the joined tool splits P1's evidence after the world's 7082.
- Fresh setup capture and a fresh joined capture of 634..1533 (independent
  unhooked endpoint equal at 1533): native `--world-session` matches the setup
  and, with no supplied loops, **all 899 fade-timer states** (with curves),
  **all 899 P1 calls** (as each wrapper returned them; 18 sound requests),
  FF33E0 every frame with 7126's final camera write, and **all 899 object
  loops**: P1 entering the door at 1515 (the sign released, the door vanishing,
  FF0F00, the camera words, P1 handed to 710E), 710E's exit fade (1516) and 7126
  ending the level at 1532 (FF33E0 = 7); 899 tracking values and 166 owner
  positions cross-checked; 32 palette requests on the fades' level steps.
  Release/sanitize reuse the capture with the same digest.
- The session validator changed again (13208 traced, `exit_transition`): the
  mixed, early/late P1 and effect regressions were recaptured fresh and rerun on
  every preset; every digest is unchanged.
- Regressions on every preset: spell, ingredient, delivery, pickup-hit,
  return-only, collision and table-motion corpora; the setup fixtures (only the
  world pool's output changed: FF0F00 and the camera words).
- **230 Python tests, zero skips; 46/46 CTests per preset**; builds warning-free.
- Coverage: **147 bounded plus nine partial / 165 indexed**; +152 classified
  bytes (31,287); 2,463 cumulative executed instructions.
- Failures: none in recorded comparisons; the first joined capture's native
  comparison stopped on a wrong per-frame check of the camera position (FF0732/34)
  and then on P1 printed after the world's hand-off; both fixed before the fresh
  capture.
- Not rerun: corpora of untouched routines, whole-movie survey and SDL3. No
  pushes/uploads.

Evidence: `re/door_entry_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0050-door-entry]],
[[08_Sessions/2026-10-23-053-door-entry]]. TASK-0010 remains in progress.
**Native playability: none.**

## Historical: session 2026-10-23-052 — the spell's completion: native to the exit door

- Restricted original execution (`tools/completion_compare.py`,
  `re/completion_step.json`): **14,720 cases per debug/release/sanitize** match
  exactly: 3,141 anchor walks (388 fade-outs from 13294, 217 completions
  reached, 226 reveals), 3,333 completions (256 completed, 791 waits and every
  stop: 677 other recipes, 371 no-recipe or 9288, 465 FF31A8, 225 9182, 82
  two-player, 73 9682, 69 9614, 324 exhausted), 4,110 sparkle runs (1,240 with
  particles, 1,616 releases) and 4,136 door-and-sign runs (443 doors opened,
  519 entries stopped, 351 two-player stops). All 219 new instructions execute
  (430 in all); GNU corroborates fifteen forms.
- Fresh setup capture of 0..1066 (the walk recipe changed) and a fresh joined
  capture of 634..1515 (independent unhooked endpoint equal at 1515): native
  `--world-session` matches the setup and, with no supplied loops, **all 881
  fade-timer states, all 881 P1 calls** (18 sound requests) and **all 881
  object loops**: 13294's fade-out (1433), the completion (1447: D269, fruits 6
  and 5, the sparkle, sign and door), the fade-in and 7B8A (to 1461), the
  sparkle's 65 walks and 31 particles, the door's puff (1478) and opening
  (1508); P1's evidence in three segments joined by exactly the world's 13294
  and 1324E writes; 881 tracking values and 166 owner positions cross-checked;
  24 palette requests on the fade's level steps. Release/sanitize reuse the
  capture with the same digest.
- The session validator learned 1345A's 134D4 return, so the mixed `[1066,1100)`,
  early `[700,1067)` and late `[3100,3200)` P1 and effect `[700,1090)` sessions
  were recaptured fresh and rerun on release/sanitize; every digest is unchanged.
- Regressions on every preset: the spell (8,330: the anchor corpus moved),
  ingredient, delivery, pickup-hit, return-only, collision and table-motion
  corpora; the setup capture's fifteen comparisons (fourteen digests unchanged;
  the world pool's seed and output add the completion's world fields).
- **229 Python tests, zero skips; 46/46 CTests per preset**; builds warning-free.
- Coverage: **146 bounded plus nine partial / 164 indexed**; +1,671 classified
  bytes (31,135); 2,434 cumulative executed instructions.
- Failures: none in recorded comparisons; reference-harness corrections before
  the first comparison and three stops in the first joined capture's evidence
  (loop-time trace events on the timer frames, 1345A's 134D4 return, the native
  timer print after the world's write), each fixed before the fresh captures.
- Not rerun: corpora of untouched routines, whole-movie survey and SDL3. No
  pushes/uploads.

Evidence: `re/completion_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0049-spell-completion]],
[[08_Sessions/2026-10-23-052-spell-completion]]. TASK-0010 remains in progress.
**Native playability: none.**

## Historical: session 2026-10-23-051 — the second ingredient and the spell mix: native to 1433

- Restricted original execution (`tools/spell_compare.py`, `re/spell_step.json`):
  **10,420 cases per debug/release/sanitize** match exactly: 4,186
  second-ingredient walks (387 callbacks: 320 messages shown, 67 refused; 152
  negative drifts), 2,090 anchor countdowns (775 stops at 13294) and 4,144 7CC8
  calls (931 reloads; 930 exchanges, 930 kept). All 73 new instructions execute
  (248 in all); GNU corroborates twelve forms.
- Fresh setup capture of 0..1066 (its tools changed) and a fresh joined capture
  of 634..1433 (P1 and world replays; independent unhooked endpoint equal to
  both at 1433): native `--world-session` matches the setup and, with no
  supplied loops, **all 799 fade-timer states, all 799 P1 calls** (14 sound
  requests) and **all 799 object loops**: P1's reversal effect in the shared
  pool (1067), the second delivery (1103), the second ingredient (1133: D22F
  shown, FF31B8 slot 66, the FF31C0 anchor's 7B42) and every 7CC8 call (299
  countdowns, six reloads to FF31BC 6, 46 exchanges, 311 audited writes);
  cross-checked for 799 tracking values and 166 owner positions.
  Release/sanitize reuse the capture with the same digest.
- Regressions on every preset: ingredient (4,172), delivery (8,557), pickup-hit
  (6,576), return-only (286,848), collision (478,345) and table-motion (406,634)
  corpora; the setup capture's fifteen comparisons (fourteen digests unchanged;
  the world pool output adds FF31B0); mixed, effect and early/late P1 fixtures
  with their recorded digests.
- **228 Python tests, zero skips; 46/46 CTests per preset**; builds warning-free.
- Coverage: 79B6/7AD6 promoted, 7CC8 bounded, 7B42 partial: **136 bounded plus
  five partial / 150 indexed**; +318 classified bytes (29,464); 2,215 cumulative
  executed instructions.
- Failures: none in recorded comparisons; the first joined capture's evidence
  stopped at 1067 (P1's reversal effect, not yet modeled) and native at its
  600-call session cap; both were fixed and the captures rerun fresh.
- Not rerun: corpora of untouched routines, whole-movie survey and SDL3. No
  pushes/uploads.

Evidence: `re/spell_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0048-spell-mixing]],
[[08_Sessions/2026-10-23-051-spell-mixing]]. TASK-0010 remains in progress.
**Native playability: none.**

## Historical: session 2026-10-23-050 — the level-start fade: native from the first loop

- A fresh P1 capture of 634..1066 validated with an active 1345A timer
  (independent unhooked endpoint equal to the world capture's), joined with the
  session-047 world capture: native `--world-session` matches the setup and,
  with no supplied loops, **all 432 fade-timer states**, **all 432 P1 calls**
  from one seed and 432 held rows, and **all 432 object loops** consuming P1's
  own tracking and position; cross-checked for 432 tracking values and 128 owner
  positions; the fade's eight palette requests match its level steps.
  Release/sanitize reuse the capture with the same digest.
- Fresh regression captures because the session validator changed: mixed
  `[1066,1100)` (digest unchanged), early `[700,1067)` and late `[3100,3200)` P1
  sessions and the effect session `[700,1090)`, each rerun on release/sanitize.
- **226 Python tests, zero skips; 46/46 CTests per preset**; builds warning-free.
- Coverage unchanged (composition).
- Failures: none in recorded runs (one parameter-name clash fixed before any run).
- Not rerun: restricted corpora (no routine changed), a fresh world capture,
  whole-movie survey and SDL3. No pushes/uploads.

Evidence: `re/fade_session_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0047-level-start-fade]],
[[08_Sessions/2026-10-23-050-level-start-fade]]. TASK-0010 remains in progress.
**Native playability: none.**

## Historical: session 2026-10-23-049 — the native player joined to the world

- A fresh P1 capture of 669..1066 (independent unhooked endpoint equal to the
  world capture's) joined with the session-047 world capture (revalidated by the
  current tool): native `--world-session` matches the setup, the 35 supplied
  loops (634..668, level-start fade), **all 397 P1 calls** (actor, scratch,
  tracking, input, 12 sound requests, banner requests) from one seed and 397
  held rows, and **all 397 joined object loops** consuming P1's own tracking and
  position. Cross-check: 397 tracking values and 128 emitter owner positions of
  the world capture equal P1's. Release/sanitize reuse the capture (same digest).
  Toggling a held button at 700 or 775 breaks the comparison there.
- Regressions per preset: the world capture's fifteen comparisons (world digest
  unchanged), the `[1066,1100)` mixed session (digest unchanged), pickup hit
  6,576, delivery 8,557, ingredient 4,172 cases and the context probe.
- **225 Python tests, zero skips; 46/46 CTests per preset**; builds warning-free.
- Coverage unchanged (composition).
- Failures: none in recorded runs. Before them, the 634 survey found the fade
  timer; the first joined capture was superseded after a tool fix; one unit test
  layout was corrected.
- Not rerun: corpora not driving pool hits, a fresh world or mixed capture,
  whole-movie survey and SDL3. No pushes/uploads.

Evidence: `re/world_session_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0046-world-session]],
[[08_Sessions/2026-10-23-049-world-session]]. TASK-0010 remains in progress.
**Native playability: none.**

## Historical: session 2026-10-23-047 — the retained level world

- Fresh hooked replay of frames 0..1066 with independent unhooked endpoint
  (report in `re/world_pool_validation.json`): native `--world-pool` builds the
  whole `[6886,68D4)` setup from its entry stack and matches the setup line and
  **all 432 object loops (634..1065)**: 5,732 walk updates (31 releases), 33
  births (31 trail particles, the sparkle, the copy), 128 emitter walks with
  owner positions, both 6C00 hits (780, 980), nine 7910 hits with the 823
  delivery, the 853 first-ingredient path, three sound requests and the E60E row
  clear; the free stack, generations, records, FF31AC, links, FF31B4/FF31B8,
  FF31C0, both controls' messages, FF31BE, the private globals, E918 state and
  both links' objects match after every loop. Pool bytes change only inside
  walks. Per-loop inputs: 78EE tracking, the owner position, five external E918
  calls (object FFFF32C2) as counts and four message-producer updates. All
  fourteen earlier comparisons reproduce with their bounds; release/sanitize
  reuse the capture.
- Sabotage on the exploration capture: each dropped or shifted input differs at
  its loop or makes native reject.
- Impacted restricted corpora per debug/release/sanitize: collision 478,345,
  pickup service 136,848, pickup hit 6,576, delivery 8,557, ingredient 4,172 and
  783A quad 8,746 cases match.
- **224 Python tests, zero skips; 46/46 CTests per preset**; builds warning-free.
- Coverage unchanged: no new mapping, bytes or instructions (composition).
- Failures: none in recorded runs. Before them, the first world run found the
  foreign E918 calls; one expectation and one byte check were corrected; the
  exploration capture was superseded when the tool changed.
- Not rerun: unchanged-target regressions (return-only through effect), other
  pair/setup variants, input through score corpora, mixed-session comparisons,
  other captures, whole-movie survey and SDL3. No pushes/uploads.

Evidence: `re/world_pool_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0045-retained-world]],
[[08_Sessions/2026-10-23-047-retained-world]]. TASK-0010 remains in progress.
**Native playability: none.**

## Historical: session 2026-10-18-046 — callback79B6 and 7AD6: the first ingredient

- **4,172 restricted original/native first-ingredient walk cases per
  debug/release/sanitize** match exactly: 340 callbacks (211 P1 / 129 P2
  controls; 285 D20E messages shown, 55 refused by a higher held priority; 76
  with the fast cadence), 3,811 walks that only animate and 21 second-ingredient
  stops. Every copy, FF31B4-object, record, message, global and free-stack byte
  outside the printed fields is checked, with CB9A's VDP words sunk and checked.
  29 new instructions, all native (178 executed in all).
- Fresh hooked replay of frames 0..1066 with independent unhooked endpoint
  (report in `re/ingredient_validation.json`): the copy's 853 walk (D20E
  accepted, row clear at VRAM E60E; slot 67 becomes the table object; FF31AC and
  record 1 name it; slot 47 released; FF31BE = 0050, FF31BC = 0) matches
  natively, and all 213 later walks of slot 67 (853..1065) match one at a time
  and chain. Every earlier comparison and bound reproduces (fourteen matched
  comparisons); release/sanitize reuse the capture.
- Mixed `[1066,1100)`: the session-035 capture reused with all rebuilt presets.
- **218 Python tests, zero skips; 46/46 CTests per preset**; builds warning-free.
  29 regressions, every earlier pair/setup variant, the pickup, delivery and
  ingredient corpora and the context probe pass.
- Coverage: 154 new classified bytes; 133 bounded mappings plus six partial /
  148 indexed plus four setup fragments; 29 new executed instructions (2,142
  cumulative); fresh twenty-six-corpus union 1,787, or 1,793 with the writer
  instructions.
- Failures: none in recorded runs. Test corrections preceded any recorded
  comparison; one matching capture was superseded to add the new step metadata
  to its recorded sources. A separate user BizHawk session was running and left
  untouched.
- Not rerun: eight other component corpora (actions through score), debug/release
  runs of the eight sanitized corpora, a fresh mixed capture, other captures,
  whole-movie survey and SDL3 availability. No pushes/uploads.

Evidence: `re/ingredient_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0044-first-ingredient]],
[[08_Sessions/2026-10-18-046-first-ingredient]]. TASK-0010 remains in progress.
**Native playability: none.**

## Historical: session 2026-10-18-045 — 7910 probe hits: delivering the carried fruit

- **8,557 restricted original/native cases per debug/release/sanitize** match
  exactly: 4,425 probe walks (807 P1 / 202 P2 deliveries, 44 cases with two, 476
  dormant-link returns, 781 closed FF31B0 gates, 836 repeat touches after a
  delivery, 268 allocator-exhaustion and 67 probe-callback stops) and 4,132
  later walks of the created objects (83 sparkle releases, 78 copy 79B6 stops).
  Every probe, link, created-object and global byte outside the printed fields
  is checked; each copy equals its link except the mode byte and the pops are
  the stack's top entries in order. 40 new instructions, all native (41 with the
  already classified 7A56 RTS).
- Fresh hooked replay of frames 0..1066 with independent unhooked endpoint
  (report in `re/delivery_validation.json`): nine ordinary 7910 hits, all P1 on
  the slot-63 probe. Frame 823 delivers link 53's fruit (sparkle in slot 54, copy
  in slot 47); 824..831 return at 7A56. All nine walks match natively from the
  original entry states with the real free stack, and all 60 later walks of the
  sparkle (release at 853) and the copy (79B6 at 853, rejected natively) match
  one at a time and chain. Link 53 stays unchanged from 823 to its 6C00 reuse at
  980. Every earlier comparison and bound reproduces (fourteen matched
  comparisons); release/sanitize reuse the capture.
- Mixed `[1066,1100)`: the session-035 capture reused with all rebuilt presets.
- **218 Python tests, zero skips; 46/46 CTests per preset**; builds warning-free.
  29 regressions, every earlier pair/setup variant, the pickup service and hit
  corpora and the context probe pass.
- Coverage: 180 new classified bytes; 133 bounded mappings plus four partial /
  146 indexed plus four setup fragments; 40 new executed instructions (2,113
  cumulative); fresh twenty-five-corpus union 1,756, or 1,764 with the writer
  instructions.
- Failures: none in recorded runs. Unit-test and evidence-derivation corrections
  preceded any recorded comparison; one capture and some comparison runs made
  before a metadata correction (7A56 was already classified) matched and were
  superseded. A separate user BizHawk session was running and left untouched.
- Not rerun: eight other component corpora (actions through score), debug/release
  runs of the eight sanitized corpora, a fresh mixed capture, other captures,
  whole-movie survey and SDL3 availability. No pushes/uploads.

Evidence: `re/delivery_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0043-fruit-delivery]],
[[08_Sessions/2026-10-18-045-fruit-delivery]]. TASK-0010 remains in progress.
**Native playability: none.**

## Historical: session 2026-10-18-044 — 6C00 pickup hits: carrying and swapping fruit

- **6,576 restricted original/native pickup-walk cases per debug/release/sanitize**
  match exactly: 974 P1 / 182 P2 conversions of a dormant link into the carrying
  emitter, 862 P1 / 143 P2 exchanges, 554 FAA4 releases, 49 re-dresses that stay
  collectable, 128 repeat hits, 137 family stops (6E32/6E5E/6E8A) and the seeded
  callback stop; every pickup, link and global byte outside the printed fields is
  checked. 115 instructions, all new and native (244 executed in all).
- Fresh hooked replay of frames 0..1066 with independent unhooked endpoint
  (report in `re/pickup_hit_validation.json`): both ordinary hits (780 on pickup
  54, 980 on pickup 55) are 6D22 conversions of P1's link 53; all 62 hit-pickup
  walks, including the releases at 810 and 1010, match natively one walk at a
  time and chain exactly. At 823 the unsupported hit7910 path resets link 53 to
  dormant, so the exchange path is compared only by restricted cases. Every
  earlier comparison and bound reproduces; release/sanitize reuse the capture
  (thirteen matched comparisons each).
- Mixed `[1066,1100)`: the session-035 capture reused with all rebuilt presets.
- **217 Python tests, zero skips; 46/46 CTests per preset**; builds warning-free.
  29 regressions, every earlier pair/setup variant, the pickup service and the
  context probe pass.
- Coverage: 564 new classified bytes; 131 bounded mappings plus four partial /
  144 indexed plus four setup fragments; 115 new executed instructions (2,073
  cumulative); fresh twenty-four-corpus union 1,715, or 1,724 with nine writer
  instructions.
- Failures: none in recorded runs. Harness, corpus and comparator corrections
  preceded any recorded comparison; session 043's expected 980 exchange was
  refuted by the capture. A separate user BizHawk session was running and left
  untouched; the external tree's owner added one untracked note during the pass.
- Not rerun: eight other component corpora (actions through score), debug/release
  runs of the eight sanitized corpora, a fresh mixed capture, other captures,
  whole-movie survey and SDL3 availability. No pushes/uploads.

Evidence: `re/pickup_hit_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0042-pickup-hit]],
[[08_Sessions/2026-10-18-044-pickup-hit]]. TASK-0010 remains in progress.
Next was hit7910, the fruit delivery. **Native playability: none.**

## Historical: session 2026-10-18-043 — gated pairs and the `[68C4,68D4)` setup step

- **8,941 restricted original/native `[68C4,68D4)` cases per debug/release/sanitize**
  pass: every stack depth with all gates open (the original stops at FA1E after
  each of 0..7 pops), all sixteen gate combinations with both pop orders, wrapped
  P2 origins, varied and unrepresentable residue. Native creates 6,269 cases
  byte-identically and otherwise rejects at the first failing pop (1,272
  exhausted, 1,400 unknown inheritance). 110 instructions, all new and native.
- Fresh hooked replay of frames 0..1066 with independent unhooked endpoint
  (report in `re/setup_pairs_validation.json`): frame 629's gated step returns at
  once from all four initializers (gates zero, A5 = FF0690), with exactly four
  return pushes, no F9E2 call and the 52-entry free stack unchanged; matched
  natively. No open path runs and no F9E2 call returns into them anywhere in
  [0,1066); the gates are zero at 1066. All earlier comparisons and bounds
  reproduce; release/sanitize reuse the capture (twelve matched comparisons each).
- Mixed `[1066,1100)`: the session-035 capture reused with all rebuilt presets.
- **216 Python tests, zero skips; 46/46 CTests per preset**; builds warning-free.
  29 regressions, every earlier pair/setup variant, the pickup service and the
  context probe pass.
- Coverage: 512 new classified bytes; 124 bounded mappings plus four partial /
  137 indexed plus four setup fragments; 110 new executed instructions (1,958
  cumulative); fresh twenty-three-corpus union 1,600, or 1,609 with nine writer
  instructions.
- Failures: none in recorded runs. One sign-conversion warning and one test
  variable-name clash were corrected before any comparison. A separate user
  BizHawk session was running and was left untouched.
- Not rerun: eight other component corpora (actions through score), debug/release
  runs of the eight sanitized corpora, a fresh mixed capture, other captures,
  whole-movie survey and SDL3 availability. No pushes/uploads.

Evidence: `re/setup_pairs_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0041-gated-pairs]],
[[08_Sessions/2026-10-18-043-gated-pairs]]. TASK-0010 remains in progress.
Next the 6C00 pickup hit for ordinary kinds. **Native playability: none.**

## Historical: session 2026-10-12-042 — setup message, 6EF0 gate, pickup service

- **4,717 restricted original/native `[68BC,68C4)` cases per debug/release/sanitize**
  match exactly: every priority byte against both messages, every kind count, all
  gate words and wrapping rows/tilemaps; 1,879 open-6EF0 cases reject natively.
  73 instructions, all new (CB9A's 32 research-only rendering; VDP writes sunk
  and sequence-checked).
- **136,848 restricted 6BD6 pickup-service cases per preset** match, all 9
  instructions; hits stop at 6C00 and reject natively.
- Fresh hooked replay of frames 0..1066 with independent unhooked endpoint
  (report in `re/setup_message_validation.json`): frame 629 selects and shows
  MIX THOSE FRUIT (+53 0 → 64) with exactly four RAM writes and 29 reported VDP
  writes (VRAM E00E); 6EF0 returns at once. Native matches every field. All
  earlier comparisons and bounds reproduce; release/sanitize reuse the capture.
- Mixed `[1066,1100)`: the session-035 capture reused with all rebuilt presets.
- **215 Python tests, zero skips; 46/46 CTests per preset**; builds warning-free.
  29 regressions and the context probe pass.
- Coverage: 373 new classified bytes; 120 bounded mappings plus four partial /
  133 indexed plus three setup fragments; 82 new executed instructions (1,848
  cumulative); fresh twenty-two-corpus union 1,490, or 1,499 with nine writer
  instructions.
- Failures, all resolved: the first fresh capture's message write check counted
  the real system stack (FF00xx) as message writes; it now excludes a window
  below the fragment's SP, the saved artifacts revalidated offline and a final
  capture used final sources. Harness/comparator corrections preceded any
  recorded comparison. A separate user BizHawk session was running and was left
  untouched.
- Not rerun: eight other component corpora, debug/release runs of the eight
  sanitized corpora, a fresh mixed capture, other captures, whole-movie survey
  and SDL3 availability. No pushes/uploads.

Evidence: `re/setup_message_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0040-setup-message]],
[[08_Sessions/2026-10-12-042-setup-message]]. TASK-0010 remains in progress.
Next the four gated pair initializers from 68C4. **Native playability: none.**

## Historical: session 2026-10-12-041 — pickups, control links and setup tail

- **8,820 restricted original/native `[68A4,68BC)` cases per debug/release/sanitize**
  pass: 0..16 pickups with every frame family, the original stopping at FA1E
  after each of 0..17 pops; native creates 5,290 tails byte-identically and
  rejects 1,833 as exhausted and 1,697 as unknown inheritance. 106 successful
  instructions, 92 new. The prefix (8,748), 783A (8,746) and pair (8,714 each)
  corpora rerun identically in every preset.
- Fresh hooked replay of frames 0..1066 with independent unhooked endpoint
  (report in `re/setup_tail_validation.json`): the ordinary tail at 629 makes
  pickups 55/54 and links 53/52 as one exact 153-write block beside the 216-write
  prefix block. Native builds the tail from the 68A4-entry stack, matches 146
  walks and **rejects at frame 780, the first unsupported 6C00 pickup hit** (which
  also turns link 53 into the trail emitter); pickup 55 is hit at 980. All other
  bounds reproduce; twelve followed slots equal the 1066 seed. Release/sanitize
  reuse the capture.
- Mixed `[1066,1100)`: the session-035 capture reused with all rebuilt presets.
- **214 Python tests, zero skips; 46/46 CTests per preset**; builds warning-free.
  29 regressions and the mixed-pool context probe pass.
- Coverage: 364 new classified bytes; 118 bounded mappings plus two partial / 129
  indexed plus two setup fragments; 92 new executed instructions (1,766
  cumulative); fresh twenty-corpus union 1,408, or 1,417 with nine writer
  instructions.
- Failures, all resolved: the first fresh capture read 6AF0's final object
  after A6 was restored; offline diagnosis then exposed MULU.W's D2 upper-word
  effect; both are encoded and a final capture used the final sources. Harness,
  corpus and test mistakes were corrected without native changes.
- Not rerun: eight other component corpora, debug/release runs of the eight
  sanitized corpora, a fresh mixed capture, other captures, whole-movie survey
  and SDL3 availability. No pushes/uploads.

Evidence: `re/setup_tail_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0039-setup-tail]],
[[08_Sessions/2026-10-12-041-setup-tail]]. TASK-0010 remains in progress. Next
7DB8 and 6EF0 from 68BC. **Native playability: none.**

## Historical: session 2026-10-12-040 — dormant initializers and setup prefix

- **8,748 restricted original/native `[6886,68A4)` cases per debug/release/sanitize**
  pass: the original stops at FA1E after each of 0..11 pops; native creates the
  4,625 representable prefixes byte-identically and rejects 1,745 as exhausted
  and 2,378 as unknown inheritance. 131 successful instructions, 15 new (the
  fragment plus 6EC8/6EDC). The 783A, 7772, 7C26 and 7B9C corpora rerun
  identically in every preset.
- Fresh hooked replay of frames 0..1066 with independent unhooked endpoint
  (report in `re/setup_prefix_validation.json`): one ordinary prefix at frame
  629 pops 67..56 in order as one exact 216-write block; native builds the whole
  prefix from the 6886-entry stack and matches all twelve members and the
  FF31B4/FF31B8/FF31C0 identities. Dormant slot 66 matches 432 inactive walks.
  Dormant slot 67 matches 219 walks, then **unsupported 7AD6 copies slot 47 into
  it at frame 853** (213 original-only walks). The 783A bound at frame 823 and
  every other retained slot reproduce; eleven followed slots equal the 1066
  seed. Release/sanitize reuse this capture.
- Mixed `[1066,1100)`: the session-035 capture reused with all rebuilt presets.
- **212 Python tests, zero skips; 46/46 CTests per preset**; builds warning-free.
  29 regressions and the mixed-pool context probe pass.
- Coverage: 70 new classified bytes; 113 bounded mappings plus two partial / 124
  indexed plus one setup fragment; 15 new executed instructions (1,674
  cumulative); fresh nineteen-corpus union 1,316, or 1,325 with nine writer
  instructions.
- Failures, all resolved: the restricted harness first omitted F9E2's frame
  low byte from the dormant write set and then hit the default per-call budget;
  test mistakes were corrected without native changes; the previous handoff's
  "fourteen pops" was corrected to twelve.
- Not rerun: eight other component corpora, debug/release runs of the eight
  sanitized corpora, a fresh mixed capture (tool unchanged), other captures,
  whole-movie survey and SDL3 availability. No pushes/uploads.

Evidence: `re/setup_prefix_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0038-setup-prefix]],
[[08_Sessions/2026-10-12-040-setup-prefix]]. TASK-0010 remains in progress. Next
extend the prefix through 68BC (6A94, 6EB6 ×2). **Native playability: none.**

## Historical: session 2026-10-12-039 — 783A collision quad initializer

- **8,746 restricted original/native 783A cases per debug/release/sanitize**
  pass: the original creates 4,542 quads and stops at FA1E after 0/1/2/3 pops in
  1,058/1,062/1,054/1,030 cases; native creates the 2,592 representable quads
  byte-identically and rejects 3,372 as exhausted and 2,782 as unknown
  inheritance. 45 successful instructions, 31 new. The 7772, 7C26 and 7B9C
  corpora (8,714 each) rerun identically in every preset.
- Fresh hooked replay of frames 0..1066 with independent unhooked endpoint
  (`local/generated/pair-initializer-capture/`, report in
  `re/collision_quad_validation.json`): 783A runs once (frame 629, caller 6898,
  A5 = FF0690, slots 63..60) with an exact 65-write block in a complete frame-629
  audit beside 7772 (43), 7B9C (40) and 7C26 (38). Native matches the quad's
  initialization and its first 189 retained walks, then rejects at frame 823,
  the first of **nine ordinary 7910 hits (823..831)** from the slot-63 probe.
  All ten retained slots continue in the original through 432 walks and equal
  the 1066 mixed seed. Release/sanitize reuse this capture.
- Mixed `[1066,1100)`: the session-035 fresh capture (tool unchanged) reused with
  all rebuilt presets; 633 records plus the anchor and the same output hash
  (`c6167d3a…`) as session 036.
- **209 Python tests, zero skips; 46/46 CTests per preset**; builds warning-free.
  29 regressions pass (six component corpora and the P1 fixture per preset,
  eight sanitized corpora); the mixed-pool context probe passes.
- Coverage: 180 new classified bytes; 111 bounded mappings plus two partial /
  122 indexed; 31 new executed instructions (1,659 cumulative); fresh
  eighteen-corpus union 1,301, or 1,310 with nine writer instructions.
- Failures, all resolved or bounded: the first fresh capture stopped on the
  unexpected ordinary 7910 hits; native comparison is now bounded at the first
  hit, the saved artifacts revalidated offline and a final fresh capture used
  the final sources. A first ad hoc regression runner omitted `--rom` flags and
  was replaced by the session-036 script; a comment-only header edit made build
  provenance stale, so every preset was rebuilt and every comparison rerun; new
  test goldens were corrected without native changes.
- Not rerun: eight other component corpora, debug/release runs of the eight
  sanitized corpora, a fresh mixed capture (tool unchanged), other captures,
  whole-movie survey and SDL3 availability. No pushes/uploads.

Evidence: `re/collision_quad_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0037-collision-quad]],
[[08_Sessions/2026-10-12-039-collision-quad]]. TASK-0010 remains in progress.
Next the 6EC8/6EDC dormant initializers and the native `[6886,68A4)` prefix.
Hit7910, callback79B6, 7AD6, overlap-hit FF31C0 readers and gate producers
remain unsupported. **Native playability: none.**

## Historical: session 2026-10-05-036 — 7772 rising pair initializer

- **8,714 restricted original/native 7772 cases per debug/release/sanitize**
  pass with the shared outcome split; 41 successful instructions, 27 new. A5 is
  preserved and stored, A4 left on the first member. 7C26 and 7B9C corpora rerun
  identically in every preset.
- Fresh hooked replay of frames 0..1066 with independent unhooked endpoint
  (`local/generated/pair-initializer-capture/run-7hufk1gg/report.json`): 7772 runs once (frame 629, caller 6898, A5 = FF0690, slots 65/64)
  with an exact 43-write block in a complete frame-629 audit alongside 7B9C (40)
  and 7C26 (38). Six retained slots survive 33 allocations, 31 releases and 432
  walks; 2,592 native updates match with zero observed gates and the 1066 states
  equal the mixed seed. Write traces complete in 435/436 frames. Release/sanitize
  reuse this capture.
- Mixed `[1066,1100)`: the session-035 fresh capture (tool unchanged) reused with
  all rebuilt presets; 633 records plus the anchor and the same output hash.
- **208 Python tests, zero skips; 46/46 CTests per preset**; builds warning-free.
  29 regressions pass (six component corpora and the P1 fixture per preset,
  eight sanitized corpora).
- Coverage: 150 new classified bytes; 110 bounded mappings plus two partial /
  121 indexed; 27 new executed instructions (1,628 cumulative); fresh
  seventeen-corpus union 1,270, or 1,279 with nine writer instructions.
- Failures, all resolved: the first fresh capture's continuity audit applied the
  7CA4 writer table to the 7808 slots; per-variant writer tables were added, the
  saved artifacts revalidated, and a final fresh capture used final sources. Two
  new-test mistakes were corrected without native changes.
- Not rerun: eight other component corpora, debug/release runs of the eight
  sanitized corpora, a fresh mixed capture (tool unchanged), other captures,
  whole-movie survey and SDL3 availability. No pushes/uploads.

Evidence: `re/rising_pair_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0036-rising-pair]],
[[08_Sessions/2026-10-05-036-rising-pair]]. TASK-0010 remains in progress.
Next the 783A four-object initializer. callback79B6, 7AD6, overlap-hit FF31C0
readers, gate producers and hit7910 remain unsupported. **Native playability: none.**

## Historical: session 2026-10-05-035 — 7C26 gated-visibility pair initializer

- **8,714 restricted original/native 7C26 cases per debug/release/sanitize**
  pass: 3,989 identical pairs, 2,491 exhaustion and 2,234 unrepresented-
  inheritance rejections. 35 successful instructions execute, 21 new; FF31C0 is
  read-only in that mode and unchanged. The 7B9C corpus reruns identically.
- Fresh hooked replay of frames 0..1066 with independent unhooked endpoint
  (`local/generated/pair-initializer-capture/run-rgs3r3w9/report.json`): 65 F9E2 and 32 F994 calls; 7B9C and 7C26 at frames 156 and 629,
  with complete exact write audits (40 and 38 writes each). The frame-156 7C26
  run spans 156–157 and contains one level-6 VBlank exception frame at 7C50,
  recognized by its exact shape. Slots 59/58/57/56 survive 33 allocations,
  31 releases and 432 walks; 1,728 native updates match with zero observed
  gates, and the 1066 states equal the mixed seed. Write traces complete in
  435/436 frames (632 dropped). Release/sanitize reuse this capture.
- Fresh `[1066,1100)` mixed capture (`local/generated/mixed-session/run-q_wuylbz/report.json`) with the tightened private adapter
  and independent unhooked replay: **633 records plus the FF31C0 anchor** match
  every preset; output SHA-256 `c6167d3ae56ed8f1b6b18ec594311a40e564268009d64daff6b06206884176b2` is unchanged from session 034.
- **207 Python tests, zero skips; 46/46 CTests per preset**; builds warning-free.
  29 regressions pass: return-only, collision, table, private, trail, reversal
  and the 390-call P1 fixture per preset, plus eight sanitized corpora.
- Coverage: 126 new classified bytes; 109 bounded mappings plus two partial /
  120 indexed; 21 new executed instructions (1,601 cumulative); fresh
  sixteen-corpus union 1,243, or 1,252 with nine writer instructions.
- Failures, all resolved: the first fresh capture rejected the frame-156 7C26
  block because the VBlank exception frame is reported at a 7C26 PC; the saved
  artifacts revalidated after the fix and a final fresh capture used final
  sources. A comparator off-by-one and three new-test mistakes were fixed before
  recorded runs.
- Not rerun: eight other component corpora, debug/release runs of the eight
  sanitized corpora, other historical/controlled captures, whole-movie survey and
  SDL3 availability. No pushes/uploads.

Evidence: `re/visibility_pair_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0035-visibility-pair]],
[[08_Sessions/2026-10-05-035-visibility-pair]]. TASK-0010 remains in progress.
Next the 7772 rising pair. callback79B6, 7AD6, overlap-hit FF31C0 readers, gate
producers and hit7910 remain unsupported. **Native playability: none.**

## Historical: session 2026-10-05-034 — F9E2 allocation and 7B9C pair initializer

- **8,714 restricted original/native pair cases per debug/release/sanitize**
  pass: 3,989 byte-identical pairs, 2,491 exhaustion cases (original stops at
  FA1E after 0 or 1 pops; native allocates nothing) and 2,234 unrepresented
  inheritance cases (original retains residue; native rejects). All 37
  successful instructions execute; FA1E..FA30 never does. Closed graph and eight
  GNU register-form checks pass; GNU cannot decode the immediate/absolute forms.
- Fresh hooked replay of frames 0..1066 with independent unhooked endpoint
  (`local/generated/pair-initializer-capture/run-r781581b/report.json`): 65 F9E2 calls (25 sites, one frame crossing) and 32 F994 calls
  verified; two ordinary 7B9C runs (frames 156, 629) with complete exact
  40-write audits and native matches. The frame-629 pair (slots 59/58) survives
  33 allocations/31 releases, 432 walks and 864 updates to equal the 1066 seed;
  FF31C0 constant. Write traces complete in 435/436 frames (632 dropped).
  Debug/release/sanitize reuse this capture with the final builds.
- Fresh `[1066,1100)` mixed capture (`local/generated/mixed-session/run-wkefr83n/report.json`) and independent unhooked replay:
  **633 ordered records plus the FF31C0 anchor** per call match every preset;
  zero FF31C0 writes, edits, drops or overflow.
- **205 Python tests, zero skips; 46/46 CTests per preset** pass. Builds
  warning-free. Tests cover LIFO order, inheritance, exhaustion at both pops,
  unknown/released residue, anchor rollback, transport limits, a collision
  context with the anchor header, and synthetic evidence tampering.
- Return-only 286,848; collision 478,345; table 406,634; private 277,232; trail
  209,082; reversal 203,586 cases and the 390-call P1 fixture pass per preset.
  Eight sanitized corpora pass: input 1,024; banner 66,880; presentation
  347,320; actor 152,093; dispatch 138,149; airborne 415,940; movement 282,233;
  terrain 614,436.
- Coverage: 216 new classified bytes, two bounded mappings (108 plus two partial
  / 119 indexed), 37 new executed instructions (1,580 cumulative); fresh
  fifteen-corpus union 1,222, or 1,231 with nine writer instructions.
- Failures, all resolved: the first anchored mixed capture failed natively
  because the transport parsed collision context only for exactly 13 header
  fields; fixed, tested and recaptured. The first regression batch was stopped
  and rerun on final builds. A synthetic test model was corrected.
- Not rerun: eight other component corpora (actions through score), debug/
  release runs of the eight sanitized corpora, other historical/controlled
  captures, whole-movie survey and SDL3 availability. No pushes/uploads.

Evidence: `re/pair_initializer_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0034-pair-initializer]],
[[08_Sessions/2026-10-05-034-pair-initializer]]. TASK-0010 remains in progress.
Next the 7C26 private-pair initializer. callback79B6, 7AD6, overlap-hit FF31C0
readers and hit7910 remain unsupported. **Native playability: none.**

## Historical: session 2026-10-05-033 — retained return-only objects

- **286,848 original/native cases per debug/release/sanitize** pass; all 42
  supported successful instructions execute. Existing 67-instruction static
  graph and four selected GNU checks pass. Invoked null callbacks reject.
- Final fresh ordinary capture and independent unhooked replay: **633 ordered
  records** match in every preset, comprising 565 spawn/update/release events
  plus 68 inactive observations. Added active work: 170 return-only updates.
  Full free order/RNG, 34 banners, two sounds and all prior object states match.
  Zero edits, drops or overflow; zero external reservations in this interval.
- All seven objects retain fields and identities. Their 271 writes comprise
  101 animation writes and 170 zero render clears; dormant slots have none.
  Exact call order, stacks, owner registers, unknown fields, extra invocations
  and complete write evidence are checked.
- **198 Python tests, zero skips; 46/46 CTests per preset** pass. Includes
  dormant-versus-free occupancy, generations, allocation exhaustion/order,
  callback and evidence rejection, and late whole-session rollback. Builds
  warning-free; no native/reference mismatch or test failure.
- Collision 478,345; table 406,634; private 277,232; trail 209,082; reversal
  203,586 cases and older 390-call P1 fixtures pass per preset. Table writer
  research reruns 131,422 cases. Eight additional sanitized corpora pass:
  input 1,024; banner 66,880; presentation 347,320; actor 152,093; dispatch
  138,149; airborne 415,940; movement 282,233; terrain 614,436.
- No added original function/instruction/byte classification. Fresh fourteen-
  corpus union 1,185 plus nine writer instructions; cumulative scope stays 1,543.
- A local report summary was attempted before two comparison processes finished;
  rerun successfully after completion. This did not affect test/capture results.
- Not rerun: eight other component corpora, other historical/controlled captures,
  whole-movie survey and SDL3 availability. Original inputs and the external
  installation are preserved. No pushes/uploads.

Evidence: `re/return_only_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0033-return-only-objects]],
[[08_Sessions/2026-10-05-033-return-only-objects]]. TASK-0010 remains in progress.
Next F9E2 allocation and 7B9C pair initialization. callback79B6/hit7910 remain
unsupported. **Native playability: none.**

## Historical: session 2026-10-05-032 — retained collision miss service

- **478,345 original/native comparisons per debug/release/sanitize** pass:
  341,497 overlap, 66,376 service and 70,472 scheduled cases. All 28 new
  instructions execute. ROM hash/decode, closed graph and four GNU checks pass.
  Hit7910 stops before execution; native hits, callbacks and missing P2 reject.
- Fresh ordinary movie plus independent unhooked replay; **34 collision updates
  and 395 ordered pool events** match in every preset, including full free
  order/RNG, 34 banners and two sounds. Seven reservations remain. Zero edits,
  drops or overflow; 32 X misses and two Y-only misses checked at instruction,
  register, stack and return boundaries. Native playability remains none.
- **68 P1 tracking writes** match the known wrapper sites. Mask=03FF, gate=0 and
  P2 tracking=0 have no writes, including transients. Native P1 tracking feeds
  collision directly; P2/configuration producers remain outside scope.
- **196 Python tests, zero skips; 44/44 CTests per preset** pass. Tests include
  inclusive/overflow arithmetic, full-word gates, consumed-input boundaries,
  sentinel tracking and rollback after earlier pool/P1/allocation/RNG work.
- Table 406,634, private 277,232, trail 209,082, reversal 203,586 cases per preset
  and older 390-call P1 fixtures pass. Table research writer audit reruns 131,422
  cases. Eight more sanitized corpora pass: input 1,024; banner 66,880;
  presentation 347,320; actor 152,093; dispatch 138,149; airborne 415,940;
  movement 282,233; terrain 614,436. Final builds warning-free.
- Fresh thirteen-corpus union 1,185 plus nine research writer instructions;
  cumulative 1,543 includes historical tests not rerun. One bounded helper and
  one partial service promote 96 preclassified bytes. Totals: 106 bounded plus
  two partial / 117 indexed; byte classification unchanged.
- Initial capture validation incorrectly required all misses to end at X;
  fixed the validator and performed a fresh capture/unhooked replay. Native
  arithmetic needed no correction; no native/reference semantic mismatch.
- Not rerun: eight other component corpora, other historical/controlled captures,
  whole-movie survey and SDL3 availability. callback79B6 and collision-hit7910
  remain unsupported. External sources/runtime and original inputs are unchanged.

Evidence: `re/collision_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0032-collision-miss]],
[[08_Sessions/2026-10-05-032-collision-miss]]. TASK-0010 remains in progress.
Next replace the seven return-only presentation/occupancy reservations, including
inactive occupied slots. **Native playability: none.**

## Historical: session 2026-10-05-031 — retained table motion

- **406,634 original/native table cases per debug/release/sanitize** pass: every
  countdown/toggle/delta word, all 24 cursor positions, both directions, wrap,
  count+1 loops through 65,536, presentation and explicit rejected boundaries.
  All nineteen handler instructions execute; primary hash/closed graph and four
  selected GNU checks pass. Immediate MOVE.W is not GNU-corroborated.
- **131,422 research writer-fragment cases** per comparator run pass against
  authored arithmetic, executing all nine fragment instructions. This does not
  implement callback79B6 or the complete FF31BC producer.
- Fresh ordinary movie capture plus independent unhooked replay; final binaries
  revalidate saved evidence in every preset. **34 table updates / 361 pool events**
  match, plus 34 P1/emitter calls, 136 trail/twelve reversal/136 private updates,
  nine allocations/releases, full free order/RNG, 34 banners and two sounds.
  No edits, drops or overflow. Eight external reservations remain.
- FF31BC=0 / FF31BE=80 have no writes; producer prefix executes 34 times with
  FF31B0=0. Single-seed scope only; active producers remain unimplemented.
- **194 Python tests, zero skips; 42/42 CTests per preset** pass. Authored tests
  verify exact cycle/reversal goldens, retained count changes, malformed cursors,
  writer transients, missing inputs, budgets, callbacks and full-session rollback.
- Private 277,232, trail 209,082 and reversal 203,586 cases pass per preset.
  Eight sanitized regressions pass: input 1,024; banner 66,880; presentation
  347,320; actor 152,093; dispatch 138,149; airborne 415,940; movement 282,233;
  terrain 614,436. Older 390-call P1 fixture freshly matches in every preset.
- Fresh twelve-corpus union 1,157, plus nine research writer instructions;
  cumulative 1,515 includes historical corpora not rerun. One native mapping
  promotes 78 preclassified bytes; writers add 52 classified research bytes.
- Initial debug build caught a missing explicit `<optional>` include; fixed
  before final successful builds. No native/reference semantic mismatch. Final
  builds are warning-free; the external Genesis sources/runtime remain unchanged.
- Not rerun: eight other component corpora, other old/controlled captures,
  whole-movie handler survey and SDL3 availability. No game boot/render/audio or
  full-frame parity established. callback79B6 and collision-hit7910 stay unsupported.

Evidence: `re/table_motion_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0031-table-motion]],
[[08_Sessions/2026-10-05-031-table-motion]]. TASK-0010 remains in progress;
next bound 78EE no-hit collision and AC5E overlap context. **Native playability none.**

## Historical: session 2026-10-05-030 — private-object updates

- **277,232 original/native cases per preset** for 7808/7CA4; all twenty handler
  instructions execute. Full countdown/word-gate ranges, longword gate boundaries,
  wrap, equality stop, scheduled presentation and callback rejection pass.
- Fresh ordinary movie `[1066,1100)` plus independent unhooked replay; debug uses
  the fresh capture, release/sanitize revalidate saved evidence. **136 private
  updates and 327 ordered pool events** match per preset, along with 34 P1/emitter
  calls, 136 trail/twelve reversal updates, nine allocations/releases and full
  free-stack order. Four more objects are native; nine reservations remain.
- Three private gates are zero with zero writes throughout; transient writes
  reject. Their producers remain outside scope. Nonzero branches are restricted
  synthetic original execution, not ordinary or edited full-machine observations.
- **192 Python tests, zero skips; 40/40 CTests per debug/release/sanitize** pass.
  Authored tests check retained gate changes, malformed fields/evidence, missing
  context, budget/callback failures and rollback after earlier release/private work.
- Trail 209,082 and reversal 203,586 comparisons per preset pass. Eight additional
  sanitized corpora pass: input 1,024; banner 66,880; presentation 347,320;
  actor 152,093; dispatch 138,149; airborne 415,940; movement 282,233; terrain 614,436.
  Older P1/reversal fixture matches 390 calls freshly per preset, output unchanged.
- Fresh restricted union 1,138 instructions; cumulative 1,487 partly historical.
  Two native mappings promote 86 already classified bytes; no new byte coverage.
- Static primary hash/closed graph and four GNU checks pass. Initial missing
  executable registration and unsupported GNU MOVE.W checks were corrected before
  final runs. No native/reference semantic mismatch or final compiler warning.
  Project research harness rebuilt; external runtime unchanged.
- Not rerun: eight other corpora, other old/controlled captures, whole-movie
  survey, SDL3 availability. No native full-frame, rendering/audio or boot claim.

Evidence: `re/private_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0030-private-object-updates]],
[[08_Sessions/2026-10-05-030-private-object-updates]]. TASK-0010 stays in progress;
next reconstruct 7A88 table motion. **Native playability remains none.**

## Historical: session 2026-10-05-029 — retained mixed pool

- **34 retained P1/emitter calls per native preset**, with no per-call environment
  feeds. All 136 trail-particle updates (39 initial-live plus 97 newborn), twelve
  reversal updates, nine allocations/nine releases and 191 ordered pool events
  match; full free-stack order, owner state and RNG remain native.
- One final fresh ordinary movie capture `[1066,1100)` and independent unhooked
  replay agree on exposed endpoint state. Three native comparisons revalidate
  that same capture. Thirteen audited reservations omit private object state;
  collision-hit path, foreign allocations or occupancy changes reject evidence.
- 9,767 routine events / 52,895 native events; no drop/overflow. Separate cadence:
  102 conversions, 136 polls, 34 inactive timers, 214 scratch writes. Audited
  writes: 1,205 managed slots, 906 reserved slots and 27 free-stack.
- **190 Python tests, zero skips; 38/38 CTests per debug/release/sanitize.** Tests
  cover both facings, seeded particles, nontrivial free order, earlier/later
  births, release/reuse/generations and late whole-session rollback.
- **209,082 trail and 203,586 reversal original/native cases per preset** pass.
  Eight other sanitized regressions pass: input 1,024; banner 66,880;
  presentation 347,320; actor 152,093; dispatch 138,149; airborne 415,940;
  movement 282,233; terrain 614,436. Fresh union 1,118; historical cumulative 1,467.
- Older P1/reversal fixture matches 390 calls freshly in every native preset;
  native output unchanged. These runs reuse historical original evidence.
- Static audit: 260 code bytes / 67 instructions plus 48 table bytes; exact
  hashes, closed graph with explicit unsupported exit, primary decode and five
  GNU checks pass. No new native function or restricted-execution count claimed.
- No native/reference mismatch. Initial transport indentation warning corrected;
  final builds have no warnings. No reference runtime/harness rebuild.
- Not rerun: eight other corpora, other old/controlled captures, whole-movie
  survey, SDL3 availability. ROM/movie/worker and 104 runtime binaries preserved;
  no user GUI, Sonic or WL3PC changes; no uploads/pushes.

Evidence: `re/mixed_session_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0029-mixed-object-pool]],
[[08_Sessions/2026-10-05-029-mixed-object-pool]]. TASK-0010 stays in progress;
next reconstruct 7808/7CA4 private updates. Native playability remains none.

## Historical: session 2026-10-05-028 — trail allocator client

- **209,082 original/native cases per debug/release/sanitize**: emitter 69,638;
  scheduled emitter 69,766; particle 4,102; RNG 65,551; initializer 25. All 62
  new instructions execute. Primary hashes/closed graph and five GNU checks
  pass; GNU's absolute EOR.W limitation is recorded.
- One fresh ordinary movie capture `[1066,1100)` and independent unhooked replay
  agree on exposed endpoint state. Three fresh native comparisons reuse those
  artifacts: **34 retained emitter calls, eight spawns, sixteen RNG calls and
  97 newborn particle updates**. Four complete/four partial lifetimes; six
  next-frame and two same-frame births. Owner position/capacity remain per-call
  context; emitter, RNG and each particle's state persist natively.
- Capture validates 533 emitter writes, 64 RNG writes, 8,183 routine events and
  52,895 native events; no drops/overflow. New particles still execute the fixed
  handler and service after their release callback.
- **187 Python tests, zero skips; 36/36 CTests per preset.** Authored signed and
  wrap boundaries, late owner/capacity/callback rollback, retained sequence state
  and evidence rejection tests pass. No native/reference mismatch.
- Nine sanitized regressions pass: input 1,024; banner 66,880; reversal 203,586;
  presentation 347,320; actor 152,093; dispatch 138,149; airborne 415,940;
  movement 282,233; terrain 614,436. Fresh ten-corpus instruction union **1,118**;
  cumulative union **1,467** includes historical results.
- Previous P1/reversal fixture freshly matches 390 calls in each native preset,
  using saved original evidence, with unchanged native output. This remains
  separate from the new trail component; no mixed-world parity claim.
- Corrected discovery failures: wrong hook `registers` value type and incorrect
  inherited F76C instruction count. Failed attempts are not complete evidence.
- Not rerun: eight other corpora, other old/controlled captures, whole-movie
  survey or SDL3 availability. ROM/BK2/worker and all 104 runtime binaries retain
  their hashes. Owned workers closed; no external rebuild, GUI action or push.

Evidence: `re/trail_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0028-trail-allocator-client]],
[[08_Sessions/2026-10-05-028-trail-allocator-client]]. TASK-0010 remains in
progress. Next: bounded ordered mixed-object pool/session, seeded with existing
live particles. Native playability remains none.

## Historical: session 2026-10-05-027 — retained reversal session

- **390 one-seed wrappers per debug/release/sanitize**, 390 banners/twelve sound
  requests, one spawn/twelve effect updates/one release. Single fresh ordinary
  capture plus independent unhooked replay; current validation and fresh native
  runs in all three presets reuse that raw evidence. Zero per-call state feeds.
- Original cadence: 1,170 conversions, 1,560 polls, 390 inactive timers, 5,350
  scratch writes; 102,510 managed routine events and 610,828 native events with
  no overflow/drop. Twelve exact service returns and 82 owned-effect writes.
- Shared pool observations: 38 foreign allocations/36 releases; 47..53 real
  free pointers. The first report included the zero sentinel (48..54); current
  validation corrects the count from unchanged raw chunks and retains original
  source identity. Native outputs do not depend on that count and are unchanged.
- **203,586 reversal comparisons per preset**, all 119 declared component
  instructions; eight sanitized regressions: input 1,024, banner 66,880,
  dispatch 138,149, presentation 347,320, actor 152,093, airborne 415,940,
  movement 282,233, terrain 614,436. Fresh restricted union 1,054; historical
  cumulative union 1,403. New static context is not added to those counts.
- **184 Python tests, zero skips; 34/34 CTests per preset.** Both-facing
  birth/release, pool reuse/order, capacity/budget/owner failure and rollback,
  initial ownership and changed/unhashed/mismatched fixture guards pass.
- Three static context ranges/seven instructions and four GNU checks pass.
  No native/reference mismatch or final failure. No reference runtime rebuild.
- Not rerun: eight other component corpora, other old/controlled movie captures,
  whole-movie selector survey or SDL3 availability. Original ROM/movie/runtime
  are preserved; no user GUI, Sonic or WL3PC changes and no upload/push.

Evidence: `re/effect_session_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0027-retained-reversal-session]],
[[08_Sessions/2026-10-05-027-retained-reversal-session]]. TASK-0010 stays in
progress; next reconstruct the competing 6D8C allocator client and its spawned
object. Dedicated native P1 pool is not whole shared-pool parity. Native
playability remains none.

## Historical: session 2026-10-05-026 — banner and earlier session

- **66,880 banner comparisons per debug/release/sanitize**, identical outputs;
  all 25 native-scope and 46 reference-only rendering instructions execute.
  Original callees use a declared VDP write sink, not native pixel comparison.
- **367 earlier retained wrappers per native preset**, 367 banner requests and
  twelve sound requests, one initial seed and physical-only later rows. Release
  and sanitize each use fresh ordinary captures/unhooked replays; debug reuses
  the hash-verified release capture and reruns its evidence validation.
- Per early window: 1,101 conversions, 1,468 polls, 367 inactive timers and
  5,205 scratch writes (367 banner + 4,838 queries). No overflow/drops. Pinned
  state/resources reject hidden writers; unused FF33DE permits only its observed
  zero byte clear and zero snapshots. No general world-schedule claim.
- Later `[3100,3200)` session freshly rerun in debug: 100 wrappers/four sound
  requests and independent unhooked endpoint match; output digest unchanged.
- **181 Python tests, zero skips; 34/34 CTest targets in all presets.** Authored
  banner branches, arithmetic boundaries, transport rejection and late rollback
  pass. Failed-reference and tampered-artifact fixture checks reject as expected.
- Seven sanitized regressions: input 1,024; wrapper 138,149; presentation 347,320;
  actor 152,093; airborne 415,940; movement 282,233; terrain 614,436. Fresh union
  with banner: **935 instructions**. Cumulative 1,403 is partly historical.
- Primary decode/hash/closed graph and four GNU corroborations pass. The known
  GNU CPU-selection limitation remains. No native parity mismatch.
- Discovery failures: combined trace response exceeded transport size; final
  captures drain both streams per frame. Preliminary debug capture rejected an
  incorrect equal-SP assertion at 17AA0/63E2; static JSR and fresh hooks establish
  the four-byte push. The failed capture is not claimed as complete parity.
- Not rerun: nine other prior corpora, other old/controlled captures, whole-movie
  selector survey, SDL3 development availability. ROM/BK2/worker and all 104
  runtime binaries retain their hashes; external source/runtime remain untouched.

Evidence: `re/banner_session_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0026-level-banner-session]],
[[08_Sessions/2026-10-05-026-level-banner-session]]. TASK-0010 stays in progress;
next integrate owned reversal/effect state beyond frame 1067. Native playability
remains none.

## Historical: session 2026-10-05-025 — physical input and retained session

- **1,024 input comparisons per debug/release/sanitize**, every combined raw
  byte with four prior fills and all 54 instructions. Preserved control bytes
  and D1..A6 checked by restricted original execution.
- **100 one-seed movie wrappers per preset**, physical held sets only after the
  initial 32 fields/resources. Actor, scratch, tracking, input fields and four
  ordered sound requests match; identical native output hashes in all presets.
  Three independent unhooked runs match covered-state endpoints.
- Measured separately per window: 600 input conversions, 800 polls, 100 actor
  invocations and 100 inactive timer calls. All 892 scratch writes belong to
  P1's query; native write tracing rejects hidden changes to pinned parameters,
  gate, globals/mailbox/selector/transition and terrain collision data/addressing.
  All 108,064 native events are captured without overflow using per-frame drains.
- **179 Python tests, zero skips; 34/34 CTest targets per preset.** Authored
  session tests include both facings, jump press/hold/release, reversal, immediate
  landing/callback order, tracking wrap, rollback and unsupported/budget failures.
- Six fresh sanitized corpora: wrapper 138,149; presentation 347,320; actor
  152,093; airborne 415,940; movement 282,233; terrain 614,436. Fresh successful
  instruction union including conversion: 864. No final failure/mismatch.
- Static primary decode/closed graph/hash/transfer checks and three GNU checks
  pass. An initial extra GNU memory-BTST check failed; the probe now records
  that decoder limitation explicitly. Original 68000 execution covers all 54.
- Not rerun: nine other prior differential corpora, older movie/controlled
  captures, full selector survey and SDL3 availability. Historical union plus
  this new routine is 1,332 instructions, not a fresh full-corpus run.
- ROM/BK2/worker and all 104 frozen runtime binaries retain their hashes.
  Only project-owned research harness rebuilt; external runtime unchanged.

Evidence: `re/session_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0025-p1-session]],
[[08_Sessions/2026-10-05-025-p1-session]]. TASK-0010 remains in progress.
Native playability remains none; next extend the session by reconstructing the
intervening scratch writers in movie `[700,1067)`.

## Historical: session 2026-10-05-024 — secondary tally and score

- **328,916 comparisons per debug/release/sanitize preset**, identical output
  hashes, 20 authored goldens and all 72 scoped instructions. Groups: 313,556
  flat/state, 4,608 authored-terrain, 10,752 cataloged-terrain. Separate sweeps
  are not a full Cartesian proof. Scope adds 280 bytes / 71 instructions plus
  one previously rejected, already classified transfer.
- Five expected malformed/nonterminating cases reject without output in both
  transports. Invalid consumed decimal digits are research/native domain guards,
  not original-game validation. Native tests cover budget and late-service rollback.
- **Four controlled movie branches / eleven wrappers**: five tally sounds,
  three sample requests, six threshold advances; all outputs match. Four separate
  unhooked workers repeat identical RAM edits and neutral inputs and match the
  declared covered-state endpoints. These are not ordinary secondary-score hits.
- **174 Python tests, zero skips; 32/32 CTest targets per preset.** No final
  failures or original/native mismatches. Review tightened snapshot extent
  validation and added a negative test; affected captures/suites were rerun.
- Fourteen fresh sanitized prior corpora: 348,668 exit tally, 160,680 bonus,
  214,448 palette, 231,475 tally, 87,571 coasting, 306,528 transition, 138,149
  wrapper, 146,638 actions, 347,320 presentation, 152,093 actor, 203,586 reversal,
  415,940 airborne, 282,233 movement, 614,436 terrain. Fifteen-corpus successful
  instruction union: **1,278**, including six reference-only sound guards.
- Fresh replay regressions: 231 ordinary exit wrappers plus one controlled
  equality wrapper; 175 tally / five sounds; 191 ordinary / 72 input-branch
  wrappers; 17 transition actor / 17 timer; one coasting initializer / 16 calls;
  37 controlled palette wrappers and three controlled bonus wrappers. Independent
  unhooked checks pass. Full selector survey and old 507/92/24 captures not rerun.
- Static byte/transfer/closed-graph and four new GNU checks pass. Earlier decoder
  limits persist; no new limitation in this scope. ROM/BK2/worker and all 104
  frozen runtime binary hashes match. No external reference runtime rebuild.

Evidence: `re/score_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0024-secondary-score]],
[[08_Sessions/2026-10-05-024-secondary-score]]. TASK-0010 remains in progress;
native playability remains none. Next: bounded native P1 session/input scheduling.

## Historical: session 2026-10-03-023 — exit tally and deferred transition

- **348,668 original/native cases per debug/release/sanitize preset**, identical
  outputs, 22 independent goldens and all **31 successful new instructions**.
  Groups: 333,308 flat/state, 4,608 authored-terrain, 10,752 cataloged-terrain.
  Separate exhaustive countdown/remaining/direction/equality sweeps do not prove
  the full Cartesian state space. The extra 5166 branch is classified but its
  target 53F2 rejects; two Start variants reject in both transports without output.
- **231 ordinary continuous wrappers** at [4807,5038), 215 in 5132 and 16 in 5188,
  two sound requests, last-unit delay=60 at 4933, transition start 5021 and
  completion 5037. All native outputs and independent unhooked endpoint match.
- **One controlled equality/marker experiment**, with two explicit RAM edits at
  5037 and the unchanged input row. Marker clearing and completion match native;
  independent unhooked endpoint agrees. No overflow; no ordinary equality claim.
- **169 Python tests, zero skips; 30/30 CTest targets per preset.** Initial
  synthetic tracking-coordinate omission was corrected. Final suites pass;
  no original/native semantic mismatch. Runtime tests cover deferred sequencing,
  timer separation, marker equality, unsupported score/context failures and late
  service rollback. Trace negatives exercise nesting, missing boundaries/writes.
- Thirteen fresh sanitized regressions: **160,680 bonus, 214,448 palette,
  231,475 tally, 87,571 coasting, 306,528 transition, 138,149 wrapper, 146,638
  actions, 347,320 presentation, 152,093 actor, 203,586 reversal, 415,940 airborne,
  282,233 movement, 614,436 terrain**. Fourteen corpora visit **1,206 scoped
  successful instructions**, including six reference-only sound guards.
- Fresh prior movie/experiment regressions: 175 ordinary tally wrappers / five
  sounds; 17 transition actor / 17 timer; one coasting initializer / 16 calls;
  191 ordinary / 72 input-branch wrappers; 37 controlled palette wrappers;
  three controlled bonus wrappers. All independent unhooked endpoints match.
  Older 507 actor/presentation and 92 actor / 24 effect contracts were not rerun.
- Fresh complete-movie survey: **4,139 P1 calls/services, zero unregistered
  selector addresses**, only 12646 services, recorded unhooked baseline matches.
  This is selected-address discovery with zero native comparisons.
- Static byte/transfer/closed-graph checks and two new GNU checks (BSR/RTS) pass.
  Initial probe correctly rejected GNU's invalid JMP abs.l/CMP.W abs.l decoding
  at 5182/51B2. These limits are recorded, with primary decoding and original
  execution as evidence; inherited presentation BCHG limitation remains.

Pinned evidence: `re/exit_tally_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0023-exit-tally]],
[[08_Sessions/2026-10-03-023-exit-tally]]. ROM, BK2, worker and 104 runtime binary
hashes match. TASK-0010 stays in progress; native playability remains none.

## Historical: session 2026-10-03-022 — bonus table selection

Fresh results, distinct from historical checkpoints below:

- **160,680 original/native cases per debug/release/sanitize preset**, identical
  output hashes, sixteen goldens and all **43 new instructions** visited.
  Groups: 145,320 flat/state, 4,608 authored-terrain, 10,752 cataloged-terrain.
  Every cursor/source word, counts 1–11, sentinel prefixes, both handlers/facings,
  eligibility inputs, repeated calls and arithmetic boundaries are covered in
  separate sweeps; this is not an exhaustive Cartesian proof.
- Four malformed/nonterminating cases reject in each original/native transport:
  zero divisor, count beyond declared extent, scan escape and cyclic selection.
  No rejected row is published. Partial success at a negative sentinel is a
  separate successful path and is compared exactly.
- **Three controlled one-wrapper RAM/input experiments at 3403**: five writes,
  partial/reset success, and exhausted table. All modeled state and request/
  assignment order match native. Independent unhooked workers repeating each
  edit/input match all three declared endpoints. No overflow. These are not
  ordinary movie hits. Exploratory B+C+Start missed the branch; A+C+Start hits it.
- **164 Python tests, zero skips; 28/28 CTest targets per preset.** No final
  failures or original/native semantic mismatches. Authored tests cover cursor
  word wrap, zero/negative source values, missing contexts, full transaction
  rollback and continuous table/gate assertions. Trace negatives reject missing
  boundaries, wrong stack/flags/source/extents, unexpected writes and overflow.
- Fresh sanitized regressions: **214,448 palette, 231,475 tally, 87,571 coasting,
  306,528 transition, 138,149 wrapper, 146,638 actions, 347,320 presentation,
  152,093 actor, 203,586 reversal, 415,940 airborne, 282,233 movement and
  614,436 terrain**. Thirteen corpora visit **1,175 scoped instructions**,
  including six reference-only sound guards.
- Fresh movie regressions: **175 ordinary tally wrappers / five sound requests**,
  **17 transition actor / 17 timer calls**, **one coasting initializer / 16 calls**,
  **191 ordinary / 72 explicit input-branch wrappers**, and **37 controlled
  palette wrappers**. All independent unhooked endpoint checks pass. Older
  507 actor/presentation, 92 actor / 24 effect contracts and full survey were
  not rerun in this pass.
- Static exact bytes/transfers/closed graph and four new GNU checks pass.
  Inherited presentation BCHG limitation remains; no new decoder limitation.
  4770's other mode at 47BA is unsupported. ROM, BK2, 104 runtime binaries and
  worker hashes match the starting preservation audit.

Evidence: `re/bonus_validation.json`,
[[03_Reverse_Engineering/findings/FIND-0022-bonus-slots]],
[[08_Sessions/2026-10-03-022-bonus-slots]]. Table selection does not establish
object allocation, table-consumer/render/audio behavior or native frame parity.
TASK-0010 remains in progress. Native playability remains none.

## Historical: session 2026-10-03-021 — tally palette and deferred waits

Fresh results, distinct from historical checkpoints below:

- **214,448 original/native cases per debug/release/sanitize preset**, identical
  output hashes, sixteen authored goldens and all **56 new instructions** visited.
  Groups: 199,088 flat/state, 4,608 authored-terrain and 10,752 cataloged-terrain.
  Every raw color word appears in every slot; every direction word is tested for
  both handlers. This is not an exhaustive Cartesian state-space proof.
- **37 continuous P1 wrappers in two controlled RAM-edit experiments** at movie
  boundary 3403: one ready transition and one initial wait with a poisoned
  destination. Preparation, exact helper returns, retained fields, deferred 5204
  and deferred 5222 all match. Independent unhooked workers repeating identical
  edits/inputs match both covered-state endpoints. These are not ordinary-game hits.
- **Unedited movie regressions:** 175 tally wrappers / five sound requests /
  completion at 3577; 17 transition actor / 17 timer calls; one coasting
  initializer / 16 wrappers. All declared endpoints match independent replay.
- **159 Python tests, zero skips; 26/26 CTest targets per preset.** Initial test
  expectations/fixtures were corrected, and a stale-build-provenance attempt was
  rejected and rerun after rebuilding. Final runs pass; no original/native
  semantic mismatch. Trace negatives cover missing boundaries, stack/extent/bank,
  mutation, destination drift and overflow. Runtime tests cover full rollback.
- Fresh sanitized regressions: **231,475 tally, 87,571 coasting, 306,528 transition,
  138,149 wrapper, 146,638 actions, 347,320 presentation, 152,093 actor, 203,586
  reversal, 415,940 airborne, 282,233 movement and 614,436 terrain**. Twelve corpora
  visit **1,132 scoped instructions**, including six reference-only sound guards.
- Static pinned ranges/closed graph and four new GNU checks pass. Inherited
  presentation BCHG limitation remains; no additional decoder gap. 5266 remains
  an explicit rejected exit. Ordinary/branch 191/72, older 507/92/24 contracts
  and the full survey were not rerun this pass.

Exact hashes/builds/commands and ignored artifact paths:
`re/palette_validation.json`. Preservation audit verifies ROM, original BK2,
104 frozen runtime binaries and worker. No emulator enters native targets.
Palette consumer/rendering, world/P2 scheduling, audio playback and full native
playability remain unimplemented. TASK-0010 remains in progress.
See [[03_Reverse_Engineering/findings/FIND-0021-tally-palette]] and
[[08_Sessions/2026-10-03-021-tally-palette]].

## Session 2026-10-03-020 — bounded tally path

Fresh results, distinct from the historical checkpoints below:

- **231,475 original/native cases per debug/release/sanitize preset**, identical
  output hashes and nineteen authored goldens. All **48 new instructions** are
  visited. Groups: 216,115 flat/state cases, 4,608 authored-terrain and 10,752
  cataloged-terrain cases. Separate full word sweeps cover countdown, remaining
  and credit; other combinations are bounded, not a Cartesian proof.
- **175 continuous ordinary P1 wrappers at 3403–3577**, retaining native actor,
  service, tracking and mutable tally counters. Five sound requests and mode=3
  completion at 3577 match. Independent unhooked endpoint equality; no input,
  RAM, register or ROM edits. World scheduling/audio playback remain outside scope.
- **154 Python tests, zero skips; 24/24 CTest targets in every preset.** Authored
  tests check same-call branching, deferred completion, held Start, wrapped cap,
  continuity drift, unsupported branches and late-service rollback.
- Fresh sanitized regressions: **87,571 coasting, 306,528 transition, 138,149
  wrapper, 146,638 actions, 347,320 presentation, 152,093 actor, 203,586 reversal,
  415,940 airborne, 282,233 movement and 614,436 terrain**. Eleven corpora visit
  **1,076 scoped instructions**, including six research-only sound guards.
- Prior movie contracts rerun: one coasting initializer / 16 wrappers,
  17 transition actor / 17 timer calls and 191 ordinary / 72 input-branch wrappers.
  All declared endpoints match independent unhooked replay. Older 507/92/24
  windows and the complete survey were not rerun; do not sum overlapping scopes.
- Exact ROM ranges, CPU sentinels and closed graph pass with explicit rejected
  exits at 51D0/5266. Four new GNU checks pass. The inherited presentation BCHG
  limitation remains explicit; no additional secondary-decoder limitation.

No original/native mismatch, final failing check or skipped test. The new partial
handlers deliberately reject the nonzero palette and special allocation paths;
those rejections are tested behavior, not parity claims for unimplemented effects.
Reports, source/output hashes and preservation audit: `re/tally_validation.json`.
Movie report: `local/generated/tally-movie/run-0x1impxc/report.json`.
ROM/movie, all 104 runtime binaries and the worker remain unchanged.

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
```

Build/test/tally-compare also ran for release and sanitize. All ten previous
simulation corpora ran with `--rom --preset sanitize`. Evidence/limits:
[[03_Reverse_Engineering/findings/FIND-0020-tally-handler]],
[[08_Sessions/2026-10-03-020-tally-handler]]. TASK-0010 remains in progress;
native playability remains none.

## Historical: session 2026-10-02-019 — deferred coasting entry and handler

Fresh results, distinct from historical records below:

- **87,571 original/native cases per debug/release/sanitize preset**, identical
  output hashes, eleven goldens and all **eight new instructions** executed.
  Groups: 13,680 coasting/flat, 66,211 initializer, 2,304 authored terrain and
  5,376 cataloged terrain. Selector/first-frame/vertical words share a correlated
  exhaustive sweep; arithmetic/input combinations are bounded, not Cartesian.
- **One P1 initializer at frame 1742 and sixteen continuous wrappers at
  1743–1758**, with native actor/service/tracking retained across the boundary.
  Exact association, pending tail return and actual caller return are checked.
  Independent unhooked replay matches; no state/input/ROM edits. P2 initialization
  is retained as observation only. Other world-object effects remain outside scope.
- Fresh sanitized regressions: **306,528 transition, 138,149 wrapper, 146,638
  actions, 347,320 presentation, 152,093 actor, 203,586 reversal, 415,940 airborne,
  282,233 movement, 614,436 terrain**. Ten corpora visit **1,028 scoped instructions**,
  including six reference-only sound guards.
- Prior movie contracts pass freshly: **17 transition actor / 17 timer calls**,
  plus **191 ordinary / 72 input-branch wrappers** with intermediate checks.
  All declared endpoints match fresh unhooked replays. Older 507/92/24 windows
  and the complete movie survey were not rerun.
- **149 Python tests, zero skips; 22/22 CTest targets in every preset.** Tests
  verify deferred movement, retained fields/coordinates, context independence,
  budgets, unknown-service rollback, sequence drift and trace rejection.
- Exact range hashes and closed graph pass; three new supported GNU checks.
  Absolute-long JMP remains an explicit secondary-decoder limitation.

Reports/hashes: `re/coasting_validation.json`. New movie report:
`local/generated/coasting-movie/run-g7vzhcyq/report.json`. No final failures/skips
or original/native semantic mismatch. ROM/movie, all 104 runtime binaries and
the worker remain unchanged. No GUI changes, external rebuild, push or upload.

```sh
python3 -B tools/build_terrain_reference.py
python3 -B tools/project.py coasting-probe --disassemble
python3 -B tools/project.py build --preset debug
python3 -B tools/project.py coasting-compare --rom --preset debug
python3 -B tools/project.py test --rom --preset debug
python3 -B tools/project.py coasting-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py transition-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py dispatch-capture local/generated/capture-qb2htq3j/recording.json --preset debug
```

Build/coasting-compare/test also ran with release and sanitize. All nine prior
simulation corpora ran with `--rom --preset sanitize`. Evidence and limits:
[[03_Reverse_Engineering/findings/FIND-0019-coasting-handler]],
[[08_Sessions/2026-10-02-019-coasting-handler]]. TASK-0010 remains in progress;
native playability remains none.

## Historical: session 2026-10-02-018 — transition actors and timer

Fresh results, separate from the historical checkpoints below:

- **306,528 original/native cases in each debug/release/sanitize preset**, with
  identical output hashes, sixteen independent goldens and all 68 new instructions.
  Groups: 27,816 actor/flat boundaries, 263,352 timer, 4,608 authored terrain and
  10,752 cataloged terrain. Word timer sweeps and signed coasting bucket edges
  are covered; this is not an exhaustive Cartesian input space.
- **17 ordinary continuous actor-wrapper and 17 separate timer calls** from the
  unedited movie at [1516,1533), including immediate initializer tail, deferred
  wait handler, actual caller returns and completion at 1532. Fresh independent
  unhooked endpoint match. Palette consumption and world scheduling remain outside
  the comparison; shared external changes are explicit environment inputs.
- Fresh sanitized regressions: **138,149 wrapper, 146,638 actions, 347,320
  presentation, 152,093 actor, 203,586 reversal, 415,940 airborne, 282,233 movement,
  614,436 terrain**. Nine corpora visit **1,020 scoped instructions**, including
  six research-only sound guards. Prior wrapper movie contract rerun: **191
  ordinary / 72 input-branch calls**, each with intermediate checks and four
  independent unhooked matches. Older 507/92/24 windows and full survey not rerun.
- **144 Python tests, zero skips; 20/20 CTest targets in every preset.** Late
  unsupported-service rollback covers both initialization and completion; native
  tests also exercise mid-coast resource failure, fixed work budget, missing
  contexts, timer wrap and transport continuity/resource rejection.
- Static hashes and closed graph pass. Six new GNU checks corroborate supported
  instructions; the installed GNU decoder rejects absolute-long JMP/SUBQ. That
  limitation is explicit; primary decoding and original execution cover them.

Exact reports/hashes/logs: `re/transition_validation.json`. New movie report:
`local/generated/transition-movie/run-i6q8a7yy/report.json`; wrapper regression:
`local/generated/dispatch-movie/run-f8s_q4o3/report.json`. ROM/movie and all 104
runtime binaries plus worker remain unchanged. No final failures/skips or native/
original semantic mismatches. An initially ineffective authored terrain-failure
fixture and GNU decoder limitations are recorded in the session.

```sh
python3 -B tools/build_terrain_reference.py
python3 -B tools/project.py transition-probe --disassemble
python3 -B tools/project.py build --preset debug
python3 -B tools/project.py transition-compare --rom --preset debug
python3 -B tools/project.py test --rom --preset debug
python3 -B tools/project.py transition-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py dispatch-capture local/generated/capture-qb2htq3j/recording.json --preset debug
```

Build/transition-compare/test also run with release and sanitize. All eight prior
simulation corpora run with `--rom --preset sanitize`. Finding and limits:
[[03_Reverse_Engineering/findings/FIND-0018-actor-transition]]. TASK-0010 stays
in progress; native playability remains none.

## Historical: session 2026-10-02-017 — actor wrapper through return

Fresh results, not inherited historical counts:

- **138,149 original/native cases per debug/release/sanitize preset**, with
  identical output hashes, thirteen goldens and all fifteen new instructions.
  Groups: 135,585 wrapper boundaries, four callback-only, 768 authored terrain,
  1,792 cataloged terrain. Two unknown-selector cases reject in both programs.
- **191 ordinary wrapper calls and 72 explicitly branched input calls** pass,
  each with independent presentation and selected-handler boundary checks. Four
  fresh unhooked endpoint matches; no RAM/register/ROM edits. Whole wrapper
  means F8F6 through actual RTS, restricted to verified return-only +46 service.
  Actor/service/tracking coordinates persist; world context remains external.
- Fresh sanitized regressions: **146,638 actions, 347,320 presentation, 152,093
  actor, 203,586 reversal, 415,940 airborne, 282,233 movement, 614,436 terrain**.
  Eight corpora visit **952 scoped instructions**, including six reference-only
  sound guards. Fresh old movie contracts: **507 actor/presentation checks** and
  **92 actor / 24 effect updates**, each with independent unhooked replay.
- **139 Python tests, zero skips; 18/18 CTest targets in every preset.** Static
  original-68000/closed-graph checks and six new GNU checks pass. Tests include
  inactive/sentinel tracking, word wrap, both facings, same-call landing and
  rollback after action sample requests and reversal allocation.
- A fresh complete-movie survey observes **4,139 selected return-only services**
  and matches the recorded unhooked final baseline. **Discovery only, zero
  additional native comparisons.** Six other selected handler identities remain.

Exact reports/hashes/logs: `re/dispatch_validation.json`. Primary movie report:
`local/generated/dispatch-movie/run-zefqb8xw/report.json`. No final failures/skips
or native/original semantic mismatches. One manual landing golden, a caller-
return assumption and an import-order error were corrected and recorded in
[[08_Sessions/2026-10-02-017-actor-wrapper]]. ROM/movie, all 104 runtime binaries
and worker hashes remain unchanged. No GUI control, external rebuild, push/upload.

```sh
python3 -B tools/build_terrain_reference.py
python3 -B tools/project.py dispatch-probe --disassemble
python3 -B tools/project.py build --preset debug
python3 -B tools/project.py dispatch-compare --rom --preset debug
python3 -B tools/project.py test --rom --preset debug
python3 -B tools/project.py dispatch-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/genesis_movie_survey.py local/generated/capture-qb2htq3j/recording.json
```

Repeat build/dispatch-compare/test for release and sanitize; all seven earlier
simulation `*-compare --rom --preset sanitize` corpora were run. Older movie
commands and exact full recipes are retained in the session. Evidence/limits:
[[03_Reverse_Engineering/findings/FIND-0017-actor-wrapper]]. TASK-0010 is still
in progress; native playability remains none. The sections below are historical.

## Session 2026-10-02-016 — up/down actions

Fresh checks, distinct from historical results below:

- **146,638/146,638 original/native action cases per debug/release/Clang
  ASan+UBSan preset pass**, with identical output hashes, eighteen authored
  goldens and all **81 new instructions** visited. Groups: 139,936 handler,
  2,072 contextual presentation, 2,070 scheduled, 768 authored terrain and
  1,792 cataloged terrain. All interval/cooldown words, raw bytes, both facings,
  callback continuation, deferred jump and transactional failures are covered.
- **184 continuous actor calls + 184 presentation checks** pass from unchanged
  movie windows [1615,1690) and [3230,3339). Two explicit input branches add
  **72 actor calls + 72 presentation checks**, including one sample mailbox
  request and both hold-jump transitions. Zero memory/register/ROM edits.
  All four endpoints agree with independent unhooked workers. Shared world
  globals/mailbox/scratch/controls remain environment feeds, not native world
  computation. Input branches overlap source frames and are labeled separately.
- **Fresh sanitized regressions:** 203,586 reversal, 347,320 presentation,
  152,093 actor, 415,940 airborne, 282,233 movement, 614,436 terrain comparisons
  all pass. Seven corpora visit **937 scoped instructions**, including six
  reference-only sound guards.
- Both old movie contracts pass freshly: **507 actor + 507 presentation checks**,
  and **92 actor + 24 complete reversal-effect updates**, with unhooked endpoint
  agreement. Different/overlapping contracts are not unique whole native frames.
- **135 Python tests pass, zero skips; 17/17 CTest targets pass per preset.**
  Static graph/CPU checks pass, with five new short GNU corroborations. Prior
  decoder limitations remain explicitly excluded from corroboration claims.

`re/actions_validation.json` pins exact reports, outputs, logs and preservation
hashes. Final action capture: `local/generated/actions-movie/run-ee3uhda0/report.json`.
The original ROM/movie and all 104 runtime manifest binaries plus the worker
remain unchanged. No external rebuild, GUI operation, upload or push.

Early failed attempts are retained in the session: one hand-written golden
missed a second terrain-settle call (native/original already agreed); the proposed
movie window included unsupported 12646/AA50 and later reversal-allocation
contracts; the older actor rejection check still expected Down to fail and Up's
old message. Corrected exact contracts pass. **No final failures or skips** and
no native/original output mismatch. Audio consumption/playback and +46/world
services remain unimplemented. Native playability is none.

```sh
python3 -B tools/build_terrain_reference.py
python3 -B tools/project.py actions-probe --disassemble
python3 -B tools/project.py build --preset debug
python3 -B tools/project.py actions-compare --rom --preset debug
python3 -B tools/project.py build --preset release
python3 -B tools/project.py actions-compare --rom --preset release
python3 -B tools/project.py build --preset sanitize
python3 -B tools/project.py actions-compare --rom --preset sanitize
python3 -B tools/project.py test --rom --preset debug
ctest --preset release --output-on-failure
ctest --preset sanitize --output-on-failure
python3 -B tools/project.py reversal-compare --rom --preset sanitize
python3 -B tools/project.py presentation-compare --rom --preset sanitize
python3 -B tools/project.py actor-compare --rom --preset sanitize
python3 -B tools/project.py airborne-compare --rom --preset sanitize
python3 -B tools/project.py movement-compare --rom --preset sanitize
python3 -B tools/project.py terrain-compare --rom --preset sanitize
python3 -B tools/project.py actions-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py reversal-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py movie-actor-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py check-vault
python3 -B tools/project.py check-hygiene
```

Finding: [[03_Reverse_Engineering/findings/FIND-0016-up-down-actions]].
Handoff: [[08_Sessions/2026-10-02-016-up-down-actions]].

## Historical: session 2026-10-02-015 — fast reversal and owned effects

Freshly executed checks, distinct from historical results below:

- **203,586/203,586 original/native comparisons pass per debug, release and
  Clang ASan+UBSan preset**, with identical output hashes. Groups: 1,670 flat
  actor, 192 scheduled sequences, 197,372 effect cases, 768 authored terrain,
  3,584 cataloged terrain. Ten hand-calculated goldens and four exact exhaustion
  rejection checks pass per preset. All **119 new instructions** are visited,
  including both original active effect-dispatch fragments.
- **92/92 continuous actor calls and 24/24 effect updates pass** from ordinary
  unedited movie windows [1048,1090) and [2170,2220). Two allocation/release
  lifetimes and two sound requests agree. Fresh unhooked replay matches both
  declared endpoint hashes; trace overflow, missing phases, unexpected writes,
  ownership/stack errors and state reseeding are rejected.
- The old movie windows were rerun: **507/507 actor calls and 507/507 intermediate
  presentation checks pass** with independent unhooked endpoint agreement.
  Source windows overlap; these are separate comparison contracts, not sums of
  unique gameplay frames or proof of whole-frame native execution.
- **Fresh sanitized regressions pass:** 347,320 presentation, 152,093 actor,
  415,940 airborne, 282,233 movement and 614,436 terrain. Together with reversal,
  all **856 scoped original instruction addresses** are visited, including six
  research-only sound-selector guard instructions.
- **129 Python tests pass, zero skips; 16/16 CTest targets pass in all presets.**
  Native tests cover ownership, stale generations, LIFO reuse, double release,
  coordinate wrapping, same-call reversal/completion/jump and rollback after
  allocation. Transport/evidence checks enforce complete phases and continuity.
- The static graph and CPU sentinels pass. Five new reversal instructions and
  five prior scheduler instructions pass GNU corroboration. GNU's F9A0 absolute
  MOVE.L decoding limitation is recorded explicitly alongside the older BCHG
  limitation; neither unsupported decode is claimed as corroborated.

`re/reversal_validation.json` pins exact reports/hashes, corpus output hashes,
logs, build provenance and preservation checks. Final new movie report:
`local/generated/reversal-movie/run-llim31lv/report.json`. Old-window rerun:
`local/generated/movie-actor/run-0yo4xcu0/report.json`. All 104 external manifest
binaries, the separate worker, original ROM and user movie retain their hashes.
No native/original mismatch or final suite failure occurred. The initial compile
warning was fixed; a vault check made before creating the session note reported
its missing links, now resolved. No golden was changed to hide a mismatch.

Reproduction (explicitly build each native preset before its comparison):

```sh
python3 -B tools/build_terrain_reference.py
python3 -B tools/project.py reversal-probe --disassemble
python3 -B tools/project.py build --preset debug
python3 -B tools/project.py reversal-compare --rom --preset debug
python3 -B tools/project.py build --preset release
python3 -B tools/project.py reversal-compare --rom --preset release
python3 -B tools/project.py build --preset sanitize
python3 -B tools/project.py reversal-compare --rom --preset sanitize
python3 -B tools/project.py test --rom --preset debug
ctest --preset release --output-on-failure
ctest --preset sanitize --output-on-failure
python3 -B tools/project.py presentation-compare --rom --preset sanitize
python3 -B tools/project.py actor-compare --rom --preset sanitize
python3 -B tools/project.py airborne-compare --rom --preset sanitize
python3 -B tools/project.py movement-compare --rom --preset sanitize
python3 -B tools/project.py terrain-compare --rom --preset sanitize
python3 -B tools/project.py reversal-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py movie-actor-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py check-vault
python3 -B tools/project.py check-hygiene
```

The native effect store excludes other object competition and owner destruction.
Up/down actions, later +46 services, world scheduling, rendering and audio remain
unimplemented. A814 completion is authored/Musashi evidence; the selected ordinary
right reversal instead becomes airborne through terrain. **Native playability
remains none.** Finding:
[[03_Reverse_Engineering/findings/FIND-0015-fast-reversal]].
Handoff: [[08_Sessions/2026-10-02-015-fast-reversal]].

## Historical: session 2026-10-02-014 — presentation and continuous movie state

Fresh runs; historical counts below are not substituted for these checks.

- **123 Python tests pass, zero skips; 15/15 CTest targets pass** in debug,
  release and Clang ASan+UBSan. Tests include 24 independent presentation goldens,
  callback-before-handler sequences, target arrival versus callback invocation,
  inactive objects, zero reload wrap, unsupported callback rollback and evidence
  rejection for missing phases, stack/order/selector mismatch or state reseeding.
- **347,320/347,320 original/native cases pass in each preset** with identical
  native output hashes: 330,920 presentation, 2,256 scheduled flat, 2,496 authored
  varied terrain and 11,648 cataloged-terrain cases. All 90 new instructions are
  visited. Four exact unknown-callback rejection checks pass per preset.
- **507/507 continuous scheduled actor comparisons pass**, plus 507 intermediate
  presentation comparisons, over unedited movie windows [700,1067), [3100,3200)
  and [4360,4400). Eighteen state/scratch fields, ten callback observations and
  16 ordered sound requests are covered. A fresh unhooked worker matches all
  three hooked window-end covered-state hashes. No complete frame/audio parity.
- **Fresh sanitized regressions pass:** 152,093 actor, 415,940 airborne, 282,233
  movement and 614,436 terrain cases. Across five corpora all 737 scoped original
  instruction addresses are visited. The six sound-guard instructions remain
  research execution, not a native audio subsystem.
- The ordinary user-movie survey observes 4,139 active P1 calls and 16,840 selected
  trace events over 5,298 input rows. It rejects overflow and matches the earlier
  unhooked movie's covered-state hash at its end. This survey contributes zero
  native comparisons and locates still-unsupported action/allocation paths.

`re/presentation_validation.json` pins exact report paths, hashes, output hashes
and counts. Current finding: [[03_Reverse_Engineering/findings/FIND-0014-presentation-scheduler]].
All ROM/movie bytes are preserved; external runtime binaries are unchanged.
No native playability, sprite rendering, general animation asset interpretation,
+46 service, world scheduling or sound playback is claimed.

Reproduction (build each preset before its comparisons):

```sh
python3 -B tools/build_terrain_reference.py
python3 -B tools/project.py presentation-probe --disassemble
python3 -B tools/project.py build --preset debug
python3 -B tools/project.py presentation-compare --rom --preset debug
python3 -B tools/project.py build --preset release
python3 -B tools/project.py presentation-compare --rom --preset release
python3 -B tools/project.py build --preset sanitize
python3 -B tools/project.py presentation-compare --rom --preset sanitize
python3 -B tools/project.py test --rom --preset debug
ctest --preset release --output-on-failure
ctest --preset sanitize --output-on-failure
python3 -B tools/project.py actor-compare --rom --preset sanitize
python3 -B tools/project.py airborne-compare --rom --preset sanitize
python3 -B tools/project.py movement-compare --rom --preset sanitize
python3 -B tools/project.py terrain-compare --rom --preset sanitize
python3 -B tools/project.py movie-actor-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/genesis_movie_survey.py local/generated/capture-qb2htq3j/recording.json
```

The first static probe rejected an unsupported instruction because installed
`m68k.gnu` rejects immediate BCHG 086e. The final probe records that limitation,
uses five other GNU corroborations and preserves the independent decoder and
original-execution coverage. No native comparison mismatch was observed, no
expected output was changed to hide a failure, and final required checks pass.
No final suite skips. Idle-turn callback completion A2E8/A380 is covered by
Musashi/authored tests but not observed in the selected ordinary movie windows.

## Historical: session 2026-10-02-011 — grounded actor dispatcher

These are fresh runs from this session, not the previous handoff's totals.

- **117 Python tests PASS, zero skips; 14/14 CTest targets PASS** in debug,
  release and Clang ASan+UBSan. Seventeen hand-worked actor goldens pass without
  ROM/emulation. Tests cover stateful press/hold/release, idle-to-motion,
  same-call landing, presentation preservation, unsupported actions, terrain
  rejection, continuation budgets and whole-call rollback.
- **152,093/152,093 actor comparisons PASS in each preset**, with identical
  native output hashes across all three. The corpus has 135,901 flat/arithmetic,
  4,544 authored varied and 11,648 cataloged-terrain cases. It applies 167,453
  actor invocations; these are not game frames. It includes all 65,536 values of
  jump delay and impulse independently, both facings, control priority/gate,
  signed threshold, wrap and retained scratch cases. All 315 new scoped
  instructions execute (309 actor, six original sound-selector guard/return).
- **10 rejection checks PASS per preset:** five inputs in both native and
  original processes, including invalid terrain and four explicit unsupported
  action/allocation boundaries. Original rejected PCs are recorded exactly.
- **283/283 GPGX actor comparisons PASS**, with 281 ordinary gameplay calls and
  two controlled RAM-edited landing cases. Eighteen actor/scratch fields and
  eight ordered sound requests agree. All six branches match unhooked replay at
  the declared covered-state boundary. Ordinary routes hit A27E once, A6C8 17
  times and A88E 27 times. The original frame-2013 A408 → AAEA → AB04 same-call
  sequence remains observed; both edited zero-speed landings execute idle
  before F906. All traces have zero drops, no overflow or hook errors.
- **Fresh sanitized regressions PASS:** 415,940 airborne, 282,233 movement and
  614,436 terrain cases, retaining their rejection checks. Four corpora together
  visit all 647 scoped instruction addresses. Native and reference sanitizer
  output is clean. Emulator code remains outside native runtime targets.
- **135/135 damping fixture recheck PASS** for the supplied
  `scenarios-jbc97cle/routine-fixture.json`. This is a separate scalar contract,
  not added to the new actor-call count.
- Static actor probe PASS: 21 range hashes, exact direct transfers, the combined
  graph with explicit rejected exits, CPU sentinel and seven GNU checks.

`re/actor_validation.json` is the tracked non-bulk evidence summary with native
output hashes, trace/checkpoint hashes and exact build ID. Detailed command,
status and duration logs are in `local/logs/grounded-controller/`; reproduction
summary is `reproduction.json` there. All artifacts below are relative to
ignored `local/generated/`:

| Check | Report |
| --- | --- |
| Actor debug | `actor-comparison/run-den6zrty/report.json` |
| Actor release | `actor-comparison/run-dmaa4i3n/report.json` |
| Actor sanitize | `actor-comparison/run-swbg7ya_/report.json` |
| Static probe | `actor-probe/run-yn1p3c22/report.json` |
| GPGX actor capture | `genesis-actor/run-cnph4jtf/report.json` |
| Airborne regression | `airborne-comparison/run-ib5alldr/report.json` |
| Movement regression | `movement-comparison/run-knpuzxkp/report.json` |
| Terrain regression | `terrain-comparison/run-uz3jpro6/report.json` |

Early research failures were corrected without changing semantic expectations:
a generated Boolean input needed integer encoding; sandbox tracing prevented
LeakSanitizer and the worker launcher from using their normal facilities; a
short GNU decode window was inconclusive; an expanded rejection test expected
a memory error where the original reached a forbidden instruction. The harness
now reports the exact rejected PC, distinct from instruction-budget exhaustion.
Failed artifacts/logs remain local. No original/native semantic divergence or
unresolved final test failure occurred. See the session handoff for details.

**Not covered:** presentation/frame scheduling, allocating fast reversal,
up/down action execution, active native audio, full register/CCR ABI, device
cycle equivalence, other pad modes/multiplayer, SDL3 app or native game replay.
Musashi uses sound selector zero and executes real mismatch returns; GPGX leaves
its actual sound driver active. Only requests are compared, not playback.
Codec/image differential corpora were not repeated; their normal CTest targets
passed. Native playability remains none; TASK-0010 remains in progress.

Evidence: [[03_Reverse_Engineering/findings/FIND-0013-actor-dispatch]],
[[08_Sessions/2026-10-02-011-grounded-controller]].

## Historical session 2026-10-02-009 — airborne motion and landing

- **111 Python tests PASS, zero skips/failures.** Five new checks cover explicit
  continuation exits, rejected graph escapes, hashes, corpora and metadata scope.
- **12/12 CTest targets PASS** in debug/release/Clang ASan+UBSan, including new
  airborne native units and transport. Thirty-six hand-worked cases, unsigned/
  signed boundary behavior, pending continuations, unsupported handlers, work
  budgets and whole-call rollback are covered without ROM or CPU reference.
- **415,940/415,940 original airborne cases PASS per preset**: 393,924 flat/
  arithmetic cases, 10,240 authored varied cases, 11,776 real-resource cases.
  All 21 defined outputs agree, including applied calls and immediate continuation.
  All 172 new instructions are visited, 246 overall in this corpus.
- **All native output hashes match across presets**, release invoked from `/tmp`.
  The reference and native sanitizer runs have no diagnostics. One out-of-map
  airborne case rejects in both processes without output.
- **282,233 movement and 614,436 terrain regression cases PASS** with the changed
  reference and sanitized native builds, retaining their rejection checks. The
  union of the three simulation corpora visits all 332 scoped instructions.
- **Static airborne probe PASS:** eleven ranges, 706 bytes, 54 transfers,
  172 new instructions, combined 332-instruction graph with exactly two declared
  continuation exits; CPU sentinel and twelve GNU corroborations pass. Previous
  movement probe/closed graph and expanded sega2asm metadata dry-run also pass.
- Original ROM size/hash unchanged. No new source download or package/global
  changes. Native libraries/executables contain no CPU core.

Exact commands/statuses/durations/logs: `local/logs/airborne-update/commands.json`.
Cross-preset hashes: `local/logs/airborne-update/reproduction.json`.
Final reports under ignored `local/generated/`:

| Check | Report |
| --- | --- |
| Airborne debug | `airborne-comparison/run-7_nzyx5_/report.json` |
| Airborne release from `/tmp` | `airborne-comparison/run-0x39p6wa/report.json` |
| Airborne ASan/UBSan | `airborne-comparison/run-uv6tdnsd/report.json` |
| Airborne static/CFG/decoders | `airborne-probe/run-55cnepnj/report.json` |
| Movement regression | `movement-comparison/run-u320cp4j/report.json` |
| Terrain regression | `terrain-comparison/run-ba85tsyc/report.json` |

An initial two-call hand expectation omitted final y and the second gravity
subtraction. Native and original already agreed; arithmetic review corrected
only that expectation to y109/vertical -8. The initial/corrected values and
reason are retained in `local/generated/airborne-research/golden-correction.json`.
No implementation or reference result was changed to mask divergence. Exploratory
misaligned/truncated windows remain unpromoted. No unresolved final failure.

**Unperformed:** idle/grounded handlers beyond the explicit continuation boundary,
physical pad/full controller/frame scheduling, full game boot/device timing,
full register/CCR ABI, SDL3 window/audio, mods/saves/replays. Asset/image codec
comparisons were not repeated; their normal CTest targets pass. Prior comparison
results remain historical evidence. Native playability stays none.

Evidence: [[03_Reverse_Engineering/findings/FIND-0012-airborne-update]],
[[08_Sessions/2026-10-02-009-airborne-update]]. Final staged review and vault/index
checks are recorded in the session handoff.

## Session 2026-10-02-008 — native actor movement

- **106 Python tests PASS, zero skips/failures.** Five new movement metadata,
  transfer/CFG, fixture and corpus checks join the prior 101.
- **10/10 CTest targets PASS** in debug, release and Clang ASan/UBSan. New native
  movement unit/transport targets cover 26 hand-worked goldens, all 65,536 speed
  words for each damping/clamp entry, overflow/count edges, state assignments,
  resource errors and rollback after an earlier successful pixel step.
- **282,233/282,233 original movement comparisons PASS in each preset**:
  262,265 flat/arithmetic cases, 8,192 varied authored cases, 11,776 cataloged-map
  cases. All sixteen semantic output fields match, including horizontal-step
  and airborne-entry counters. 74/74 new instruction addresses visited, 149
  overall in the movement corpus. These are constructed states, not frames.
- **All three preset output hashes match**, release invoked from `/tmp`.
  One out-of-map movement input explicitly rejects in both processes without
  output. Native and independent reference sanitizer runs have no diagnostics.
- **614,436/614,436 terrain regression cases PASS** with the extended reference
  and sanitized native executable, including its existing three rejection cases.
- **Static movement probe PASS:** fifteen hashed ranges, 650 bytes, 55 transfers,
  74 new executable and 84 static context instructions; combined executable
  graph closes across 160 instructions; ten short GNU corroborations pass.
- Original ROM size/hash unchanged before/after. No CPU core linked into native
  targets. No new third-party source, dependency or system package this pass.

Commands, exit statuses, durations and logs: `local/logs/movement-step/commands.json`.
Cross-preset digest check: `local/logs/movement-step/reproduction.json`.
Final local reports under `local/generated/`:

| Check | Report |
| --- | --- |
| Movement debug | `movement-comparison/run-a8qzn6c7/report.json` |
| Movement release, invoked from `/tmp` | `movement-comparison/run-7_q7c4d3/report.json` |
| Movement ASan/UBSan | `movement-comparison/run-_xsye617/report.json` |
| Static code/CFG/decoders | `movement-probe/run-fxk9b89l/report.json` |
| Terrain regression | `terrain-comparison/run-h7ydwdjz/report.json` |

No unresolved final failure or skipped test. Exploratory arbitrary/truncated
instruction windows stayed local and were not promoted as complete functions.
Code review improved the transactional-error test to fail on the second pixel,
not just the first; no expected output was changed to mask a mismatch.

**Unperformed:** airborne update/landing execution, complete controller/input
ownership, full Genesis/game boot, frame/device timing, full register/CCR ABI,
SDL3 window/audio, mods/saves or gameplay replay. Codec/image comparisons were
not repeated this pass; previous recorded results remain historical evidence,
while all their normal CTest targets passed. Native playability remains none.

Evidence: [[03_Reverse_Engineering/findings/FIND-0011-movement-step]],
[[08_Sessions/2026-10-02-008-movement-step]]. Final split/vault/index review is
recorded in that session note.

## Session 2026-10-02-007 — native terrain/contact execution

- **101 Python tests PASS, zero skips/failures.** Six new ROM-free research/
  metadata/provenance checks join the previous 95.
- **8/8 CTest targets PASS** in debug, release and Clang ASan/UBSan. New native
  terrain units cover all 32 attribute combinations, scratch/word wrap, supported
  aliases, invalid addresses, byte flags and settling. Four transport tests
  include 18 independently hand-worked cases and 2048 byte/height comparisons.
- **614,436/614,436 original-routine comparisons PASS in each of three presets**:
  221,220 authored cases across bases0/257,393,216 actual-resource cases. Native
  outputs/state/NZVC match executed original68000 routines. All 86/86 instruction
  addresses in six functions are visited; no full-game coverage implied.
- **All preset outputs are byte-identical**; release was invoked from `/tmp`.
  Each reference run also rejects three out-of-fixture addresses without output.
  Both native and independent reference execution run cleanly under ASan/UBSan.
- **Static terrain probe PASS:** seven hashed ranges (348 bytes),97 instructions,
  ten reviewed calls, branch closure, original68000 sentinel and 12 independent
  GNU corroborations. The duplicate44-byte contact fragment is static-only.
- **51/51 codec comparisons PASS** (49 authored +2 real blocks). Existing scene
  still matches262,144 independent specification pixels and retains PNG SHA-256
  `476cb65271060616db42300cd0efe1880bb1ef64774be9cacd81d491a52bea92`.
- Expanded function/symbol metadata passes sega2asm dry-run. ROM size/hash remains
  unchanged before/after all processing. Normal native code links no CPU core.

Exact commands/status/durations/logs: `local/logs/terrain-query/commands.json`.
Cross-preset digest verification: `local/logs/terrain-query/reproduction.json`.
Final reports under ignored `local/generated/`:

| Check | Report |
| --- | --- |
| Terrain debug | `terrain-comparison/run-epwn49js/report.json` |
| Terrain release, invoked from `/tmp` | `terrain-comparison/run-jurt6_en/report.json` |
| Terrain ASan/UBSan | `terrain-comparison/run-mffjajzg/report.json` |
| Static code/CFG/decoders | `terrain-probe/run-8yloy3nw/report.json` |
| Codec regression | `rnc-comparison/run-rcksapc6/report.json` |
| Scene regression | `scene-preview/run-vh4uxbox/report.json` |

**Unperformed:** full Genesis/game boot, frame/device timing, full register ABI,
complete actor/player controller, SDL3 window/input/audio, audio-driver execution,
mods/saves and gameplay replays. Native playability remains none. The comparison
contract excludes out-of-resource original RAM and original pattern-relocation
overflow. Six terrain/contact semantic routines are verified, including a
one-pixel movement primitive. This is the first bounded M2 behavior milestone.

One exploratory hand calculation treated y `0x807F` as a valid map row. Original
execution rejected it: signed ADDA.W addresses outside the fixture. The case
was moved into the explicit rejection corpus after arithmetic review; no native
logic or successful golden was changed to mask divergence. Arbitrary truncated
research disassembly remains unpromoted. No unresolved final test failure.

Evidence: [[03_Reverse_Engineering/findings/FIND-0010-terrain-query]],
[[08_Sessions/2026-10-02-007-terrain-query]].

Final checkpoint checks: 45 vault notes and 129 indexed files pass their
validators; explicit staged review and whitespace checks pass. Protected inputs
and bulk/generated/reference source content remain excluded.

## Session 2026-10-02-004 — original resource loader

**83 Python tests pass, zero failures/skips**, including nine new ROM-free tests
for bank layout/count bounds, signed word indexing after multiplication, direct
call decoding, strict disassembly parsing and closed-CFG rejection. Both native
Clang ASan/UBSan CTest entries pass; native C++ code is unchanged this pass.

| Check | Result and limits |
| --- | --- |
| `rnc-loader-probe --disassemble --decoded-bank ...` | Exit 0, six exact code-range hashes, selector/wrapper/caller/consumer fields and decoded structure verified |
| Decoder CFG | 147/147 instructions reachable statically, 181 edges, sole RTS at `0x1959C`; not dynamic coverage |
| Independent instruction corroboration | 16 selected original-68000 instructions match reviewed GNU mnemonics/operands; GNU limitations retained |
| CPU selection sentinel | `49C0` invalid under 68000 and EXTB.L under 68020; installed rasm2 5.9.8 |
| Known resource schema | Exact partition: 32-byte palette + 2-byte count + 442*32 pattern bytes + 442*8 opaque-record bytes = 17,714 |
| Codec regression | All 49 authored + one ROM differential cases pass using sanitized native codec; original routine not executed |
| Native extraction | Same decoded hash/CRC/length as prior checkpoint; added catalog fields cause no byte changes |
| Original ROM | Size/SHA-256 unchanged before and after analysis/extraction |

Evidence: `local/logs/rnc-loader/commands.json`,
`local/generated/rnc-loader/run-s3737ul_/report.json` and adjacent decoder
artifact, `local/generated/rnc-comparison/run-1htpq8v3/report.json`.
Full interpretation: [[03_Reverse_Engineering/findings/FIND-0007-rnc-loader]].

Failed exploratory approaches: arbitrary pre-call disassembly starts were
misaligned/truncated and emitted invalid/filler operands. They are not verified
code. The final probe validates reviewed boundaries and rejects fabricated
instruction extents. Complete primary hardware PDF fetches failed at three
mirrors (403, TLS-name mismatch, tool size limit); indexed excerpts did not
establish pixel layout or display colors. No TLS verification was disabled.

Not run: original CPU/emulator, game or SDL graphics/audio, native structured-bank
parser/renderer, companion scene parsing, movement/collision comparison, other
133 compressed candidates, mods/saves or gameplay replays. No full-game
recompilation or playability claim follows from this static result.

## Previous: session 2026-10-02-003

**74 Python tests pass, zero failures/skips on this host.** This includes the
prior 63 plus two authored-corpus checks, five native publication/metadata checks,
and four build-provenance tests. The 49 authored token cases were independently
validated before native implementation; their expected bytes are not generated
by the decoder under test.

| Check | Result and scope |
| --- | --- |
| GCC16.1.1 debug and release | Configure/build pass without warnings; both CTest entries pass in each preset |
| Clang22.1.7 ASan/UBSan | Configure/build and both CTest entries pass, no native sanitizer diagnostic |
| Native C++ API tests | Known CRC vectors, explicit caller limits, fixed literal fixture and 10,000 seeded malformed streams with valid packed CRC; rejection stress, not proof of semantic completeness |
| Native CLI tests | 10 methods, including 49 valid cases and malformed extents, CRCs, missing input/terminator, invalid matches, truncations, output overflow, early end and trailing bytes |
| Codec differential | All 50 cases pass per preset: 49 authored + 1 ROM block, full bytes and exact consumption, independent output CRC and reference digest |
| Native/reference extraction | Both independently publish identical 17,714-byte output after all integrity checks; native is the default |
| Artifact provenance/publication | Changed sources/executable, wrong/missing provenance and symlink redirects reject; failed process/CRC/consumption preserve prior asset |
| Immutable input | Original size/SHA-256 unchanged after all processing |

Actual host: Fedora44 x86_64, CMake4.3.0, Ninja1.13.2, Python3.14.6.
CTest uses the wrapper's Python interpreter. The first direct CMake invocation
selected installed Python3.12.13; explicit project configuration subsequently
selected `/usr/bin/python3` 3.14.6 for all final preset runs.

Evidence: `local/logs/native-rnc2/commands.json`, its named logs,
`local/generated/rnc-comparison/run-jv84_pye/report.json` (sanitizer),
`run-wa1rr2k4/report.json` (debug), `run-l9oph170/report.json` (release),
`local/generated/rnc-validation/run-m5zxfbx6/report.json`, and
[[03_Reverse_Engineering/findings/FIND-0006-native-rnc2]].
Final vault/Git review: [[08_Sessions/2026-10-02-003-native-rnc2]].

Unrun: gameplay/original CPU execution, SDL window/audio, original-vs-enhanced
profiles, semantic graphics/audio extraction, other 133 candidates, mods/saves,
deterministic gameplay replays and ROM round trip. Optional upstream tests still
intentionally reproduce the old decoder failures; native tests reject malformed
streams without triggering the reference's invalid memory accesses.

## Previous: session 2026-10-02-002

**63 tests pass, zero failures/skips on this host.** The 39 foundation tests
remain, plus 10 RNC parser/CRC/output tests, 3 upstream RNC probes, 6 independent
reference checks, and 5 output-publication tests. Synthetic tests remain ROM-free;
`test --rom` separately checks the recorded input identity.

| Check | Executed result |
| --- | --- |
| `rnc-validate` | Exit 0; first block extent and packed CRC `0x3673` verified |
| `rnc-validate --decode` | Exit 0; 17,714 output bytes, unpacked CRC `0xAF73`, exact 10,821 total input consumption |
| Independent reference | Pinned ScummVM compiled with Clang22.1.7 ASan/UBSan; real block and literal-A fixture pass without sanitizer diagnostics |
| Adversarial reference inputs | Malformed extents/CRCs reject; two invalid streams terminate under ASan with no output, as asserted by tests; not production hardening |
| Upstream RNC probe | Expected exit 2, `rejected_output`: 25 rather than 17,714 bytes; authored A fixture becomes G despite correct length |
| Publication guards | Failed CRC, process failure, or incorrect consumption preserve existing output |
| Repeated extraction | Stable decoded SHA-256 `048aec81ffb0e5463029b931c2716e5aaa818539b5f72c078f7a19cc195a9ac7` |
| GCC sanitizer build | Failed because libasan/libubsan runtime packages are absent; Clang compiler-rt is installed and works |
| Original ROM | Size/hash unchanged before and after processing |

Evidence: `local/logs/rnc-tests-current.log`, `local/logs/rnc-pass/commands.json`,
`local/generated/rnc-validation/run-yvge20iw/report.json`, and FIND-0004/FIND-0005.
Final Git/vault/hygiene results: [[08_Sessions/2026-10-02-002-rnc-validation]].
Final review passes: 30 vault notes, 66 indexed files, no protected/generated
content staged, and no staged/unstaged whitespace errors.

Unrun: original CPU/emulator execution, gameplay differential/replay tests,
native game/SDL3 builds, semantic graphics/audio extraction, other 133 RNC
candidates, modes/progression, mods/saves and ROM round trip. The sanitizer
coverage above belongs only to the isolated decompression reference.

## Foundation: session 2026-10-02-001

Executed on the actual Fedora44 x86_64 host, Python3.14.6. Exact tool/package
versions: [[02_Workflow/ENVIRONMENT]]. ROM identity:
[[03_Reverse_Engineering/ROM_IDENTITY]]. Scope definitions:
[[05_Validation/TEST_STRATEGY]].

| Check | Result and limits |
| --- | --- |
| `python3 tools/project.py test --rom` | **39 tests pass, 0 fail, 0 skipped**; additional manifest identity check passes |
| Parser tests | 10 authored synthetic tests: checksum, headers/vectors, malformed/truncated/unsupported/oversized inputs, immutable reads |
| Reset field/output tests | 9 synthetic tests; original-68000 displacements, masks, counts, bounds, safe outputs |
| sega2asm wrapper/probes | 9 tests, including two executions reproducing pinned upstream errors on synthetic bytes |
| Vault-checker tests | 7 tests: explicit links/anchors, ignored code examples, fields/IDs and task consistency |
| Git hygiene tests | 4 disposable-repository tests: scoped ignores, staged-content inspection, tracked protected paths, blanket Markdown ignores |
| `rom-identify --verify` | Size/SHA exact, checksum `0xC0DE`; unchanged from before analysis |
| `reset-probe --disassemble` | Static checks pass; 68000/68020 sentinel and ten short GNU corroborations recorded; no dynamic execution |
| `split --dry-run` / `split` | Both exit 0 with final safe raw config; 1,048,064 raw bytes compare exactly |
| `doctor` | Audit exit 0; records missing prerequisites honestly |
| `doctor --require-native` | **Exit 1 as expected:** SDL3 development files absent; native build not validated |
| Reserved `build` command | Exit 2 with unimplemented diagnostic, as intended |
| Compiler probes | GCC and Clang compile/run C++20 span/rotl probe, both exit 0; not a game build |
| Upstream `go test ./...` | 11 packages compile, **no test files**; not upstream semantic coverage |
| RNC header rescan | 134 candidates, method2 and declared extents in file; zero CRC/decode checks |

Evidence under ignored `local/logs/validation/`: `commands.json`, per-command
logs, and `rnc-header-scan.json`. Final integrated split reports:
`local/generated/sega2asm/dry-run-srt8135u/run.json` and
`local/generated/sega2asm/split-20bw7mng/run.json`. Reset reports:
`local/generated/reset/report.json` and `decoder-evidence.json`.

Final `check-vault` passes for 25 notes; `check-hygiene` passes for 49 explicitly
indexed owned files. Staged/unstaged whitespace and protected-content review
pass. The suite also passes all 39 tests invoked by absolute path from `/tmp`
without requesting ROM-dependent validation. Author identity was supplied and the checkpoint commit completed; see [[08_Sessions/2026-10-02-001-foundation]].

## Failed approaches and unrun layers

The first sega2asm m68k attempt generated wrong MOVEM/MOVE-to-SR assembly despite
zero exit. Tests reproduced that and upstream's swallowed write error. The final
configuration exports affected code raw and the wrapper rejects m68k output as
unverified. Earlier local success labels measured artifact presence only and
are explicitly superseded. See FIND-0002.

The GNU decoder plugin cannot decode instructions longer than four bytes and
enables extra CPU flags; it is restricted to selected corroboration. An attempted
rasm2 file-slice invocation read the wrong region; exact hex-slice commands
replace it. Details are preserved in FIND-0001. A stalled metadata network
fetch was stopped; bounded curl succeeded for the local tool bootstrap.

**Not run / not established:** native app or game build, SDL graphics/audio,
sanitizers, emulator reference run, gameplay differential tests, deterministic
replay, RNC decode/CRC, graphics/audio extraction, audio sequencing, mods, saves,
whole-ROM reassembly. None is implied by the 39 passing infrastructure tests.
There are no reconstructed native gameplay functions. See
[[03_Reverse_Engineering/COVERAGE]].


## Session 2026-10-02-005 — structured native graphics bank

- **91 Python tests PASS, zero skips** on the actual Fedora44 x86_64 host.
- All **4/4 CTest targets PASS in debug, release and Clang ASan/UBSan**:
  RNC2 unit/streams and pattern-bank unit/transport. Native transport includes
  three tests; one checks all 256 single pattern bits against the independent
  bitplane model. Authored tests cover raw/converted palette semantics, record
  preservation, count1/65536, larger 1000 bank, malformed extents/IDs and limits.
- Native ROM-dependent extraction and static loader/disassembly probe PASS.
  All **50/50** independent codec cases (49 authored + one cataloged block) PASS:
  `local/generated/rnc-comparison/run-xupq_f_2/report.json`.
- First real bank: **442/442 patterns, 28,288/28,288 pattern pixels**, plus
  384/384 padding pixels, agree with the source-derived specification model.
  This is not an executed emulator/game differential.
- **PNG repeatability PASS** across debug/release/sanitizer and repeat invocation
  from `/tmp`: SHA-256
  `988b4d3eb88dfaf59bcdcde7fd7216a96870f9704fb5f10e05e882e24f5d71e6`.
  Native rasterization is shared; PNG encoding adds no pixel transformations.
- Local image inspection completed: coherent terrain-like pattern fragments;
  no scene identity or collision interpretation inferred.
- Original ROM identity verified unchanged before/after processing. Whitespace
  checks PASS; vault checker PASS for 39 notes; staged hygiene PASS for 99 indexed
  files, including protected-path/content checks.

Exact command/status/log records: `local/logs/pattern-bank/commands.json`.
Image reports: `local/logs/pattern-bank/atlas-reproduction.json`. Canonical debug
example: `local/generated/bank-atlas/run-8ushhgd8/report.json` and `atlas.png`.

No tests were skipped in the executed suites. **Unperformed:** original CPU or
MAME execution, original-frame color comparison, SDL3 window/input/audio,
scene/gameplay replay, collision, mod/enhancement capacity demonstration.
The palette is an explicit diagnostic scale, not a brightness fidelity claim.
No third-party emulator code is linked into either native asset library.


## Session 2026-10-02-006 — companion scene and native terrain plane

- **95 Python tests PASS, zero skips.**
- **6/6 CTest targets PASS** in debug/release/Clang ASan+UBSan: codec unit/streams,
  bank unit/transport, scene unit/transport. Scene transport has two authored
  tests; native units test coordinate/word wrap, resource joins, records, flips,
  unsupported shapes/references, all truncation extents and allocation bounds.
- **51/51 codec comparisons PASS:** 49 authored + 2 cataloged ROM blocks.
  New companion decode 13,700 bytes has both CRCs and exact consumption verified;
  native and independent sanitized reference outputs match byte-for-byte.
- **Static scene probe PASS:** three exact ranges (472 bytes),56 field checks,
  67+11+36 decoded instructions, 16 independent GNU instruction corroborations.
  Original68000 sentinel passes. No CPU execution coverage implied.
- **Native scene PNG PASS:** 1024x256, all 4096 map cells / 262,144 pixels compared
  with an independent bitplane/palette/flip specification model. Debug, release,
  sanitizer and repeat-from-`/tmp` PNG hashes are identical:
  `476cb65271060616db42300cd0efe1880bb1ef64774be9cacd81d491a52bea92`.
- Existing bank-atlas digest remains unchanged. Expanded metadata passes pinned
  sega2asm dry-run. Original ROM identity remains unchanged before/after reads.

Evidence: `local/logs/companion-scene/commands.json` and `reproduction.json`;
`local/generated/scene-probe/run-yr2s7pku/report.json`;
`local/generated/rnc-comparison/run-1aaljm3a/report.json`;
`local/generated/scene-preview/run-g73_3ur2/report.json` and `scene.png`.
Image opened locally: coherent terrain-map structure, no named-stage claim.

No tests were skipped in executed suites. **Unperformed:** original CPU/debugger
reference, original-frame comparison, gameplay/movement/collision, SDL3 window,
audio, mods and replays. The scene is one diagnostic map plane, with source
priority retained but no multi-layer/camera/entity simulation. Opaque records
remain uninterpreted. No golden outputs changed to conceal a regression.

Final checkpoint checks: vault checker passes all 42 notes; staged hygiene passes
113 indexed files with no protected inputs or bulk outputs. Explicit staged
review and whitespace checks pass. Original ROM digest is unchanged.
