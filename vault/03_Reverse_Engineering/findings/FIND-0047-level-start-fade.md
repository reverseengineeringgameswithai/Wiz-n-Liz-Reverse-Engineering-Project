---
id: FIND-0047
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# The level-start fade in the native session: the world native from its first loop

Task: [[07_Tasks/TASK-0010-grounded-controller]]. ROM SHA-256:
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`. Validation:
`re/fade_session_validation.json`. Source: `src/sim/session.*`,
`src/sim/mixed_pool.cpp`, `tools/native/session_main.cpp`. Evidence:
`tools/genesis_world_session.py`, `tools/genesis_session_capture.py`
(`active_timer`). Extends
[[03_Reverse_Engineering/findings/FIND-0046-world-session]] with the timer of
[[03_Reverse_Engineering/findings/FIND-0018-actor-transition]]. No new ROM
routine is mapped.

## Observations (ordinary recording, frames 634..1066)

- The 1345A timer runs once per frame, bracketed by its entry, its single RTS at
  134B0 and the return to EBF2, before the banner (63E2) and the input
  conversions, as in the inactive case. Every path through `[1345A,134D6)`
  leaves through 134B0.
- From 634 to 668 FF0B90 is FFFF: FF0B92 counts 0014 → 0000 (634..654), then
  FF0B96 steps 0 → 0E by two every other frame and FF0B90 clears at 668's call.
  All writes to FF0B90..FF0BA3 in the window come from inside the timer.
- The timer writes FF0EDC = FFFF exactly on its eight level-step frames (654,
  656, …, 668); 1344C (in the 13432 palette consumer) clears it eight times.
- With the timer's own state set aside, P1's evidence over 634..668 has the same
  shape as from 669: the wrapper does not read the active timer here.
  Interpretation (probable): the level's palette fade-in; P1 is already
  controllable but idle (return-only service) during most of it.

## Native implementation

`P1SessionState::transition` (optional `TransitionState`) holds the timer;
`step_p1_session` and `step_mixed_session` run `step_transition_timer` once per
call before the banner and commit or roll it back with everything else. Absent,
the call is the observed inactive no-op, so earlier sessions are unchanged.
`wiznliz-session --world-session` takes the timer row after the P1 seed and
prints the timer's four words after each frame's banner. P1's actor update is
not given the timer (its transition handlers are outside this window).

## Comparison

A fresh hooked replay of 634..1066 (independent unhooked endpoint equal to the
world capture's) validated with `active_timer`, joined with the session-047
world capture: native matches the setup line and, with **no supplied loops**,
all 432 frames: the timer's direction, countdown, reload and level after every
1345A call, **all 432 P1 calls** from one seed and 432 held rows, and **all 432
object loops** consuming P1's own tracking and position (cross-checked for 432
tracking values and 128 owner positions). The eight dirty requests match the
timer's level steps. Release and sanitize reuse the capture with the same
output digest.

## Limits and next validation

The fade's palette consumers (13432, 1350E), rendering and audio are not
native; the message producer and the FFFF32C2 object's E918 calls remain inputs.
The run ends at the world capture's frame 1066; the second fruit delivery, 79B6's
second-ingredient path and 7B42 lie later. Next: extend the joined run past 1066.
TASK-0010 remains in progress; **native playability: none**.

Update: [[03_Reverse_Engineering/findings/FIND-0048-spell-mixing]] extends the
joined run to 1433 (the second delivery, the second ingredient, 7CC8 and P1's
reversal effect in the world pool).
