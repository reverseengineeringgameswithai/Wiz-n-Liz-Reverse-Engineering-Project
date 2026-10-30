---
id: TASK-0002
type: task
status: complete
deliverable: Validate or reject the RNC candidate at file offset 0x348B2 with bounded decode and integrity evidence
acceptance: ["Candidate bounds and header fields verified against ROM-LOCAL-0001", "Packed CRC independently checked", "Decode attempted with pinned reviewed implementation and bounded output", "Decoded length and unpacked CRC checked or exact failure reproduced", "Synthetic malformed-input tests and canonical evidence note added", "No gameplay asset meaning inferred from signature alone"]
---
# Validate one RNC candidate

The pinned tool's README mentions Wiz 'N' Liz, and an initial local scan found
134 `RNC` byte occurrences. These are candidates, not 134 proven assets.
The first is at file `0x348B2`, method byte 2, declared unpacked size 17,714,
packed size 10,803, CRC fields `0xAF73` (unpacked) / `0x3673` (packed).
These were initial header hypotheses; this task now validates only the first
block, as recorded below.

Read [[03_Reverse_Engineering/SEGA2ASM]],
[[03_Reverse_Engineering/findings/FIND-0003-rnc-candidates]],
[[03_Reverse_Engineering/ROM_IDENTITY]], `third_party/manifest.lock.json`, and
the pinned upstream `compress/lzh_rnc.go` implementation before decoding.
It omits CRC validation; independently verify both integrity fields. Bound all
reads/allocations and local output.

Verify the candidate interval, integrity algorithm and CRC coverage independently
of the decoder. Attempt exactly one reproducible decode into `local/`. Crosscheck
decoded length and CRC, preserving a minimal failure case if the selected tool
is unsuitable. Do not label decoded bytes graphics, audio or level data until
structural or runtime evidence supports that interpretation. Do not add compressed
segments to the canonical split just from a signature match.

Deliver a significant finding with commands, versions, identities, ranges,
integrity results, limitations and a deterministic extraction recipe if proven.
This contributes an asset-decoding dependency toward a future native slice;
it is not itself native game logic. SDL3 and MAME are not prerequisites.

Related prior task: [[07_Tasks/TASK-0001-foundation]]. Current priorities:
[[01_Project/NEXT_ACTIONS]].

## Completion

Both CRCs and declared extents pass independent checks. The pinned ScummVM
reference consumes exactly 10,803 packed payload bytes and produces 17,714
bytes under Clang ASan/UBSan; output is saved atomically under a stable logical
ID. The pinned sega2asm decoder fails both a real block and an authored one-byte
fixture; its incorrect results are rejected rather than accepted as extraction.

Evidence: [[03_Reverse_Engineering/findings/FIND-0004-first-rnc-block]] and
[[03_Reverse_Engineering/findings/FIND-0005-rnc-upstream-defect]]. All 63 project
tests pass, including malformed-input and no-overwrite guards. No original CPU
ran, no resource role was inferred, and the ROM remains unchanged. Handoff:
[[08_Sessions/2026-10-02-002-rnc-validation]]. Next:
[[07_Tasks/TASK-0003-native-rnc2]].
