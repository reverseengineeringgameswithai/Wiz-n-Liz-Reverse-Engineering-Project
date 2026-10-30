---
id: FIND-0044
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# callback79B6 and 7AD6: the first ingredient collected

Task: [[07_Tasks/TASK-0010-grounded-controller]]. ROM SHA-256:
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`. Scope/hashes:
`re/ingredient_step.json`; validation: `re/ingredient_validation.json`. Source:
`src/sim/mixed_pool.*`. Evidence: `tools/ingredient_compare.py`,
`tools/genesis_pair_initializer.py`. Continues
[[03_Reverse_Engineering/findings/FIND-0043-fruit-delivery]] (the copy),
[[03_Reverse_Engineering/findings/FIND-0031-table-motion]] (7A88 and the
`[7A46,7A58)` FF31BC writer, which is 79B6's tail),
[[03_Reverse_Engineering/findings/FIND-0040-setup-message]] (CB72/CB9A) and
[[03_Reverse_Engineering/findings/FIND-0038-setup-prefix]] (the FF31B4 object).

## Static ranges and contract

| Half-open range | Instructions | Contract |
| --- | --- | --- |
| `[79B6,7A00)` | 14 | The copy's callback (F84E's JMP (A0), A6 = the copy): X + 8, Y + 4; +06 = +08 = +22, +0A = +26; mode 81; JSR 6BB2 (cadence from +10, still the carried count); handler +16 = 7A88, +2E = 7A58 (cursor 0), +36 = 0; A5 = +4A; A0 = FF31AC, nonzero continuing at 7A00 |
| `[7A26,7A46)` | 5 | FF31AC zero: +46(A5) = D20E and JSR CB72; +32 = FFFF; +10 = 000E; JSR 7AD6 |
| `[7A46,7A58)` | 3 | Already classified (the FF31BC writer fragment): FF31BE = 0050, FF31BC = 0000, RTS |
| `[7AD6,7AE6)` | 3 | A4 = FF31AC; zero branches to 7B22 |
| `[7B22,7B42)` | 7 | A4 = FF31B4; FF31AC = A4; FB06 copies the copy into it; the copy's +42 record names it; JSR FAA4 releases the copy |

154 new bytes / 29 new instructions. 79B6 and 7AD6 read FF31AC once each and
nothing between changes it. The walk then reads the released copy's handler,
now 7A88, and runs it on the released slot with the new FF31BC (0), then the
12646 service. CB72 reads only the message's first byte: D20E `01 14 FE 01 5A
"FIRST INGREDIENT COLLECTED!" FF` has priority 01, so it is refused while +53
holds a higher signed priority.

Not reconstructed (FF31AC nonzero, the second ingredient): `[7A00,7A26)` posts
D22F (`01 14 FE 01 5A "SECOND INGREDIENT COLLECTED!" FE 01 3C FE 01 5A "SPELL
BEING MIXED!" FF`), sets +32 to the negated +32 of the FF31AC
object and +10 = 000E; `[7AE6,7B22)` copies into FF31B8, stores that object in
FF31B0 (the 7910/7808 gate), names it in the record, releases the copy, then
gives the FF31C0 anchor handler 7B42, +4A = A5 and +10 = 012C. 7B42 counts down
and runs 13294, then 7B58 waits on FF0B90, posts D269 (`01 78 "SPELL COMPLETED!"
FE 01 3C FE 01 78 "DOOR OPEN!" FF`) through CB72 and runs 7E18 and 1324E (7B8A);
none of it is native.

**Interpretation (probable):** delivering the first fruit makes it the first
collected ingredient: the copy becomes a bobbing table-motion sprite held in the
FF31B4 slot, FIRST INGREDIENT COLLECTED! is shown, and FF31AC remembers it so
the second delivery takes the other path: the second sprite mirrors the first's
drift, the spell is mixed and the anchor's 7B42 chain announces SPELL COMPLETED!
and DOOR OPEN!, the level's exit.

## Native implementation

