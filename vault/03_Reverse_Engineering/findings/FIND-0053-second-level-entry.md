---
id: FIND-0053
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# After the hub: the hint screen and the second level's entry

Task: [[07_Tasks/TASK-0010-grounded-controller]]. ROM SHA-256:
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
Continues [[03_Reverse_Engineering/findings/FIND-0052-scene-change]] (the level
and the hub as one native run, 634..1758). Session:
[[08_Sessions/2026-10-28-056-second-level-entry]].

## Correction of the planned order

Session 055's plan read 0x4A4..0x73E statically and expected the top-level
loop to return to 0x424 and 6664 (the first level's setup) next. The recording
shows otherwise: the BSR to 754 at 0x4EA is itself the second level. 754 sets
FF33E0 = 0013 and loops at 0x792 while FF33E0 stays 0013; it returns (0x4EE)
only when that level ends, and only then does FF33E0's dispatch (3, 1, 0B, 0C,
else 73E) run. 6664 is not reached between the hub and the second level.

## Survey: frames 1757..2116

Two research traces of the preserved recording (owned workers, no edits): a
frame map of the top-level PCs over 1755..2400, and every return in the
sequence below with P1's actor, both controls, the timer, FF0ED8..FF0F1F,
FF4442..FF444D, FF3398..FF341F, FF13C0..FF1417, FF3170..FF31C7 and the pool
head, plus the RAM at every frame boundary (`local/generated/second-level-research/`
`framemap-6dy3_fr6`, `survey-crv67jxz`):

- **1758:** the hub's 6024 returns (603E); 0x4A4: 10D8 sets FF33F0 = 33400 +
  FF3398's +4 × 22 (here 00033400); 10F8 sets FF0690's +10C/+110 and FF33CA/
  FF33CC (0002/0003) from the FF33F8/FF33F4 tables. FF13E2 is 0, so FF33F4's
  +0E goes into FF32BE and 1959E runs.
- **1758..2067, the hint screen (1959E):** unless FF32BE is FFFFFFFF; 16EA4
  (1758..1763: both actors zeroed, the pool reset, 131C2's fade-in with
  FF0B92 = 001E), its text and one scripted sprite (stride 0x90 over the pool's
  memory), FF0F10 = 00F0 (1766). Its loop (19676) runs once per frame from 1767:
  after the frame's 1345A, unless FF0F0E is set, 14DA2 and 14E3C read the pads;
  while FF0B90 is nonzero (the fade-in, 1767..1810) it waits; then Start (the
  raw byte's bit 7 clear) or FF0F10 decremented below zero (1811..2051, 241
  decrements; Start was not pressed) sets FF0F0E and starts 13208's fade-out;
  once FF0F0E is set it returns when FF0B90 is zero (2067). 301 loops. The
  text includes "COLLECT THE LETTERS", "THE FAIRY POINTS TO THE DYING WABBIT".
- **2067..2106, E2A:** 16EA4 again (fade-in, 001E), FF0690's +A2/+A4 and +78/
  +7A cleared, +F2 = FFFF, +38 from the FF33F8/FF33FC tables and FF33C4, then
  9880 rebuilds both actors at their anchors (P1 at (0114, 00B0)); the map,
  graphics, palettes and HUD load (2072..2106).
- **2106, 754's head:** FF33C8 += 1; 118C: 54BA (E918 draws until a map column
  passes its test; the control's +3C/+3E), +1A6 cleared, FF3410 = 00B4, FF33CE
  cleared, FF33D8 = FFFF (FF3402 = 003C is above 000A), 2512's ten objects,
  4484 (the letters), 1386, 1454 (control words), FF33E4 = 1, 9952 on FF0690
  again (P1's appearance: counter 3, flags 0), 17298, E876, FF3400/FF3404; then
  FF33E0 = 0013 (0x774) and 14A4 (the level's music, FCB7E).
- **2107 on, the second level's loop (0x792):** 30C4, B7B6, C842 (FF3404, the
  level's countdown), 976E, 1720C, 14DA2, 14E4E (P1's input, return 0x7DA),
  5716, 57E6, F8F2 (P1's wrapper, return 0x7EC), 3326, 340E, 27A0, B0B0, the
  pool walk (F76C, +16, +46), B0C8, 10868. The 1345A timer runs each frame
  before it (the fade-in, 2107..2150).

The carried state P1's session reads changes only as follows: 16EA4 zeroes
P1's actor twice and restarts the timer; 9880 and 118C's 9952 rebuild the
actor; 98DE and 118C clear the tracking selector; 118C sets FF33D8 = FFFF;
0x774 sets FF33E0 = 0013. P1's tracking position (FF80, FF80) and the terrain
scratch (016C, 004D) carry from the hub; the parameters are 9952's again;
FF33DA stays 000C. E918's state does not change from the hub's end until 2106,
whose code draws it **13 times** (54BA, 1386, 2512's objects); each later loop
draws once.

## P1 in the second level

A P1 session capture of 2107..2700 (`local/generated/second-level-research/`
`p1-l2owkpkt`) shows the input cadence of this loop: 14DA2's two conversions
and P1's at 0x7DA every frame, and 30C4's extra 14DA2 and 14E4E (return 0x313A)
only when FF0B90 is zero after the frame's 1345A (3126 tests it; with Start
held there it would pause, ECF14, which is not native). The existing late-window
P1 session (3100..3200) runs in this same loop.

## Native implementation (checkpoint)

Scope/hashes: `re/second_level_step.json` (six ranges, 182 bytes, 38
instructions, all new). `src/sim/hub.*`: `reset_actor_appearance` (9952's
actor part; `make_hub_actor` now uses it), `merge_action_buttons` (14E3C),
`HintScreen`, `continue_hint_screen`, `step_hint_screen`. `src/sim/mixed_pool.*`:
`enter_hint_screen`, `choose_action_cooldown` ([11A6,11EE) with E918),
`SecondLevelInputs`, `enter_second_level` (E2A's 16EA4 and saved-position
clear, 9880, 54BA's counted draws, FF33D8, the other counted draws, 9952,
FF33E0 = 0013). Transport: `wiznliz-collision --second-level|--hint-screen`
(reference modes 14 and 15); `wiznliz-session --game-session` with the second
level's scene and bank.

Restricted original execution (`tools/hub_compare.py`, debug at this
checkpoint): **10,625 cases match** (1,023 second-level entries, 1,019 hint
loop tests and the hub's 8,583); all 38 new instructions execute.

Offline joined comparison (fresh after-hub and second-level captures with the
fresh all-in-one run `run-s49_3nc8`'s level/hub/scene, through
`tools/genesis_game_session.py`; `local/generated/second-level-research/`
`offline-0fbd1vt2`): the after-hub evidence passes (the carried state changes
only in the reconstructed routines; 301 hint loops 1767..2067; E918 drawn 1 +
0 + 12 times in 2106); P1's evidence holds for 2107..2135 and **rejects exactly
at 2136**: the second level's ten objects (2512's, slots 58..67) query the
terrain through the scratch P1's session owns. One native run then matches the
level and hub (1,095 P1 calls and loops), **all 301 hint loops**, the entry's
P1 seed and 14-field timer row, and **all 29 second-level P1 calls** from one
seed at 634. **Open:** E918's native state at the entry is two draws behind
the capture (11 rather than 13 steps from the hub's-end state F00EED1F): two
E918 draws between the level's last counted draw and the hub's end are not
counted by the joined run. The fresh all-in-one capture, the presets' corpora
and the fresh regression captures are pending.
