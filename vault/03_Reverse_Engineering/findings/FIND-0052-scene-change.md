---
id: FIND-0052
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# The scene change: the level and the hub as one native run

Task: [[07_Tasks/TASK-0010-grounded-controller]]. ROM SHA-256:
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`. Scope/hashes:
`re/scene_change_step.json`; validation: `re/scene_change_validation.json`
(completed in [[08_Sessions/2026-10-28-056-second-level-entry]]).
Source: `src/sim/hub.*` (`make_hub_actor`, `hub_actor_parameters`),
`src/sim/transition.*` (`start_fade_in`), `src/sim/mixed_pool.*`
(`reset_object_pool`, `HubSceneInputs`, `HubSceneEntry`, `enter_hub_scene`).
Evidence: `tools/hub_compare.py` (its `scene-change` corpus),
`tools/genesis_game_session.py`. Continues
[[03_Reverse_Engineering/findings/FIND-0051-hub-doors]] (the hub) and
[[03_Reverse_Engineering/findings/FIND-0050-door-entry]] (the level's end);
promotes four static-only fragments of
[[03_Reverse_Engineering/findings/FIND-0011-movement-step]] (9880, 98DE's call,
9952 and F940's actor bindings).

## Survey: what the scene change does to the carried state

A research trace of 1531..1564 (every return in the sequence below, with P1's
actor, both controls, the timer, scratch, the action globals and the pool head,
plus the RAM at every frame boundary) showed:

- **1532:** after the level loop returns (FF33E0 = 7) the top-level loop calls
  17400, copies FF4446/48 into FF0690's +A2/+A4 (0x488; FF0732 is that +A2) and
  calls 5D30.
- **1533..1536:** 16EA4: VDP and RAM setup; 17024 zeroes the 68 slots and both
  actors (1535), F872 (called by 170E2 at 171AE, then by F850) gives them their 12646 selectors and F940
  rebuilds the free stack (slot 0 at FF300C .. 67) and the controls' actor
  pointers (1536); its tail clears FF0F16 and control words, runs 131C2 (the
  fade-in: FFFF, level 0, countdown 6, reload 1, the exit curves) and sets
  FF0B92 = 001E.
- **1537:** 9880 rebuilds both actors: 98DE clears the control's +1A6; 9952 sets
  +4A, clears +12/+22, writes the movement parameters (the level's values),
  +B6 and 5964's appearance (mode 87, 0227..021E) with callback AA50; then +0C =
  19, flags 0800 and the position (0114, 00B0) + the control's +A2/+A4. 17284
  clears both controls' message fields; 446C writes four words per control.
- **1537..1562:** the map, graphics and palettes load (the controls' +3C/+3E
  are written); at 1562 63A4/60E6 build the doors, 63E2 sets the scratch row
  (000D) and 5ED4 sets FF0B92 = 000A.

The timer does not run from the level's last loop until the hub's first
(1563). P1's actor is therefore rebuilt entirely; what carries over from the
level is FF4446/48 (the timer's requested position), P1's tracking
coordinates, the scratch X, the action globals and the terrain-independent
session state.

## Static ranges and contract

| Half-open range | Instructions | Contract |
| --- | --- | --- |
| `[488,49E)` | 3 | FF0690's +A2/+A4 = FF4446/FF4448 |
| `[17024,17058)` | 14 | FF1B50..FF3007 and both actors zeroed |
| `[F850,F872)`, `[F872,F8F2)`, `[F940,F994)` | 7 + 25 + 19 | F872 (each slot and actor: mode, +06, +12, +14 cleared, selectors 12646), F940 (actor pointers, mode cleared; FF3008 = 0, slots 0..67, FF311C), 1720C, FF17AC..FF17B3 = FFFFFFFF |
| `[1720C,17256)` | 12 | Render lists (FF148C.., FF17AC.., FF1AA8..FF1AB1); research-only |
| `[16FB4,16FBA)`, `[16FF8,17004)` | 1 + 2 | FF0F16 cleared; BSR 131C2, FF0B92 = 001E |
| `[131C2,13208)` | 9 | The fade-in timer |
| `[9880,98DE)`, `[98DE,9952)`, `[9952,99D4)` | 17 + 25 + 26 | Both controls' actors as surveyed; +08/+0C/+18/+3A/+96/+98/+B6 and 9952's +68 are not native |
| `[1737E,173C6)` | 16 | Camera words (+9A..+A0, +A6/+A8 = +A2/+A4 >> 3, +B2..+B8, +108/+10A); research-only |
| `[17284,17298)` | 4 | 17298 on both controls (message fields); research-only |
| `[5D6A,5D7E)`, `[446C,4484)` | 4 + 5 | 446C on both controls (+11A, +144, +16E, +F2); research-only |
| `[5ED4,5EDC)` | 1 | FF0B92 = 000A |

966 code bytes / 190 instructions, 274 of the bytes (54 instructions) already
statically classified by FIND-0011: **692 newly classified bytes** and 190
newly executed instructions.

## Native implementation

`make_hub_actor` (9880/9952 on one control) and `hub_actor_parameters` (9952's
limits, slow with +30 set), `start_fade_in` (131C2) and `reset_object_pool`
(17024 and F850). `enter_hub_scene` composes them on a `MixedSessionState` in
the original's effect order: P1's actor at the timer's requested position +
(0114, 00B0), the tracking selector 0, the reset pool, the cleared gate, the
fade-in with 001E, FF33E0 = 7, the level's world dropped, the hub world
(`initialize_hub`: 63A4/60E6), 63E2's banner (scratch Y 000D) and 000A. It
returns the parameters and gate for the session's configuration. Two players
reject.

## Restricted original comparison

The `scene-change` corpus of `tools/hub_compare.py` (reference mode 13) runs, in
order, 0x488 to 049E, 17024, F850, 16FB4 to 16FBA, 16FF8 to 17004, 9880, 17284,
5D6A to 5D7E and 5ED4 to 5EDC over pseudo-random RAM: 1,012 cases (FF4446/48
and FF0838's +A2/+A4 including the word wrap, each control's +30, FF33E2,
FF13E0) compare both actors' fields, +4A, the actor pointers, both +1A6, the
nine native parameters, the timer block, FF0EDE, FF0F16 and the reset pool;
the camera, HUD, message and render words listed above are declared, and every
other byte is checked unchanged. With the hub corpora: **8,583 cases match in
debug, release and sanitize**; all 375 new instructions of both steps execute.

## Ordinary recording evidence

`tools/genesis_game_session.py` replays the level (634..1533), the scene
change (1532..1563: every return in the sequence with the carried state, the
RAM at every boundary) and the hub (1562..1759). Session 055 compared the
joined run offline (a fresh scene-change capture with session 054's level and
hub captures) before a restart stopped its all-in-one capture; session 056 ran
that fresh capture (`local/generated/game-session/run-s49_3nc8`, hooked and
unhooked endpoints equal for each part) with the unchanged tools and builds,
and its fixtures on every preset.

Across the scene change the carried state changes only at 0x488 (the anchor),
17024 and 170E2's F872 (the actor), 16EA4's tail (the timer), 9880 (the actor
and selector), 63E2 (the scratch row) and 5ED4 (the timer); the pool only in
1535, 1536 and 1562, reset at 1537 exactly as `reset_object_pool` makes it;
the timer stays still.

One native `wiznliz-session --game-session` run built the level's setup from
one P1 seed at 634, ran its 899 loops, applied `enter_hub_scene` (inputs: the
records, FF33C4, FF13E2, FF3398 and FF0690's +30 as 1562/1533 left them),
switched to the hub's terrain and ran the hub's 196 loops. The level's lines
matched as `genesis_world_session` checks them; the scene change's line equals
the hub's first P1 call (all 32 seed fields), its full timer row, 63E2's banner
request (label 0, E680, number 1 at E6B8) and 60E6's pool; the hub's lines
matched as `genesis_hub_session` checks them: **1,095 P1 calls and loops from
one seed**, P1 never reseeded at the hub (seed digest `bc8e1384…`, output
`8fab99e3…`, as offline; debug, release and sanitize fixtures reproduce both).
Fresh standalone captures of the refactored level and hub tools reproduce
session 054's digests, and their fixtures match on every preset.

## Limits and next validation

The scene change's VDP, map, graphics and palette loading, the HUD, the
controls' camera/message words and P2's actor (compared in the corpus, not
carried by a session) are not native; the terrain is switched to the hub's
captured resource rather than loaded natively; two-player scene changes
reject. The level loop's 179F8, the message producer, renderer and audio remain
outside. What follows the hub (the hint screen and the second level) is
[[03_Reverse_Engineering/findings/FIND-0053-second-level-entry]].
TASK-0010 remains in progress; **native playability: none**.
