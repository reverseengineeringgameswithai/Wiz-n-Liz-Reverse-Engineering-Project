---
id: FIND-0020
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# Bounded tally path through 51C8 and 5222

[[07_Tasks/TASK-0010-grounded-controller]] now implements the recorded zero-gate
51C8 path, the common 5222 path with an explicit unsupported bonus branch, and
its countdown/credit helpers. **210 disjoint bytes / 48 instructions** have
original/native comparisons. This is partial handler coverage, not complete
reconstruction of either handler. `re/tally_step.json` defines exact executable
and rejected ranges; `re/tally_validation.json` indexes this pass's evidence.

## Boundaries and native behavior

| Half-open range | Verified behavior |
| --- | --- |
| `[51C8,51D0)` | Test FF33CE; zero branches immediately to 5222 without assigning a new handler; nonzero reaches unsupported 51D0 |
| `[5222,5266)` | Reload associated control from actor+4A; JSR A148; remaining-unit/Start/shared-gate decisions; special combination reaches unsupported 5266 |
| `[52A6,52B0)` | Set shared world mode to 3 and RTS; preserve handler selection |
| `[537C,53DE)` | Countdown or consume one remaining unit, add three credits, request sound and reload countdown |
| `[AF98,AFB0)` | Wrapped word addition followed by unsigned cap at 180 |
| `[4F8C,4F8E)` | Shared return-only RTS |

The native dispatcher retains `MotionUpdate::tally` (51C8) or `tally_wait`
(5222). Branching from 51C8 to 5222 happens within the current invocation; the
original pending return remains F906. A148 is a subroutine here: its pending
return is 522C. The 537C continuation is a tail branch with F906 still pending.
AF98 returns to 53AE and the sound request returns to 53D4. No branch is treated
as a new game frame. Existing A148 coasting and persistent scratch are reused.

`TallyState` supplies the exact word fields:

| Logical field | Original storage | Ownership/scope |
| --- | --- | --- |
| palette_gate | FF33CE | External world gate; nonzero 51C8 path unsupported |
| remaining | associated control +84 | Decremented by 537C |
| skip | FF0F0E | Shared flag; Start sets FFFF only while previously zero |
| countdown | FF340A | Shared word; decrement until negative, then reload 3 on consumption |
| credit | FF3402 | Shared accumulated word; wraps before unsigned clamp |
| special_gate | FF0104 | External gate for the unimplemented special path |

`ActorInput::start` models control+21 separately from the raw +14 byte. With
remaining units, zero skip plus any nonzero Start bypasses the countdown once.
Otherwise a nonnegative countdown decrements and returns—even zero merely
becomes FFFF. A negative countdown consumes one unit. Consumption adds three
credits, emits `(140,6,192,1)` and sets countdown=3. It does not complete the
world mode in that invocation when the last unit becomes zero.

With no remaining units, nonzero skip or Start can set mode=3. When skip and
special_gate are both zero, Start plus raw bits `(raw & 70)==10` reaches 5266.
That sample/allocation path rejects transactionally. The separate nonzero
palette-gate path rejects before coasting. Missing required context, resource/
budget failure or an unknown late service rolls back actor, scratch, tracking,
tally/global state and requests. Inactive wrappers invoke neither handler path.
Sound requests are logical effects; audio consumption is outside this contract.
The broader gameplay meanings of remaining and credit are not assigned here.

## Evidence and limits

- Exact ROM hashes, original-68000 sentinels, instruction boundaries and closed
  graph pass, with explicit exits at 51D0 and 5266. Four new GNU checks pass;
  the inherited presentation BCHG decoder limitation remains documented.
- **231,475 original/native cases per debug/release/sanitize preset**, identical
  output hashes, nineteen authored goldens and all 48 new instructions visited.
  Separate sweeps cover every countdown, credit and remaining-unit word;
  bounded raw-byte/Start/skip combinations, repeated calls, both facings,
  inactive states, arithmetic extremes and authored/cataloged terrain also pass.
  This is not a Cartesian proof of all state combinations.
- Native tests verify deferred completion, retained selectors, signed countdown,
  wrapped credit, held Start, continuous counters, unsupported paths and rollback.
  Synthetic trace tests reject missing boundaries, wrong pending returns,
  out-of-handler mutations, unknown completion modes and overflow.
- The ordinary preserved movie at **[3403,3578)** supplies **175 continuous P1
  wrappers**: 142 countdown-helper calls, five credit/sound events, 33 empty-unit
  decisions, and completion at **3577**. Actor/service/tracking and mutable
  tally counters persist natively across every invocation; no actor/counter
  reseeding. Input, scratch and other world feeds remain explicit.
- The wrapper returns to **7EC** in this window. No ROM/RAM/register/input edits
  are used. An independent unhooked replay matches the declared covered-state
  endpoint, which excludes hidden device state. This is not whole-frame parity.

The recorded path never enters 51D0, 5204 or the special allocation at 5266.
These are not silently skipped or claimed implemented. Surrounding world entry,
P2/shared scheduling, palette consumers and complete allocation remain open.
Prior coasting, transition and wrapper movie contracts were rerun separately;
older 507 actor/presentation and 92 actor / 24 effect contracts and the full
survey were not rerun this pass. See [[05_Validation/RESULTS]].

## Exact next task

Reconstruct **51D0's nonzero-gate path and deferred handler 5204**, including
137CE/1372C palette preparation and 1324E initialization, before advancing to
5132/5188. Use a labeled controlled-state experiment because the preserved
ordinary 51C8 window takes the zero branch. Derive exact mutations and compare
hooked/unhooked endpoints. Keep 5266's allocation path separately unsupported.
TASK-0010 stays in progress; native playability remains none.


Subsequent scope: [[03_Reverse_Engineering/findings/FIND-0022-bonus-slots]] now
implements 5266 and the D2=0 helper path. Its control-table assignments supersede
the earlier allocation lead and unsupported statement above. Earlier validation
counts remain historical; no original report is rewritten.
