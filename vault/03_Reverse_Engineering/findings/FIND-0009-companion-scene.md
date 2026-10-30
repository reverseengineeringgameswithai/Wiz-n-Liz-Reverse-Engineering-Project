---
id: FIND-0009
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_decoded_resource_offset
confidence: confirmed
task: TASK-0006
---
# Companion scene structure and native map-plane reconstruction

Task: [[07_Tasks/TASK-0006-companion-scene-resource]]. **Confirmed scope:**
static selection/consumer relationships, exact integrity-checked resource
extents, native parsing of those fields and diagnostic single-plane composition.
No original CPU, camera, player or gameplay session was executed.

## Identity and selection

ROM-LOCAL-0001: 1,048,576 bytes, SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`, no normalization.
Ranges below are half-open. ROM CPU addresses are direct file offsets only in
the established ROM window; RAM/device effective addresses are not file offsets.

The dispatcher `[0x1896,0x18EE)` compares signed words at offset `+0x26` in the
two state structures rooted at `0xFFFF0690` and `0xFFFF0838`. Its exchange/branch
leaves the smaller signed word in D1. It sign-extends, uses DIVU.W by 3, adds one
if the descriptor index from `(A2+4)` equals 8, then shifts the quotient word by 2
and fetches a longword through a signed-word indexed address. Negative values,
division overflow, the permissible state range and gameplay meaning are not
established. No unbounded table interpretation is implied.

For **descriptor index 0 and a smaller state word in [0,2]**, the selected
companion slot is 0. The pointer at file `0x33400` is `0x48FD4` (PACK tag), with
RNC2 header at `0x48FD8`. This conditional pairing uses the known first pattern
bank selected at descriptor `+0x1C`, not an invented scene/resource pairing.
The paired loader saves A1, restores it into A0 at `0x3D0A`, tests PACK, skips 4,
calls decoder `0x19462` at `0x3D20` with destination `0xFFFF8844`, and passes that
buffer to consumer `0x3E14` at `0x3D2C`. Non-PACK input bypasses decompression.

## Second validated RNC2 block

Stable logical ID: **`scene.companion.0001`**. ROM range
`[0x48FD8,0x4A604)`, 5,676 bytes: 18-byte header + 5,658-byte payload.
Unpacked size 13,700; packed CRC16 `0x9B01`, unpacked CRC16 `0x0E0B`.
Block SHA-256: `7fe064883f2dda127a3b522cc034e82a9c3ab1e00c8933b4765c133c080b799d`.
Decoded SHA-256: `4f043e8a070b98053fa84b7af8c773c6d447994458e0440fdd6c73036f1452c4`.
Both the bounded native codec and independently pinned sanitized ScummVM process
consume the declared extent and emit identical bytes with both CRCs validated.
Header/decoded identity remains catalog authority `re/rnc_blocks.json`.

## Consumer observations

| Code range | Role | Scope |
| --- | --- | --- |
| `[0x3E14,0x3F34)` | Consume coordinates, starts, additional patterns, map header and records | FUNC-0008, bounded entry through RTS, calls helper below |
| `[0x3F34,0x3F60)` | Relocate/copy 4096 map words | FUNC-0009, nested DBF32x128, RTS |
| `[0x406C,0x40F8)` | Read a map column using width-dependent row stride | Internal fragment only, has exits outside range; not a complete function |

`scene-probe` checks these exact range hashes, 56 reviewed instruction fields,
call/DBF targets, transfer widths and 16 independent short-instruction GNU
corroborations. Capstone is explicitly selected for original 68000 with a
68020-only sentinel rejected. No linear-sweep function count is claimed.

Decoded ranges derived from these reads:

| Range | Content / observed count |
| --- | --- |
| `[0,2)` | BE coordinate count-minus-one 12 => 13 pairs |
| `[2,54)` | 13 pairs of BE x/y words, purpose unknown |
| `[54,62)` | Two pairs copied into the two state structures at offsets+0x3C/+0x3E |
| `[62,64)` | BE pattern count-minus-one 135 => 136 patterns |
| `[64,4416)` | 136 additional 32-byte patterns |
| `[4416,4420)` | Words 128 and 32; first controls width/row strides, second is skipped by this consumer |
| `[4420,12612)` | 4096 BE map words, row-major 128 columns x 32 rows |
| `[12612,13700)` | 136 additional opaque eight-byte records |

Coordinate additions are **16-bit wrapping**: x+128,y+112 for the first list,
x+128,y+120 for the two state starts. The original list goes to `0xFFFF4C80`
and is followed by two FFFF sentinel words. Native vectors retain count and
source/translated coordinates without needing an in-memory sentinel. The two
state structures are probably player-related, but this pass does not claim the
coordinates' gameplay roles or turn them into dummy entities.

First-bank loader `0x3D46` advances the pattern/record cursors by its measured
442 entries; companion patterns/records append after those entries. Map setup
reads each word and writes `((word + original_base) mod 65536) OR 0x4000` into
RAM `[0xFFFF4D02,0xFFFF6D02)`. This is a full word addition, not a separately
masked index addition. Native `relocate_map_word` preserves that arithmetic;
normal native resources retain logical relative pattern indices instead of
hardware addresses. Original relocation overflow/VRAM aliasing is not modeled
by diagnostic scene composition.

The column reader adds column*2 to that table, adds signed row*width*2, and then
steps by width*2; its row bound 31 corroborates 32 rows. All 4096 map words copy
regardless of header values. The current importer therefore accepts only the
verified 128x32 shape; it rejects other headers explicitly rather than inventing
another format. This is an import restriction, not a permanent host world limit.

## Map interpretation and native implementation

Pinned MAME `get_nametable` at revision in `third_party/vdp_reference.lock.json`
corroborates index bits 0–10, horizontal flip 11, vertical flip 12, palette 13–14,
and priority 15. All observed raw words use palette bits 0; OR 0x4000 selects
palette 2, matching the first bank's palette destination. Maximum relative index
is 576; 561 unique indices refer within 442+136=578 supplied patterns.

`src/assets/scene.hpp/.cpp` implements bounded `parse_scene`, wrapping coordinate
conversion, map-word relocation and `make_scene_image`. Raw coordinate values,
map words, flags and opaque records are retained. Scene/base links use stable
IDs, host-sized vectors and explicit pixel budgets. Missing palettes, wrong bank
links and invalid pattern references fail. No emulator code or original CPU
stream is linked/executed. Shared pattern decoding is reused by both resources.

`scene-preview` verifies both extracted input hashes and executable provenance,
then launches `wiznliz-scene-preview`. Native C++ supplies all pixels. The
independent Python model uses pinned bitplane layout plus row/list reversals,
checks every pixel, and packages unchanged RGBA as PNG. This is specification
comparison, not an executed emulator differential. The output preserves alpha
and uses `normal-rgb3-rounded-v1` diagnostic color scaling. It shows one map
plane without entities, backdrop, camera, inter-plane priority or audio.

## Reproduction and results

```sh
python3 tools/project.py build --preset debug
python3 tools/project.py rnc-validate --block scene.companion.0001 --decode
python3 tools/project.py scene-probe --disassemble \
  --decoded-scene local/extracted_assets/rnc/scene.companion.0001.bin
