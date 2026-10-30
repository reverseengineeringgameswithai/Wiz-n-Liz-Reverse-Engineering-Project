---
id: SESSION-2026-10-18-045
type: session
status: completed
---
# The 7910 probe hit: delivering the carried fruit

Started clean at `b527dca5fc11b2368dbbef88b72157d264010ab0` on
`work/airborne-update`, with an empty index, no stash and no
merge/rebase/cherry-pick/revert operation. A separate user BizHawk 2.11.1
session (EmuHawk with a SonicClassicHeroes movie) was running throughout and was
left untouched; no project workers were running at start. The user asked to
continue with the next task and, before leaving, allowed going on to the next
item afterwards. Authorized local implementation, validation, vault sync and a
reviewed local commit; no pushes/uploads. No subagents; no external tool changes.

Intended checkpoint: `Reconstruct the 7910 probe hit and fruit delivery`.

## Delivered scope

7910, the 783A probe's 78EE hit target, delivers a carried fruit. It returns
while the long FF31B0 is set or the touching control's +1A2 link is dormant
(7A56). With a carrying link it requests sound 008C, pops the 59AE sparkle (F9E2
then 59BC, at the link's position − (8,8)), runs 5964 on the link, moves it to
(00A4,00F6) with callback 79B6, pops an F994 copy that FB06 fills from the link
and clears the link's mode. Its +42 store writes back the value just copied, so
no record changes. The copy's callback79B6 posts FIRST/SECOND INGREDIENT
COLLECTED! (ROM strings D20E/D22F) and calls 7AD6; both stay unsupported.

Native: `walk_collision_probe`, `DeliveredPickup`, `step_delivered_pickup`,
`deliver_carried`, `MixedPool::walk_probe` and probe hits in `MixedPool::step`
(with a `PickupWorld` and FF31B0); `wiznliz-collision --probe-hit` and
`--delivered`. The pickup transport's link seeding/printing is now shared.

Tools: reference `--probe-hit` (86-field cases: probe, both links, FF31B0, 78EE
inputs, explicit top two free entries, up to 64 walks, separate P1/P2
departures; stops at the FA1E/F9D0 loops or a seeded probe callback) and
`--delivered` (21-field later walks of a sparkle or copy; stops at 79B6);
`project.py delivery-compare` with the corpora in `tests/delivery_cases.py`; the
evidence tool traces the 7910 internals and the free stack and compares every
hit and every later walk of the created objects natively.

See [[03_Reverse_Engineering/findings/FIND-0043-fruit-delivery]],
`re/delivery_step.json` and `re/delivery_validation.json`.

## Validation

- **8,557 restricted cases per preset** (debug/release/sanitize): 4,425 probe
  walks and 4,132 later walks; 40 new instructions, all native (41 with the
  already classified 7A56). Every earlier setup, pair and pickup corpus reruns
  per preset.
- Fresh hooked replay of frames 0..1066 with independent unhooked endpoint:
  `local/generated/pair-initializer-capture/run-5ascs0mo/report.json`. Nine
  ordinary 7910 hits (823 delivers into slots 54 and 47; 824..831 return) and
  all 60 later walks of the sparkle and the copy match natively and chain; the
  copy's 79B6 at 853 rejects natively; link 53 stays unchanged to 980. Fourteen
  comparisons match; release (`run-5pwv96uj`) and sanitize (`run-5tj5b3zi`) reuse
  the capture.
- **218 Python tests, zero skips; 46/46 CTests per preset**; warning-free; 29
  regressions and the context probe pass. Totals: 133 bounded plus four partial
  / 146 indexed plus four fragments; 28,992 classified / 1,019,584 unclassified
  bytes; 2,113 cumulative; union 1,756 (1,764 with writers).

## Attempts, failures and skips

No recorded run failed. Before any recorded comparison: a unit test built pools
with free objects missing from the free stack (constructor rejection); the first
evidence derivation required two free entries at every hit although only a
delivery pops (the synthetic dormant-return walk exposed it). Review then found
that 7A56 was already classified and executed with the `[7A46,7A58)` writer
fragment, so the scope is 180 bytes / 40 new instructions; the metadata marks it
previously classified. One capture (`run-mssa81pe`) and comparison runs made
before that edit matched and were superseded; the final capture also labels the
copy's FAA4 release inside 79B6/7AD6 separately from supported releases. The
first delivery corpus (8,531 cases) was replaced by one biased toward rare
classes (8,557). The synthetic evidence test's frame 802 uses artificial marks.

The BizHawk tree's status, tracked diff, 59 GenesisDebug sources and 104 runtime
binaries equal the baseline. WL3PC's owner committed during the pass
(`efc88b5` → `83de5f4`); it was only read. The worker's ignored
`local/worker-publish.lock` is touched by `run-worker.sh` as before.

Not rerun: action through score corpora, debug/release runs of the eight
sanitized corpora, a fresh mixed capture, other captures, whole-movie survey and
SDL3.

## Reproduction and handoff

```sh
python3 -B tools/build_terrain_reference.py
python3 -B tools/project.py build --preset debug
python3 -B tools/project.py delivery-compare --preset debug
python3 -B tools/project.py pair-initializer-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py pair-initializer-capture local/generated/capture-qb2htq3j/recording.json --preset release --fixture local/generated/pair-initializer-capture/run-5ascs0mo/report.json
python3 -B tools/project.py test --rom --preset debug
python3 -B tools/project.py check-vault
python3 -B tools/project.py check-hygiene
```

Next: **callback79B6 and 7AD6's first-ingredient path** (frame 853). See
[[01_Project/NEXT_ACTIONS]]. TASK-0010 is **in progress**; native playability is
**none**.

Preservation: the baseline was taken at pass start. ROM, BK2/recording,
worker/build manifest, 104 runtime binaries and 59 GenesisDebug sources verify;
owned workers closed; the user's EmuHawk session was left running. Explicit
staged review precedes the local checkpoint commit. No pushes/uploads.
