---
id: SESSION-20261002-009
type: session
status: complete
task: TASK-0009
---
# Airborne motion and bounded landing continuations

## Initial state and objective

Continued [[07_Tasks/TASK-0009-airborne-update]] after reading actual entry
points, canonical brief/workflow/Git rules, current handoff, task, findings and
source. Actual root/cwd: `~/WizNLizPC`. Started at
`8d489f46bb4fea8668f7f4cfdca982f15755d061` on clean `work/movement-step`, with an
empty index, no pre-existing work or Git operation in progress. Created local
branch `work/airborne-update`. Repository author identity was already configured.

ROM identity was checked before analysis and after validation. No original
changes, external downloads, system/package/global changes, pushes/publication
or persistent services. Rebuilt existing pinned Musashi with the updated
restricted harness; no CPU reference code enters native targets.
Checkpoint subject: `Reconstruct airborne motion and bounded landing continuations`.

## Delivered scope

- Eight native routine mappings for airborne horizontal motion, delayed/falling
  update, landing and signed presentation reload. Two idle initializer fragments
  have explicit same-call continuation boundaries. New exact scope: 706 bytes,
  172 instructions; 31 indexed functions total, 22 simulation mappings plus two
  initializer fragments. Hashes/transfers live in `re/airborne_update.json`.
- `src/sim/airborne.*` preserves delay sign-bit overflow, boost/damping/control/
  gravity order, left priority, terrain queries, vertical word arithmetic and
  all landing assignments. State/scratch commit atomically. Parameters, flags,
  input fields and budgets are explicit; no legacy RAM or CPU runtime.
- `AirborneResult::immediate_continuation` preserves zero-speed landing's direct
  entry into idle. Reference stops before `0xA1BE/0xA246` with caller return
  pending; native reports the same event. Unsupported idle/grounded execution
  fails instead of silently advancing a tick. Other landings return normally.
- `wiznliz-airborne`, authored fixtures/goldens/unit/transport tests,
  `airborne-probe`, `airborne-compare`, strict continuation graph handling and
  reference `--airborne` mode. Six native executable hashes are now recorded.

Canonical evidence: [[03_Reverse_Engineering/findings/FIND-0012-airborne-update]].

## Validation and reproduction

Exact argv/cwd/status/duration/log records: `local/logs/airborne-update/commands.json`.
Cross-preset digests and combined instruction visits: `reproduction.json` in the
same directory. Reference bootstrap was `python3 tools/build_terrain_reference.py`
using existing sources. Final validation used:

```sh
python3 tools/project.py build --preset debug
ctest --preset debug
python3 tools/project.py build --preset release
ctest --preset release
python3 tools/project.py build --preset sanitize
python3 tools/project.py test --rom --preset sanitize
python3 tools/project.py airborne-probe --disassemble
python3 tools/project.py airborne-compare --rom --preset debug
python3 ~/WizNLizPC/tools/project.py airborne-compare --rom --preset release
python3 tools/project.py airborne-compare --rom --preset sanitize
python3 tools/project.py movement-probe --disassemble
python3 tools/project.py movement-compare --rom --preset sanitize
python3 tools/project.py terrain-compare --rom --preset sanitize
python3 tools/project.py split --dry-run
python3 tools/project.py rom-identify --verify
python3 tools/project.py check-vault
python3 tools/project.py check-hygiene
git diff --check
git diff --cached --check
```

Release comparison ran from `/tmp`; other commands from repo root. All
**111 Python tests PASS with zero skips**, and **12/12 CTest targets PASS** per
preset. Airborne: **415,940/415,940 comparisons PASS in each preset**, all 21
defined outputs and cross-preset hashes agree. All 172 new instructions execute,
246 total in this corpus. The three simulation corpora together visit 332 scoped
addresses, including eight idle initializer instructions. The updated reference
retains **282,233 movement / 614,436 terrain regression PASS**, including rejection
cases. Reference and native ASan/UBSan runs are clean.

Static probe passes eleven range hashes, 54 transfers, 332-instruction combined
graph with two explicit continuation exits, CPU sentinel and twelve GNU checks.
Previous movement probe and expanded metadata split dry-run pass. Exact report
paths: [[05_Validation/RESULTS]]. Codec/image comparisons were not repeated;
all their normal CTest targets passed and previous results remain historical.

## Corrected calculation and limits

The first hand-written two-call golden incorrectly retained initial y107 and
vertical -4. Both implementations already produced y109 and vertical -8: first
call moves onto contact, then second call applies gravity again before landing.
Independent arithmetic review corrected that one expectation. Initial/corrected
values and rationale are in `local/generated/airborne-research/golden-correction.json`;
reference/native initial outputs are adjacent. No code or reference output was
changed to hide divergence. Misaligned/truncated exploratory dumps stayed local
and were not promoted. No unresolved final failure or skipped test.

**Native playability remains none.** Idle/grounded handlers, complete controller,
physical input/frame scheduler, SDL3 app, audio, mods/saves/replays and full-game
boot remain outstanding. Semantic call sequences are not frames. Immediate idle
continuation is pending same-call work, not implemented idle behavior. Full
register/CCR ABI, hardware/timing and original invalid-RAM behavior are excluded.

Next: [[07_Tasks/TASK-0010-grounded-controller]], starting at `0xA1BE/0xA246`
and landing-selected handlers. Discovery context is recorded there; don't infer
complete handlers from partial disassembly or convert unknown effects to no-ops.
SDL3 development files remain absent; headless reconstruction is unblocked.

Original remains 1,048,576 bytes, SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
Original content, bulk evidence, reference sources and builds remain ignored.
Final explicit staging, vault and indexed-content review is recorded in
`local/logs/airborne-update/checkpoint-review.log`. Code and Obsidian are committed
together; no unrelated user work is included and no publication is requested.

Final review passes: **51 vault notes and 155 indexed files**, explicit 36-path
staging, and staged/unstaged whitespace checks. Staged content matches the
reviewed files; native/reference provenance matches the validated sources. No
unstaged or untracked owned work remains. No temporary process needs shutdown.
