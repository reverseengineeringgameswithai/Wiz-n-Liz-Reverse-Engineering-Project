---
id: PROJECT-NEXT
type: project
status: active
---
# Next actions

[[09_References/KEV]] remains an accepted research aid: use it for evidence
screening or investigation triage where it helps, with review appropriate to the
conclusion. Perfect accuracy is not required. No Kev integration is required for
the next native task.

Stack: [[06_Decisions/ADR-0001-presentation-shell]] was rejected on 2026-10-23
at the user's delegation; SDL3 stays and no Godot work is planned. SDL3 is not
needed until a playable shell is built (it needs `SDL3-devel`, absent, with the
user's authorization). Scope: [[02_Workflow/PROJECT_BOUNDARIES]]; never read,
query or baseline other home-directory projects (such as WL3PC).

Continue [[07_Tasks/TASK-0010-grounded-controller]]. Read
[[08_Sessions/2026-10-28-056-second-level-entry]],
[[03_Reverse_Engineering/findings/FIND-0053-second-level-entry]],
[[03_Reverse_Engineering/findings/FIND-0052-scene-change]],
`tools/genesis_game_session.py` and `src/sim/mixed_pool.*`.

Session 055's validation is complete (session 056). **Current bounded task,
in progress in session 056 (banked mid-pass): from the hub into the second
level.** Resume with the session note's two steps: the two uncounted E918
draws, then the fresh captures, fixtures, corpora on every preset and the
validation summary. The survey
corrected the plan: after the hub (1758) the top-level loop runs 10D8/10F8, the
hint screen (1959E, 1758..2067), E2A (2067..2106) and 754, whose own loop
(0x792, FF33E0 = 0013) is the second level from 2107; 6664 is not reached.

Exact leads and acceptance:

1. Verify actual Git state and read the handoff. Reuse the preserved 5,298-row
   recording with owned workers; do not change the GUI or external tools.
2. Reconstruct the change with restricted corpora first: the hint loop's test
   (14E3C, [1972E,19766)), E2A's anchor clear, 9880 at a zero anchor, 118C's
   FF33D8 ([11A6,11EE) with E918), 9952 again and FF33E0 = 0013.
3. Extend the joined run past 1758: the hint screen's loops on the carried
   timer, the second level's entry, then P1 alone on the second level's
   captured terrain from 2107 (30C4's pause poll only while FF0B90 is zero; the
   second level's world is not native) and report the first rejection exactly.
4. Test debug/release/sanitize and impacted regressions; synchronize vault,
   validation and coverage without inflating counts; commit reviewed owned work.
   No pushes/uploads; TASK-0010 in progress; native playability none.

Context: the terrain is switched to each scene's captured resource; native
loading of maps from the ROM (the RNC codec and scene parser are native) is a
later step. Two-player scene changes reject.

Reuse requires matching recipe/source/input/artifact hashes. Keep the original
ROM, BK2/recording and GenesisDebug sources/runtime unchanged and the user's
BizHawk GUI and Sonic bridge untouched.
