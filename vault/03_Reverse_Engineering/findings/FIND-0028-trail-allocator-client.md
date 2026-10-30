---
id: FIND-0028
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# 6D8C trail client, particle allocation and random state

Task: [[07_Tasks/TASK-0010-grounded-controller]]. ROM SHA-256:
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
Exact ranges/hashes/transfers: `re/trail_step.json`; results and provenance:
`re/trail_validation.json`. Native implementation: `src/sim/trail.*`.
The trail/particle names describe measured behavior; no claim about the visible
asset's identity, collection rules or the earlier initializer is made.

## Handler and dataflow

`[6D8C,6E32)` contains 39 instructions. It loads A5 from object +4A, decrements
the word at +36, and tests the result's sign using BPL. A negative result resets
the countdown to three. Thus zero becomes FFFF and fires; 8000 becomes 7FFF and
does not fire; 8001 becomes 8000 and fires. Preserve wrap and the sign test.
On that expiry it compares the full longwords +22 and +26: **both X and Y** of
the newest two saved positions determine whether to emit. Equal history resets
the countdown but skips allocation and random calls.

Emission saves A5, passes the emitter's **old** X/Y to 5A9A, then calls E918 twice.
Each result contributes `(low_word & 7) - 4` to the particle's corresponding
coordinate, with word wrap. It overwrites the particle's countdown/reload bytes
with two, then restores A5. The allocator and random effects precede owner lookup.

At 6DDE the handler resolves A4 from `(A5)`, outputs the oldest saved position
(+32/+34) into its own X/Y, shifts five saved position pairs toward the oldest,
then writes `(owner.x + 4, owner.y)` as the newest pair. Current captures resolve
+4A=FFFF0690 and `(FFFF0690)`=FFFF1AB4. Native code uses `ActorId` and an explicit
resolved position; it never uses original addresses or host pointers as IDs.
The emitter's presentation/flags/target remain intact in the handler-only API.

The scheduled API first applies the active gate and F76C presentation. The
observed emitter loops presentation mode 81, frames 638..643. Unknown invoked
callbacks reject; a cleared active bit skips all work. After 6D8C, +46 selects
the existing return-only service 12646 and returns through 69C2.

## Allocation and particle lifetime

`[5A9A,5AE4)` contains thirteen instructions, including its RTS at **5AE2**, also
used as the spawned object's return-only handler. It calls F994 and initializes
mode 85, presentation frame/begin 227, end/target 234, counter/reload three,
callback FAA4, X/Y from D0/D1. F994 supplies flags=0, +14=0 and service=12646.
Unconsumed original object bytes remain outside the typed particle contract.
Native `make_trail_particle` represents this successful allocation/init with
explicit caller-provided capacity; it does not reproduce the general free table.
The 6D8C caller changes the two rate bytes to two, yielding sixteen active
presentation updates before release (the unmodified helper's rate three yields
24). Position remains fixed after jitter.

F76C invokes FAA4 on reaching the target; FAA4 clears mode and returns the slot.
The original loop still runs 5AE2 and 12646 on that release invocation. Native
`step_trail_particle` returns a release event and preserves that final presentation
state. It does not own a shared pool; a future world caller must consume the event.
Exhaustion reaches F9D0's hardware loop in the original. The restricted harness
stops before that unsupported boundary; native code throws atomically.

Slot order changes the birth update. Fresh movie `[1066,1100)` has eight spawns:

| Births | Physical slots | First update |
| --- | --- | --- |
| 1069 / 1085 | FFFF29A2 | Next frame; slot is before emitter FFFF2B76 |
| 1073 / 1089 | FFFF2A8C | Next frame |
| 1077 / 1093 | FFFF2ADA | Next frame |
| 1081 / 1097 | FFFF2BC4 | Same frame; slot is after emitter |

Four new lifetimes finish at 1085, 1089, 1093 and 1096. Four are still active at
the final boundary. The comparison covers **97 updates**, explicitly including
partial lifetimes. Earlier-slot particles can release before the emitter and
be reallocated later in the same world pass. Do not schedule every newly born
particle immediately as the earlier P1 reversal-only projection could do.

