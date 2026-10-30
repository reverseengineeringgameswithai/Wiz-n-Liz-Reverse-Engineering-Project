---
id: FIND-0048
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# The second ingredient, the spell countdown and the 7CC8 producer

Task: [[07_Tasks/TASK-0010-grounded-controller]]. ROM SHA-256:
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`. Scope/hashes:
`re/spell_step.json`; validation: `re/spell_validation.json`. Source:
`src/sim/mixed_pool.*` (`walk_delivered`, `mix_spell`, `step_world_phase`),
`src/sim/return_only.*` (`SpellCountdown`, `step_spell_countdown`). Evidence:
`tools/spell_compare.py`, `tools/genesis_world_session.py`,
`tools/genesis_world_pool.py`. Continues
[[03_Reverse_Engineering/findings/FIND-0044-first-ingredient]] (the
FF31AC-zero paths), [[03_Reverse_Engineering/findings/FIND-0031-table-motion]]
(7A88 and the 7CC8 writer fragment) and
[[03_Reverse_Engineering/findings/FIND-0047-level-start-fade]] (the joined run).

## Static ranges and contract

| Half-open range | Instructions | Contract |
| --- | --- | --- |
| `[7A00,7A26)` | 8 | 79B6 with FF31AC nonzero: +46(A5) = D22F and JSR CB72; D0 = +32 of the FF31AC object (A0 survives CB72); NEG.W; +32 = D0; +10 = 000E; JSR 7AD6; RTS (no FF31BE/FF31BC store) |
| `[7AE6,7B22)` | 13 | 7AD6 with FF31AC nonzero: A4 = FF31B8; FF31B0 = A4; FB06 copies the copy into it; the copy's +42 record names A4; JSR FAA4 releases the copy; A6 = FF31C0 (the anchor): +16 = 7B42, +4A = the copy's control, +10 = 012C; A6 restored; RTS |
| `[7B42,7B4E)`, `[7B56,7B58)` | 4 | The anchor's handler: SUBQ.W #1,+10; BPL to the RTS; a negative result calls 13294 (not reconstructed; the +16 = 7B58 store at 7B4E stays static) |
| `[7CC8,7CEA)` | 6 | Already classified (the table-motion writer fragment): with FF31B0 nonzero, FF31BE − 1, and on a negative result FF31BC + 1 and FF31BE = 0028 |
| `[7CEA,7DB8)` | 48 | With FF31AC and FF31B0 both nonzero: when the FF31AC object's +32 is non-negative and the FF31B0 object lies lower (CMPA/BCS), or negative and it lies higher (CMPA/BHI), the two objects exchange +06, +08, +0A, +0C, +0D, +10, +36, +32, +2E, +02 and +04; RTS |

318 new bytes / 73 new instructions. 7CC8 is called by BSR at 6972 in the main
loop each frame, after the banner and before P1's last input conversion (697A)
and the object loop. D22F is `01 14 FE 01 5A "SECOND INGREDIENT COLLECTED!" FE
01 3C FE 01 5A "SPELL BEING MIXED!" FF` (priority 01, refused while +53 holds a
higher signed priority). FF31B0 is the object identity that 7808's rising pair
and 7910 already test for zero; FF31C0 is the second member of the setup's 7B9C
pair, dormant until 7AE6.

**Interpretation (probable):** the second delivered fruit becomes a second
bobbing ingredient that drifts opposite to the first; the two are kept in
screen order by 7CC8 as they cross, FF31BC counts 41-frame steps of the
mixing (0028 reloads), and the anchor's 300-frame countdown ends the mixing at 13294, where
7B58 later announces SPELL COMPLETED! / DOOR OPEN!.

## Native implementation

`MixedPool::walk_delivered` now takes both 79B6 paths. With FF31AC naming a
table object it posts `SetupMessage::second_ingredient`, gives the copy the
negated drift, makes the dormant FF31B8 object that table object, names it in
the record and in `PickupWorld::spell` (FF31B0; `PrivateGlobals::rise_gate`
becomes a nonzero marker so 7808's rising pair moves), and turns the
`PickupWorld::anchor` (FF31C0, moved out of the session's return-only anchor
by `establish_world`) into a `SpellCountdown` with countdown 012C and the copy's
control. `step_spell_countdown` runs the 7B42 handler (with the shared
presentation step) and rejects with no change at 13294. `MixedPool::mix_spell`
is 7CC8: `step_world_phase` runs it before the object loop. Native P1 consumes no
pool or FF31BC/FF31BE state, so running 7CC8 after P1 rather than between the
banner and 697A changes nothing the session models; the joined comparison
checks it every frame. Each call is transactional; a
missing FF31B8 object, anchor, record or FF31BC, or a non-table FF31AC/FF31B0
object, rejects with no change. `wiznliz-collision` gains `--second-ingredient`,
`--anchor` and `--spell-mix`.

## Restricted original comparison

`re/spell_step.json` declares the regions, 13 transfers and the previously
mapped scope; the probe decodes 248 instructions (GNU corroborates twelve
register/short forms) and requires every transfer to stay inside the declared
graph or reach a declared exit (13294, 7B4E, the first-ingredient branches).

- `--second-ingredient` (4,186 cases, up to 64 walks each): 387 second-ingredient
  callbacks (229 P1, 158 P2 controls; 320 messages shown, 67 refused; 152
  negative and 235 non-negative drifts) and 3,799 walks that only animate. The
  harness checks the VDP sequence of the row clear, that the FF31B8 object
  equals the called-back copy and is not changed afterwards, the anchor's
  handler, control and countdown, FF31B0/FF31AC/the record, the free stack and
  every uncontracted RAM byte.
- `--anchor` (2,090 cases, up to 512 walks): 775 completion stops at 13294 (two
  pushes deep), 294 counting and 1,021 inactive anchors.
- `--spell-mix` (4,144 cases): 2,808 with a spell (931 reloads, 1,877
  countdowns; 930 exchanges, 930 kept), 1,336 without; writes outside
  FF31BC/FF31BE, the pool and the stack fail.

**10,420 cases match exactly in debug, release and sanitize**; all 73 new
instructions execute (248 in all, including the six 7CC8 writer instructions
now run as native code).

## Ordinary recording evidence

A light survey trace of 1066..2628 found what follows 1066; this pass's joined
capture of 634..1433 (a P1 replay and a world replay with the pair capture's walk
recipe, frame boundaries and write records; independent unhooked endpoint equal
to both at 1433) then validated it loop by loop:

- **1067:** P1's wrapper pops slot 55 from the shared stack (F994 from its
  reversal code, A6 = FFFF1AB4) for a reversal effect, which walks in the loops
  that follow ([[03_Reverse_Engineering/findings/FIND-0029-mixed-object-pool]]).
- **1103:** P1 touches the 783A probe (slot 63) while link 53 carries pickup 55's
  fruit: the second 7910 delivery (sparkle and the copy in slot 48); link 53 is
  dormant again.
- **1133:** the copy reaches 79B6 with FF31AC = slot 67: D22F is shown (a second
  row clear), the copy's drift is 0001 (FFFF negated), 7AE6 copies it into the
  FF31B8 object (slot 66), FF31B0 and the record name slot 66, the copy is
  released and the FF31C0 anchor (slot 58, walked later in the same loop) takes
  7B42 with countdown 012C; 7808's rising pair now sees FF31B0 nonzero.
- **1134..1432:** 7CC8 runs every frame: FF31BE counts down from 0050 and
  reloads 0028 six times (1214, 1255, 1296, 1337, 1378, 1419), FF31BC reaching
  6 (311 producer writes, all from 7CC8, audited with every E918 write); on 46
  frames (first 1134, last 1429) the two ingredients (slots 67 and 66) exchange,
  each predicted from the previous loop's identities and drift sign and checked
  byte for byte.
- **1433** (survey; the joined capture ends before it): the anchor's 301st walk
  drives +10 negative and calls 13294.

Over the 799 loops the world makes 10,362 walk updates, 45 births (42
particles, two copies and P1's reversal effect) and 47 releases, with two pickup
hits, 17 probe hits, two deliveries, two ingredients and 166 emitter walks.
Native `wiznliz-session --world-session` matches the setup line and, with **no
supplied loops**, all 799 fade-timer states, **all 799 P1 calls** (14 sound
requests) from one seed and 799 held rows, and **all 799 object loops** from 634
through 1432; the cross-check ties 799 tracking values and 166 owner positions
to P1. Release and sanitize reuse the capture with the same output digest.

## Limits and next validation

13294, the 7B58 store and the rest of the chain (7B58's wait on FF0B90, D269
through CB72, 7E18's recipe lookup at 83DA with its effect and 95EE, 1324E from
the world and 7B8A) are not native, nor 6EF0's allocating path; the run ends at
1432. The message producer, the FFFF32C2 object's E918 calls, rendering and
audio remain outside it. Next: reconstruct the spell's completion from 1433.
TASK-0010 remains in progress; **native playability: none**.

Update: [[03_Reverse_Engineering/findings/FIND-0049-spell-completion]] continues the
anchor through 13294, 7B58's completion and 7B8A; its corpus moved to
`tools/completion_compare.py`.
