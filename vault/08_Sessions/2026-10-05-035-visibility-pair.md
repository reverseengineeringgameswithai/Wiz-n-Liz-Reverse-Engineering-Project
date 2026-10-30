---
id: SESSION-2026-10-05-035
type: session
status: completed
---
# The 7C26 gated-visibility pair initializer

Started clean at `792b77c26cb4b931b1f23dd733e53ebfdaaa5c6d` on
`work/airborne-update`, with an empty index, no stash/worktree and no merge/
rebase/cherry-pick/revert operation. No existing user changes and no emulator,
GUI or worker processes. The user approved continuing with the recorded next
task after session 034. Read the handoff, FIND-0034/FIND-0030, pool/private code
and the evidence tooling. Authorized local implementation, validation, vault
sync and a reviewed local commit; no pushes/uploads. No subagents or external
tool changes.

Intended checkpoint: `Reconstruct the 7C26 gated-visibility pair initializer`.

## Delivered scope

`[7C26,7CA4)` calls F9E2 twice and builds two 7CA4 gated-visibility objects with
no flags or FF31C0 store, leaving A6 as the second object. Native
`make_visibility_pair_member` and `MixedPool::initialize_visibility_pair` share
one transactional template with 7B9C (`initialize_pair`); the shared
`InheritedObjectFields`, `PairMember` and `ObjectPair` moved to
`src/sim/reversal.hpp`. `tools/native/pair_transport.hpp` now holds the authored
case and seeded-pool transports used by `wiznliz-return-only` and
`wiznliz-private` (`--pair`, `--pair-pool` with per-phase gate rows). The harness
gains `--visibility-pair`; the comparator gains `--variant visibility`.

`tools/genesis_pair_initializer.py` now validates both initializers from one
replay with a variant table, audits creation writes per group of touching frame
spans, recognizes only the exact interrupt exception-frame shape, and follows
all four frame-629 slots to 1066 with the 7CA4 gate inputs each walk observes.
The mixed-session private seed adapter now verifies unrepresented bytes.

See [[03_Reverse_Engineering/findings/FIND-0035-visibility-pair]],
`re/visibility_pair_step.json` and `re/visibility_pair_validation.json`.

## Validation

- **8,714 restricted original/native cases per preset** for 7C26 and again for
  7B9C: 3,989 identical, 2,491 exhaustion, 2,234 unrepresented inheritance.
  7C26 executes 35 successful instructions, 21 new.
- Final fresh hooked replay of frames 0..1066 and independent unhooked endpoint
  `3f66b79f…`: `local/generated/pair-initializer-capture/run-rgs3r3w9/report.json`.
  7C26 at frame 156 (caller 1EC58, slots 41/40, finishing in 157) and 629 (caller
  68A4, slots 57/56); both enter with A6 naming 7B9C's second object. Creation
  groups [156,157] and [629] are complete: 40 + 38 exact writes each and one
  VBlank exception frame at 7C50. Four retained slots, 432 walks, 1,728 native
  updates, gates zero, 1066 seed equality; 2,863 audited continuity writes.
  Release/sanitize reuse it. Its 2,134 owned worker checkpoints were removed.
- Fresh mixed capture `local/generated/mixed-session/run-q_wuylbz` with the
  tightened adapter; release/sanitize reuse it. 633 records plus the anchor match.
- **207 Python tests, zero skips; 46/46 CTests per preset**; warning-free builds.
- 29 regressions pass (six component corpora and the P1 fixture per preset, eight
  sanitized corpora). Totals: 109 bounded plus two partial / 120 indexed; 26,599
  classified / 1,021,977 unclassified bytes; 1,601 cumulative; union 1,243 (1,252).

## Attempts, failures and skips

The first fresh capture (`capture-first-debug.log` in
`local/generated/private-pair-research/`) failed its creation-frame audit: a
level-6 VBlank interrupt arrives before 7C50 in the frame-156 run, and its
exception frame (PC long, saved SR word) is reported at that 7C26 PC. The tool
now recognizes exactly that shape, still rejecting any foreign write to pair
slots or FF31C0; the saved artifacts revalidated offline before the final fresh
capture. The generalized comparator's success-row length was off by one (fixed
before recorded runs). New tests initially took a temporary's address, used an
off-by-one output index and assumed zero generations for occupied seeds; tests
were corrected without native changes. Not rerun: actions through score corpora,
debug/release runs of eight sanitized corpora, other captures, whole-movie survey
and SDL3 availability.

## Reproduction and handoff

```sh
python3 -B tools/build_terrain_reference.py
python3 -B tools/project.py build --preset debug
python3 -B tools/project.py pair-initializer-compare --preset debug --variant visibility
python3 -B tools/project.py pair-initializer-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py pair-initializer-capture local/generated/capture-qb2htq3j/recording.json --preset release --fixture local/generated/pair-initializer-capture/run-rgs3r3w9/report.json
python3 -B tools/project.py mixed-session local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py test --rom --preset debug
python3 -B tools/project.py check-vault
python3 -B tools/project.py check-hygiene
```

Next: **the 7772 rising-pair initializer** (slots 65/64 at frame 629), which also
writes the caller's A5 as control link, clears the countdown and derives the
second position from the first. See [[01_Project/NEXT_ACTIONS]]. Callback79B6,
7AD6, overlap-hit FF31C0 readers, gate producers and hit7910 stay unsupported.
TASK-0010 is **in progress**; native playability is **none**.

Final preservation verifies ROM, BK2/recording, worker/build manifest, runtime
binaries and external source files; owned workers are closed and no GUI,
Sonic19420 or external source/runtime changes occurred. WL3PC advanced during
the pass by its owner's own commit (`88095b4`); this pass issued only read-only
`git` queries there and records the observation in the validation metadata.
Explicit staged review precedes the local checkpoint commit. No pushes/uploads.