`MixedPool::walk_delivered(id, globals, world)` and `MixedPool::step` (with a
`PickupWorld`) run a delivered copy's walk; when its presentation fires 79B6
with FF31AC absent they apply the whole first-ingredient path: the copy's
fields become a `TableMotion` (mode 81, frames back, 6BB2 cadence, cursor 0,
+32 = FFFF, +36 = 0, +10 = 000E); `post_message` (CB72, now shared with 7DB8)
posts `SetupMessage::first_ingredient` to the copy's control and returns CB9A's
`MessageRowClear`; the dormant FF31B4 object becomes that table object, FF31AC
and the record name it, FF31BE = 0050 and FF31BC = 0; the copy is released and
its slot keeps a mode-0 table object after one 7A88 run with FF31BC = 0.
`PickupWorld` gains FF31AC, FF31B4/FF31B8, both controls' message fields, the
tilemap, FF31BE and the row clears; `MixedPool::step` takes mutable
`PrivateGlobals`, so 79B6's FF31BC store reaches later table objects in the
same phase and commits with it. FF31AC present, a missing or non-dormant FF31B4
object, a missing record, message or globals reject with no change.
`wiznliz-collision --ingredient` exposes the walk.

## Restricted original comparison

`--ingredient` walks a seeded copy (up to 64 walks) through 69AA, F76C, 79B6,
6BB2, CB72/CB9A (VDP words sunk and checked: 8004, a VRAM write command, 26 data
words of 1 while FF010C is 1, 8014), 7AD6, FB06, FAA4 and 7A88 on the released
copy, with FF31AC, FF31B4, the record, the control's +46/+53/+56, the tilemap,
FF31BC and FF31BE; it stops at the second-ingredient branch (7A00). It checks
every copy, FF31B4-object, record, message, global and free-stack byte outside
the printed fields, that the FF31B4 object equals the called-back copy and that
the released copy differs from it only where FAA4 and 7A88 write.
**4,172 cases per debug/release/sanitize** match exactly: 340 callbacks (211 P1,
129 P2 controls; 285 messages shown, 55 refused; 76 with the fast cadence),
3,811 walks that only animate and 21 second-ingredient stops. All 29 new
instructions execute (178 in all). GNU corroborates ten register forms.

## Ordinary recording evidence

A fresh hooked replay of frames 0..1066 with an independent unhooked endpoint
now also traces FF31AC..FF31BF, both controls' +46..+57 and the FF0D60 tilemap
at every walk, and the FF31B4 object after FB06 at the FAA4 call. At **frame
853** the copy (slot 47, carrying pickup 54's fruit, record 1) reaches 79B6 on
its 30th walk with FF31AC zero. P1's +46 was FFFFFFFF with +53 = 0 (MIX THOSE
FRUIT no longer held), so CB72 accepts D20E: +53 = 01 and CB9A clears message
row 12, the write trace reporting command 660E0003 (VRAM E60E). 7AD6 takes
7B22: FB06 copies the copy into the dormant FF31B4 object (**slot 67**), FF31AC
and record 1 (which named link 53) name slot 67, FAA4 releases slot 47 (free
depth 51 → 52), FF31BE = 0050, FF31BC = 0, and 7A88 then runs once on the
released slot 47. Native `--ingredient` matches that walk from its entry state:
the released copy, slot 67, FF31AC, the record, +46/+53/+56, the row clear,
FF31BC, FF31BE and the free depth.

Slot 67 then walks as the table object in the same frame and every later frame:
native `wiznliz-table-motion --scheduled` matches **all 213 walks (853..1065)**
one at a time from each entry state with that walk's FF31BC (0 throughout), and
consecutive walks chain; no byte outside the table object's represented fields
changes. This replaces the 213 original-only slot-67 walks of
[[03_Reverse_Engineering/findings/FIND-0038-setup-prefix]] with native
comparisons; the retained-slot continuity itself still stops at the conversion.

Update: [[03_Reverse_Engineering/findings/FIND-0045-retained-world]] runs the 853
walk inside the native retained world, with P1's message fields carried from the
setup and updated only where the message producer changed them; the
retained-slot continuity is no longer the only follower of slot 67.

## Limits and next validation

Newly mapped: 79B6 and 7AD6 (partial: their FF31AC-nonzero paths reject).
The second-ingredient path, the anchor's 7B42 handler chain (13294, 7B58 with
D269, 7E18, 1324E, 7B8A), FF31B0 as an object identity, the mixed session's
`PickupWorld`, the 6C00 family branches, the gated-pair leads, overlap-hit
FF31C0 readers and gate producers remain unreconstructed or unsupported.
TASK-0010 remains in progress; **native playability: none**.

Update: [[03_Reverse_Engineering/findings/FIND-0048-spell-mixing]] makes the
FF31AC-nonzero paths native (D22F, FF31B8/FF31B0, the anchor's 7B42 countdown)
and adds 7CC8; 13294 and the rest of the 7B58 chain remain.
