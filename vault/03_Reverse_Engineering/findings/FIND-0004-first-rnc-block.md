---
id: FIND-0004
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset
confidence: confirmed
task: TASK-0002
---
# First RNC2 block: integrity and bounded reference decode

**Confirmed scope:** this exact block's bounds, packed CRC, reference decoding,
produced length, unpacked CRC, and byte consumption. Its gameplay role and the
original game's decompressor routine remain unknown; no original CPU ran.
Task: [[07_Tasks/TASK-0002-rnc-block]]. Prior hypothesis:
[[03_Reverse_Engineering/findings/FIND-0003-rnc-candidates]].

## Identity, observations and interpretation

ROM-LOCAL-0001 is 1,048,576 bytes, SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
No normalization. All intervals here are half-open file offsets.

| Observation | Verified value |
| --- | --- |
| Stable logical block ID | `rnc.unclassified.0001` |
| Header | `[0x348B2,0x348C4)`; `RNC`, method 2 |
| Packed payload | `[0x348C4,0x372F7)`; 10,803 bytes |
| Whole block | `[0x348B2,0x372F7)`; 10,821 bytes |
| Declared and produced output | 17,714 bytes |
| Packed CRC, stored and two implementations | `0x3673` |
| Unpacked CRC, stored and two implementations | `0xAF73` |
| Observed input consumption | 10,821 bytes total, 10,803 after header |
| Header bytes 16 and 17 | `4`, `2`; no game-specific interpretation established |
| Next signature | `0x372FC`; the five intervening bytes are outside this block |

Whole-block SHA-256:
`a005c823ca9749f3ffffffe310832fcb4de5896828e2b8a0e868757787f2a505`.
Packed-payload SHA-256:
`f4715dcb73dea9811d510a1cda38bfb932221c371c9cca64b8199882080bb113`.
Decoded SHA-256:
`048aec81ffb0e5463029b931c2716e5aaa818539b5f72c078f7a19cc195a9ac7`.

Interpretation: a valid method-2 compressed block under the pinned reference
algorithm, with both stored integrity fields matching. This supports the first
candidate, not the other 133 candidates. A CRC match is not dump provenance and
does not determine sprite/map/audio/text meaning.

## Verification and implementation

`tools/rnc.py` independently implements bitwise reflected CRC16 (polynomial
`0xA001`, initial 0, no final xor), bounded header parsing and output checks.
The independent ScummVM decoder uses its own table CRC implementation. The
Python inspector caps declared packed/unpacked resources at 4 MiB before decode;
the catalog currently exposes exactly this one ROM-dependent block.

ScummVM revision `e60a6799188cc04e6ef0fba34978f8afd4f25d43` is the pinned
reference, using unmodified `common/compression/rnc_deco.cpp` and `.h`.
The separately compiled C++20 harness observes source/destination pointers and
requires exact consumed/produced extents. Clang 22.1.7 AddressSanitizer and
UndefinedBehaviorSanitizer are mandatory. The actual block passes without
sanitizer diagnostics. Upstream malformed-stream memory accesses are contained
by sanitizer termination, CPU/alarm limits and a parent timeout; this is not a
hardened production decoder. A GCC sanitizer attempt failed because system
libasan/libubsan runtimes are absent; installed Clang compiler-rt works.

`tools/rnc_validate.py` checks original identity, recorded block metadata,
packed CRC, reference process/metadata, output length/CRC/hash, exact consumption
and original identity again before atomically saving the result. Its tests
ensure corrupt or failed output cannot overwrite an existing asset. Plain
`rnc-validate` checks only packed integrity; `--decode` performs extraction.

Authoritative metadata: `re/rnc_blocks.json`. Output:
`local/extracted_assets/rnc/rnc.unclassified.0001.bin`. Role, dimensions and
palette remain null. No source ROM offset becomes a permanent native resource
pointer. The reference is research/extraction tooling under GPL-3.0-or-later,
not a native game component; downloaded implementation remains ignored. Lock:
`third_party/rnc_reference.lock.json`.

## Reproduce and inspect evidence

```sh
# Existing pinned local sources; no downloads:
python3 tools/build_rnc_reference.py
python3 tools/project.py rnc-validate
python3 tools/project.py rnc-validate --decode --backend reference
python3 tools/project.py test --rom
```

Only if source downloads are absent, explicit bootstrap:
`python3 tools/build_rnc_reference.py --download`. Normal validation does not
download or build. Local build provenance includes exact compiler command,
source/harness/builder/executable hashes. Successful executable in this pass:
SHA-256 `bf03544d9c691a6612f4ef1028dba145aff8ea847a5941c2fd7656e1861805f6`.
Rebuilds may have a different binary hash because sanitizer debug paths are
recorded; source pins and decoded-byte expectations remain fixed.

Evidence: `local/generated/rnc-validation/run-yvge20iw/report.json`,
`local/generated/rnc-reference-initial/runs.json`,
`local/tools/rnc-reference/build.json`, and `local/logs/rnc-pass/commands.json`.
The first decode and subsequent integrated reruns produce the same bytes/hash.
`tests/test_rnc.py`, `test_rnc_reference.py`, `test_rnc_validate.py` and
`test_rnc_upstream.py` use authored fixtures, never the game payload.

## Limits and next useful step

No caller, original decompressor entry, destination RAM/resource consumer,
graphics layout, palette assignment, animation or audio sequencing is mapped.
A raw search for big-endian 32-bit `0x348B2` and `0x372FC` found no matches in the
ROM; this does not exclude relative tables, computed addresses or other packing.
It is only a lead, not proof of absent references. No broader asset extraction
or original execution was performed.

Next: [[07_Tasks/TASK-0003-native-rnc2]], a bounded C++20 asset codec with
independent differential tests. Later establish the decoded resource's consumer
and structured layout. See [[03_Reverse_Engineering/ASSET_FORMATS]] and
[[04_Native_Implementation/PORTING_MAP]].

Follow-up: [[03_Reverse_Engineering/findings/FIND-0006-native-rnc2]] completes
[[07_Tasks/TASK-0003-native-rnc2]]. The default `--decode` backend is now the
project-native codec; use `--backend reference` to reproduce the research path
recorded above. This supersedes the earlier dependency/next-task statements,
without changing the baseline output or establishing any resource semantics.

Subsequent static linkage: [[03_Reverse_Engineering/findings/FIND-0007-rnc-loader]]
identifies original decoder `0x19462`, the PACK wrapper/caller chain and first-bank
consumer layout. That supersedes this note's earlier unknown-address/role and
next-task statements. Output identity is unchanged. Original execution,
rendered appearance and gameplay equivalence remain untested.
