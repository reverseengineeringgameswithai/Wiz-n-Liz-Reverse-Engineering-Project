---
id: FIND-0049
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# The spell's completion: the recipe, the sparkle and the exit door

Task: [[07_Tasks/TASK-0010-grounded-controller]]. ROM SHA-256:
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`. Scope/hashes:
`re/completion_step.json`; validation: `re/completion_validation.json`. Source:
`src/sim/spell.*` (recipes, `SpellSparkle`, `ExitDoor`, `DoorSign`),
`src/sim/mixed_pool.*` (`complete_spell`, `walk_anchor`, `walk_sparkle`),
`src/sim/return_only.*` (`SpellPhase`, `step_spell_countdown`),
`src/sim/transition.*` (`start_spell_fade_out`). Evidence:
`tools/completion_compare.py`, `tools/genesis_world_session.py`,
`tools/genesis_world_pool.py`. Continues
[[03_Reverse_Engineering/findings/FIND-0048-spell-mixing]] (the anchor's 7B42
countdown), [[03_Reverse_Engineering/findings/FIND-0021-tally-palette]] (1324E),
[[03_Reverse_Engineering/findings/FIND-0040-setup-message]] (CB72 and the 6EF0
gate) and [[03_Reverse_Engineering/findings/FIND-0047-level-start-fade]] (the
session's 1345A timer).

## Static ranges and contract

| Half-open range | Instructions | Contract |
| --- | --- | --- |
| `[7B4E,7B56)` | 1 | After 13294: the anchor's +16 = 7B58 |
| `[13294,132D2)` | 8 | 1324E's fade-out twin: FF0B90 = 0001, FF0B92 = 0006, FF0B94 = 0000, FF0EDE cleared, FF0B98/9C/A0 = 135EA; FF0B96 (the level) kept |
| `[7B58,7B8A)` | 11 | Returns while FF0B90 is nonzero; else +46(A5) = D269 ("SPELL COMPLETED! / DOOR OPEN!", priority 01) through CB72, A6 saved around BSR 7E18, JSR 1324E, +16 = 7B8A |
| `[7B8A,7B9C)` | 4 | Returns while FF0B90 is nonzero; else +16 = 12646 |
| `[7E18,7ED6)` | 49 | The FF31AC and FF31B0 objects' fruit, (+08 - 0260) / 6 by DIVU.W, into FF31C4/FF31C6; 7ED6 on each; FF31A8, FF31B0, FF31AC cleared; the first 83DA entry naming the pair in either order: sound 9C, JSR (A2), JSR 95EE; none: BRA 9288 |
| `[7ED6,7EF4)` | 8 | Mode 0; with FF31A8 zero the +42 record's object is cleared and its FF312C entry set to FFFF (the FF31A8 path at 7EF4 is outside scope) |
| `[8652,867E)` | 9 | Recipe {6, 5}: FF316C set branches to 9182; else BSR 7F08 at FF0690's (+3C, +3E + 24), FF316C = FFFF, BRA 6F02 |
| `[7F08,7F6A)` | 18 | F9E2; mode 80, frame 021D, (x, y + 4), extents 0010/0010, handler 7F6A, +10 = 0040; sound 90 |
| `[7F6A,7FBE)` | 22 | +10 - 1; negative: JMP FAA4; else E918, and when its low byte is at most 73: E918 Y and X offsets ((r & 1F) - 10), 5A9A, then a fourth E918 whose bit 0 sets the particle's +12 = 4000 |
| `[6F02,6F44)`, `[6F7A,6FB6)` | 26 | 6EF0's allocating path: two F9E2 pops ordered so A4 is lower; the door (higher) gets +36 = A4, (FF0690+3C - 8, +3E + 24), frame 021D, +10 = 001E, handler 6FB6, mode 80, +4A = FF0690, and FF316E names it; A4 keeps F9E2's defaults at (0,0). FF33E2 set (6F44, random positions) is outside scope |
| `[6FB6,6FCA)` | 5 | +10 - 1; negative: 5964 (mode 87, frames 0227..021E, cadence 3, flags & 9FFF) and callback +1A = 6FCA |
| `[6FCA,705C)` | 27 | Sound 95; +2 + 8, +4 - 8; frames 00B0/00A8/00B7, cadence 3, extents 0010/0020, mode 81, +46 = 705C, +16 = 12646; 4C08 on the +36 object, door +3A = it, its +6 = 00D2 |
| `[4C08,4C34)`, `[4C34,4C52)` | 16 | The sign: mode 80 at (x, y - 24), +6 = FF0690+3A (then 00D2), handler 4C34 with +22 = 4C52; 4C34 adds the next table word to Y, wrapping after fourteen |
| `[705C,7072)`, `[7080,7082)` | 6 | AC5E against FF0690; a contact (7082, entering the door) and FF33E2 set (7072) are outside scope |
| `[95EE,9614)` | 9 | MOVEM around: FF31A6 set calls 9682, FF31A4 set calls 9614 (both outside scope) |

1,012 new code bytes / 219 instructions, plus the 83DA recipe table (631 bytes:
105 six-byte entries and the FF terminator) and the 4C52 sign table (28 bytes):
1,671 newly classified bytes. The recipe table names 105 unordered fruit pairs,
each with its own effect routine (105 distinct addresses); 9288 is both the
{7, 1} effect and the no-match branch. Only 8652 is reconstructed.

**Interpretation (probable):** after the 300-frame mix the screen fades out,
the two ingredients disappear and the recipe their fruits select is cast: in
this level {6, 5} conjures sparkles where the spell was mixed and opens the
exit door there (a puff, then the door with a bobbing sign above it), announced
as SPELL COMPLETED! / DOOR OPEN! as the screen fades back in. Touching the door
ends the level.

## Native implementation

`SpellCountdown` gains `SpellPhase` (7B42, 7B58, 7B8A); `step_spell_countdown`
takes the session's `TransitionState` and runs 13294 (`start_spell_fade_out`)
and the two waits, reporting `complete` or `revealed`. `MixedPool::step` (with
the timer as a new parameter, committed with the phase) runs
`complete_spell` for `complete`: D269 through `post_message`, 7E18's fruit and
7ED6 (records cleared, FF312C entries FFFF), the `recipes` table lookup, sound
9C, recipe 8652 (sound 90, `make_spell_sparkle`, FF316C = FFFF, `make_door_sign`
and `make_exit_door` from two allocations, FF316E), the 95EE gates and 1324E;
`revealed` installs the RTS handler (the object becomes a `ReturnOnlyObject`).
`SpellSparkle` (7F6A), `ExitDoor` (6FB6, 5964 with 6FCA, 705C) and `DoorSign`
(4C34) walk in the pool; 6FCA's 4C08 raises the sign through the door's +36
identity. `PickupWorld` carries FF31A8, FF316C, FF33E2, FF0690's +3C/+3E,
FF31C4/FF31C6 and FF316E. Every unsupported path rejects with no change:
another recipe or none, 9182, FF31A8 set, two players, the 95EE gates,
exhausted allocation, any other presentation callback and entering the door.

## Restricted original comparison

`re/completion_step.json` declares the regions, the two tables, 44 transfers
and the previously mapped scope; the probe decodes 437 instructions (GNU
corroborates fifteen forms) and requires every transfer to stay in the graph or
reach a declared stop (every other recipe effect among them).

- `--anchor` (3,141 cases, up to 512 walks): 388 fade-outs started from 7B42,
  217 completions reached, 226 reveals, 629 waits, 139 countdowns, 1,542
  inactive anchors; the transition block is compared after every case.
- `--completion` (3,333 cases): 256 completions (207 messages shown, 49
  refused; 142 P1, 114 P2 controls), 791 waits, and every stop: 677 other
  recipes, 371 no-recipe or 9288, 465 FF31A8, 225 9182, 82 two-player, 73 9682,
  69 9614, 324 exhausted allocations. Every uncontracted RAM byte, the CB9A VDP
  sequence, the free stack and the three new objects' handlers are checked.
- `--sparkle` (4,110 cases, up to 96 walks): 1,616 releases, 1,240 with
  particles (1,124 flagged 4000), 1,772 exhausted allocations.
- `--door` (4,136 cases, up to 96 walks of door and sign in slot order): 322
  puffs started, 443 doors opened (sound 95), 1,821 bobbing signs, 519 entries,
  351 two-player stops, 11 callbacks.

**14,720 cases match exactly in debug, release and sanitize**; all 219 new
instructions execute (430 in all). The session-051 anchor corpus moved here:
its reference mode now continues through 13294.

## Ordinary recording evidence

Fresh P1 and world replays of 634..1515 (the walk recipe now also traces FF31A8,
FF316C..FF3171, FF31C4..FF31C7 and FF0690's +3C/+3E; independent unhooked
endpoint equal to both) with a fresh setup capture:

- **1433:** the anchor (slot 58) runs 13294 from its walk: the session's timer
  restarts in the positive direction from level 14 (1345A returns through its
  second RTS, 134D4, on the level steps 1440..1446; the last step, at 1447,
  clears FF0B90 and returns through 134B0).
- **1447:** with FF0B90 clear, 7B58 posts D269 (row 12 cleared at VRAM E60E),
  7E18 reads fruits 6 and 5 (FF31C4/FF31C6), deactivates slots 67 and 66 (their
  records cleared, two FF312C entries FFFF), clears FF31A8/FF31B0/FF31AC and
  selects 8652: sound 9C, the sparkle in slot 55 at (352, 252) with sound 90,
  FF316C = FFFF, then 6F02's pops: the sign in slot 47 at (0, 0) and the door in
  slot 48 at (344, 248), FF316E naming it; 1324E restarts the timer for the
  fade-in (level steps 1454..1461).
- **1448..1512:** the sparkle walks 65 times (157 E918 calls, 31 particles) and
  releases itself on the 65th; 7B8A sees FF0B90 clear at 1461 and installs
  12646 (the anchor is a return-only object again).
- **1478:** the door's 30-walk countdown ends: 5964's puff (mode 87 from 0227).
- **1508:** the puff reaches 021E: 6FCA requests sound 95, moves the door to
  (352, 240), dresses it (00B0..00B7) and raises the sign above it, which bobs
  from 1509; 705C then misses P1 every frame until 1514.

FF0690's +3C/+3E (352, 224) has no writer in the window and FF33E2 stays 0.
Native `wiznliz-session --world-session` matches the setup line and, with **no
supplied loops**, all 881 fade-timer states (the timer as each frame's 1345A
left it; the world's 13294 and 1324E restart it inside the loop), **all 881 P1
calls** (18 sound requests) and **all 881 object loops** from 634 through 1514:
12,040 walk updates, 79 births (73 particles, two copies, P1's reversal effect,
the sparkle, the door and the sign) and 69 releases. P1's evidence is checked in
three segments split after 1433 and 1447, each joined by exactly what 13294 and
1324E write; the cross-check ties 881 tracking values and 166 owner positions to
P1, and the fade's 24 palette requests match its level steps. Release and
sanitize reuse the capture with the same output digest.

## Limits and next validation

Entering the door (705C's 7082 path at 1515, with 4CA2 and the switch of P1's
actor to the 710E exit handler), the other 104 recipes, 9288 and 9182, the
FF31A8 path, the 95EE gates and both two-player branches are not native; the
run ends at 1514. The message producer, the FFFF32C2 object's E918 calls, the
fade's palette consumers, rendering and audio remain outside it. Next: P1
enters the door at 1515. TASK-0010 remains in progress; **native playability:
none**.

Update: [[03_Reverse_Engineering/findings/FIND-0050-door-entry]] makes entering the
door native (705C's 7082 with 4CA2) and carries the joined run to the level's end
at 1532.
