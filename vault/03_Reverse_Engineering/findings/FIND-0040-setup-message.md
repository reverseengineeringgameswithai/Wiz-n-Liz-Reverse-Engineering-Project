---
id: FIND-0040
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# 7DB8 setup message, the 6EF0 gate and the 6BD6 pickup service

Task: [[07_Tasks/TASK-0010-grounded-controller]]. ROM SHA-256:
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`. Scope/hashes:
`re/setup_message_step.json` and `re/pickup_service_step.json`; validation:
`re/setup_message_validation.json`. Source: `src/sim/mixed_pool.*`,
`src/sim/collision_probe.*`. Evidence: `tools/pair_initializer_compare.py
--variant setup-message`, `tools/collision_compare.py --variant pickup`,
`tools/genesis_pair_initializer.py`. Continues
[[03_Reverse_Engineering/findings/FIND-0039-setup-tail]].

## Static ranges and contract

| Half-open range | Instructions | Contract |
| --- | --- | --- |
| `[68BC,68C4)` | 2 | BSR 7DB8, BSR 6EF0 (fragment) |
| `[7DB8,7E18)` | 23 | Two players: return. FF31AA set: clear it, FF0690+46 = D2A2. Else count FF312C kinds other than FFFF; with ≥ 2, +46 = D28C. Either store then `JSR CB72` |
| `[CB72,CB9A)` | 11 | Save D0/A4; compare the message's first byte with +53 (`CMP.B`, `BLT`): lower → +46 = FFFFFFFF; else +53 = it and `BSR CB9A` |
| `[CB9A,CC18)` | 32 | Message-row clear: save FF010C and set it to 1, VDP 8004, a VRAM write command for (FF0D60 + 14 + (+56 << 7)) low word, 26 words of 1, restore FF010C, VDP 8014 |
| `[6EF0,6F02)` | 5 | Return unless FF33E2 or FF316C is set; the allocating path at 6F02 (two F9E2 pops, E918 RNG) is not reconstructed |
| `[6BD6,6C00)` | 9 | The pickup service: 78EE's exact miss shape with hit target 6C00 |

The two messages are ROM data, not code: D28C `64 78 FE 01 78 "MIX THOSE FRUIT!"
FF` and D2A2 `64 78 FE 01 78 "FRUIT RETURNED!" FF` (43 bytes). Both lead with
priority byte 0x64. FF0690's +46 here is a message pointer and +53 a signed
message priority; these are fields of the P1 control record, not the actor's
service. 373 bytes in all, none previously classified.

## Native implementation

`continue_level_setup(state, tables)` runs 7DB8 then 6EF0 as one transaction.
`SetupGates` (FF33E2, FF31AA, FF316C, FF0D60) and `ControlMessage` (+46 as an
optional logical `SetupMessage`, +53, +56) are explicit inputs whose producers are
not native. CB72's gate compares 0x64 with +53 as signed bytes. CB9A becomes a
logical `MessageRowClear{vram}` request with the destination word computed as
above; no VDP is emulated natively. 6EF0's closed gate does nothing; an open gate
rejects (`unsupported 6EF0 pair allocation`) with no change, including the
FF31AA clear. `wiznliz-return-only --message` exposes it. The 6BD6 miss path is
`step_pickup`, now exposed by `wiznliz-collision --pickup-service` and
`--pickup-scheduled`.

## Restricted original comparison

`--setup-message` executes `[68BC,68C4)`, 7DB8, CB72, CB9A and the 6EF0 gate, and
stops at 68C4 or at 6F02 (the open path). It reads only the declared gates,
kinds, message fields, tilemap word, lock and the two strings; VDP writes are
sunk and checked as 8004, a VRAM write command, 26 data words of 1 written while
FF010C is 1, then 8014. **4,717 cases per debug/release/sanitize** match exactly:
every priority byte against both messages, every kind count, all gate words,
wrapping rows and tilemaps (1,636 MIX shown, 185 refused; 892 RETURNED shown, 95
refused; 30 with nothing selected; 1,879 open-6EF0 rejections). 73 instructions,
all new; CB9A's 32 are **research-only rendering**, not a native mapping.

`--pickup-service`/`--pickup-scheduled` reuse the 78EE service corpus with 6BD6
installed and the object on record 0: **136,848 cases per preset** match, all 9
instructions execute, and primary/secondary hits stop at 6C00 in the original and
reject natively.

## Ordinary recording evidence

The fresh frames 0..1066 replay verifies one `[68BC,68C4)` run at frame 629 at one
stack depth. Single player, FF31AA zero and two pickup kinds select **MIX THOSE
FRUIT**; +53 was 0, so CB72 accepts it, stores priority 0x64 and calls CB9A.
The 7DB8/CB72/CB9A RAM writes are exactly the +46 store, the +53 store and FF010C
set and restored (it was already 1). The trace also reports **29 VDP port writes**:
8004, command 600E0003 (VRAM E00E = tilemap E000 + 14 + row 0), 26 data words of
1, and 8014. 6EF0's gate is closed (FF33E2 and FF316C zero), so it returns at
once. Native from the 7DB8-entry inputs matches every field, including VRAM E00E.
All earlier retained-slot results and bounds are unchanged.

Update: [[03_Reverse_Engineering/findings/FIND-0042-pickup-hit]] makes the 6C00
hit native, so 6BD6 (FUNC-0133) is now a bounded mapping.

## Limits and next validation

Newly mapped: 7DB8 and CB72 (bounded), the 6EF0 gate and 6BD6 (partial), and the
fragment. The 6EF0 allocating path, native rendering of CB9A and the display that
consumes +46, the 6C00 pickup hit, 6D22/FB06, 7AD6/callback79B6, hit7910 and the
setup from 68C4 (7FBE, 7154, 735E, 7568, then 9874/FCB94 and globals) remain
unreconstructed or unsupported. TASK-0010 remains in progress; **native
playability: none**.
