---
id: RE-ASSET-FORMATS
type: technical
status: partial
---
# Resource formats and extraction

Two compressed blocks have integrity-checked native/reference output and
verified static consumers: a base graphics bank and a companion scene resource.
The base bank consists of palette inputs, a count, 32-byte patterns and parallel
eight-byte records. The companion adds coordinates, patterns and map words. Normal 8x8 pixel order and color-bit positions are now corroborated by a pinned
reference implementation. Native parsing and a diagnostic atlas work; exact
display brightness and runtime camera/layers remain unvalidated. The eight-byte
records now have verified terrain contact use; see FIND-0010 below.
A diagnostic static map plane now composes natively.

## RNC2 block container

The offsets below are relative to a block header, not CPU addresses:

| Range | Observed field |
| --- | --- |
| `[0,3)` | ASCII RNC |
| `[3,4)` | Method byte; 2 on the validated block |
| `[4,8)` | Big-endian unpacked length |
| `[8,12)` | Big-endian packed-payload length, excluding 18-byte header |
| `[12,14)` | Big-endian unpacked CRC16 |
| `[14,16)` | Big-endian packed CRC16 |
| `[16,18)` | Additional header bytes observed as 4 and 2; original game interpretation pending |
| `[18,18+packed_length)` | Compressed payload |

CRC width16, reflected polynomial `0xA001`, initial0 and no final XOR are
independently implemented by `tools/rnc.py` and the pinned reference. On the
first block both stored CRCs match, and the reference consumes exactly the
declared byte extent. Padding before the next signature is excluded.

Authoritative catalog: `re/rnc_blocks.json`, stable ID `rnc.unclassified.0001`.
It records ROM range, decode method, lengths, CRCs and input/output hashes;
structure and consumer findings are recorded; remaining semantic unknowns are null. File-offset splitting remains separately governed
by `re/sega2asm/segments.json`; its raw remainder contains this now-verified
subrange. No compressed handler is added to the defective upstream splitter.

## Current reproducible extraction

```sh
python3 tools/project.py configure --preset debug
python3 tools/project.py build --preset debug
python3 tools/project.py rnc-validate --decode
```

The default backend is the bounded project C++20 codec `wiz_rnc2`. It uses no
original CPU stream and links no reference implementation. Build source and
executable hashes must match the local provenance record. The decoder accepts
one nonempty method-2 block, defaults to 4 MiB packed/output safety limits,
and verifies every read, match and output extent plus both CRCs and termination.
The wire grammar and measured scope are in
[[03_Reverse_Engineering/findings/FIND-0006-native-rnc2]].

Output is atomically replaced only after all checks pass:
`local/extracted_assets/rnc/rnc.unclassified.0001.bin`, 17,714 bytes, SHA-256
`048aec81ffb0e5463029b931c2716e5aaa818539b5f72c078f7a19cc195a9ac7`.
Per-run reports record exact invocation, backend, executable/source identity,
consumption and diagnostics under `local/generated/rnc-validation/`.
Header-only `rnc-validate` verifies packed integrity without extracting.

The independent GPL ScummVM research process is optional for extraction and
required for explicit differential checks:

```sh
python3 tools/build_rnc_reference.py
python3 tools/project.py reference-test --rom --preset debug
python3 tools/project.py rnc-validate --decode --backend reference
```

Only if pinned sources are absent, explicitly bootstrap with
`python3 tools/build_rnc_reference.py --download`. No build/validation command
silently downloads dependencies. Source/license hashes are pinned in
`third_party/rnc_reference.lock.json`. The reference's unchecked accesses are
contained by mandatory Clang ASan/UBSan and process limits; it must stay outside
the native library. Tool licenses grant no rights over extracted content.

Full block evidence: [[03_Reverse_Engineering/findings/FIND-0004-first-rnc-block]].
Rejected alternative: [[03_Reverse_Engineering/findings/FIND-0005-rnc-upstream-defect]].
The other 132 signature candidates remain unvalidated. Timing, device audio,
scene identity and exact display response remain unknown. Terrain record use is
now verified by [[03_Reverse_Engineering/findings/FIND-0010-terrain-query]].
Next: [[07_Tasks/TASK-0008-movement-step]].

## First bank structure and original consumer

[[03_Reverse_Engineering/findings/FIND-0007-rnc-loader]] establishes original
RNC2 decoder `[0x19462,0x1959E)` and the descriptor-zero path from table
`0x33400` through the PACK wrapper at `0x348AE`, to scratch RAM `0xFFFF8844`,
then consumer `0x3D46`. The descriptor points four bytes before the RNC header;
this resolves the previously missing direct-header pointer.

| Decoded range | Consumer-derived role |
| --- | --- |
| `[0,32)` | 16 two-byte palette inputs; original palette loader `0x13754` |
| `[32,34)` | Big-endian count-minus-one `0x01B9`, hence 442 records |
| `[34,14178)` | 442 patterns, 32 bytes each, transferred by eight longword writes |
| `[14178,17714)` | 442 opaque eight-byte records copied into RAM |

The format is named `pattern_bank_v1` by this project. All 17,714 bytes are
accounted for; component hashes are in the local probe report. The stable ID
`rnc.unclassified.0001` is retained even though its role is now better understood.
Catalog `re/rnc_blocks.json` is authoritative for measured structure; analysis
metadata is `re/rnc_loader.json`. Reproduce with:

