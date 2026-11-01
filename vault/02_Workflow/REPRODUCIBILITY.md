---
id: WORKFLOW-REPRODUCIBILITY
type: workflow
status: active
---
# Reproducibility and metadata authority

Run commands in repository root unless an example explicitly changes directory.
`tools/project.py` locates that root from its own resolved file path; shell
quoting is still required if paths contain spaces. No Python packages or venv
are needed for current project tools.

| Knowledge | Authoritative tracked record | Generated / local outputs |
| --- | --- | --- |
| Supported input identity | `re/rom_manifest.json` | `rom-identify --verify` JSON stdout |
| Segmentation | `re/sega2asm/segments.json` | per-run `config.yaml` under `local/generated/sega2asm/` |
| Symbols | `re/symbols.csv` | per-run `symbols.txt` |
| Function-entry/boundary status | `re/functions.csv` | technical annotations; unknown ends stay empty |
| RNC block identity/extraction expectations | `re/rnc_blocks.json` | `local/extracted_assets/rnc/` and per-run validation reports |
| Native codec build inputs | `CMakeLists.txt`, `CMakePresets.json`, `src/core/`, `tools/native/` | `build/PRESET/` binaries, provenance and CTest logs |
| Original RNC2 loader/caller analysis | `re/rnc_loader.json` plus FIND-0007 | `local/generated/rnc-loader/run-*/` static report, CFG and decoder evidence |
| RNC research reference pin | `third_party/rnc_reference.lock.json` | isolated source/build under `local/tools/rnc-reference/` |
| Tool source/build identity | `third_party/manifest.lock.json` | local tools, caches and build logs |
| Current interpretation | canonical vault technical notes | historical session notes link evidence |
| Static reset arithmetic/consumers | `tools/reset_probe.py` plus FIND-0001 | `local/generated/reset/report.json` |

Metadata paths and symbols are not permanent native asset IDs. None of the
generated assembly should be manually edited as the only record of a discovery.
Header disassembly is annotation, not proven byte-preserving reassembly.

## Commands and exit meanings

```sh
python3 tools/project.py doctor
python3 tools/project.py doctor --require-native
python3 tools/project.py rom-identify --verify
python3 tools/project.py test --rom
python3 tools/project.py reset-probe --disassemble
python3 tools/project.py split --dry-run
python3 tools/project.py split
python3 tools/project.py configure --preset debug
python3 tools/project.py build --preset debug
python3 tools/project.py test --preset debug
python3 tools/project.py rnc-validate --decode
python3 tools/project.py reference-test --rom --preset debug
python3 tools/project.py check-vault
python3 tools/project.py check-hygiene
git diff --check
git diff --cached --check
```

Doctor exits 0 for a completed audit even if optional tools are absent;
`--require-native` exits 1 for unavailable native prerequisites. Inspector,
test/check commands exit 1 on validation failure. CLI syntax and reserved
unimplemented interfaces return 2; reset/split tools also use 2 for their own
failure, with a diagnostic/report. Split records `complete`, `tool_failure` or
`partial_extraction`; an upstream zero exit alone is insufficient. Missing local
ROM input is failure for requested ROM checks, never an implied pass.

Synthetic tests use original authored data. Two optional regression probes run
the pinned sega2asm on synthetic bytes; they skip explicitly if that executable
is absent. `test --rom` verifies the original identity; it does not automatically
claim reset execution, extraction correctness or gameplay equivalence.

## Vault schema

All actual notes require flat YAML frontmatter with nonempty `id`, `type` and
`status`. Use scalar strings, `null`, or JSON-style arrays, not multiline YAML
objects. Tasks additionally require `deliverable` and a nonempty `acceptance`
string array. Findings require `rom_id`, `address_space`, `confidence`, and a
`task` stable ID; the body must explicitly link that task. Confidence vocabulary
is confirmed/probable/hypothesis/unknown/rejected. Task filenames start with their
stable ID and a hyphen. Duplicate IDs, unresolved links/anchors, missing fields
and inconsistent task references fail the checker.

Fenced and inline code examples are excluded from link scanning. Use explicit
vault-relative note links; source-file paths outside the vault stay in code
format. Future templates must themselves be valid notes and put placeholder
frontmatter/links in code fences. Personal hidden Obsidian data is excluded.

`check-hygiene` verifies root, ignore samples, actual indexed paths and indexed
file contents. It rejects protected paths, the original ROM digest under any
name, and files above a 2 MiB review threshold. It is an aid to explicit staged
review, not proof that every small derived artifact is safe to track.


