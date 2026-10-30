---
id: VALIDATION-STRATEGY
type: validation
status: active
---
# Validation strategy

Current implemented layers:

1. Synthetic Python tests: ROM parsing, narrow original-68000 field arithmetic,
   wrapper range/path/output validation, vault consistency. Fixtures are authored
   and do not require proprietary bytes. Two optional pinned-tool failure probes
   use synthetic bytes and explicitly skip if the tool is absent.
2. Local ROM identity validation: exact manifest size/hash, checksum observation,
   read-only inspection. Requested missing input is a failure.
3. Static research checks: bounded reset table consumption and selected decoder
   corroboration; sega2asm actual dry-run/split, raw range equality, reported
   artifacts and unchanged ROM. These do not execute the game.

Future differential tests must derive expectations from independently observed
original execution and record initial state, input, reference version/method,
synchronization points, compared outputs and justified exclusions. Native code
must not generate all its own expected results. Build canonical replay-state
serialization rather than hashing C++ object memory. Include RNG/tick/entity/
objective/timer state once identified; add rendering/audio event comparisons.

Add runtime sanitizers and bounds checks with native code. Test original and
intentional enhanced behavior separately; document any accepted divergence.
Never replace a golden merely to silence a failure. Scope coverage honestly by
[[03_Reverse_Engineering/COVERAGE]]. Executed outcomes and unrun layers are in
[[05_Validation/RESULTS]].

The RNC layer now adds actual independent decompression comparison: a manually
encoded literal fixture has a fixed expected byte; pinned ScummVM validates it
and the real block with its own CRC implementation. Python bitwise CRC verifies
those checks separately. The broken upstream Go decoder supplies a regression
case showing that output length alone cannot establish correctness. Native codec tests now compare 49 authored cases and the first ROM block
against these independent results.

Malformed reference tests deliberately expect child-process ASan termination;
that validates containment, not safe production decoding. Native codec tests
reject the same inputs without invalid memory access. Asset-publication
tests assert that failures preserve pre-existing outputs rather than overwriting
them. Optional tool tests explicitly skip only when their dependencies are
absent; provenance mismatches fail.

Native validation uses required CTest targets in each selected preset. Missing
or stale native builds fail when requested; `test` without a preset explicitly
reports that CTest was not requested. `reference-test` currently means RNC2
codec comparison only, and requires the pinned reference instead of skipping.
The native corpus checks fixed/pattern-authored expectations; seeded malformed
trials with recomputed packed CRC separately test rejection and sanitizer safety.
No random trial is counted as gameplay or exhaustive semantic coverage.
See [[03_Reverse_Engineering/findings/FIND-0006-native-rnc2]].

The loader probe verifies reviewed code-region identities, original-68000
operand/branch relationships, and a closed decoder CFG. It distinguishes
raw byte transfer candidates from corroborated callers and refuses disassembler
output that exceeds the supplied slice or disagrees with its bytes. Independently
checked consumer loops define the structured resource parser expectations;
synthetic zero-count, multiple-count and malformed cases exercise those bounds.
Static closure and exact resource accounting are not original execution or
gameplay differential tests. See [[03_Reverse_Engineering/findings/FIND-0007-rnc-loader]].


Structured graphics tests use authored palette primaries/unused bits, asymmetric
rows, all 256 single pattern bits, count1/count65536, every truncated extent,
opaque-record preservation, invalid IDs and atlas budgets. Expected bitplane
ordering comes from pinned MAME source, implemented separately in Python;
expected colors use explicit authored values and the documented diagnostic
policy, not snapshots emitted by the native renderer. This is independent
specification checking, not an executed emulator differential. The local atlas
checks every pixel against that model. PNG tests independently parse chunks,
check CRCs and decompress raster bytes, including multiple stored blocks.


Scene tests use original authored fixtures with asymmetric corner colors,
base/additional-bank references, all four H/V flip combinations, priority-bit
preservation, coordinate wrap and full-word relocation carry. Native malformed
checks cover every truncated byte extent, unsupported shape, bad resource IDs,
missing pattern/palette, image limits and overflow. PNG transport is compared
with fixed spatial/color expectations and a separate bitplane/row-reversal
model. The real scene checks all 262,144 pixels; static-model agreement is not
original CPU execution or a gameplay differential test.

## Executed original terrain comparisons

`terrain-compare` is separate from codec `reference-test` and from ROM-free
CTest. It requires a verified pinned Musashi harness and exact original code;
missing dependencies fail instead of skipping. The reference supplies observed
semantic outputs, position/scratch and flags. Eighteen hand-worked authored
cases separately validate the reference outputs before trusting larger corpora.
Normal CTest uses only authored assets and expectations; it needs no ROM or CPU
reference and includes all 256 byte values against eight comparison heights.

614,436 reference comparisons per preset span all x words, valid y aliases and
sentinel paths, all attribute combinations, actual-map pixels and contact/settle
cases. Three invalid original addresses must fail fixture guards. Instruction
addresses are counted separately from cases and whole-game reachability. No
hardware/frame timing, full register ABI or out-of-resource memory contract is
inferred. All native debug/release/sanitizer output hashes must agree. Inputs,
commands, source pins, hashes, process diagnostics and boundaries remain in
local per-run reports. See [[03_Reverse_Engineering/findings/FIND-0010-terrain-query]].

## Executed movement comparisons

`movement-compare` reuses the pinned original-68000 research build with a separate
movement transport. Twenty-six hand-worked goldens validate its outputs; ROM-free
CTest separately checks signed arithmetic for every word value and transactional
host failures. The 282,233-case original corpus exercises damping/clamps, flat
contact, slopes, empty records, wrap/loop boundaries and extracted terrain,
including retained state across up to sixteen calls. Calls are not game frames.

Compare all defined position/speed/presentation/delay/handler/scratch fields and
explicit step/transition counts. Count original instruction visits separately:
74 new instructions, 149 overall in the movement corpus. The existing terrain
corpus covers all 86 older instructions and remains a required regression when
the shared reference harness changes. No full register/CCR ABI, unknown RAM or
airborne handler execution is implied. A default native work budget and complete
rollback on resource errors are documented host policies. Compare preset output
hashes and preserve exact inputs/reference provenance under ignored local paths.

## Airborne return and continuation comparisons

`airborne-compare` compares 415,940 constructed original/native states in each
preset, including exhaustive individual delay/vertical words and all signed
speeds for both landing directions/reload helpers. Thirty-six independent
hand-worked cases validate reference outputs. The corpus is not the exhaustive
Cartesian state space. Cases retain flags/scratch and can follow up to sixteen
airborne handler calls, reporting the number applied before a grounded event.

Reference execution ends at original RTS or before a declared immediate idle
continuation, with the expected stack boundary for each. Native must report the
same pending work; a same-call transition cannot become a silent return or new
tick. All 21 semantic outputs, counters and continuation fields compare. No
full register/CCR ABI or frame timing claim. Every new instruction must be
visited for comparison success. Native tests separately verify transactionality,
unsupported handlers and budgets. Shared harness/graph changes require the
existing movement and terrain regressions. See
[[03_Reverse_Engineering/findings/FIND-0012-airborne-update]].
