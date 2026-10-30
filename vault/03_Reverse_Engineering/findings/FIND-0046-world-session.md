---
id: FIND-0046
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# The native player joined to the retained level world

Task: [[07_Tasks/TASK-0010-grounded-controller]]. ROM SHA-256:
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`. Validation:
`re/world_session_validation.json`. Source: `src/sim/mixed_pool.*`
(`establish_world`, `step_world_phase`, `step_mixed_session`),
`tools/native/session_main.cpp` (`--world-session`),
`tools/native/world_transport.hpp`. Evidence: `tools/genesis_world_session.py`.
Joins [[03_Reverse_Engineering/findings/FIND-0045-retained-world]] (the world)
to the P1 session of [[03_Reverse_Engineering/findings/FIND-0025-p1-session]],
[[03_Reverse_Engineering/findings/FIND-0026-level-banner-session]] and
[[03_Reverse_Engineering/findings/FIND-0029-mixed-object-pool]]. No new ROM
routine is mapped.

## Observations (ordinary recording)

- From 669 every object loop's 78EE tracking is P1's control +42/+44 after its
  wrapper and every 6D8C owner position is P1's actor X/Y (FFFF1AB4 +02/+04):
  checked for all 397 frames 669..1065 and all 128 emitter walks between a fresh
  P1 capture and the world capture, whose endpoints at 1066 are equal.
- **Level-start fade:** at 634 FF0B90 is FFFF (negative direction) and the
  shared 1345A timer runs every frame: FF0B92 counts 0014 → 0000 (634..654),
  then FF0B96 steps 0 → 0E by two every other frame (writers 13472, 1348E,
  134A0, 134A8) until 669, when FF0B90 is 0000. The P1 session contract (an
  inactive timer at its seed, no FF0B90 writers) therefore rejects 634..668.
  Interpretation (probable): the palette fade-in after the level setup;
  [[03_Reverse_Engineering/findings/FIND-0018-actor-transition]] already
  reconstructs this timer, but the session does not schedule it.
- From 669 the existing early-session evidence (banner, three input
  conversions, wrapper returning at 6986) validates every frame to 1066.

## Native implementation

`MixedSessionState::world` holds the carried `PickupWorld`. `establish_world`
moves the setup's links, records, FF31AC, FF31B4/FF31B8, P1 message fields and
tilemap into it with what the setup does not produce (FF312C kinds, the logical
controls, P2's message fields, FF31BE) and clears the moved session fields, so
one copy stays authoritative; every world identity must stay live.
`step_world_phase` applies `WorldUpdates` (a count of E918 calls by non-pool code,
advanced through E918 itself, and message-producer updates), runs
`MixedPool::step` with the globals, collision inputs and world, commits all of it
together and returns the loop's FCB32 requests and CB9A clears.
`step_mixed_session` now runs banner, input and P1, then `step_world_phase` with
P1's tracking and actor position, so hits, emitter owners and collisions come
from native P1. `--world-pool` (session 047) uses the same functions with
supplied inputs and still produces byte-identical output.

`wiznliz-session --world-session` takes the P1 seed, the world's setup rows, the
collision configuration, the supplied loops before P1 runs natively, then per
frame only the held buttons, the E918 count and message updates.

## Comparison

One fresh hooked replay of 669..1066 (independent unhooked endpoint, equal to
the world capture's) with the world capture of session 047 revalidated by the
current tool. Native matches the setup line, the 35 supplied loops (634..668)
and, from one seed and 397 physical held rows, **all 397 P1 calls** (actor,
scratch, tracking, input, 12 sound requests, banner requests) and **all 397
joined object loops**, in debug, and release/sanitize reuse the capture with the
same output digest. Toggling a held button at 700 or 775 breaks the comparison
at that frame.

Update: [[03_Reverse_Engineering/findings/FIND-0047-level-start-fade]] schedules
the fade timer in the session; the joined run now starts at 634 with no supplied
loops.

## Limits and next validation

Loops 634..668 keep supplied tracking until the session schedules the level-start
fade. The message producer, the FFFF32C2 object's E918 calls, rendering and audio
are not native; the second-ingredient paths, 7B42, the 6C00 family branches,
gated-pair leads, 6EF0's allocating path and the gate producers are not reached
or stay unsupported. Next: schedule the native 1345A timer phase in the session
(before the banner, as observed) so P1 joins from the first loop. TASK-0010
remains in progress; **native playability: none**.
