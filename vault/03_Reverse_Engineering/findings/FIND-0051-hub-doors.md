---
id: FIND-0051
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# The scene after the level: its doors, natively from setup to exit

Task: [[07_Tasks/TASK-0010-grounded-controller]]. ROM SHA-256:
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`. Scope/hashes:
`re/hub_step.json`; validation: `re/hub_validation.json`. Source: `src/sim/hub.*`
(`HubDoorRecord`, `update_hub_door_states`, `HubDoor`, `step_hub_door`,
`vanish_hub_door`, `hub_requested_position`, `hub_loop_ends`),
`src/sim/mixed_pool.*` (`HubWorld`, `MixedPool::initialize_hub_doors`,
`enter_hub_door`, `initialize_hub`, the hub branch of `step_world_phase` and
`step_mixed_session`). Evidence: `tools/hub_compare.py`, `tests/hub_cases.py`,
`tools/genesis_hub_session.py`, `genesis_session_capture.py`'s `hub` variant.
Continues [[03_Reverse_Engineering/findings/FIND-0050-door-entry]] (the level's
end), [[03_Reverse_Engineering/findings/FIND-0019-coasting-handler]] (630A/632A),
[[03_Reverse_Engineering/findings/FIND-0016-up-down-actions]] and
[[03_Reverse_Engineering/findings/FIND-0018-actor-transition]] (13208).

## Survey: from the level's end to the next scene

Research traces of 1530..1800 (ignored `local/generated/scene-research`):
the level loop returns at 1532 (FF33E0 = 7 is not 0E); the top-level loop
(0x424 calls the level, 0x42A.. tests FF33E0, 0x470 calls 17400, 0x488 copies
FF4446/48 into the control's +A2/+A4) calls **5D30**, the scene between levels.
Its setup: 16EA4 (VDP, clears, F850's pool reset at 1535..1536: F872 then
F940), 9880 (each control's actor at the control's +A2/+A4 + (0114, 00B0),
movement parameters, 5964's appearance with callback AA50: the two 5964 calls
at 1537), 17284, 660E, FF33E0 = 7, 446C on both controls, map, graphics and
palette loading, 3C2A, then at 1562 **63A4 and 60E6** (the doors), 63E2's
banner with D1 = 0D, FF3412 = C7C8 (the HUD sprite callback C086), FCB94/FCB7E
(music 4F) and FF0B92 = 0A. Its loop 5EEA..603E has the level loop's shape
without 179F8 (so no per-frame banner, no 6554), 7CC8 or C086: input, 976E,
1720C, 14DA2, P1 converted at 5F2E and its wrapper returning at **5F3A**, the
68-slot walk, cameras, the renderer (B0C8, whose sprite pass clears each
visible object's +14) and **6024's exit test**. In the movie P1 walks (Up/Down
held on 110 frames), touches door 0 at **1742**, coasts through the exit fade
and the loop returns at **1758**; the next scene starts after it.

## Static ranges and contract

| Half-open range | Instructions | Contract |
| --- | --- | --- |
| `[5E86,5E8E)` | 2 | The setup's BSR 63A4, BSR 60E6 |
| `[63A4,63E2)` | 15 | FF33E2 clear and FF33C4 & 7 zero: the first eight records' +8 = FF33C4 >> 3, FF33DE (byte) cleared |
| `[60E6,611E)` | 14 | Eight FF330C records (nine with FF33E2), 14 bytes: +0 X, +2 Y, +4 number, +8 state, +A marker; BSR 611E each |
| `[611E,61F6)` | 45 | F9E2: +22 number, (X, Y), mode 80, frame 00B0, handler 12646; BSR 6334, +26/+2A its objects; +8 non-negative: mode 81, frames 00A8/00B7, 3/3, +10 = 003C, handler 61F6; negative: a F9E2 lock at (X - 8, Y), frame 00CD, then with FF33E2 and +A non-negative a F9E2 partner at (X - 1, Y + 7), frame 0217 (+A nonzero: X + 2, 0218, +12 EOR 0800) |
| `[6334,639A)` + `[639A,63A4)` | 22 + 10 data | Two F994 objects (A4, A5), mode 80: (X - 10, Y - 0A), (X + 8, Y - 0A), frames 00B8 + the 639A byte at the number's EXT.W low byte, and that plus one |
| `[61F6,621A)` | 7 | +10 - 1; negative: extents 0010/0018, +46 = 621A, +16 = 6218 (an RTS) |
| `[621A,623C)` | 9 | AC5E with FF0690, then FF0838 behind FF33E2; a contact continues at 623C |
| `[623C,630A)` | 35 | JSR 17298 (A5: the touching control); FF4446/FF4448 = +2/+4 - 0114/0098, AND FFF8; FF3398 = FF330C + LEA (A0, MULU.W #0E of +22 as a word); X - 4, Y + 8, mode 85, frames 021E/021E/0227, target 0227, 3/3, callback FAA4, +10 = 0, handler FAC4, service 6218; FA8C on +26, then +2A; 630A on FF0690 and FF0838; JSR 13208 |
| `[17298,172BE)` | 8 | The control's +46/+4E = FFFFFFFF, +52/+53/+54/+56/+58 cleared |
| `[FA8C,FAA4)` | 7 | A5's mode cleared, its slot pushed |
| `[FAC4,FAE4)` | 7 | +10 - 1; negative: X - 4, mode 85, +6 = +8, +16 = FAE2 (an RTS) |
| `[5F5E,5F76)` | 7 | The hub loop's walk body: active gate, F76C, handler, service |
| `[6024,6040)` | 7 | FF0690's +1A6 = FFFF and FF0B90 zero: RTS at 603E (the scene ends); else BRA 5EEA |

866 code bytes / 185 instructions plus the 10-byte number table: **876 newly
classified bytes**. The 6090 seed records (6040, not executed in the window)
place eight open doors and a closed ninth for two players.

**Interpretation (probable):** after a level the game shows a map with eight
numbered doors; each opens after a second, and touching one stores where the
player stood (FF4446/48, the position the next return to this scene uses),
names the chosen record (FF3398), puffs the door away, takes both players'
control (630A) and fades out; the scene ends when the fade does.

## Native implementation

`HubDoorTable`/`update_hub_door_states` (63A4) and
`MixedPool::initialize_hub_doors` (60E6 with 611E and 6334, every pop in
order, all-or-nothing; exhaustion names its allocator) build `HubDoor`s (phases
`closed`, `waiting`, `open`, `vanishing`, `puffing`) and their number, lock and
partner objects as `ReturnOnlyObject`s. `step_hub_door` walks a door (FAA4
releases a puff; FAC4 reviving a released slot rejects); a contact makes
`MixedPool::enter_hub_door` run 623C: the entry (17298's control and the door's
number) for the session, FF4446/48 into the session timer's requested
position, FF3398 (`HubWorld::selected`), the vanish, both FA8C releases and
13208 on the timer. `MixedSessionState::hub` (never beside a level world) makes
`step_world_phase` skip 7CC8 and apply 630A to P1 after the loop, and
`step_mixed_session` let Up/Down reach P1's actor (with the session's action
globals) and report 6024's `scene_ended`. P2's 630A is reported, not native.

## Restricted original comparison

`tools/hub_compare.py`: the probe decodes 314 instructions (GNU corroborates
fifteen forms), every transfer stays in the graph or reaches a declared stop
(5E8E, 5F76, FA1E, F9D0, CAF0, 5EEA). Reference modes 10..12 of
`terrain_reference.c` (`--hub-doors`, `--hub-door`, `--hub-exit`):

- `--hub-doors` (3,122 cases: the movie's records over an empty pool, every
  stage class, closed records with locks and partners, every number low byte,
  exhaustion at every allocation, random records and slot orders): 2,492
  setups (923 rewriting +8, 1,414 with closed doors, 824 with partners), 247
  F9E2 and 383 F994 exhaustion stops. Every uncontracted RAM byte is checked.
- `--hub-door` (4,163 cases, 181,385 walks): 410 openings, 448 entries (379 by
  FF0690, 69 by FF0838), 471 puffs, 50 releases, 22 seeded-callback stops and
  the authored revival stop; FF4446/48, FF3398, the timer, both selectors,
  actors and message blocks are compared after an entry.
- `--hub-exit` (286 cases): 80 ends, 206 continues.

**7,571 cases match exactly in debug, release and sanitize**; all 185 new
instructions execute (311 in all).

## Ordinary recording evidence

Fresh P1 and world replays of 1562..1759 (`tools/genesis_hub_session.py`;
independent unhooked endpoint equal to both):

- **1562 (setup):** the reset left all 68 slots free (0..67 bottom first) and
  zero but their 12646 selectors; 63A4 (FF33C4 = 0) rewrote +8, then 60E6 popped
  door 0 into slot 67 with its numbers in 66 and 65 ... door 7 into 46 (24
  objects); all 408 world writes come from 60E6's chain.
- **1563..1741:** 1345A runs the fade-in; each door counts 60 walks and opens
  (1623); P1 walks and holds Up/Down (its actions; FF33E0 = 7, so no sample).
- **1742:** P1 (tracking 01A1/00BC) touches door 0: 17298 clears FF0690's
  message fields, FF4446/48 = 0098/0008, FF3398 = FF330C, the puff at
  (01AC, 00AC), slots 66 and 65 pushed, 630A on both controls (FF0838's actor
  too), 13208's exit fade.
- **1743..1758:** P1 coasts (632A); FAC4 then FAE2 walk the puff; at 1758 1345A
  clears FF0B90 and 6024 returns.

B0C8's sprite pass writes zero over +14 806 times; every other world write of
the 196 loops (3,196) comes from the hub's routines. Native `wiznliz-session
--hub-session` builds the doors from the records and the free stack and, with
one P1 seed and physical held sets, matches the setup's pool image, **all 196
P1 calls** (two sound requests), the timer after every 1345A, FF4446/48 and
FF3398 after every loop, the entry at 1742, 6024's end at 1758 and **the
pool image (every occupied slot's fields and the free stack) after every
loop**. P1's evidence is validated in two segments split after 1742, joined by
exactly what 630A and 13208 wrote.

## Limits and next validation

The scene change before 1562 (the main loop's exit, F850's reset, 9880's
actor initialization at FF4446/48 + (0114, 00B0), 446C, the map and graphics
loading) is not native; the hub session is seeded at its first loop (P1, the
timer) and builds its world from the records, so the level run and the hub are
not yet one joined run. Closed doors, two-player entries and P2's actor are
covered only by the restricted corpora; the message producer (which rewrites
P1's +56 after the entry), the HUD, renderer, audio and the next scene remain
outside. Next: join the level's run to the hub through the scene change.
TASK-0010 remains in progress; **native playability: none**.

Update: [[03_Reverse_Engineering/findings/FIND-0052-scene-change]] makes the scene
change native, so the level and this scene run as one native run from one P1
seed (1,095 P1 calls and loops), P1 no longer reseeded at 1563.
