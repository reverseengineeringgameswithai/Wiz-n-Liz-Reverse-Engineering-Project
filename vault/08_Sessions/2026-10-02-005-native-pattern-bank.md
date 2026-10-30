---
id: SESSION-20261002-005
type: session
status: complete
task: TASK-0005
---
# Structured native graphics-bank checkpoint

## Objective and starting state

Implement [[07_Tasks/TASK-0005-native-pattern-bank]]: bounded C++20 structured
loader, corroborated pixel/color interpretation and deterministic local atlas.
Read the real entry points, status, next actions, session004, task and related
technical notes before edits. Repo root `~/WizNLizPC`; starting branch
`work/rnc-loader`, commit `2d77bfd`. Tree/index clean, no unfinished Git operation
or pre-existing changes. Created `work/native-pattern-bank`. Local author name
and the previously supplied email were already configured; no global changes.
Checkpoint subject: `Load structured graphics banks and render verified native atlases`.

## Work and durable findings

Added `wiz_assets`, `PatternBank`, preserved raw/converted palette and opaque
records, indexed tile decode, bounded atlas construction and native PAM output.
Added `bank-atlas` catalog interface, strict hash/path/provenance/metadata checks,
independent bitplane specification model, deterministic PNG packaging and local
reports. Build provenance schema2 tracks each native executable independently.

Corroborated normal 8x8/channel/transparent-index interpretation from pinned MAME
source, not emulator execution. Explicit diagnostic color policy avoids claiming
analog brightness or original-frame equivalence. The known resource loads as
442 patterns and yields a 256x112 atlas. Opaque records remain uninterpreted.
Current truth: [[03_Reverse_Engineering/findings/FIND-0008-native-pattern-bank]],
[[03_Reverse_Engineering/ASSET_FORMATS]], [[04_Native_Implementation/PORTING_MAP]],
[[04_Native_Implementation/ARCHITECTURE]], [[03_Reverse_Engineering/COVERAGE]].

Files/interfaces: `src/assets/pattern_bank.*`, `tools/native/pattern_bank_main.cpp`,
`tools/bank_atlas.py`, `tools/bank_reference.py`, CMake targets, native build record,
project dispatch, synthetic native/Python tests, `re/rnc_blocks.json`, reference
lock/main manifest, README and canonical vault notes. The static loader probe
now explicitly reports that it does not itself check pixel interpretation.

## Verification and evidence

91 Python tests pass, zero skips; 4/4 CTest targets pass in debug, release and
Clang ASan/UBSan. 50/50 codec comparison cases pass. Extraction and bounded static
loader/disassembly probe pass. Every real-bank pixel matches the separate
bitplane/palette model. All four atlas runs (three presets plus `/tmp` repeat)
have identical PNG bytes. Image opened locally; no level name asserted.
Original ROM retains its 1,048,576-byte size and SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.

Exact commands/status: `local/logs/pattern-bank/commands.json`; images/reports:
`local/logs/pattern-bank/atlas-reproduction.json`. Debug artifact:
`local/generated/bank-atlas/run-8ushhgd8/atlas.png`, SHA-256
`988b4d3eb88dfaf59bcdcde7fd7216a96870f9704fb5f10e05e882e24f5d71e6`.
Detailed results and unperformed layers: [[05_Validation/RESULTS]].
Vault check passes all 39 notes; staged hygiene passes 99 indexed files.
Whitespace and explicit staged code/metadata review pass; no protected content
or pre-existing user changes enter the checkpoint.

## Reproduce

```sh
python3 tools/project.py configure --preset debug
python3 tools/project.py build --preset debug
python3 tools/project.py rnc-validate --decode
python3 tools/project.py bank-atlas --bank rnc.unclassified.0001 --columns 32
python3 tools/project.py configure --preset release
python3 tools/project.py build --preset release
ctest --preset release
python3 tools/project.py configure --preset sanitize
python3 tools/project.py build --preset sanitize
python3 tools/project.py test --rom --preset sanitize
python3 tools/project.py bank-atlas --preset sanitize
python3 tools/project.py reference-test --rom
python3 tools/project.py rnc-loader-probe --disassemble \
  --decoded-bank local/extracted_assets/rnc/rnc.unclassified.0001.bin
python3 tools/project.py check-vault
python3 tools/project.py check-hygiene
git diff --check
```

No command silently downloads tools or alters packages. The atlas command alone
works from the verified extracted resource without the raw ROM. Optional RNC
comparison requires the previously built pinned reference. Source-reference
hashes and download recipe: [[09_References/SOURCES]].

## Failed approaches, limits and next task

Another manual PDF mirror returned 403. GitHub API resolution stalled; terminated
that owned process and used successful `git ls-remote` plus pinned raw downloads.
These failures did not block implementation; no TLS bypass. No temporary server
or emulator was started. No failing implementation test or changed golden was
hidden; executed final tests all pass.

Native playability remains none. No SDL3 app, gameplay, audio sequencer, mod
runtime or emulated sound driver exists. The independent codec remains optional
research; MAME is source evidence only. SDL3-devel and dynamic reference execution
remain outstanding. Full palette-update behavior, scene selection, companion
format and collision meaning remain unknown; diagnostic colors are not analog
fidelity. Synthetic larger imports do not establish enhanced game capacity.

Next: [[07_Tasks/TASK-0006-companion-scene-resource]]: trace A1 selection and
`0x3E14`, validate one source/structure, then implement its first verified native
placement/map parser. Resolve scene composition before movement/collision and
independent gameplay comparisons. Git/Obsidian checkpoint has no identity blocker;
only reviewed owned paths are committed, no protected assets or outputs.
