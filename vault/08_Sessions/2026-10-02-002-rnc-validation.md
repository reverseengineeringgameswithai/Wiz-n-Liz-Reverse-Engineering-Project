---
id: SESSION-2026-10-02-002
type: session
status: complete
task: TASK-0002
---
# First RNC2 validation and local extraction

## Objective and starting Git state

Task: [[07_Tasks/TASK-0002-rnc-block]]. Validate exactly the first candidate's
extent, packed integrity, bounded reference decode, output integrity and consumed
boundary, or preserve a reproducible failure. Unknown resource meaning stays
visible. The user authorized continued work and supplied the missing Git email.

On turn entry, branch `work/m0-foundation` was unborn with exactly 49 staged
owned foundation files, no unstaged/untracked user changes and no unfinished
operation. Initial index listing SHA-256 was
`1b86f7bdd64ff4af8e6ae0525ba5c3e1efab4f69915f45d331e14854b3438283`.
The root and immutable ROM identity were rechecked. User-supplied name/email
were set repository-locally; the reviewed foundation became commit **acab0f1**,
`Establish protected ROM analysis and reproducible reset findings`.

Started this bounded technical pass from that clean checkpoint on a new local
branch `work/rnc-validation`. No unrelated changes were discarded, hidden or
committed. Intended current commit subject:
`Validate first RNC2 resource with isolated reference decoding`.
Do not embed this commit's future hash in its files.

## Work performed and findings

- Added `tools/rnc.py` bounded header/CRC/output checks and authored tests.
- Added catalog `re/rnc_blocks.json`, authoritative for verified block ranges,
  identities and decode expectations; semantic fields remain null.
- Added `rnc-validate [--decode]` through the project dispatcher. Extraction
  publishes bytes atomically only after identity, CRC, size/hash, reference
  metadata and exact-consumption checks. Existing output survives failures.
- Built pinned ScummVM source under ignored local tools using an original
  C++20 observation harness, mandatory Clang ASan/UBSan and process limits.
  Source/license hashes and build recipe are in a separate linked lock manifest.
- Added a bounded offline Go adapter against unmodified pinned sega2asm to
  reproduce its broken RNC2 behavior, including an authored one-byte fixture.
- Updated canonical findings, format/coverage notes, porting map, environment,
  status, blockers, reproduction instructions and the next native codec task.

FIND-0004 verifies `[0x348B2,0x372F7)` (10,821 bytes including header), packed
CRC `0x3673`, 10,803-byte payload consumption, 17,714-byte output and unpacked
CRC `0xAF73`. Output SHA-256:
`048aec81ffb0e5463029b931c2716e5aaa818539b5f72c078f7a19cc195a9ac7`.
Stable output: `local/extracted_assets/rnc/rnc.unclassified.0001.bin`.

FIND-0005 rejects sega2asm output: 25 bytes/CRC `0xAF60` with no decoder error.
The valid authored literal-A fixture becomes G under that decoder, again
without an error; independent CRC catches the same-length corruption.

The first candidate hypothesis is superseded by scoped validation; the other
133 remain unvalidated. No game CPU ran, no caller/decompressor address is
identified, and no graphics/audio/resource-role conclusion is drawn.

## Verification, failures and limitations

All **63 tests pass, zero skips** on the actual Fedora44 x86_64 host. This includes
24 new tests: 10 parser/output checks, 3 Go probe tests, 6 independent reference
tests and 5 publication checks. Header-only validation and complete reference
decode exit 0. The upstream probe deliberately exits 2 for rejected output.
ROM SHA-256 remains
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.

The real block passes Clang sanitizer execution without diagnostics. Malformed
stream tests intentionally trigger upstream reference invalid access, which
ASan terminates without output; this is containment, not production hardening.
The new native codec task must handle those cases without UB.

Failed GCC sanitizer build: runtime libasan/libubsan packages are absent;
Clang22.1.7 compiler-rt works without installation. Failed build evidence:
`local/tools/rnc-reference/build-6wdgky1_/build.json`. No source patch was needed.
The sega2asm RNC decoder is demonstrably unsuitable and remains unpatched;
the corrected strategy is an independent isolated reference. Simple searches
for the first/next candidate addresses as big-endian absolute longwords found
none, so no caller was inferred from them. Relative/computed references remain
possible and uninvestigated.

No native game/SDL3 target, emulator run, gameplay differential replay, asset-role
identification, audio sequencing, mods, saves or whole-ROM rebuild was performed.
The C++ harness is a GPL research tool, not a reconstructed native game. No
proprietary outputs or third-party decoder implementation enter Git history.
All temporary subprocesses and agent-owned background work ended.

## Exact reproduction commands

```sh
cd ~/WizNLizPC
# Uses existing verified sources; add --download explicitly only if absent:
python3 tools/build_rnc_reference.py
python3 tools/project.py rnc-validate
python3 tools/project.py rnc-validate --decode
python3 tools/rnc_upstream_probe.py  # expected exit 2: rejected_output
python3 tools/project.py test --rom
python3 tools/project.py check-vault
python3 tools/project.py check-hygiene
git diff --check
git diff --cached --check
sha256sum "Original_Game/Wiz 'N' Liz (USA).md"
```

Build downloads never happen implicitly. On a different machine, optional tool
tests report missing dependencies as skips. Source/hash mismatches fail rather
than silently replacing the tool. Reference downloads and licensing are pinned
in `third_party/rnc_reference.lock.json`.

Main evidence: `local/logs/rnc-pass/commands.json`,
`local/logs/rnc-tests-current.log`,
`local/generated/rnc-validation/run-yvge20iw/report.json`,
`local/generated/rnc-reference-initial/{runs,malformed-runs}.json`,
and failed upstream reports linked from FIND-0005. Build provenance:
`local/tools/rnc-reference/build.json`.

## Handoff

Canonical evidence: [[03_Reverse_Engineering/ASSET_FORMATS]],
[[03_Reverse_Engineering/findings/FIND-0004-first-rnc-block]],
[[03_Reverse_Engineering/findings/FIND-0005-rnc-upstream-defect]],
[[03_Reverse_Engineering/COVERAGE]], [[05_Validation/RESULTS]].

Next exactly: [[07_Tasks/TASK-0003-native-rnc2]], bounded C++20 RNC2 asset codec,
headless CMake/Ninja targets and independent reference comparisons. No SDL3 or
new system package is required. Keep the research decoder out of native runtime
code and preserve actual unknown game addresses/resource meaning.

Final review: 35 explicitly staged owned paths, 66 total indexed files and 30
vault notes. Vault, hygiene and staged/unstaged whitespace checks pass. No ROM,
decoded payload, third-party implementation download, generated binary or bulk
trace is indexed. No unstaged or untracked source work remains after explicit
staging. All changes belong to this pass; the foundation commit preserved the
prior owned checkpoint. The local commit uses the subject above, and its final
hash is reported outside this file. No unresolved Git identity issue remains.
