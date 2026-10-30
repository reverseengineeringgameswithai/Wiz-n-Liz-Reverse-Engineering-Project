---
id: SESSION-20261002-008
type: session
status: complete
task: TASK-0008
---
# Horizontal actor movement and original state transitions

## Objective and initial state

Continued the agenda through [[07_Tasks/TASK-0008-movement-step]]. Read actual
entry points, canonical workflow/brief/Git rules, latest handoff, task, related
findings and source. Actual root/cwd: `~/WizNLizPC`. Started at
`41da180b31abfc4469925fc9cd1d2de011cd94c0` on clean `work/terrain-query`, empty
index, no pre-existing changes or Git operation in progress. Created local
branch `work/movement-step`. Repository identity was already configured.

Original ROM stayed immutable. No package/global setting changes, push,
publication, new external download or persistent process this pass. Existing
pinned Musashi reference was rebuilt for the extended restricted harness.
Checkpoint subject:
`Reconstruct actor movement and airborne transitions with original execution checks`.

## Delivered

- Eight native mappings: counted/one-unit damping, horizontal dispatcher,
  left/right terrain response, airborne-state assignment and signed clamps.
  Exact 260-byte executed scope plus 390 bytes of static ownership/caller
  context are pinned in `re/movement_step.json`. Function index now has 23 entries.
- Confirmed the two A5 control/A6 actor bindings and backlinks statically.
  Preserved original position/speed widths, word overflow, body-first DBF count,
  probe ordering and continuation after speed/handler changes. The minimum speed
  word 8000 executes 64,513 steps in the original; native budgeting is explicit.
- Added `src/sim/movement.*` to `wiz_sim`, with semantic state/parameters/events
  and atomic state/scratch update on success. No original CPU/RAM runtime.
  `MotionUpdate::airborne` records the original assignment to `0xAAEA`; the
  handler itself is the next task, not silently executed as a stub.
- Added `wiznliz-movement`, ROM-free authored tests and independent goldens,
  `movement-probe`, `movement-compare`, reference mode and bounded access rules.
  Updated native/reference build provenance and canonical Obsidian handoff.

Evidence: [[03_Reverse_Engineering/findings/FIND-0011-movement-step]].

## Validation and reproduction

Exact argv, cwd, exit statuses, durations and log paths are in
`local/logs/movement-step/commands.json`. Cross-preset hashes are in
`local/logs/movement-step/reproduction.json`. Key commands:

```sh
python3 tools/build_terrain_reference.py
python3 tools/project.py build --preset debug
ctest --preset debug
python3 tools/project.py build --preset release
ctest --preset release
python3 tools/project.py build --preset sanitize
python3 tools/project.py test --rom --preset sanitize
python3 tools/project.py movement-probe --disassemble
python3 tools/project.py movement-compare --rom --preset debug
python3 ~/WizNLizPC/tools/project.py movement-compare --rom --preset release
python3 tools/project.py movement-compare --rom --preset sanitize
python3 tools/project.py terrain-compare --rom --preset sanitize
python3 tools/project.py rom-identify --verify
python3 tools/project.py split --dry-run
python3 tools/project.py check-vault
python3 tools/project.py check-hygiene
git diff --check
git diff --cached --check
```

Release comparison above was invoked from `/tmp`; other commands use repo root.
All **106 Python tests pass, zero skips**, and **10/10 CTest targets pass** in
every preset. Movement original/native comparison is **282,233/282,233 PASS per
preset**; all sixteen output fields and cross-preset output hashes agree.
74/74 new instruction addresses are visited, 149 overall in that corpus.
Shared reference changes retain **614,436/614,436 terrain regression PASS**;
the two corpora together visit all 160 mapped simulation instructions.
Both reference and native sanitizer runs are clean. Out-of-map cases reject.

Static probe verifies 15 range hashes, 55 transfers, 160-instruction combined
closure and ten GNU corroborations. Expanded CSV metadata passes the pinned
sega2asm dry-run. Reports and exact scopes: [[05_Validation/RESULTS]].

Exploratory arbitrary/truncated disassembly windows remain local, not promoted
as complete routines. Review strengthened a transactional-error unit to fail
after one successful pixel. No expected result changed to conceal a mismatch;
no unresolved final test failure. Codec/image differential comparisons were not
repeated; their normal native tests passed and prior results remain recorded.

## Limits and next handoff

**Native playability remains none.** No full controller/physical input mapping,
airborne handler or landing implementation, game frame scheduling, SDL3 app,
audio, mod/save/replay runtime or full Genesis boot exists. Static paired-slot
ownership is established, not captured game reachability. Repeated entry calls
are not frames; full register/CCR ABI and device/cycle effects are excluded.
Presentation field consumers remain untraced. Native budget and transactional
rejection policies are distinguished from original out-of-resource behavior.

Next: [[07_Tasks/TASK-0009-airborne-update]]. Follow assigned handler `0xAAEA`,
continuation `0xAB04`, vertical helper `0x9BAC` and landing lead near `0xAB8A`.
The exploratory `local/generated/movement-research/aa50.txt` is a lead only.
Validate exact ranges and called effects before promoting or extending harness
permissions. Preserve horizontal loop semantics and terrain scratch ordering.

ROM remains 1,048,576 bytes, SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
Generated evidence, original bytes, builds and downloaded reference sources stay
under ignored local paths. Final vault/index/explicit staging review is recorded
in `local/logs/movement-step/checkpoint-review.log`; no unrelated work is included.

Final review passes: **48 vault notes, 142 indexed files**, explicit 34-path
staging and both whitespace checks. Staged source/tests/metadata match the
reviewed working files; no unstaged or untracked owned work remains. The local
checkpoint commits code and synchronized Obsidian together; no push requested.
