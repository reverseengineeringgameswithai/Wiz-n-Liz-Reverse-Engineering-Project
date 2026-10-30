---
id: SESSION-2026-10-05-034
type: session
status: completed
---
# F9E2 allocation and the 7B9C pair initializer

Started clean at `c53a43a763fb41ed71cca2f10176ef9dec11cc6d` on
`work/airborne-update`, with an empty index, no stash/worktree and no merge/
rebase/cherry-pick/revert operation. No existing user changes and no running
emulator, GUI or worker processes. The user asked to continue TASK-0010 onto
F9E2 and 7B9C autonomously through one verified checkpoint. Read AGENTS/CLAUDE,
entry points, status/next actions, session 033, FIND-0033 and its validation,
pool/return-only/reference code and external worker interfaces. Authorized
local implementation, validation, vault sync and a reviewed local commit; no
pushes/uploads. No subagents or external tool changes.

Intended checkpoint: `Reconstruct F9E2 allocation and the 7B9C pair initializer`.

## Delivered scope

F9E2 is the A6 twin of F994: the same FF311C LIFO pop, but the object replaces
the caller's A6. It writes only +00/+06/+12/+14/+16/+46; every other byte is
inherited from the slot. Exhaustion loops forever at FA1E with the head
unchanged. 7B9C calls it twice, stores both members and puts the second in
FF31C0. The pool reset F872 does not clear inherited fields; FF31C0 survives
resets. A ROM-wide search finds one FF31C0 writer and six readers (7AD6 plus
five overlap-hit +16 resets), all unreconstructed.

Native `InheritedObjectFields`, `PoolSlot::inherited`, seed tag 9,
`make_return_only_pair_member`, `MixedPool::initialize_return_only_pair` and the
session-level anchor API implement exactly that scope. Exhaustion or unknown
inheritance rejects without allocation; any allocation clears inheritance, so a
released slot is unknown. `MixedSessionState::return_only_anchor` is carried by
mixed header 14 and validated every call. The restricted harness gains
`--pair-initializer`; `wiznliz-return-only` gains `--pair` and `--pair-pool`.

See [[03_Reverse_Engineering/findings/FIND-0034-pair-initializer]],
`re/pair_initializer_step.json` and `re/pair_initializer_validation.json`.

## Validation

- **8,714 restricted original/native cases per debug/release/sanitize**: every
  stack depth 0..68, six slot pairs, inheritance and random cases. 3,989 pairs
  identical; 2,491 exhaustion and 2,234 unrepresented-inheritance rejections.
  All 37 successful instructions execute; FA1E..FA30 never executes.
- Final fresh hooked replay of frames 0..1066 and independent unhooked endpoint
  `3f66b79f…`: `local/generated/pair-initializer-capture/run-r781581b/report.json`.
  65 F9E2 and 32 F994 calls verified; 7B9C at frames 156 (caller 1EC54, slots
  43/42) and 629 (caller 68A0, slots 59/58), both with complete exact 40-write
  audits and native matches. Slots 59/58 stay occupied through 33 allocations,
  31 releases and 432 walks; 864 native updates equal the 1066 seed. Write audit
  complete in 435/436 continuity frames; frame 632 dropped, boundaries cover it.
  Its 2,134 owned per-seek worker checkpoints (~997 MB) were removed by the tool.
- Debug/release/sanitize reuse that capture with final builds (`--fixture`).
- Final fresh mixed capture `local/generated/mixed-session/run-wkefr83n` with
  independent unhooked replay; release/sanitize reuse it. **633 ordered records
  plus the FF31C0 anchor** per call match; output SHA-256
  `c6167d3ae56ed8f1b6b18ec594311a40e564268009d64daff6b06206884176b2`.
- **205 Python tests, zero skips; 46/46 CTests per preset**; builds warning-free.
- 29 regressions pass: return-only, collision, table, private, trail, reversal
  and the 390-call P1 fixture per preset; eight sanitized corpora.
- Totals: 108 bounded mappings plus two partial / 119 indexed; 26,473 classified
  / 1,022,103 unclassified bytes; 1,580 cumulative executed instructions; fresh
  fifteen-corpus union 1,222 (1,231 with writers).

## Attempts, failures and skips

Discovery used owned workers on the unchanged recording (`discover.py`,
`frame629.py` under `local/generated/pair-initializer-research/`), finding both
7B9C runs. The first fresh capture `run-ktiqtizv` passed before the tool removed
its own worker checkpoints; its 954 MB checkpoint directory was removed after
confirming it held only state files, and the final capture used final sources.
The first anchored mixed capture failed natively with "collision inputs
unavailable": collision context parsed only for exactly 13 header fields. Fixed
to `>=13`, a collision-plus-anchor transport test added, and recaptured. The
running regression batch was stopped and rerun on final builds. An initial unit
test misassigned slot inheritance and assumed mode 81 tests target; the fixed
test asserts mode 81 never fires. A synthetic F9E2 model wrongly zeroed popped
stack entries; the validator was correct. The installed GNU plugin cannot decode
immediate/absolute forms here; eight register-form checks are used instead.

Not rerun: actions/transition/coasting/tally/palette/bonus/exit-tally/score
corpora, debug/release runs of the eight sanitized corpora, other historical or
controlled captures, whole-movie survey and SDL3 availability. No controlled
memory edit was needed.

## Reproduction and handoff

```sh
python3 -B tools/build_terrain_reference.py
python3 -B tools/project.py build --preset debug
python3 -B tools/project.py pair-initializer-compare --preset debug
python3 -B tools/project.py pair-initializer-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py pair-initializer-capture local/generated/capture-qb2htq3j/recording.json --preset release --fixture local/generated/pair-initializer-capture/run-r781581b/report.json
python3 -B tools/project.py mixed-session local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py test --rom --preset debug
python3 -B tools/project.py check-vault
python3 -B tools/project.py check-hygiene
```

Next: **the 7C26 7CA4 private-pair initializer**, called at 68A0 right after
7B9C and popping slots 57/56 at frame 629; their 629→1066 continuity is not yet
verified. See [[01_Project/NEXT_ACTIONS]]. Callback79B6, 7AD6, overlap-hit
FF31C0 readers and hit7910 stay unsupported. TASK-0010 is **in progress**;
native playability is **none**. Boot, world scheduling, rendering/audio and P2
remain unfinished. Original execution remains reference tooling only.

Final preservation verifies ROM, BK2/recording, worker/build manifest, runtime
binaries and external source files; owned workers are closed and no GUI,
Sonic19420, WL3PC or external source/runtime changes occurred. Explicit staged
review precedes the local checkpoint commit. No pushes/uploads.