```sh
python3 tools/project.py rnc-loader-probe --disassemble \
  --decoded-bank local/extracted_assets/rnc/rnc.unclassified.0001.bin
```

The original palette routine transforms input pair `[a,b]` into
`[b & 15, (b & 240) | (a & 15)]` in a RAM palette buffer. It preserves the source
pointer. TASK-0005 now implements the structured loader and corroborates normal-mode
pixel/color bits; its diagnostic scale is described below. Original malformed-
input behavior is unsafe and intentionally not reproduced by native parsers.

## Native bank and diagnostic atlas

[[03_Reverse_Engineering/findings/FIND-0008-native-pattern-bank]] documents the
normal 8x8 row-major indexed representation: four packed bytes per row, high
nibble first. CRAM R/G/B use bits1–3/5–7/9–11. Native resources preserve raw
palette bytes, converted words and all opaque records; count uses host-sized
storage. Bounds distinguish the format's 1–65536 count from future engine limits.

`normal-rgb3-rounded-v1` is an explicit diagnostic scale, rounded full-range
3-bit RGB. It does not reproduce analog brightness, fades or shadow/highlight.
Index zero is transparent with RGB retained; unused atlas cells are transparent
black. The image is a resource inspection artifact, not an assembled game scene.

```sh
python3 tools/project.py bank-atlas --bank rnc.unclassified.0001 --columns 32
```

This command needs the verified extracted blob and recorded native build, but
neither the raw ROM nor an emulator. The C++ executable produces all pixels;
Python checks them against an independent bitplane specification model and
packages the unchanged raster into PNG. Paths, process status, provenance and
input/output digests are recorded per run under `local/generated/bank-atlas/`.
The default atlas is 256x112 with 442 patterns and six empty cells. Opaque records
remain in the structured resource, not encoded as invented collision data.


## Companion scene v1

[[03_Reverse_Engineering/findings/FIND-0009-companion-scene]] establishes
`scene.companion.0001`, conditionally paired with `rnc.unclassified.0001` by
descriptor 0/slot 0. PACK tag `0x48FD4`, RNC2 range `[0x48FD8,0x4A604)`, decoded
13,700 bytes, SHA-256
`4f043e8a070b98053fa84b7af8c773c6d447994458e0440fdd6c73036f1452c4`.

| Decoded range | Meaning |
| --- | --- |
| `[0,2)` | Coordinate count-minus-one 12 |
| `[2,54)` | 13 raw x/y pairs; original adds 128/112 with word wrap |
| `[54,62)` | Two state starts; original adds 128/120 with word wrap |
| `[62,64)` | Additional pattern count-minus-one 135 |
| `[64,4416)` | 136 packed 8x8 patterns, appended after base 442 |
| `[4416,4420)` | Header 128,32; width/stride and skipped second word |
| `[4420,12612)` | 4096 map words, 128x32, corroborated row stride/bounds |
| `[12612,13700)` | 136 opaque eight-byte records |

`parse_scene` preserves source/translated coordinates, words, flags and records.
Coordinate purpose remains unknown. Record terrain use is verified below. Map
setup uses full 16-bit
wrapping ADD of the original pattern base followed by OR 0x4000. The native
resource uses relative pattern indices; a focused helper preserves that original
word operation for tests/reconstruction. The current importer rejects shapes
other than the verified 128x32; host resource containers are not permanently fixed.

Name-table index bits 0–10, H/V flips 11/12, palette 13–14 and priority 15 are
corroborated by pinned MAME source. This map uses palette 2 after the original OR.
Its 561 unique pattern indices, maximum 576, fit within the combined 578 patterns.
`make_scene_image` composes a single 1024x256 plane with diagnostic colors and
alpha, no original CPU execution. Unsupported palette or missing pattern fails.
No actors, backdrop, camera or collision behavior are substituted.

```sh
python3 tools/project.py rnc-validate --block scene.companion.0001 --decode
python3 tools/project.py scene-probe --disassemble \
  --decoded-scene local/extracted_assets/rnc/scene.companion.0001.bin
python3 tools/project.py scene-preview --scene scene.companion.0001
```

Catalog: `re/rnc_blocks.json`; code/dataflow authority: `re/scene_loader.json`.
Outputs/reports are local only; the extracted resource is sufficient after
extraction, with the base bank and verified native build. `reference-test --rom`
now checks both cataloged blocks instead of assuming a singleton catalog.


## Terrain records: verified consumer semantics

[[03_Reverse_Engineering/findings/FIND-0010-terrain-query]] confirms that the
parallel eight-byte record is indexed by local x modulo8, reversed for map bit11.
Bit12, palette and priority do not alter this lookup. Contact callers compare
its unsigned byte with `(local_y & 7)+1`; values0–8 occur in all 578 current
records. The original routines and native replacements agree in independent
execution. This establishes per-column contact levels for these consumers,
not every collision rule. Native assets retain all bytes under the existing
`opaque_record` field; `src/sim/terrain.cpp` interprets the verified use.
Above-map queries preserve prior scratch coordinates, and out-of-resource
addresses reject explicitly. Full contracts and evidence are in FIND-0010.
