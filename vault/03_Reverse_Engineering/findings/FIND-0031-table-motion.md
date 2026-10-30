---
id: FIND-0031
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# Native table motion and retained input

Task: [[07_Tasks/TASK-0010-grounded-controller]]. ROM SHA-256:
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
Exact hashes/ranges: `re/table_motion_step.json`. Validation:
`re/table_motion_validation.json`. Source: `src/sim/table_motion.*`,
`src/sim/mixed_pool.*`; comparison: `tools/table_motion_compare.py`.

## Instruction-derived contract

FUNC-0115 is `[7A88,7AD6)`: 78 bytes / nineteen instructions. The handler loads
+4A into A5 without dereferencing it and loads the full FF31BC word into D7.
The loop body runs before DBRA: count zero executes once, FFFF executes 65,536
times. No signed pretest or zero-count shortcut is valid.

Each iteration XORs **the full +36 word** with 1. Only a zero result skips motion.
Toggles 0/1 alternate movement and idle iterations; any other value moves on
every iteration. A moving iteration reads one signed table word, adds it to Y
with word wrap, advances the cursor, then adds +32 to X with word wrap. It next
decrements +10. Only a negative wrapped countdown negates +32 and reloads 28.
The old direction therefore supplies this iteration's X change. Countdown 8000
becomes 7FFF without reversal; 8001 becomes 8000 and reverses. Negating 8000
preserves its bit pattern. There is no position clamp.

The 48-byte table `[7A58,7A88)` contains 24 words. Its nonzero offsets are
+1,+1,+2,+1,+1 in the first half and their negatives in the second half, with
interleaved/trailing zeros. Advancing A0 wraps only on equality with 7A88.
Native `TableMotion::cursor` is a logical word index, never a ROM/host pointer.
The capture adapter accepts only even original pointers in `[7A58,7A88)`;
malformed, aliased and one-past pointers reject. The native handler checks a
cursor when consumed, before indexing; inactive or skipped work does not read it.

| Original object field | Native state |
| --- | --- |
| +02 / +04 | Wrapped `position.x` / `position.y` |
| +00, +06/+08/+0A, +0C/+0D, +0E | Presentation mode, words, counter/reload and target |
| +10 / +12 | Reversal countdown / preserved flags |
| +2E / +32 / +36 | Logical table cursor / wrapped horizontal delta / full-word toggle |
| +4A | Opaque logical control identity, preserved without owner lookup |
| +16 / +1A / +46 | Typed handler contract / unsupported callback79B6 / fixed return-only service |

The scheduled API skips inactive objects, advances presentation once, then
executes the handler and the fixed RTS service. An invoked callback79B6 rejects
before handler work; its stored address alone does not invoke it. Mode 81 in the
ordinary capture uses cyclic presentation without invoking that callback.
Any failure publishes no presentation or motion changes. The default native
budget is 4,096 loop iterations, a host safety bound; the component API can accept
65,536 explicitly. The retained pool uses the default and rejects excessive input.

## FF31BC inputs and writers

An aligned full-ROM scan finds three direct absolute-long FF31BC operands:
7A52 (reset destination), 7A8E (handler read), 7CDE (increment destination).
This is a direct-reference audit, not proof that no indirect writer exists in
unexamined game modes. Complete write tracing supplies the interval guarantee.

- `[7A46,7A58)`, eighteen bytes / three instructions, writes FF31BE=80 and
  FF31BC=0 then returns. It is a fragment inside the unsupported callback79B6
  path, after other calls. Executing this isolated fragment does **not** implement
  or validate the callback, allocation, control changes or preceding calls.
- `[7CC8,7CEA)`, 34 bytes / six instructions, tests the entire FF31B0 longword.
  Zero preserves both words. Otherwise FF31BE decrements with word wrap; a
  negative result increments FF31BC with word wrap and reloads FF31BE=40.
  Restricted execution stops before 7CEA, where pointer/collision work follows.
  The remainder and general scheduling are not reconstructed.

**131,422 restricted-original cases per preset invocation** verify both fragments
against authored arithmetic, including exhaustive countdown and increment words,
full-width gate edges and reset. All nine fragment instructions execute. These
are research checks, not additional original/native mappings.

