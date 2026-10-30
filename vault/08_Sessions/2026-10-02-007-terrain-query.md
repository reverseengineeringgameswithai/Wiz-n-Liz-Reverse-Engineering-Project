---
id: SESSION-20261002-007
type: session
status: complete
task: TASK-0007
---
# Terrain semantics to independently executed native behavior

## Objective and initial state

Continue the recommended [[07_Tasks/TASK-0007-terrain-query]], expanding its
bounded scope to three direct contact callers and the original one-pixel
settling routine. Read actual entry points, canonical workflow/brief/Git rules,
current handoff, task, related findings and source. Cwd and actual root were
`~/WizNLizPC`. Started at `cc22e096b2525b83cdcaa88b52e87d3f24b3c3c8`,
clean branch `work/companion-scene`, empty index, no pre-existing changes or Git
operation in progress. Created local branch `work/terrain-query`.

Original ROM stayed immutable and local. Repository identity was already
configured. No privileged/package/global setting changes, push or publication.
The only new external source is a pinned local Musashi research dependency.
Checkpoint subject: `Reconstruct terrain contact and settling with original CPU comparisons`.

## Delivered

- Validated map-query entry `0x99D4` and record query `0x9A18`, plus three probes
  and settling. Promoted six function mappings and seven hashed code ranges
  (one duplicate contact fragment stays static-only). Ten verified calls,
  original68000 decode/CFG and 12 independent GNU corroborations.
- Implemented native `wiz_sim`: logical map/record lookup, persistent scratch,
  word wrap, signed row-address aliasing, horizontal record reversal with vertical
  bit ignored, byte-level NZVC contact tests, and one-pixel downward settling.
  Native CLI reads extracted scene/bank resources; no ROM/CPU runtime.
- Added explicit pinned Musashi builder and restricted research harness. Original
  code executes on constructed state with bounded reads/writes/code/stack and
  instruction limits. ASan/UBSan is mandatory; source/build provenance is checked.
- Added `terrain-probe` / `terrain-compare`, authored fixtures/goldens, semantic
  and malformed tests, actual-map cases and cross-preset result checks.

Canonical evidence: [[03_Reverse_Engineering/findings/FIND-0010-terrain-query]].
Updated formats/control flow/memory map, architecture/porting/coverage, validation,
reproduction/environment/source notes, status/blockers/tasks and README.

## Executed verification

**101 Python tests PASS, zero skips. 8/8 CTest targets PASS in each of debug,
release and Clang ASan/UBSan.** All 614,436 terrain comparison cases pass in each
preset: 110,610 authored cases at each of two bases plus 393,216 real-resource
cases. The latter includes every 262,144 map pixel position and 131,072 contact/
settling cases. All 86 instruction addresses in six routines are executed.
Eighteen hand-worked golden cases independently check reference observations.
Three out-of-map address cases fail explicitly in the reference and native tests.

Output hashes agree across all presets, including release invoked from `/tmp`.
51/51 codec comparisons pass. Static probe and expanded sega2asm dry-run pass.
The native scene retains its existing checked PNG hash. Original ROM remains
1,048,576 bytes with SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.

Exact commands, statuses, durations and logs:
`local/logs/terrain-query/commands.json`; cross-preset summary `reproduction.json`.
Final terrain reports: `local/generated/terrain-comparison/run-epwn49js/`
(debug), `run-jurt6_en/` (release), `run-mffjajzg/` (sanitizer), each `report.json`.
Static evidence: `local/generated/terrain-probe/run-8yloy3nw/`.
Codec: `local/generated/rnc-comparison/run-rcksapc6/report.json`.
Scene: `local/generated/scene-preview/run-vh4uxbox/report.json`.
Full result/limitations record: [[05_Validation/RESULTS]].

## Reproduce

```sh
python3 tools/build_terrain_reference.py --download
python3 tools/project.py configure --preset debug
python3 tools/project.py build --preset debug
python3 tools/project.py terrain-probe --disassemble
python3 tools/project.py terrain-compare --rom --preset debug
python3 tools/project.py configure --preset release
python3 tools/project.py build --preset release
ctest --preset release
python3 tools/project.py terrain-compare --rom --preset release
python3 tools/project.py configure --preset sanitize
python3 tools/project.py build --preset sanitize
python3 tools/project.py test --rom --preset sanitize
python3 tools/project.py terrain-compare --rom --preset sanitize
python3 tools/project.py reference-test --rom --preset sanitize
python3 tools/project.py scene-preview
python3 tools/project.py split --dry-run
python3 tools/project.py check-vault
python3 tools/project.py check-hygiene
```

Both cataloged resources must already be extracted; see README. Omit reference
`--download` when sources exist. The current dependency build reused inspected
verified files from `local/tools/musashi-src/` into the pinned upstream directory;
it did not modify upstream sources. The explicit download recipe is available
for reproduction; normal builds/tests do not download or run the CPU reference.
GCC16.1.1 native debug/release and Clang22.1.7 sanitizer/ref tested on Fedora44
x86_64; CMake4.3.0, Ninja1.13.2, Python3.14.6, rasm2 5.9.8.

## Failed approaches and limits

Discovery disassembly had truncated slices/misaligned starts, retained only as
local research. Final probes require exact reviewed boundaries and closed branch
edges. One initial authored hand calculation wrongly considered y `0x807F` a
valid last row; original execution rejected undeclared RAM because ADDA.W uses
signed low16 row displacement. It is now an explicit negative case; the native
algorithm was already rejecting it. No successful output golden was rewritten
to conceal a mismatch, and no unresolved final test failure remains.

The first bounded M2 native-behavior checkpoint is reached; **native playability
is none**. Musashi is optional research only, with no native runtime linkage.
Constructed function states are not captured full-game states. Full register ABI,
cycle/prefetch/device timing, reset-to-game reachability, complete player/actor
controller, input, SDL3 rendering/audio, audio-driver execution, saves/mods and
gameplay replay remain unperformed. Native resource bounds intentionally reject
out-of-resource RAM reads; original relocation-index overflow is excluded from
the logical-resource contract.

## Exact next task and checkpoint

[[07_Tasks/TASK-0008-movement-step]]: establish A5/A6 ownership and the original
horizontal-step/collision-response chain around `0x9AAE/0x9AC8/0x9B04`. Resolve
all side effects/exits and original step-count arithmetic, compare bounded state
transitions using the now-working CPU harness, then implement explicit native
state/events. Do not replace the real movement logic with an invented platformer.

Only explicitly reviewed owned source/tests/metadata/notes enter the checkpoint.
No user work needed preservation beyond the immutable ROM; generated assets,
trace-like outputs and third-party sources stay ignored. No persistent service
or emulator process was started. Git and Obsidian describe the same milestone.

Final checkpoint review: vault validation passes all 45 notes; staged hygiene
passes 129 indexed files. Explicit source/test/metadata/note review and both
whitespace checks pass. No protected ROM, derived bulk content, build or
third-party implementation is staged. ROM identity remains unchanged.
