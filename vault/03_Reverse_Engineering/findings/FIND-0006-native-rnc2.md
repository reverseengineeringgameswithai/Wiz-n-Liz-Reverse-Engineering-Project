---
id: FIND-0006
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset
confidence: confirmed
task: TASK-0003
---
# Native RNC2 codec matches the independent reference

Task: [[07_Tasks/TASK-0003-native-rnc2]]. Confirmed scope: 49 authored token
cases and one ROM block match the pinned independent decoder byte for byte,
including consumed extents. This is native resource decoding, not a recovered
original game routine or a gameplay-equivalence claim.

## Identity and observed result

ROM-LOCAL-0001: 1,048,576 bytes, SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
Original unchanged; no normalization. Half-open file range `[0x348B2,0x372F7)`
contains the 18-byte header plus 10,803 payload bytes. The native decoder consumes
all payload bytes and produces 17,714 bytes, CRC `0xAF73`, SHA-256
`048aec81ffb0e5463029b931c2716e5aaa818539b5f72c078f7a19cc195a9ac7`.
Packed CRC is `0x3673`. Independent baseline:
[[03_Reverse_Engineering/findings/FIND-0004-first-rnc-block]].

Native library: `src/core/rnc2.hpp` / `src/core/rnc2.cpp`,
`wiz::rnc2::decode(span, Limits)`. CLI: `tools/native/rnc2_main.cpp`.
Known original caller/callee addresses, RAM destination and resource consumer:
**unknown**. Python extraction selects this file range from `re/rnc_blocks.json`;
no CPU address is passed as a native pointer.

## Wire grammar observed in independent authored cases

Control bits are MSB-first. Control and raw bytes share the input byte cursor;
remaining bits of a loaded control byte survive intervening raw reads. The
first two bits are consumed without interpretation, agreeing with the pinned
reference for all four bit combinations. This establishes reference behavior,
not their original game meaning. Header bytes 16/17 remain opaque.

| Token prefix | Action |
| --- | --- |
| `0` | Copy next raw byte |
| `110` | Match length 2; next raw byte gives distance minus one |
| `1110` | Match length 3 |
| `1000`, `1010` | Match length 4, 5 |
| `10010`, `10011`, `10110` | Match length 6, 7, 8 |
| `10111` + 4 bits n | Copy `(n+3)*4` raw bytes (12 through 72) |
| `1111` + raw nonzero n | Match length `n+8` (9 through 263) |
| `1111` + raw zero + bit 1 | Continue to another token without output |
| `1111` + raw zero + bit 0 | Terminate |

Matches of length >=3 decode a high-distance prefix followed by a raw low byte;
distance is `high*256 + low + 1`. High values 0 through 15 use these respective
prefixes:

```text
0 110 1000 1001 10101 10111 11101 11111
101000 101001 101100 101101 111000 111001 111100 111101
```

Copies proceed one byte at a time from the growing output, preserving overlap.
Residual bits in the last loaded control byte are ignored, but additional
unconsumed payload bytes are rejected by the project format contract.

Interpretation: a declarative prefix grammar is sufficient for this resource
and all exercised reference branches. `tests/rnc2_cases.py` authors wire tokens
and expected literal/pattern bytes independently of the decoder. All 16 distance
prefixes have low-byte 0 and 255 cases, covering distances through 4096; match
lengths 2–9 and 263, literal-run lengths 12/72, refill boundaries, overlap,
continuation and termination are exercised. This is not exhaustive input coverage.

## Decision, implementation and safety policy

Implement a small C++20 asset codec with a declarative prefix table, checked
cursor, output vector and exception diagnostics. No upstream implementation is
copied or linked into this target. Understanding comes from direct ROM and
reference-source inspection plus experiments; this is **not clean-room work**.
Pinned GPL ScummVM remains an isolated research executable under
`third_party/rnc_reference.lock.json`, not a production library dependency.

The codec accepts exactly one nonempty method-2 block. Defaults cap packed and
unpacked bytes at 4 MiB before allocation. Callers may explicitly select other
limits; the defaults are project safety policy, not original machine capacity.
Reject wrong signatures/extents, zero output, CRC mismatch, truncated reads,
out-of-history matches, output overflow, missing terminator, early termination
and leftover payload bytes. Errors never return a partially decoded buffer.
Every token consumes input bits/bytes, bounding continuation-only streams.

`rnc-validate --decode` defaults to this codec. It rejects stale build sources,
changed executable hashes and symlink redirects, then independently checks
metadata, output CRC/size/hash and original identity before atomic publication.
`--backend reference` retains the old explicitly selected research path.

## Verification and reproduction

Fedora44 x86_64, GCC16.1.1, Clang22.1.7, CMake4.3.0, Ninja1.13.2,
Python3.14.6. Debug/release/sanitize headless builds pass; native ASan/UBSan emits
no diagnostic on the valid corpus, ROM block, malformed CLI cases, and 10,000
seeded random payloads with valid container/packed CRC. Random rejection stress
checks memory safety only, not semantic correctness. The two historically unsafe
reference fixtures now produce native diagnostics without invalid memory access.

```sh
python3 tools/project.py configure --preset sanitize
python3 tools/project.py build --preset sanitize
python3 tools/project.py test --rom --preset sanitize
python3 tools/project.py reference-test --rom --preset sanitize
python3 tools/project.py rnc-validate --decode --preset sanitize
```

Use debug/release presets likewise. Reference comparison needs the existing
pinned research build; normal builds/extraction do not need it or download it.
Evidence: `local/logs/native-rnc2/commands.json`,
`local/generated/rnc-comparison/run-jv84_pye/report.json` (50 cases: 49 synthetic
plus one ROM block), `local/generated/rnc-validation/run-m5zxfbx6/report.json`,
and `build/{debug,release,sanitize}/Testing/Temporary/LastTest.log`.
Tests: `tests/native_rnc2.py`, `tests/unit/rnc2_test.cpp`,
`tests/test_rnc2_corpus.py`, `tests/test_native_build.py`,
`tests/test_rnc_validate.py`.

Limitations: other 133 candidates unvalidated; resource layout/role unknown;
no original CPU, sound driver or game ran. Next validation is the loader/caller
investigation [[07_Tasks/TASK-0004-rnc-loader]]. Related:
[[03_Reverse_Engineering/ASSET_FORMATS]], [[04_Native_Implementation/PORTING_MAP]],
[[05_Validation/RESULTS]].

Subsequent static linkage: [[03_Reverse_Engineering/findings/FIND-0007-rnc-loader]]
identifies original decoder `0x19462`, the PACK wrapper/caller chain and first-bank
consumer layout. That supersedes this note's earlier unknown-address/role and
next-task statements. Output identity is unchanged. Original execution,
rendered appearance and gameplay equivalence remain untested.