In ordinary movie `[1066,1100)`, FF31BC=0 and FF31BE=80 throughout. The 7CC8
producer enters and reaches 7CEA exactly 34 times, with FF31B0=0. There are no
writes to either input word, including transients. Snapshots at every hook and
initial/final RAM agree; the callback reset is never executed. This justifies a
single native loop-count seed in this window. Producer state is observed, not
advanced natively or assumed constant elsewhere.

## Mixed session and independent evidence

Slot 67 / FFFF2FBA is now `TableMotion`, pool kind 6, with retained position,
presentation, countdown, logical cursor, delta and toggle. An eight-field header
extends the previous seven fields with FF31BC; four/seven-field inputs remain
valid for earlier scopes. Missing loop input rejects when a table object runs.
Later rows still contain physical held-button masks only. All prior free-stack,
generation, forward iteration, P1 ordering and whole-session rollback rules apply.

Eight external reservations remain, including two inactive occupied slots.
Callback79B6 and collision-hit7910 remain explicit rejects. The capture's private
write guard now attributes seven exact table write sites to managed state and
no longer permits table motion in reservations.

Fresh ordinary capture: `local/generated/mixed-session/run-k10mv8i2/`. One owned
hooked worker and independent unhooked replay agree at the declared exposed-state
endpoint. No edits, trace drops or overflow. Every preset freshly compares the
saved evidence after artifact, source, recipe, recording and identity checks.
All **34 table updates / 361 ordered pool events** agree, plus 34 P1/emitter calls,
136 trail, twelve reversal and 136 earlier private updates; nine allocations and
nine releases, complete free order, retained RNG, 34 banners and two sounds.
There are 9,835 routine events / 52,895 native events, 1,806 managed-slot writes,
305 reservation writes and 27 free-stack writes. Hidden device state is excluded
from the endpoint hash; no whole-frame/render/audio equivalence is implied.

## Verification and limits

**406,634 original/native cases per debug/release/sanitize**: 201,269 handler
and 205,365 scheduled cases. All nineteen handler instructions execute. Cases
exhaust countdown, toggle and horizontal-delta words; cover every table index,
both directions, Y/X wrap, repeated cycles, high/count maximum DBRA input,
all presentation modes and explicit cursor/callback/budget rejection.

Primary decode/hash and closed graph pass (86 handler/presentation/service
instructions); four GNU checks corroborate ADD.W, NEG.W, DBF and RTS. Immediate
MOVE.W forms are excluded from GNU corroboration. The writer fragments have
separate decode/hash/closure and restricted execution checks.

**194 Python tests, zero skips; 42/42 CTests per preset** pass. Authored checks
include exact table-cycle goldens, retained count changes, malformed pointer and
transient-write evidence, missing context, and rollback after prior release,
P1 movement, banner scratch changes and reversal allocation. Private, trail,
reversal and earlier P1 fixture regressions also pass in each preset; eight
additional sanitized corpora pass. See the validation record for hashes/counts.

One new bounded native mapping promotes 78 already classified code bytes; the
48-byte table was also classified. The two writer fragments add **52 newly
classified research bytes**. Totals: **105 bounded plus one partial / 115 indexed**;
26,257 classified and 1,022,319 unclassified ROM bytes. No producer/callback
function count is inferred from fragments. Native playability remains **none**;
TASK-0010 remains in progress. Next bound the 78EE no-hit collision service and
AC5E overlap context before replacing the remaining active reservations; retain
callback79B6 and hit7910 rejection until separately verified.

## Later refinement (session 046)

The `[7A46,7A58)` FF31BC/FF31BE writer fragment is the tail of callback79B6's
first-ingredient path, now native
([[03_Reverse_Engineering/findings/FIND-0044-first-ingredient]]); the 7A88
object in slot 67 is made there at frame 853 and its walks compare natively.

## Later refinement (session 040)

The retained 7A88 slot 67 has an observed origin before the measured window
([[03_Reverse_Engineering/findings/FIND-0038-setup-prefix]]). 6EC8 creates it
dormant at frame 629 as the FF31B4 object. At frame 853 unsupported 7AD6,
reached from callback79B6 on slot 47, copies slot 47 into it through FB06, and
the 7A88 handler runs from then on. Neither 7AD6 nor FB06 is reconstructed; the
`[1066,1100)` claims above are unchanged.