RNC reference bootstrap is explicit: `python3 tools/build_rnc_reference.py`
uses verified local sources; add `--download` only to fetch absent pinned source
and license files. `rnc-validate` never builds/downloads. The `--decode` form
defaults to the project-native executable and verifies its provenance before extraction.
Choose `--backend reference` explicitly for the GPL research process.
ROM-free tests now include optional Go RNC probes and six sanitized reference
checks; absence is a reported skip, while stale/different provenance fails.
`tools/rnc_upstream_probe.py` intentionally exits 2 for the pinned broken decoder.

Native configure/build commands use fixed CMake presets without network access.
`debug` and `release` use the host compiler; `sanitize` selects installed Clang.
`tools/native_build.py` records source and executable hashes; extraction rejects
stale/modified artifacts and symlinked build roots. Rebuild after source edits.
CMake-only builds work for headless tests, but the extraction wrapper requires
`project.py build --preset NAME` to record current provenance. `test --preset`
runs CTest in addition to Python tests; without it, native testing is unrequested.

`reference-test [--rom] --preset NAME` currently compares the RNC2 codec only:
49 authored cases, plus all cataloged ROM blocks (currently two) when requested.
It requires the independently pinned reference and records both subprocesses,
byte/CRC/extent comparisons and final ROM identity beneath
`local/generated/rnc-comparison/`. No original CPU executes. Reserved game
`run` and generic `extract` continue to fail explicitly with exit 2.

`rnc-loader-probe --disassemble --decoded-bank PATH` validates the exact
cataloged resource consumer and original decoder range. The decoded input must
match the independently recorded length/CRC/hash. All output stays under
`local/generated/rnc-loader/`; original ROM identity is checked before and after.
Without `--disassemble`, optional disassembly is explicitly unrequested; without
`--decoded-bank`, no layout check is claimed. `rasm2` is required when requested.
This command executes static analysis and decoder tools, never original CPU code.


`bank-atlas --bank ID --columns 32 --preset debug` resolves a cataloged extracted
pattern bank, validates its digest and the selected native executable, then
emits diagnostic PNG/PAM beneath ignored `local/generated/bank-atlas/run-*/`.
No ROM read or network access is required after extraction. CLI errors fail;
native subprocess failures have a recorded exit status and no success claim.
The C++ CLI accepts `logical-id bank.bin columns` and writes PAM to stdout,
JSON metadata to stderr. Python packages its raster without altering pixels.

Build provenance schema2 records a hash for each of `wiznliz-rnc2` and
`wiznliz-bank-atlas`; schema1 builds require a normal rebuild. Source hashing
includes `src/assets/` through the existing recursive native source scan.
The pattern format remains authoritative in `re/rnc_blocks.json`, source-derived
reference provenance in `third_party/vdp_reference.lock.json`, and current
semantics in [[03_Reverse_Engineering/findings/FIND-0008-native-pattern-bank]].
The older static loader probe now reports `pixel_interpretation_checked: false`
so it does not misrepresent its own structural-only checks as image validation.


`scene-probe --disassemble --decoded-scene PATH` reproduces companion selection,
consumer/stride fields, 16 GNU corroborations and cataloged decoded structure.
Identity is checked before/after; unknown regions stay unknown. Its metadata
is `re/scene_loader.json`, and function/symbol authority remains the CSV files.

`scene-preview --scene scene.companion.0001 --preset debug` requires both
cataloged extracted resources and a verified `wiznliz-scene-preview` build. It
reads no raw ROM, generates every pixel in C++, checks the full plane against an
independent source-derived model, and writes local PNG/PAM/report artifacts.
Build provenance schema2 now includes three executable hashes. Missing/new
executables require a normal project build. Normal commands remain offline.

## Original terrain execution and native simulation

`re/terrain_query.json` pins seven code ranges and ten reviewed calls. Native
mapping authority remains the function/symbol CSVs. `terrain-probe --disassemble`
records exact commands, CPU sentinel, branch closure and independent GNU checks.
`src/sim/terrain.*` and `wiznliz-terrain` are normal CMake targets; provenance
schema2 hashes the terrain executable alongside the asset transports. Rebuild existing presets after this
change. Normal native builds remain offline and have no CPU-emulator dependency.

The separate `third_party/terrain_reference.lock.json` pins Musashi revision,
source/license file hashes and harness configuration. Explicit local bootstrap:

