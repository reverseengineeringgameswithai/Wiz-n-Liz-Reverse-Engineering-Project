---
id: REFERENCE-SOURCES
type: references
status: active
---
# Sources and provenance

Access date for the following sources: **2026-10-02**. External documentation is
a lead or implementation reference, never a substitute for checking this exact
ROM. Local observations and commands live in the linked technical notes.

| Source | Revision / version | What was used |
| --- | --- | --- |
| [sega2asm upstream](https://github.com/hansbonini/sega2asm/tree/78f37b0d71d27b43b960e24c01c5437bbef55404) | commit `78f37b0d71d27b43b960e24c01c5437bbef55404`, reports v1.0.0 | README, go.mod/go.sum, CLI, config, handlers and decoder inspected; actual local build/split and defects in [[03_Reverse_Engineering/SEGA2ASM]] |
| [sega2asm header implementation](https://github.com/hansbonini/sega2asm/blob/78f37b0d71d27b43b960e24c01c5437bbef55404/types/rom.go) | same pinned revision | Header offsets/endianness corroborate original Python inspector; generated-header limitations separately reviewed in segments/header.go; no source copied |
| [Go releases](https://go.dev/dl/?mode=json) | go1.27.1 linux-amd64 | Official archive SHA-256 and size checked; local bootstrap provenance in lock manifest |
| [Motorola programmer reference](https://www.nxp.com/docs/en/reference-manual/M68000PM.pdf) | retrieved publisher PDF | Original-68000 instruction fields, sign extension, PC-relative base, register order and DBcc semantics; FIND-0001 |
| [Motorola user's manual](https://www.nxp.com/docs/en/reference-manual/MC68000UM.pdf) | retrieved publisher PDF, §2 | Original MC68000 24-bit external address width; distinction from 32-bit effective values |
| [radare2 Capstone plugin](https://raw.githubusercontent.com/radareorg/radare2/5.9.8/libr/arch/p/m68k_cs/plugin.c) | upstream tag 5.9.8; installed RPM 5.9.8-9.fc44 | CPU-mode mapping; executable sentinel verifies 68000 selection |
| [radare2 GNU plugin](https://raw.githubusercontent.com/radareorg/radare2/5.9.8/libr/arch/p/m68k_gnu/plugin.c) | same tag; source has GPL-3.0-only declaration | Four-byte callback limitation and extra CPU flags; corroboration restricted to reviewed short instructions |
| [Fedora SDL3-devel](https://packages.fedoraproject.org/pkgs/SDL3/SDL3-devel/) | page consulted; installed/cache versions recorded separately | Development package purpose and available Fedora packaging; no package installed |
| [SDL3 CMake integration](https://wiki.libsdl.org/SDL3/README-cmake) | current page, not pinned source | Planned system discovery and SDL3::SDL3 target; not evidence a local application built |
| [SDL3 Linux notes](https://wiki.libsdl.org/SDL3/README-linux) | current page | Platform prerequisites lead for later application work |
| [Git ignore documentation](https://git-scm.com/docs/gitignore) | current documentation; installed Git tested locally | Ignore rules do not remove indexed content; checker inspects both |
| [Obsidian internal links](https://obsidian.md/help/links) | current help page | Vault-relative explicit note links, aliases and heading links; no plugin dependency |
| [ScummVM RNC decoder](https://github.com/scummvm/scummvm/blob/e60a6799188cc04e6ef0fba34978f8afd4f25d43/common/compression/rnc_deco.cpp) | commit `e60a6799188cc04e6ef0fba34978f8afd4f25d43` | Method-2 reference, MSB-first controls, interleaved raw bytes and independent CRC table; built/run on the first block and authored fixtures |
| [ScummVM decoder interface](https://github.com/scummvm/scummvm/blob/e60a6799188cc04e6ef0fba34978f8afd4f25d43/common/compression/rnc_deco.h) | same pin | Protected cursors/CRC exposed only through an original observation subclass; upstream source unmodified |
| [ScummVM license](https://github.com/scummvm/scummvm/blob/e60a6799188cc04e6ef0fba34978f8afd4f25d43/COPYING) | same pin; source headers specify GPL-3.0-or-later | License and COPYRIGHT retained with ignored source; no original decoder implementation copied into tracked project runtime |

`third_party/manifest.lock.json` records actual third-party revision, licenses,
archive/executable hashes, build invocation and module dependencies. Downloads,
compiler/tool source and caches stay in ignored `local/tools/`; no third-party
implementation was copied into tracked project source. Tool licenses do not
grant redistribution rights to ROMs or generated content.

The main manifest links `third_party/rnc_reference.lock.json`, which pins four
ScummVM source/license downloads and their lengths/hashes. The original
`re/reference_scripts/rnc_reference_main.cpp` harness declares GPL-3.0-or-later
and is research tooling, not a game runtime. Exact compiler/source/harness/
builder/executable provenance is in ignored `local/tools/rnc-reference/build.json`.
Sources and observations above were accessed/tested on 2026-10-02.

The user-supplied input has only local file provenance, recorded in
[[03_Reverse_Engineering/ROM_IDENTITY]]. No online ROM database was treated as
authoritative and no proprietary content was sent to these sources.

Ghidra, MAME debugger and clownassembler remain investigation leads from the
brief; none was run or integrated in this pass. Their absence is recorded in
[[02_Workflow/ENVIRONMENT]], not treated as successful validation.

Session 2026-10-02-003 reused the same pinned ScummVM source (local inspection of
`unpackM2` and the shared bit reader) to establish a wire grammar and independently
validate 49 authored cases. The project codec uses original checked-cursor and
declarative-table code, with no imported implementation or GPL reference linked
into the native library. This was direct inspection, not clean-room work.
See [[03_Reverse_Engineering/findings/FIND-0006-native-rnc2]].

Installed CMake4.3.0 documentation was inspected via
`cmake --help-manual cmake-presets.7` on 2026-10-02: schema version6 is supported
from CMake3.25. Configure/build/CTest behavior was verified on the installed
version, not on every supported older release. No new third-party source was
copied or downloaded during this pass.

Session 2026-10-02-004 reused the installed rasm2 5.9.8 Capstone5 and GNU backends,
plus the previously consulted Motorola architecture references, for bounded
original-68000 field/CFG checks. Exact commands, version output and warnings are
captured in `local/generated/rnc-loader/run-s3737ul_/decoder-evidence.json`.
No new third-party code was imported.

Hardware-document investigation on 2026-10-02 used these **leads only**:

- [Sega Genesis Software Manual scan](https://segaretro.org/images/9/95/GenesisSoftwareManual.pdf):
  indexed Sega-manual excerpt identifies VDP area/data/control port addresses;
  full fetch returned 403. It was not used to claim pixel/color layout.
- [Another mirror of the Sega manual](https://nemesis.hacking-cult.org/MegaDrive/Documentation/GenesisSoftwareManual.pdf):
  web fetch timed out; local curl rejected a TLS hostname mismatch. No bypass.
- [Manual scan mirror landing page](https://manuals.plus/m/92e0b832b1f54ba17c6f0fc2d04f90285e1c2d4f50ab3e0acd4d9e4999285355):
  page identifies a 183-page scan. PDF exceeded web tool size limits and local
  download returned 403. No complete manual was obtained, copied into Git or
  treated as a checked pixel-format specification.

The new resource layout is derived from this ROM's consumers and checked output,
not from online claims about Wiz 'N' Liz. Remaining pixel/color validation is
explicit in [[07_Tasks/TASK-0005-native-pattern-bank]].


## Pattern-bank pass, accessed 2026-10-02

- [MAME VDP source at the inspected revision](https://github.com/mamedev/mame/blob/309bec2b8fe5279d461960a7935cc540203307c2/src/devices/video/315_5313.cpp):
  `md_debug_8x8_layout`, `write_cram_value`, `draw_tile`, sprite pixel checks.
  Corroborates normal pattern representation, CRAM channel masks and index-zero
  transparency. Does not establish this game's runtime register state.
- [MAME generic graphics decoder](https://github.com/mamedev/mame/blob/309bec2b8fe5279d461960a7935cc540203307c2/src/emu/drawgfx.cpp):
  `readbit` and `gfx_element::decode` establish plane weights and bit numbering.
  Combined with the VDP's word storage, this explains the byte ordering used
  in our independently authored reference model.
- [MAME palette implementation](https://github.com/mamedev/mame/blob/309bec2b8fe5279d461960a7935cc540203307c2/src/devices/video/315_5124.cpp):
  `sega315_5313_palette` gives channel positions and nonlinear brightness levels.
  We deliberately use a documented rounded RGB3 diagnostic scale, so do not
  claim brightness equality to this reference.
- [Netpbm PAM specification](https://netpbm.sourceforge.net/doc/pam.html):
  RGB_ALPHA header, row/tuple order, sample extent and opacity semantics.
- [W3C PNG Third Edition, 2025-06-24](https://www.w3.org/TR/2025/REC-png-3-20250624/):
  truecolor-alpha type6, byte serialization, filter0 and IHDR/IDAT/IEND framing.
  PNG raster and CRC validation uses independent Python standard-library decoding.

Revision came from `git ls-remote https://github.com/mamedev/mame.git HEAD`, then
all source URLs used the resolved immutable commit. Full SHA-256s, source paths,
local location and license scope are in `third_party/vdp_reference.lock.json`.
Inspected C++ files declare BSD-3-Clause; the repository-wide COPYING explains
MAME's broader GPL terms. The local BSD license text is also pinned. No MAME
implementation was copied into the native runtime, compiled, or executed.
Reference source inspection informed our project-authored model; not clean-room.

To refetch any pinned source, use its recorded path with:

```sh
curl --fail --location --max-time 20 \
  https://raw.githubusercontent.com/mamedev/mame/309bec2b8fe5279d461960a7935cc540203307c2/src/devices/video/315_5313.cpp \
  --output local/tools/docs/mame-vdp/315_5313.cpp
```

Compare its digest to the lock. Normal build/test/atlas commands never fetch it.
A further Sega-manual mirror at
[Fabien Sanglard's site](https://fabiensanglard.net/another_world_polygons_Genesis/GenesisSoftwareManual.pdf)
returned403 both through web access and local curl; it remains an unused lead.
An attempted GitHub API request stalled and was terminated; `git ls-remote` plus
pinned raw downloads succeeded. No certificate verification was bypassed.


## Companion scene pass, accessed 2026-10-02

Reused the pinned, locally hash-recorded MAME VDP source:
[get_nametable and draw_tile](https://github.com/mamedev/mame/blob/309bec2b8fe5279d461960a7935cc540203307c2/src/devices/video/315_5313.cpp).
These functions specify normal-mode pattern index, H/V flip, palette and priority
bit fields. They inform the independent specification model; MAME was not built
or executed. The previously documented diagnostic color policy remains unchanged.
No new external source or package was copied/downloaded this pass.

Installed rasm2 5.9.8 Capstone5/original 68000 and restricted GNU corroborations
were actually run; commands/version/warnings are in
`local/generated/scene-probe/run-yr2s7pku/decoder-evidence.json`. Existing Motorola
references support width, ADD/OR, DIVU, indexing and DBF interpretation. ScummVM
reference pin remains unchanged and actually compared both cataloged blocks.
All new ROM resource identities and code/range claims derive from local bytes,
not from web descriptions. See [[03_Reverse_Engineering/findings/FIND-0009-companion-scene]].

## Terrain execution pass, accessed 2026-10-02

[Musashi source at revision 313ebf1bd9f4d0d93341eb5ce21fd8a119e9dbdd](https://github.com/kstenerud/Musashi/tree/313ebf1bd9f4d0d93341eb5ce21fd8a119e9dbdd)
was inspected locally: `readme.txt`, `m68k.h`, `m68kconf.h`, generator, CPU and
build sources. Its MIT notice and the bundled SoftFloat Release2b custom notice
are retained unchanged under ignored `local/tools/terrain-reference/upstream/`.
Individual source/license lengths and SHA-256s are pinned in
`third_party/terrain_reference.lock.json`, linked by the main manifest. No
third-party CPU implementation is copied into tracked native source.

The project-owned `re/reference_scripts/terrain_reference.c` harness is compiled
separately with Clang ASan/UBSan, explicit M68000 selection, later CPUs disabled
and instruction hook enabled. It executes the local original ROM routines under
restricted fixture memory; a complete Genesis system is not implemented. Native
C++ has no emulator link or runtime dependency. Builder/harness/source/executable
provenance lives in `local/tools/terrain-reference/build.json`; comparison reports
record it with exact initial cases and outputs. Static disassembly reuses the
installed original-68000 and restricted GNU backends. Every game-specific
behavior claim comes from local ROM bytes and executed cases, not web descriptions.

## Engine analysis, accessed 2026-10-05

- [godot-cpp README on `master`](https://github.com/godotengine/godot-cpp/blob/master/README.md):
  versioning independent of Godot from v10, `api_version` targeting of Godot
  4.3 or later, forward-compatibility rule across minor versions, SCons build
  examples. A `4.7` branch and `cmake/README.md` returned 404; CMake support,
  minimum C++ standard and license were not confirmed from this page. Nothing
  was downloaded, copied or built.
- Historical (2026-10-05 only): the user's separate `~/WL3PC` repository
  supplied the comparison figures in the now rejected
  [[06_Decisions/ADR-0001-presentation-shell]]. It is out of scope since
  2026-10-23 ([[02_Workflow/PROJECT_BOUNDARIES]]) and is not a source.
