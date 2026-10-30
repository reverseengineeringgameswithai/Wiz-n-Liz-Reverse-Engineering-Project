---
id: FIND-0045
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# The retained level world: every object loop from the setup to frame 1066

Task: [[07_Tasks/TASK-0010-grounded-controller]]. ROM SHA-256:
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`. Validation:
`re/world_pool_validation.json`. Source: `tools/native/world_transport.hpp`
(`wiznliz-collision --world-pool`) over the existing `src/sim/mixed_pool.*`.
Evidence: `tools/genesis_world_pool.py`, `tools/genesis_pair_initializer.py`.
Composes [[03_Reverse_Engineering/findings/FIND-0038-setup-prefix]],
[[03_Reverse_Engineering/findings/FIND-0039-setup-tail]],
[[03_Reverse_Engineering/findings/FIND-0040-setup-message]],
[[03_Reverse_Engineering/findings/FIND-0041-gated-pairs]],
[[03_Reverse_Engineering/findings/FIND-0042-pickup-hit]],
[[03_Reverse_Engineering/findings/FIND-0043-fruit-delivery]],
[[03_Reverse_Engineering/findings/FIND-0044-first-ingredient]] and the 6D8C
emitter of [[03_Reverse_Engineering/findings/FIND-0028-trail-allocator-client]].
No new ROM routine is mapped; this is a recording-window comparison.

## Observations (ordinary recording, frames 629..1066)

- At the 6886 entry (frame 629) F9E2's free stack holds **all 68 slots**; the
  `[6886,68D4)` setup pops 16 (prefix 67..56, tail 55..52). Frames 630..633 run
  no object loop and no pool byte changes; every frame from 634 to 1065 runs one.
- Each loop walks **all 68 slots** in address order (69AA..69C2 for each, free
  slots included). From 634 every walked slot is free or a world object: all 33
  later allocations are the world's (31 5A9A particles of link 53's 6D8C, F994
  called from 5AA0; the 7910 sparkle by F9E2 and its copy by F994) and so are
  all releases. No pool reset, FA30 or other allocator caller runs.
- **Pool bytes change only inside walks:** each slot enters its walk as the
  previous frame left it and ends the frame as its walk left it, unless another
  walk of the same loop changed it first or afterwards (link 53 at 780, 823 and
  980; slot 67 at 853; newborn particles, the sparkle and the copy).
- **E918's state is shared.** Inside the loops only the emitter calls E918 (62
  calls, two per emission). Code at 109E4 (three calls) and 10A00 (two) for the
  object at FFFF32C2, outside the pool, calls it right after the object loops of
  frames 634, 797, 850, 1000 and 1053. In complete write records FF0BAC..FF0BB3
  has 268 writes, all by E918.
- At every emitter walk FF0690's +00 is FFFF1AB4 and that actor's X/Y do not
  change during the walk (the actor is outside the pool).
- P1's message fields change **between** loops, by the message producer that
  is not native: at 634 (+46 already consumed to FFFFFFFF, +56 0000 → 000C), 754
  (+53 64 → 00), 854 (+46 D20E consumed) and 874 (+53 01 → 00). P2's stay
  absent. FF31BC/FF31BE are written only by 79B6's tail (two writes at 853);
  FF312C kinds and FF31A4/FF31A6 never change.

## Native implementation

`wiznliz-collision --world-pool` runs one `MixedSessionState`:
`initialize_level_setup_prefix`, `initialize_level_setup_tail`,
`continue_level_setup` and `initialize_gated_pairs` from the 6886-entry stack and
verified inheritance, then one `PickupWorld` built from the setup's own outputs
(logical controls, +1A2 links, records, FF312C kinds, FF31AC, FF31B4/FF31B8, both
controls' message fields, the FF0D60 tilemap, FF31BE), the session's
`PrivateGlobals` (FF31B0 cleared by 6A94, FF31A4/FF31A6, FF31BC absent until
79B6 stores it) and `TrailRandom`, all carried by `MixedPool::step` across every
loop. The only per-loop inputs are explicit external ones: 78EE tracking (P1
+42/+44, the X mask, the P2 gate), the resolved owner position when an emitter
walks (an unconsumed position rejects; a missing one rejects in 6D8C), the
**count** of E918 calls by non-pool code since the previous loop (applied with
the native E918 recurrence, never as a new state) and message-field updates by
the producer. The transport prints each loop's events and, after it, the free
stack, E918 state, records, identities, messages, globals, FCB32 requests, CB9A
row clears and both links' objects. No `src/` change was needed.

**Interpretation (probable):** for this window the world is the level's whole
object pool, and with P1's position supplied every object behavior through the
first ingredient is native: the fruit pickups, carrying, the trail, delivery,
FIRST INGREDIENT COLLECTED! and the bobbing ingredient sprite.

## Comparison

The Python side derives every expected line from the original alone: slot kinds
and generations follow the trace (6D22 at 6D8A, 7910 at 7976/79B2, 7AD6 at its
FAA4, 5A9A's F994 pops, FAA4 releases), each event's object comes from the walk
exit (a birth from the new object's own next walk entry), and the state after a
loop from its 69CE event and the frame boundary.

A fresh hooked replay of frames 0..1066 with an independent unhooked endpoint
matches the setup line and **all 432 loops (634..1065)** in debug, and
release/sanitize reuse that capture: 5,732 walk updates (31 releases), 33 births
(31 particles, the sparkle, the copy), 128 emitter walks with owner positions,
two 6C00 hits (780, 980), nine 7910 hits with one delivery (823), the 853
first-ingredient path, three sound requests and one row clear (VRAM E60E). The
free stack and generations match after every loop.

Sabotage of the inputs on the same capture (`re/world_pool_validation.json`,
`sabotage`; identical on the exploration capture): omitting the external E918 call
before 798, omitting the 754 message update or moving the owner at 790 first
differs at that loop; withholding the owner rejects (`trail owner unavailable`);
moving P1 at 780 rejects at 781 (`unconsumed owner position`).

The per-group comparisons keep their bounds (the 783A group rejects at 823, the
FF31B4 object is followed to 853, the tail rejects at 780); the world comparison
now covers those 243, 213 and 286 original-only phases natively.

Update: [[03_Reverse_Engineering/findings/FIND-0046-world-session]] joins the
native player from 669: from there tracking and owner positions are P1's own
outputs, cross-checked against this capture.

## Limits and next validation

The P1 actor is not native here: its tracking and position are inputs. The
message producer, the FFFF32C2 object, rendering and audio are not native. The
second-ingredient paths and the 7B42 chain, the 6C00 family branches, the
gated-pair leads, 6EF0's allocating path, overlap-hit FF31C0 readers and the
gate producers are not reached in this window and stay unsupported. Next: join
the native P1 session to this world so tracking and the owner position become
native outputs. This met the pool part of the
[[06_Decisions/ADR-0001-presentation-shell]] trigger; the ADR was then rejected
(2026-10-23) and SDL3 stays. TASK-0010 remains in progress; **native playability: none**.
