---
id: FIND-0034
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# F9E2 allocation and the 7B9C return-only pair initializer

Task: [[07_Tasks/TASK-0010-grounded-controller]]. ROM SHA-256:
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`. Scope/hashes:
`re/pair_initializer_step.json`; validation: `re/pair_initializer_validation.json`.
Source: `src/sim/return_only.*`, `src/sim/mixed_pool.*`. Evidence:
`tools/pair_initializer_compare.py`, `tests/pair_initializer_cases.py`,
`tools/genesis_pair_initializer.py`, `tools/genesis_mixed_session.py`.
Builds on [[03_Reverse_Engineering/findings/FIND-0033-return-only-objects]] and
the F994 allocator in [[03_Reverse_Engineering/findings/FIND-0015-fast-reversal]].

## Static ranges

| Half-open range | Instructions | Contract |
| --- | --- | --- |
| `[7B9C,7C26)` | 23 | Two `JSR F9E2`, member stores, `MOVE.L A6,FF31C0`, RTS |
| `[F9E2,FA1E)` | 14 | Save A0, pop FF311C stack top into **A6**, defaults, restore A0, RTS |
| `[FA1E,FA30)` | 3 | Exhaustion: two VDP register writes and `BRA FA1E`, never returns |

216 bytes / 40 decoded instructions, none previously classified. Direct transfers:
7B9C and 7BDA call F9E2; F9EC branches to FA1E on the zero sentinel; FA2E loops.
The graph closes with returns at 7C24 and FA1C only. Eight register-form opcodes
are corroborated by the installed GNU plugin; it rejects every immediate and
absolute extension form here (JSR.L, `MOVE #imm,d16(An)`, absolute MOVE.L/W),
which rely on the primary decoder plus restricted and full-machine execution.

## F9E2 allocator semantics

F9E2 is the A6 twin of F994. It saves A0, loads head FF311C, tests the
predecremented entry and on nonzero stores the new head and loads the object
into **A6**, replacing the caller's current-object register. It writes only
+00=80, +16=+46=12646, +14=0, +12=0 and +06=541, then restores A0. Every other
object byte, including +01, +0E target, +10 countdown, +1A callback, +1E..+45
and +4A link, keeps the slot's previous contents. F994 performs the same pop
into **A5** and preserves A6. A third variant at FA30, by static reading only,
moves the popped top entry into the bottom stack slot and initializes the old
bottom object instead; it does not run in the recorded interval.

Exhaustion is the zero sentinel at FF3008: the test fails, the head is **not**
updated, and FA1E writes VDP registers 8703/870D forever. There is no failure
return. Restricted execution stops when PC reaches FA1E without executing it;
native code rejects instead (below). This is a documented replacement for a
hang, not an invented original result.

## 7B9C pair initializer

| Member | Allocation | Stores after F9E2 |
| --- | --- | --- |
| First | Top free entry | mode 81, X/Y 161/270, frames 916/916/921, counter/reload 4/4, +16 RTS |
| Second | Next entry | mode 81, X/Y 164/270, frames **919**/916/921, counter/reload 5/5, +16 RTS, flags 0800 |

FF31C0 receives the second A6 (its object address). A6 remains the second member
on return; D0–D7/A0–A5 are preserved. Mode 81 animates forward without the
mode-bit-2 target comparison, so an inherited target is retained but cannot
fire a callback while mode stays 81.

A ROM-wide search finds one absolute FF31C0 writer (7C1E) and six readers.
7B06 inside 7AD6, reached from unsupported callback79B6, retargets the second
member to handler 7B42 with a control link and countdown 300. 7088, 729A, 74A4,
76AE and 810E load it on overlap-hit paths after AC5E and restore its +16 handler
to 12646. None is reconstructed. No such +16 write to the pair occurs in any
write-complete frame audited here.

The pool reset at F850 calls F872, which clears only +00/+06/+12/+14 and sets
both selectors to 12646 for all 68 slots, then F940 rebuilds the FF3008 stack.
It does not clear inherited fields. In the ordinary recording the popped slots'
inherited bytes were zero apart from the selectors; that is an observation, not
a guarantee for every future level.

## Native implementation

