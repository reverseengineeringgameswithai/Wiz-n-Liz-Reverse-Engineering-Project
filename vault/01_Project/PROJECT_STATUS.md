---
id: PROJECT-STATUS
type: project
status: active
---
# Project status

Latest session: [[08_Sessions/2026-10-28-056-second-level-entry]] (in
progress, banked for a user restart), starting clean at `d8f3059` on
`work/airborne-update`: it completed session 055's validation, surveyed what
follows the hub and made the hint screen and the second level's entry native
([[03_Reverse_Engineering/findings/FIND-0053-second-level-entry]]): 10,625
restricted cases match in debug; offline, one native run matches the level,
the hub, 301 hint loops, the entry and 29 second-level P1 calls (2107..2135;
the level's objects take the terrain scratch at 2136), except E918's state,
two draws behind. Release/sanitize and the fresh captures are pending.

Side pass [[08_Sessions/2026-10-29-057-public-mirror]] (completed, no native
change): the user authorized a public GitHub mirror of the committed project
with fresh history and their identity scrubbed; see
[[02_Workflow/PUBLIC_MIRROR]]. Side pass
[[08_Sessions/2026-10-29-058-licensing]] licensed the project under MIT
([[06_Decisions/ADR-0002-project-license]]). Session 056 remains the native
handoff.

Session [[08_Sessions/2026-10-23-055-scene-change]]: **the first level, the
scene change and the scene after it run natively as one run (frames 634..1758)
from one player seed**, now confirmed by a fresh all-in-one capture and its
fixtures on every preset. After the level ends, the game clears its objects, rebuilds the
player at the position the level's exit stored and fades into the door map;
the native run does the same and continues into the map without being given
the player again. Only the map's terrain is still taken from the capture.

Previous: [[08_Sessions/2026-10-23-054-hub-scene]] (the scene after the level,
seeded at its first loop), [[08_Sessions/2026-10-23-053-door-entry]] (the level
native from its setup to its end, 634..1532),
[[08_Sessions/2026-10-23-052-spell-completion]];
[[08_Sessions/2026-10-23-048-stack-decision-and-boundaries]] rejected
[[06_Decisions/ADR-0001-presentation-shell]] at the user's delegation (SDL3
stays) and added [[02_Workflow/PROJECT_BOUNDARIES]] (other home-directory
projects such as WL3PC are out of scope). [[09_References/KEV]] remains an
accepted research aid; [[09_References/REA]] was not adopted. Git and vault
advance together; original inputs and the frozen reference installation remain
preserved.

## Current native behavior

`MixedPool` initializes every object of the `[6886,68D4)` level setup through one
transactional N-pop template over F9E2's LIFO stack, and
`initialize_level_setup_prefix`, `initialize_level_setup_tail`,
`continue_level_setup` and `initialize_gated_pairs` compose its four steps.
`establish_world` turns the setup's identities into one carried `PickupWorld`
inside `MixedSessionState`. `step_world_phase` runs one object loop
(`MixedPool::step`: reversal effects, 6D8C emitters with shared particle
allocation, particles, 7808/7CA4 private objects, 7A88 table objects, 78EE probes
with 7910 deliveries, pickups with 6C00 hits, return-only objects, delivered
copies with both 79B6/7AD6 paths, the FF31C0 spell anchor with 13294 and the
completion, the sparkle, the exit door with its entry and its sign) after
explicit `WorldUpdates` and the frame's 7CC8 call (`MixedPool::mix_spell`); the
pool step restarts the session's 1345A timer (13294, 1324E) and the door's entry
hands P1 to its exit handler (710E, 7126, run with the session's timer and
action globals);
`step_mixed_session` runs the 1345A timer (when carried), banner, input and the
P1 wrapper and then that loop with P1's tracking and position. Each call commits
everything together or rolls back.

