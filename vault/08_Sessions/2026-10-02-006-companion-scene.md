---
id: SESSION-20261002-006
type: session
status: complete
task: TASK-0006
---
# Companion scene to native terrain-map checkpoint

## Objective and initial state

Continue the canonical roadmap through
[[07_Tasks/TASK-0006-companion-scene-resource]]: resolve one companion resource,
verify its structure and implement a bounded native placement/map parser.
Read actual entry points, current status/next actions/session005, task and
related evidence before changes. Cwd/repository root `~/WizNLizPC`.
Started at `df259c2`, clean branch `work/native-pattern-bank`, empty index,
no pre-existing changes or unfinished Git operation. Created `work/companion-scene`.
Local user-supplied Git identity remains configured; no global configuration,
package/system modification, publication or push. Original ROM preserved.
Checkpoint subject: `Reconstruct companion scene resources and native terrain maps`.

## Work and findings

Resolved the conditional descriptor-zero/slot-zero A1 path to PACK `0x48FD4`
and RNC2 `0x48FD8`. Independently decoded 13,700 bytes and established exact
consumer ranges. Added original routine entries at `0x3E14` and `0x3F34`, plus
an explicitly partial map-column reader, with original 68000 decoding and 16 GNU
corroborations. Persistent authorities: `re/scene_loader.json`, `re/rnc_blocks.json`,
`re/functions.csv`, `re/symbols.csv`.

Implemented `SceneResource`, counted coordinates with original word additions,
two state starts, appended patterns/records, structured map cells, narrow map
relocation arithmetic and native single-plane composition. A 1024x256 terrain
map now comes from 442+136 patterns and 4096 actual map words; no invented map or
screenshot input. Coordinates and opaque records retain unknown roles. Priority
is preserved as data; no camera, actors or multi-plane simulation is supplied.

Added `scene-probe`, `scene-preview`, native CLI, independent pixel specification
model and authored C++/Python tests. Reused pattern decoding and checked asset
reads; expanded `reference-test --rom` from singleton to all cataloged blocks.
Native build provenance now records three executables. Canonical truth:
[[03_Reverse_Engineering/findings/FIND-0009-companion-scene]],
[[03_Reverse_Engineering/ASSET_FORMATS]], [[03_Reverse_Engineering/CONTROL_FLOW]],
[[03_Reverse_Engineering/MEMORY_MAP]], [[04_Native_Implementation/PORTING_MAP]],
[[03_Reverse_Engineering/COVERAGE]].

## Tests and local artifacts

**95 Python tests pass, zero skips.** All 6/6 CTest targets pass in debug,
release and Clang ASan/UBSan. 51/51 codec comparisons pass: 49 authored plus 2 real
blocks. Scene probe passes three range hashes, 56 instruction-field checks,
16 GNU corroborations and exact decoded extent. Existing bank atlas digest
remains unchanged; sega2asm dry-run accepts expanded symbols/functions.

Native scene PNG is 1,048,980 bytes, 1024x256, SHA-256
`476cb65271060616db42300cd0efe1880bb1ef64774be9cacd81d491a52bea92`.
All 262,144 pixels match the independent bitplane/row-reversal/palette model.
Debug/release/sanitizer and repeat-from-`/tmp` outputs match byte-for-byte.
Local viewing shows coherent terrain; no named-stage or original-frame claim.

Exact commands/status/logs: `local/logs/companion-scene/commands.json`;
all image reports: `local/logs/companion-scene/reproduction.json`.
Primary artifacts:

- `local/generated/scene-preview/run-g73_3ur2/scene.png` and `report.json`.
- `local/generated/scene-probe/run-yr2s7pku/report.json` and `decoder-evidence.json`.
- `local/generated/rnc-comparison/run-1aaljm3a/report.json`.
- `local/generated/rnc-validation/run-_x_236gr/report.json`.

ROM remains 1,048,576 bytes, SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
[[05_Validation/RESULTS]] separates completed tests from unperformed gameplay,
original CPU, SDL3, audio, mod and replay checks. Sanitizers detected no native
memory/undefined-behavior failures in executed cases.

## Reproduce

```sh
python3 tools/project.py configure --preset debug
python3 tools/project.py build --preset debug
python3 tools/project.py rnc-validate --decode
python3 tools/project.py rnc-validate --block scene.companion.0001 --decode
python3 tools/project.py scene-probe --disassemble \
  --decoded-scene local/extracted_assets/rnc/scene.companion.0001.bin
python3 tools/project.py scene-preview --scene scene.companion.0001
python3 tools/project.py configure --preset release
python3 tools/project.py build --preset release
ctest --preset release
python3 tools/project.py configure --preset sanitize
python3 tools/project.py build --preset sanitize
python3 tools/project.py test --rom --preset sanitize
python3 tools/project.py scene-preview --preset sanitize
python3 tools/project.py reference-test --rom
python3 tools/project.py bank-atlas
python3 tools/project.py split --dry-run
python3 tools/project.py check-vault
python3 tools/project.py check-hygiene
git diff --check
```

Normal commands never download or install. Reference comparison uses the already
pinned local sanitized ScummVM tool. Scene/atlas commands use extracted assets
without needing raw ROM or any emulator process. Libraries/executables are native
C++20; Python packages unchanged native RGBA into PNG and verifies evidence.

## Failed approaches and limitations

Exploratory disassembly slices ending at arbitrary limits produced a truncated
last instruction; a terrain lead starting at `0x99E0` was misaligned. Those dumps
remain local discovery artifacts, not promoted code boundaries. The reproducible
probe uses reviewed entries/ends and rejects invalid/truncated decodes. No failed
implementation test or replacement golden was hidden. No new source download,
package install or temporary server/emulator occurred.

No native playability, movement, collision response, sound sequencing, saves,
mods or original/enhanced game modes yet. The diagnostic palette does not model
analog brightness or fades. Static map composition does not establish runtime
camera/layer behavior or original relocation/VRAM aliasing. Unsupported shapes
and palettes fail explicitly; native host resources remain extensible.

Next: [[07_Tasks/TASK-0007-terrain-query]], following map/record readers near
`0x99F6`/`0x9A18`. Discovery operands reference both known pointers and suggest
per-column record lookup, but callers, byte meaning and vertical behavior still
need validation. Acquire pinned isolated original-routine execution evidence
before claiming equivalence. This is the bridge to native terrain behavior and
actual player movement, not another asset gallery.

Only reviewed owned source/tests/metadata/notes enter Git. No pre-existing dirt
or Git author blocker; generated assets and disassembly remain ignored. No
persistent process was started. Git and Obsidian describe the same checkpoint.

Final checkpoint checks: vault checker passes all 42 notes; staged hygiene passes
113 indexed files with no protected inputs or bulk outputs. Explicit staged
review and whitespace checks pass. Original ROM digest is unchanged.