`make_return_only_pair_member` builds one member from F9E2 defaults, the 7B9C
stores and explicit `InheritedObjectFields` (target, countdown, control).
`MixedPool::initialize_return_only_pair()` performs two ordered pops from the
shared LIFO stack and returns `{first, second}` identities with incremented
generations. A free `PoolSlot` may carry inherited fields only from verified
seed evidence; every allocation clears them, so a natively released slot is
unknown. Exhaustion at either pop, or unknown inheritance for either member,
rejects with no allocation, generation, inheritance or free-order change.
Unrepresented inherited bytes (+01, +1A, +1E..+45) must be zero in the adapter;
otherwise the slot is seeded as unknown and native rejects.

`initialize_return_only_pair(MixedSessionState&)` commits the pair and
`return_only_anchor` (logical FF31C0) together. `step_mixed_session` requires the
anchor, when present, to name a live return-only object and rolls back otherwise.
Mixed seed header size 14 adds the anchor as slot+1; only then is it printed after
the RNG fields. Tag 9 is a free slot with inherited fields. Native code uses no
ROM pointers or emulator code; no level-setup caller is reconstructed.

## Restricted original comparison

`--pair-initializer` executes only `[7B9C,7C26)` and `[F9E2,FA1E)` over a 68-slot
fixture, with reads limited to the pool, stack, head and FF31C0 and writes limited
to the declared fields. It checks preserved registers, A6/FF31C0, the head and
every unchanged byte, including inherited ones. **8,714 cases per
debug/release/sanitize** cover every stack depth 0..68, six top/second slot
pairs, fill patterns, inherited targets/links, unrepresented residue and
random cases. Outcomes per preset: 3,989 byte-identical pairs; 2,491 exhaustion
cases (the original stops at FA1E after 0 or 1 pops); 2,234 cases where the
original keeps unrepresented residue and native rejects. All 37 successful
instructions execute; no FA1E..FA30 instruction executes.

## Ordinary recording evidence

One fresh hooked replay of frames 0..1066 of the unchanged 5,298-row recording,
with an independent unhooked endpoint match at 1066, supports:

- **65 F9E2 calls** from 25 call sites, one crossing a completed-frame boundary.
  Each pops the current top, writes only its defaults, preserves A0/D0–D7/A1–A5
  and returns the popped object in A6. **32 F994 calls** preserve A6 and return
  A5. FA30 does not run; the pool reset runs five times.
- **Two ordinary 7B9C runs.** Frame 156 (caller 1EC54, an earlier setup routine
  before any 69A4 object walk) pops
  slots 43/42 from a 44-entry stack. Frame 629 (level setup `[6886,68A4)`, caller
  68A0) pops **59 then 58** from a 60-entry stack and stores FF31C0=FFFF2CFC.
  Both creation frames have complete write traces: exactly the 40 contracted
  writes, all other allocator writes in their forms, no foreign pair/anchor writer.
- At 629 entry FF31C0 still named slot 42 from frame 156 across three pool resets;
  resets do not clear it.
- **Continuity 629→1066:** 436 frames, 432 object walks and 864 retained updates;
  33 allocations and 31 releases never touch slots 58/59; FF31C0 never changes;
  every boundary matches. Write traces are complete in 435 frames (frame 632
  dropped), with 1,441 audited presentation/render writes to the pair.

Native initialization from each 7B9C-entry stack and verified inheritance matches
both runs; native then advances the frame-629 pair through all 432 walks and its
state equals the frame-1066 seed rows of [[03_Reverse_Engineering/findings/FIND-0033-return-only-objects]].
This establishes dynamic creation provenance for retained slots 59/58.

## Limits and next validation

Only 7B9C and F9E2's success path are mapped. The level-setup sequence, 7C26
private pair and other F9E2 callers, FA30, F850/F872/F940 resets, activation
7AD6/callback79B6, the five overlap-hit FF31C0 readers and collision-hit7910
remain unreconstructed or unsupported.
Native inheritance is seeded from evidence; reset residue is not modelled.
TASK-0010 remains in progress; **native playability: none**.

## Later refinement (session 035)

[[03_Reverse_Engineering/findings/FIND-0035-visibility-pair]] extends the same
evidence tool to 7C26 and shares the native two-pop template. Its fresh replay
re-verifies every claim above. The frame-156 creation audit now spans frames
156–157 together with 7C26, whose run is split by a VBlank exception frame; the
7B9C block itself is unchanged. `ReturnOnlyPairMember`/`ReturnOnlyPair` became
the shared `PairMember`/`ObjectPair`.
