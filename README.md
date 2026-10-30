# WizNLizPC

> [!WARNING]
> **Disclaimer:** Every step of this project was done with AI. Some things may
> be inaccurate or false.

Local reverse engineering and incremental native reconstruction of Wiz 'N' Liz.
**No playable native game exists yet.** Working components include protected ROM
inspection, static reset analysis, conservative sega2asm integration, and a
bounded C++20 RNC2 resource codec mapped to original decoder `0x19462`, and
native graphics-bank and companion-scene loaders. A 1024x256 terrain map plane
composes from verified original resources. Native terrain queries, three contact
probes, one-pixel settling, horizontal movement, damping, signed speed limits,
airborne motion and bounded landing transitions now match independently executed
original 68000 routines. A complete controller and original display behavior
remain unverified.

Read [START_HERE.md](START_HERE.md). Open `vault/` in Obsidian; begin with
[project status](vault/01_Project/PROJECT_STATUS.md) and
[next actions](vault/01_Project/NEXT_ACTIONS.md).

Build and test the headless native asset/simulation components on the audited Fedora44 host:

```sh
python3 tools/project.py configure --preset debug
python3 tools/project.py build --preset debug
python3 tools/project.py test --preset debug
```

Presets: `debug`, `release` (default system C++ compiler), and `sanitize`
(Clang ASan/UBSan). The project wrapper selects its Python interpreter for CTest.
CMake 3.25+, Ninja, a C++20 compiler and Python3 are required. No SDL dependency
is needed for these headless components. Normal commands never download tools or install packages.
Targets include `wiz_rnc2`, `wiz_assets`, `wiz_sim`, `wiznliz-rnc2`, `wiznliz-bank-atlas`, `wiznliz-scene-preview`, `wiznliz-terrain`, `wiznliz-movement`, `wiznliz-airborne`
and their tests; there is no game executable.

Local extraction and optional independent comparison:

```sh
python3 tools/project.py rom-identify --verify
python3 tools/project.py rnc-validate --decode --preset debug
# Only for independent comparison; explicit bootstrap is documented in the vault:
python3 tools/build_rnc_reference.py
python3 tools/project.py reference-test --rom --preset debug
python3 tools/project.py rnc-validate --decode --backend reference
```

`rnc-validate --decode` defaults to the project codec. Build provenance, ROM
identity, exact consumption, sizes, CRCs and the recorded decoded hash must
match before atomic publication. Output remains under ignored `local/`, using
logical ID `rnc.unclassified.0001`. The GPL reference is a separate research
process; it is not linked into the native component. `reference-test` compares
49 authored cases and, with `--rom`, both cataloged blocks. It tests codecs,
not gameplay or original CPU execution.

The original caller/consumer investigation is reproducible with:

```sh
python3 tools/project.py rnc-loader-probe --disassemble \
  --decoded-bank local/extracted_assets/rnc/rnc.unclassified.0001.bin
```

This verifies the static path and a bank of 442 patterns plus opaque records,
not a running scene. `--disassemble` requires installed `rasm2`.

Generate the native inspection atlas after extraction:

```sh
python3 tools/project.py bank-atlas --bank rnc.unclassified.0001 --columns 32
```

This validates the extracted blob by logical ID and produces a 256x112 PNG/PAM
under `local/generated/bank-atlas/run-*/`, with process/provenance/hash reports.
C++ parses the bank and supplies every RGBA pixel; Python checks the pixels
against a separate bitplane specification model and packages the PNG. This
command needs no raw ROM or emulator after extraction. Color scaling is an
explicit diagnostic policy; preserved records now have verified terrain contact use.
The companion resource is now reconstructed through consumer `0x3E14`:

```sh
python3 tools/project.py rnc-validate --block scene.companion.0001 --decode
python3 tools/project.py scene-probe --disassemble \
  --decoded-scene local/extracted_assets/rnc/scene.companion.0001.bin
python3 tools/project.py scene-preview --scene scene.companion.0001
```

This produces a checked 1024x256 native map plane under
`local/generated/scene-preview/run-*/`, combining 442 base and 136 additional
patterns with 4096 map words and H/V flips. The original resources determine the
layout; no original CPU stream runs in scene composition. Coordinates and records
remain available, but a camera/controller/full-game simulation is still pending.