## E918 random recurrence

`[E918,E948)` contains ten instructions. For unsigned 32-bit state `s` at FF0BAC:

```
next = (s << 16) | (((s >> 8) ^ (s >> 15)) & 0xFFFF)
FF0BAC = next
FF0BB0 = next
D0 = next >> 1
```

All operations wrap to 32 bits; shifts are logical. Both the state and its mirror
are retained native fields. Zero stays zero. Starting from one gives state
65536/result 32768, then state 258/result 129. This is E918 only: the alternate
E948 routine is not reconstructed or assumed equivalent.

The fresh window has sixteen E918 calls and 64 captured RNG writes, all owned
by this emitter. No other writer interrupts its retained random state there.
That observation permits a continuous native RNG seed for this window; it does
not establish whole-game random scheduling. Native tests explicitly check that
later transport rows cannot overwrite retained emitter, RNG or particle state.

## Native boundary and evidence

Emitter and RNG changes commit together after all work succeeds. Exhausted
capacity, unsupported callback and even a missing owner discovered **after**
allocation/random work preserve all caller state and return no spawn. Budgets
bound research/native transports to 32 repeats and sixteen available allocations
per case; the native component makes at most one allocation/two random calls per
update. No hardware loop or emulator enters native targets.

Fresh debug/release/sanitize each pass **209,082 original comparisons**: 69,638
handler cases, 69,766 scheduled cases, 4,102 particle cases, 65,551 RNG cases and
25 direct initializer cases. All 62 new instructions execute. Inputs include all
65,536 countdown values, distributed full-word RNG seeds, deterministic varied
histories, word/byte limits, inactivity, target/bounce behavior and repeated work.
Authored goldens and late rollback failures are independent checks.

One fresh ordinary capture and independent unhooked replay agree on exposed-state
hashes. Each native preset matches 34 retained emitter calls, eight spawns,
sixteen RNG calls and 97 particle updates. Owner positions and capacity availability
are still external inputs per emitter invocation. Particle replay starts with
**native spawn output**, then retains its state over measured invocations.
533 emitter writes and 64 RNG writes are audited; the later B126 zero-clear is
an observed no-op. No full world, pool, rendering or frame parity is claimed.

Three mappings add 288 disjoint classified bytes. Two already-classified service
instructions at 69BC/69C0 now also execute in restricted comparisons; they add
no bytes/functions. Totals: **102 bounded simulation mappings + one partial /
112 indexed**, 25,897 classified bytes, 1,022,679 unclassified; cumulative scoped
instruction union 1,467. GNU corroborates five selected opcodes; its absolute
EOR.W decode at E932 fails, so that opcode relies on primary decode and executed
original evidence. General world ordering remains distinct from call-tree inference.

Next integrate P1, this emitter/RNG and both particle kinds into a bounded native
world pool, retaining slot/free-list order and initial live particles. Other
active handlers (7CA4, 7808, 7A88 and service 78EE) remain outside this pass and
must be audited or rejected at the next integration boundary. Initializer 6D22,
shared capacity competition and native rendering/audio remain open. Native
playability is **none**; TASK-0010 remains in progress.


## Later refinement (session 041)

The ordinary movie's P1 trail emitter in slot 53 has an observed origin
([[03_Reverse_Engineering/findings/FIND-0039-setup-tail]]): 6EB6 creates it
dormant at frame 629 as the P1 control's +1A2 link, and at frame 780 the
unsupported 6C00 pickup hit initializes it through 6D22 (an FB06 copy of pickup
54, then handler 6D8C). 6D22 remains unreconstructed; the claims above are unchanged.

Update (session 047): [[03_Reverse_Engineering/findings/FIND-0045-retained-world]]
follows link 53 as this emitter through both conversions natively in the
retained world, with the resolved owner position supplied per walk, shared
particle allocation from the world's own free stack (31 particles) and E918
carried natively; the five E918 calls by the object at FFFF32C2 outside the pool
(109E4, 10A00) enter as an explicit count. The window [1066,1100) observation
above still holds; frames 634..1066 have those foreign callers.