The scene after the level: `MixedSessionState::hub` (a `HubWorld`: the FF330C
door records, FF33E2, FF3398) is built by `initialize_hub` (63A4, then
`MixedPool::initialize_hub_doors`: 60E6 with 611E and 6334) and walked by the
same `step_world_phase`/`step_mixed_session` without 7CC8: `HubDoor`s count
down, open and test P1 (621A); a contact runs `MixedPool::enter_hub_door` (623C:
FF4446/48 into the timer's requested position, FF3398, the puff, both number
objects released, 13208) and P1 coasts (630A); Up/Down reach P1's actor;
`scene_ended` reports 6024's exit. See
[[03_Reverse_Engineering/findings/FIND-0051-hub-doors]].

`enter_hub_scene` turns the level's session into the hub's: P1 rebuilt by
`make_hub_actor` at the timer's requested position, `reset_object_pool`,
`start_fade_in`, the cleared acceleration gate, FF33E0 = 7, the hub's doors and
the banner's scratch row. See
[[03_Reverse_Engineering/findings/FIND-0052-scene-change]].

Remaining inputs in the joined run: physical held buttons, the count of E918
calls by the FFFF32C2 object outside the pool and message-field updates during
the level, the scene-change inputs (the door records, FF33C4, FF13E2, FF3398,
FF0690's +30) and the hub's captured terrain. **What follows the hub (0x4A4
onward, the second level) is not native**, nor the active-link door
entry, the other 104 recipes, the FF31A8 path, the 95EE gates and the two-player
branches, five overlap-hit
FF31C0 readers, the FF31A4/FF31A6 gate producers, the 6C00 family branches, the
gated-pair lead handlers, the message producer and native rendering of
messages. The setup after 68D4, other F9E2 callers, FA30 and pool resets are
not reconstructed. See [[03_Reverse_Engineering/findings/FIND-0050-door-entry]].

Totals: **161 bounded mappings plus 13 partial / 183 indexed**, plus four
mapped setup, three hub and five scene-change fragments; 32,855 classified /
1,015,721 unclassified ROM bytes; 2,838 cumulative executed instructions. **Native
playability: none.** Boot, the level sequence before the setup, rendering/audio,
the SDL3 shell, saves and mods remain unfinished; `project.py run` is
unimplemented and M3–M6 unachieved. Emulator code stays outside native targets.

## Fresh validation

- Restricted original execution: 8,583 cases (the hub's 7,571 and 1,012 scene
  changes) match in debug/release/sanitize; all 375 new instructions of both
  steps execute.
- Joined comparison (session 056's fresh all-in-one capture; session 055 had
  compared it offline): across the scene change the carried state changes only
  inside the reconstructed routines; one native run from one P1 seed matches
  **all 1,095 P1 calls and loops** (the level's 899, the hub's 196), the scene
  change's P1, timer, banner request and pool; its debug/release/sanitize
  fixtures reproduce both digests.
- Fresh standalone level and hub captures reproduce session 054's digests and
  their fixtures match on every preset; the mixed, early/late P1 and effect
  fixtures keep theirs.
- Regressions: completion, spell, ingredient, delivery, pickup-hit, return-only,
  collision and table-motion corpora and the setup fixtures pass on every
  preset.
- **239 Python tests, zero skips; 46/46 CTests per preset**; warning-free builds.
- Evidence: `re/scene_change_validation.json` and [[05_Validation/RESULTS]].

## Stack decision

ADR-0001 was rejected on 2026-10-23 at the user's delegation: the briefed C++20
/ SDL3 / CMake / Ninja stack stands. The first SDL3 shell task will need
`SDL3-devel` (absent) with the user's authorization.

## Exact next task

Continue [[07_Tasks/TASK-0010-grounded-controller]], still **in progress**:
**from the hub into the second level**: the hint screen (1959E), E2A and
754's head natively, extending the joined run past 1758 into the second level's
loop (FF33E0 = 0013, from 2107), in progress in session 056. See
[[01_Project/NEXT_ACTIONS]]. No new user recording needed.

Leave the user's BizHawk GUI installation and its Sonic bridge (port 19420)
untouched and keep the GenesisDebug worker sources/runtime unchanged; other
home-directory projects are out of scope ([[02_Workflow/PROJECT_BOUNDARIES]]).
No pushes/uploads. ROM SHA-256:
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