```sh
python3 tools/build_terrain_reference.py --download
python3 tools/project.py terrain-probe --disassemble
python3 tools/project.py terrain-compare --rom --preset debug
```

Omit `--download` for existing sources. Source/harness/builder/lock/executable
changes invalidate the reference build. `terrain-compare` always uses original
routine ROM; `--rom` additionally uses cataloged scene/bank resources. Every run
checks immutable input identity before/after, stores exact fixture inputs,
reference/native outputs and process/source hashes under ignored local storage,
and reports mismatches/failures without publishing success. Reference read
regions, allowed writes, return sentinel, instruction limits and timeout are
explicit. All outputs remain local. No complete Genesis or frame timing model
is supplied. See [[03_Reverse_Engineering/findings/FIND-0010-terrain-query]].

## Actor movement execution

`re/movement_step.json` adds exact motion and ownership-context range hashes,
transfers and state-field documentation. `movement-probe --disassemble` checks
this scope plus the terrain call graph. `movement-compare --rom --preset NAME`
requires the existing extracted resources, original routine ROM, verified native
`wiznliz-movement`, and updated isolated reference built by:

```sh
python3 tools/build_terrain_reference.py
python3 tools/project.py build --preset debug
python3 tools/project.py movement-probe --disassemble
python3 tools/project.py movement-compare --rom --preset debug
```

No new download is needed on this host. The changed harness/lock requires its
normal explicit rebuild. Native provenance schema2 includes the movement executable
hash; rebuild old presets. Movement corpus/reports remain under ignored
`local/generated/movement-comparison/`, including inputs, process outputs,
source/build identities, original instruction visits and rejected-input checks.
The optional `--rom` adds actual terrain states; original code ROM is always
required. All normal native tests remain ROM-free and CPU-reference-free.
See [[03_Reverse_Engineering/findings/FIND-0011-movement-step]].

## Airborne and landing execution

`re/airborne_update.json` pins eleven new code fragments and two exact immediate
continuation boundaries. The function/symbol CSVs retain empty full ends for
shared-tail, noncontiguous and bounded handler paths. `airborne-probe
--disassemble` verifies hashes/transfers, CPU selection and graph closure with
only those declared boundary exits. `airborne-compare --rom --preset NAME`
compares all state/counter/continuation outputs using the restricted original
reference's `--airborne` transport.

```sh
python3 tools/build_terrain_reference.py
python3 tools/project.py build --preset debug
python3 tools/project.py airborne-probe --disassemble
python3 tools/project.py airborne-compare --rom --preset debug
```

The reference rebuild uses existing pinned local source; no download is needed
on this host. Native schema2 provenance now hashes six executables, including
`wiznliz-airborne`. Original comparison always requires the verified routine ROM;
`--rom` adds cataloged extracted terrain. Normal native builds/tests are offline,
ROM-free and CPU-reference-free. Inputs, outputs, process statuses, source/build
hashes and boundary coverage remain under ignored
`local/generated/airborne-comparison/`. Repeated calls stop
visibly at unimplemented grounded identities and are not game frames.

## Local storage

Comparison and capture commands write a new `run-*` directory each time, and
reruns of a deterministic capture or corpus are byte-identical. Tracked notes
and evidence cite many runs by path, so runs are not deleted to save space.
Instead, identical files share storage:

```sh
python3 tools/dedupe_local.py           # report only
python3 tools/dedupe_local.py --apply   # share extents of identical files
```

On btrfs the kernel's FIDEDUPERANGE ioctl compares both ranges itself and then
shares extents copy-on-write. Every path, inode, permission and content stays
the same and mtimes are checked; nothing is deleted. Files already sharing
their extents are skipped, so a rerun is cheap and a report with no
`reclaimable_bytes` confirms an earlier `--apply`. Run it after passes that add
large captures. `du` still counts every copy; free space (`df`) shows the
saving. Filesystems without extent sharing report each pair as a failure and
change nothing. See [[08_Sessions/2026-11-01-059-local-storage]].

## Independent Genesis capture

`project.py genesis-compare FIXTURE --preset debug` consumes an actual GPGX
routine fixture through the external BizHawkOpenSource consumer, verifies the
existing native build and checks original ROM identity. It never launches an
emulator in native targets. Reset routes, isolated-runtime setup, capture
commands, exact build identities and supported comparison boundaries are in
[[09_References/GENESIS_DEBUGGER]]. Bulk states, traces, images and PCM stay in
ignored local storage. Regenerate states after emulator binary changes.
