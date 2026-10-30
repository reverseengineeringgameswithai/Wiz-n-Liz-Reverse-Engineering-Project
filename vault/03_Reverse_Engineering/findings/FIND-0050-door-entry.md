---
id: FIND-0050
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# Entering the exit door: the joined run to the level's end

Task: [[07_Tasks/TASK-0010-grounded-controller]]. ROM SHA-256:
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`. Scope/hashes:
`re/door_entry_step.json` (with `re/completion_step.json`); validation:
`re/door_entry_validation.json`. Source: `src/sim/spell.*` (`DoorStep`,
`vanish_exit_door`), `src/sim/mixed_pool.*` (`enter_exit_door`,
`step_world_phase`, `step_mixed_session`), `src/sim/presentation.*`
(`begin_exit_transition`), `src/sim/session.*` (`P1SessionState::actions`).
Evidence: `tools/completion_compare.py` (door variant),
`tools/genesis_world_session.py`, `tools/genesis_world_pool.py`,
`tools/genesis_session_capture.py`. Continues
[[03_Reverse_Engineering/findings/FIND-0049-spell-completion]] (the door) and
[[03_Reverse_Engineering/findings/FIND-0018-actor-transition]] (710E, 7126,
A148 and 13208, already native).

## Static ranges and contract

| Half-open range | Instructions | Contract |
| --- | --- | --- |
| `[7082,70FE)` | 21 | 705C's contact path: FF0F00 = A5 (the control); the FF31C0 object's +16 = 12646; JSR 4CA2; with FF33E2 clear FF444A/FF444C = the door's +2/+4 - 010C/00E0, each AND FFF8; the control's +00 actor gets +4A = A5, mode 80, +6 = 021D and +16 = 710E; the control's +1A6 = FFFF; the +1A2 object's mode tested: zero returns through 7152's RTS (already classified with 7126), nonzero continues at 70FE (outside scope) |
| `[4CA2,4CBE)` | 8 | A6 saved; FAA4 on the door's +3A object (the sign); A6 restored; BSR 59BC (mode 85, frames 021E..0227, both RTS, callback FAA4); +2 - 8, +4 + 8 |

152 new bytes / 29 new instructions; 59BC, FAA4 and the 7152 RTS were already
classified. 7082's tail on P1's actor has 630A's shape with handler 710E
instead of 632A (630A also sets +1A6 = FFFF). The control's +1A6 (FF0836) is
P1's tracking selector.

**Interpretation (probable):** touching the open door ends the level: the sign
disappears, the door vanishes with a puff, the camera words are pinned near the
door and P1 hands control to the exit handler, which coasts it and fades the
screen out (13208); when the fade ends 7126 records the requested position and
sets FF33E0 = 7 (the level is over).

## Native implementation

`step_exit_door` returns `DoorStep` (`dressed`, `entered`); on `entered`
`MixedPool::enter_exit_door` runs 7082: `PickupWorld::exit_control` (FF0F00),
the anchor's 12646 (a spell anchor becomes a return-only object), the sign's
release, the door replaced by `vanish_exit_door` (a `TrailParticle`), the
single-player `exit_camera` and `door_entered`; an active +1A2 link rejects.
`step_world_phase` then applies `begin_exit_transition` to the session's P1
(selector FFFF, mode 80, frame 021D, `transition_start`). `step_mixed_session`
now gives P1's actor dispatch the session's `TransitionState` and
`P1SessionState::actions`, so the already native 710E (A148, `start_transition`)
and 7126 (A148, then `saved_position = requested_position` and mode 7) run in
the joined session. `P1SessionResult::transition` (session 052) keeps the
timer as 1345A left it for comparison.

## Restricted original comparison

The door variant of `tools/completion_compare.py` now continues through 7082
(4CA2, 59BC, FAA4, the camera words, P1's actor and +1A6, the anchor) with the
two-player test (7072) and an active link (70FE) as stops: **4,150 door cases**
(326 entries: 260 with camera words, 66 with two players and no camera words;
103 active-link stops, 412 two-player stops) within **14,734 completion cases
per debug/release/sanitize**, all matching; all 29 new instructions execute.
The reference checks every uncontracted byte, the free stack (the sign's slot
pushed) and P1's written actor bytes.

## Ordinary recording evidence

Research traces of 1510..1540 (the session recipe plus 705C, 7082, 4CA2, 710E,
7126, 13208 and the pool resets) showed the exit, and the shared session
validator, run over 1514..1533 of a faithful P1 capture, failed exactly at the
three places this pass handles: the world's FF0836 write at 1515, 13208 inside
P1's wrapper at 1516 and FF33E0 at 1532 (1517..1531, 7126 waiting, already
validated).

Fresh P1 and world replays of 634..1533 (the walk recipe now also traces FF0F00
and FF444A/FF444C; P1's adds FF4446/48 and FF0732/34) with a fresh setup
capture:

- **1515:** after P1's wrapper, the open door (slot 48) finds P1 overlapping:
  7082 releases the sign (slot 47, its slot pushed), the door vanishes at (344,
  248), FF0F00 = FF0690, FF444A/FF444C = 0048/0018, P1's actor gets mode 80,
  frame 021D and handler 710E and FF0836 becomes FFFF; the +1A2 link (53) is
  dormant.
- **1516:** P1's 710E coasts (A148), installs 7126 and tail-jumps to 13208:
  direction 1, level 14, countdown 1, reload 1, curves 1356A/1356A/135AA.
- **1517..1532:** 7126 coasts each frame while 1345A steps the fade (level steps
  1518, 1520, ..., 1530 return through 134D4; the last, at 1532, clears FF0B90);
  at 1532 7126 sees FF0B90 clear and writes FF0732/34 = FF4446/48 (0000, 0030)
  and FF33E0 = 7.

FF0732/34 is the camera position, rewritten every frame by non-native code; only
7126's final write is modeled and compared. Native `wiznliz-session
--world-session` matches the setup line and, with **no supplied loops**, all
899 fade-timer states with their curves, **all 899 P1 calls** (18 sound
requests) as each wrapper returned them, FF33E0 after every frame (7126's saved
position at 1532), and **all 899 object loops** from 634 through 1532: 12,347
walk updates, 79 births and 77 releases. P1's evidence runs in four segments,
split after 1433, 1447 and 1515 and joined by exactly what 13294, 1324E and
7082 wrote; from 1516 the session validator accepts P1's exit handlers. The
cross-check ties 899 tracking values and 166 owner positions to P1; the fade's
32 palette requests match its level steps. Release and sanitize reuse the
capture with the same output digest.

## Limits and next validation

The active +1A2 link at the entry (70FE), the two-player paths and everything
after the level (the main loop's exit on FF33E0 = 7, the pool resets at
1535..1536 and the next scene from 1562) are not native; the run ends at 1532.
The message producer, the FFFF32C2 object's E918 calls, the fades' palette
consumers, rendering and audio remain outside it. Next: the scene after the
level. TASK-0010 remains in progress; **native playability: none**.

Update: [[03_Reverse_Engineering/findings/FIND-0051-hub-doors]] surveys the scene
change and makes the scene after the level (its doors, P1's entry at 1742 and
its end at 1758) native from its setup, seeded at its first loop.