python3 tools/project.py scene-preview --scene scene.companion.0001
python3 tools/project.py reference-test --rom
python3 tools/project.py test --rom --preset sanitize
```

First configure each missing preset as documented in README. C++20 GCC16.1.1 /
Clang22.1.7, CMake4.3.0, Ninja1.13.2, Python3.14.6, rasm2 5.9.8 tested on Fedora44
x86_64. 95 Python tests and all 6 CTest targets in debug/release/sanitizer pass.
51 codec cases match independently: 49 authored plus 2 cataloged ROM blocks.

Image: **1024x256**, all 262,144 pixels match the independent model. PNG 1,048,980
bytes, SHA-256 `476cb65271060616db42300cd0efe1880bb1ef64774be9cacd81d491a52bea92`.
Native RGBA SHA-256 `588559afa09005a663e41e338bd816d10d9a949bd1b284eba5c8992559daa99f`.
Debug/release/sanitizer/repeat images are byte-identical. Local visual inspection
shows coherent terrain, not a named-stage identification or gameplay test.

Evidence: `local/generated/scene-probe/run-yr2s7pku/report.json` and adjacent
`decoder-evidence.json`; `local/generated/rnc-comparison/run-1aaljm3a/report.json`;
`local/generated/scene-preview/run-g73_3ur2/report.json` and `scene.png`.
`local/logs/companion-scene/commands.json` / `reproduction.json` record commands,
status, all preset artifacts and regression checks. Exploratory disassembly
under `local/generated/companion-research/` includes deliberately truncated or
misaligned discovery dumps; only the reviewed ranges are promoted as evidence.

## Limits and continuation

No native playability yet. Resource selection in a real session, camera/layers,
coordinate roles, collision response and sound remain unknown. Records stay
opaque despite promising byte-indexing leads. No gameplay-equivalence claim is
supported by the static preview. Next:
[[07_Tasks/TASK-0007-terrain-query]] traces readers near `0x9A18` and acquires
independent execution evidence before reconstructing terrain-query behavior.
See [[04_Native_Implementation/PORTING_MAP]], [[03_Reverse_Engineering/ASSET_FORMATS]],
[[03_Reverse_Engineering/COVERAGE]], [[05_Validation/RESULTS]].