The first headless simulation component is independently verified:

```sh
# Explicit research bootstrap only; omit --download once pinned sources exist.
python3 tools/build_terrain_reference.py --download
python3 tools/project.py terrain-probe --disassemble
python3 tools/project.py terrain-compare --rom --preset debug
```

`terrain-compare` executes six original routines in a separate pinned Musashi
process and compares 614,436 cases with native semantic outputs/state/NZVC.
It always requires the original routine ROM; `--rom` adds the actual resource
corpus to authored fixtures. Both resources must already be extracted. All
debug/release/Clang ASan+UBSan results agree, including every pixel position of
the terrain plane. Original word wrap, horizontal record reversal, ignored
vertical flip, contact flags and above-map scratch preservation are covered.

`wiz_sim` and `wiznliz-terrain` consume extracted resources and explicit state,
with no raw ROM or emulator dependency. Musashi is research-only and is never
linked or launched by a normal build/test. This is function-level evidence,
not a complete Genesis or playable game. Next is resolving grounded/idle continuations; see the current Obsidian handoff.

Horizontal movement and its state transition can also be reproduced:

```sh
# Rebuild the local reference after harness changes; existing sources suffice.
python3 tools/build_terrain_reference.py
python3 tools/project.py movement-probe --disassemble
python3 tools/project.py movement-compare --rom --preset debug
```

`movement-compare` adds eight original routine mappings and checks 282,233 cases
per preset, including all speed words for damping/clamps, terrain response and
repeated updates. It preserves the unusual 64,513-step count at speed `0x8000`;
the native API requires an explicit budget for that case. All 74 new instructions
are visited. `MotionUpdate::airborne` records the assigned next handler, now
implemented by the bounded airborne component below. The native transport uses
extracted resources; no CPU interpreter is linked into `wiz_sim`.

Airborne motion and landing now have their own bounded comparison:

```sh
python3 tools/project.py airborne-probe --disassemble
python3 tools/project.py airborne-compare --rom --preset debug
```

All 415,940 cases match original execution per preset, including delayed boost,
gated acceleration, gravity, contact and landing state. Every delay/vertical word
and both landing speed directions are covered. Zero-speed normal landing enters
idle immediately in the original; native exposes that pending same-call work
explicitly. Comparison stops before the same idle instruction, preserving the
return boundary. Full idle/grounded handlers and a game scheduler remain pending;
repeated airborne calls are not frames. `wiznliz-airborne` needs extracted assets,
not a raw ROM or emulator. All 111 Python tests and 12 native targets pass.

Other working interfaces: `doctor`, `rom-identify`, `split`, `reset-probe`,
`test`, `check-vault`, `check-hygiene`. Run command-specific `--help` for options.
Python tools find the repository from their source paths, including from another
working directory. `test` without `--preset` runs Python tests only; `--rom` adds
ROM identity checking. Requested native tests fail if the build is absent or
stale. Optional reference/upstream Python tests report missing tools as skips.

Generic `extract` and game `run` remain unimplemented and exit 2. SDL3-devel,
MAME and Ghidra are absent; see [environment](vault/02_Workflow/ENVIRONMENT.md).
No game profiles, audio, interactive renderer, mod runtime or gameplay replay exists.

The final stack remains C++20, SDL3, CMake and Ninja. Original content stays
local; the ROM's `.md` extension does not make it a Markdown document. No ROM,
extracted proprietary content, bulk disassembly or builds belong in Git.
Third-party provenance is recorded in `third_party/manifest.lock.json`; those
licenses grant no rights to game content. The only publication is the scrubbed
[public mirror](vault/02_Workflow/PUBLIC_MIRROR.md) of committed files.

## License

The project's own code, tools, tests, evidence records and notes are released
under the [MIT License](LICENSE); one optional comparison harness is
GPL-3.0-or-later. Wiz 'N' Liz itself is not covered: no ROM or game content is
included, and you need your own copy. See [NOTICE.md](NOTICE.md) for details
and [CONTRIBUTING.md](CONTRIBUTING.md) before sending changes.
