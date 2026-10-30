---
id: FIND-0008
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: decoded_resource_offset
confidence: confirmed
task: TASK-0005
---
# Native structured bank and diagnostic atlas

Task: [[07_Tasks/TASK-0005-native-pattern-bank]]. Confirmed scope: exact resource
partitioning, byte permutation, documented normal-mode pattern interpretation,
and agreement of native output with a separate specification model. This is
**not original game execution or an original-screen fidelity result**.

## Identity and observations

ROM-LOCAL-0001 is 1,048,576 bytes, SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
No normalization. Stable bank ID `rnc.unclassified.0001` comes from ROM file
`[0x348B2,0x372F7)` under the PACK tag at `0x348AE`. Its decoded 17,714-byte
SHA-256 is `048aec81ffb0e5463029b931c2716e5aaa818539b5f72c078f7a19cc195a9ac7`.
All decoded ranges below are half-open; none are host pointers.

[[03_Reverse_Engineering/findings/FIND-0007-rnc-loader]] establishes descriptor
zero, original decoder `0x19462`, consumer `0x3D46`, and palette routine
`0x13754`. Their reads partition palette `[0,32)`, BE count-minus-one `[32,34)`,
patterns `[34,14178)` and opaque records `[14178,17714)`. The two body-first DBF
loops explain 442 patterns and 442 records. No new ROM range is classified here.

## Pixel interpretation and color decision

Pinned MAME revision `309bec2b8fe5279d461960a7935cc540203307c2` supplies independent
source evidence, not an executed reference. `315_5313.cpp` defines an 8x8,
four-plane, 32-byte layout; `drawgfx.cpp` specifies MSB-first bit addressing and
plane weights. Accounting for its little-endian word storage yields four bytes
per row, high nibble before low nibble. `write_cram_value` and the palette
implementation in `315_5124.cpp` establish R bits 1–3, G 5–7, B 9–11 of a CRAM
word; drawing treats index zero as transparent. Source hashes/licenses/paths are
in `third_party/vdp_reference.lock.json`; sources remain ignored locally.
See [[09_References/SOURCES]]. The normal 8x8 interpretation is used for the
atlas; scene register state, interlace, priority and flips have not been observed.

The original palette conversion `[a,b] -> [b & 15, (b & 240) | (a & 15)]` is
implemented exactly, including otherwise unused bits. Source bytes and CRAM
words remain available in the native resource. A separate **diagnostic** policy,
`normal-rgb3-rounded-v1`, maps channel n to `(255*n+3)/7` with integer division:
`0,36,73,109,146,182,219,255`. This is an explicit digital inspection scale.
MAME uses a nonlinear brightness table; our policy does **not** claim to match
that table, an analog console, CRT response, fades, or shadow/highlight.

Index zero retains its RGB but has alpha zero; other indices have alpha 255.
Unused atlas cells are transparent black. No scene backdrop is invented.
This diagnostic policy is not an original/enhanced gameplay profile.

## Implementation and independent checks

`src/assets/pattern_bank.hpp/.cpp` supplies `wiz::assets::parse_pattern_bank`,
`palette_cram_word`, `diagnostic_rgba`, `make_atlas`, and `encode_pam`. The native
bank stores a stable logical ID, 16 raw/converted palette entries, a host-sized
pattern vector, 64 indices per pattern, and every eight-byte opaque record.
No source ROM offset or original RAM pointer is a native asset identity.

Wire count 0 means 1; 0xFFFF means65536. Bounds are checked before allocation;
truncation, trailing bytes and malformed IDs fail. The wire-format ceiling is
not an engine entity/tile limit. Atlas columns are 1–256 and the default safety
budget is 4,194,304 pixels, checked with overflow-safe products. Synthetic 1000-
and 65536-pattern banks parse successfully; this does not establish an original
hardware restriction or completed enhanced mode.

`wiznliz-bank-atlas ID BANK COLUMNS` reads extracted bytes without a ROM and
emits native RGBA as PAM. `bank-atlas` resolves a catalog ID, rejects changed or
redirected extraction, verifies executable provenance, snapshots the input,
checks metadata, and writes local artifacts atomically. Python only packages
native pixels into PNG using filter 0 and stored DEFLATE blocks, yielding stable
bytes independent of compression heuristics. Failed runs never report success.

`tools/bank_reference.py` is project-authored independent specification checking:
it uses MAME's bitplane layout instead of native nibble extraction, and derives
channels directly from source palette words. It executes neither MAME nor the
game. Tests include asymmetric authored rows/colors, 256 single-bit patterns,
all truncation boundaries, count extremes, invalid IDs/dimensions, record
preservation, PNG chunk/CRC/raster checks and stale-build rejection.

## Results and reproduction

```sh
python3 tools/project.py configure --preset debug
python3 tools/project.py build --preset debug
python3 tools/project.py rnc-validate --decode
python3 tools/project.py bank-atlas --bank rnc.unclassified.0001 --columns 32
python3 tools/project.py configure --preset sanitize
python3 tools/project.py build --preset sanitize
python3 tools/project.py test --rom --preset sanitize
```

The local atlas is **256x112**, 442 patterns / 448 cells, 28,288 pattern pixels
and 384 padding pixels. Every pixel agrees with the independent model. PNG is
114,873 bytes, SHA-256
`988b4d3eb88dfaf59bcdcde7fd7216a96870f9704fb5f10e05e882e24f5d71e6`;
RGBA SHA-256 is
`00395d04dc98c17f7ac504a82de6817849b4e2c4cc774f5542b57da214fc3257`.
The image was opened locally and displays coherent terrain-like fragments.
That observation does not identify a scene or prove composition/collision.

`local/logs/pattern-bank/commands.json` records exact invocations, status and log
paths; `atlas-reproduction.json` links debug/release/sanitizer/repeat reports.
Per-run inputs, PNG/PAM and reports are beneath `local/generated/bank-atlas/`.
Tested on Fedora44 x86_64 with GCC16.1.1, Clang22.1.7, CMake4.3.0, Ninja1.13.2
and Python3.14.6. Current totals/results: [[05_Validation/RESULTS]].

## Limits and next validation

Opaque records remain lossless and uninterpreted. No collision meaning, named
scene, original capacity, player behavior or complete palette-update routine is
claimed. The nested original palette callee `0x137CE` remains unreconstructed.
No emulator, sound driver, SDL window or original CPU stream is executed.
Next: [[07_Tasks/TASK-0006-companion-scene-resource]], tracing the A1 resource
and consumer `0x3E14` toward actual placement and scene reconstruction.
Mappings: [[04_Native_Implementation/PORTING_MAP]]. Format authority:
[[03_Reverse_Engineering/ASSET_FORMATS]] and `re/rnc_blocks.json`.
