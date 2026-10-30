---
id: SESSION-2026-10-12-042
type: session
status: completed
---
# The 7DB8 setup message, the 6EF0 gate and the 6BD6 pickup service

Started clean at `39848f3e98a1267d30294847ecb0e80a99beffac` on
`work/airborne-update`, with an empty index, no stash and no
merge/rebase/cherry-pick/revert operation; no emulator or worker processes at
start. The user asked to continue the work. Authorized local implementation,
validation, vault sync and a reviewed local commit; no pushes/uploads. No
subagents; no external tool changes.

Intended checkpoint: `Reconstruct the setup message step and pickup service`.

## Delivered scope

7DB8's "service" values D28C/D2A2 turned out to be ROM message strings ("MIX
THOSE FRUIT!", "FRUIT RETURNED!") stored in the P1 control record's +46. 7DB8
selects one, CB72 gates it by signed priority on +53, and CB9A clears the message
row through the VDP. 6EF0 is a gated two-player pair allocator.

Native: `SetupMessage`, `ControlMessage`, `SetupGates`, `MessageRowClear` and
`continue_level_setup(state, tables)` for `[68BC,68C4)`; CB9A is a logical request
only, and 6EF0's open path rejects. `wiznliz-return-only --message`,
`wiznliz-collision --pickup-service/--pickup-scheduled`.

Tools: harness `--setup-message` (sinks and checks VDP words, stops at 68C4 or
6F02) and `--pickup-service/--pickup-scheduled`; comparators
`pair-initializer-compare --variant setup-message` (exact) and
`collision-compare --variant pickup`; the evidence tool validates the message step
(model, exact RAM writes, reported VDP sequence) and compares it natively.

See [[03_Reverse_Engineering/findings/FIND-0040-setup-message]],
`re/setup_message_step.json`, `re/pickup_service_step.json` and
`re/setup_message_validation.json`.

## Validation

- **4,717 restricted message cases and 136,848 pickup-service cases per preset**;
  82 new instructions (32 research-only rendering). Earlier setup and pair corpora
  rerun per preset.
- Final fresh hooked replay of frames 0..1066 with independent unhooked endpoint:
  `local/generated/pair-initializer-capture/run-ltl5vuug/report.json`. Frame 629
  shows MIX THOSE FRUIT (+53 0 → 64), exactly four RAM writes, 29 reported VDP
  writes (VRAM E00E), 6EF0 closed; eleven native comparisons match;
  release/sanitize reuse the capture.
- **215 Python tests, zero skips; 46/46 CTests per preset**; warning-free;
  29 regressions and the context probe pass. Totals: 120 bounded plus four partial
  / 133 indexed plus three fragments; 27,736 classified / 1,020,840 unclassified
  bytes; 1,848 cumulative; union 1,490 (1,499 with writers).

## Attempts, failures and skips

The first fresh capture (`run-bq_bx2_u`) stopped because the message write check
treated the ordinary system stack (FF00xx) as message state; offline inspection
also confirmed that the trace reports VDP port writes. Stack writes are now
excluded by a window below the fragment's own SP; the saved artifacts revalidated
offline, then a final capture used the final sources. Harness and comparator
corrections (string reads, the open-6EF0 stack depth, allocator-free probing,
pickup coverage scope, a missing transfers key) preceded any recorded comparison.
At the final preservation check a separate user BizHawk 2.11.1 session was
running; the check now distinguishes owned workers and recorded it untouched.
Not rerun: action through score corpora, debug/release runs of the eight sanitized
corpora, a fresh mixed capture, other captures, whole-movie survey and SDL3.

## Reproduction and handoff

```sh
python3 -B tools/build_terrain_reference.py
python3 -B tools/project.py build --preset debug
python3 -B tools/project.py pair-initializer-compare --preset debug --variant setup-message
python3 -B tools/project.py collision-compare --preset debug --variant pickup
python3 -B tools/project.py pair-initializer-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py pair-initializer-capture local/generated/capture-qb2htq3j/recording.json --preset release --fixture local/generated/pair-initializer-capture/run-ltl5vuug/report.json
python3 -B tools/project.py test --rom --preset debug
python3 -B tools/project.py check-vault
python3 -B tools/project.py check-hygiene
```

Next: **the four gated pair initializers 7FBE/7154/735E/7568 from 68C4**. See
[[01_Project/NEXT_ACTIONS]]. TASK-0010 is **in progress**; native playability is
**none**.

Preservation: the baseline was taken at pass start. ROM, BK2/recording,
worker/build manifest, 104 runtime binaries and 59 GenesisDebug sources verify;
the BizHawk source tree did not change; owned workers closed. WL3PC was only read;
its owner committed three times during the pass. Explicit staged review precedes
the local checkpoint commit. No pushes/uploads.
