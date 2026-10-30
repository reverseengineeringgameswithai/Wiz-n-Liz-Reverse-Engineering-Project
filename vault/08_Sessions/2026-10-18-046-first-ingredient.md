---
id: SESSION-2026-10-18-046
type: session
status: completed
---
# callback79B6 and 7AD6: the first ingredient collected

Started clean at `fa33bfd83e5c7307708a288139e40d51400b973e` on
`work/airborne-update` (session 045's checkpoint, made earlier in this
conversation), with an empty index, no stash and no
merge/rebase/cherry-pick/revert operation. A separate user BizHawk 2.11.1
session (EmuHawk with a SonicClassicHeroes movie) was running throughout and was
left untouched. Before leaving, the user allowed going on to the next item after
session 045. Authorized local implementation, validation, vault sync and a
reviewed local commit; no pushes/uploads. No subagents; no external tool changes.

Intended checkpoint: `Reconstruct the first-ingredient callback and activation`.

## Delivered scope

When a delivered copy's mode-87 animation ends, F76C calls 79B6. With FF31AC
zero (no ingredient collected yet) it restores the copy's frames from +22/+26,
sets mode 81 and 6BB2's cadence, installs the 7A88 table handler (cursor 7A58,
+36 = 0), posts D20E ("FIRST INGREDIENT COLLECTED!", priority 01) to the copy's
control through CB72, sets +32 = FFFF and +10 = 000E and calls 7AD6, which
copies it into the dormant FF31B4 object, names that object in FF31AC and the
copy's record and releases the copy; 79B6's tail stores FF31BE = 0050 and FF31BC
= 0. The walk then runs 7A88 on the released copy. The FF31AC-nonzero paths
(D22F "SECOND INGREDIENT COLLECTED! / SPELL BEING MIXED!", FF31B8, FF31B0 and
the anchor's 7B42 chain with D269 "SPELL COMPLETED! / DOOR OPEN!") reject.

Native: `MixedPool::walk_delivered`, delivered copies in `MixedPool::step` with
a `PickupWorld` (now also FF31AC, FF31B4/FF31B8, both controls' message fields,
the tilemap, FF31BE and row clears), mutable shared `PrivateGlobals` in `step`,
`post_message` (CB72, shared with 7DB8) and two new `SetupMessage` values;
`wiznliz-collision --ingredient`.

Tools: reference `--ingredient` (31-field copy walks through 79B6/CB72/CB9A/
7AD6/FB06/FAA4/7A88 with the VDP words sunk and checked; stops at 7A00);
`project.py ingredient-compare` with the corpus in `tests/delivery_cases.py`;
the evidence tool traces FF31AC..FF31BF, both controls' message fields and the
tilemap, compares the callback walk natively and follows the FF31B4 object as a
table object (`wiznliz-table-motion --scheduled`).

See [[03_Reverse_Engineering/findings/FIND-0044-first-ingredient]],
`re/ingredient_step.json` and `re/ingredient_validation.json`.

## Validation

- **4,172 restricted cases per preset** (debug/release/sanitize); 29 new
  instructions, all native (178 executed). Every earlier setup, pair, pickup and
  delivery corpus reruns per preset.
- Fresh hooked replay of frames 0..1066 with independent unhooked endpoint:
  `local/generated/pair-initializer-capture/run-fw_j2m7x/report.json`. The 853 walk
  and all 213 later walks of slot 67 match natively; every earlier comparison
  reproduces (fourteen); release (`run-alhwh_nt`) and sanitize (`run-eor5mkpw`)
  reuse the capture.
- **218 Python tests, zero skips; 46/46 CTests per preset**; warning-free; 29
  regressions and the context probe pass. Totals: 133 bounded plus six partial /
  148 indexed plus four fragments; 29,146 classified / 1,019,430 unclassified
  bytes; 2,142 cumulative; union 1,787 (1,793 with writers).

## Attempts, failures and skips

No recorded run failed. Before any recorded comparison: the restricted harness
first read ROM outside its declared scope (CB72 reads a message's priority byte
and 7A88 its table), so those bytes were declared; the transport first derived
its "called" flag from FF31AC's presence, which the second-ingredient cases set
as an input; a unit test compared FF31AC against a fresh world instead of its
value before the walk (its failing line was found by giving the test's check a
source location); two synthetic-test expectations were wrong (a table walk's
expected output is its exit; the sparkle's release depth). One capture
(`run-ztohns0r`) matched every comparison and was superseded only to add
`re/ingredient_step.json` to the recorded sources.

The BizHawk tree's status, tracked diff, 59 GenesisDebug sources and 104 runtime
binaries equal the baseline. WL3PC's owner committed during the pass (`83de5f4` → `c0c973e`); it was only read.

Not rerun: action through score corpora, debug/release runs of the eight
sanitized corpora, a fresh mixed capture, other captures, whole-movie survey and
SDL3.

## Reproduction and handoff

```sh
python3 -B tools/build_terrain_reference.py
python3 -B tools/project.py build --preset debug
python3 -B tools/project.py ingredient-compare --preset debug
python3 -B tools/project.py pair-initializer-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py test --rom --preset debug
python3 -B tools/project.py check-vault
python3 -B tools/project.py check-hygiene
```

Next: **run the retained setup pool natively past its hits** (a `PickupWorld`
and link 53's emitter inputs in the continuity). See [[01_Project/NEXT_ACTIONS]].
TASK-0010 is **in progress**; native playability is **none**.

Preservation: the baseline was taken at pass start. ROM, BK2/recording,
worker/build manifest, 104 runtime binaries and 59 GenesisDebug sources verify;
owned workers closed; the user's EmuHawk session was left running. Explicit
staged review precedes the local checkpoint commit. No pushes/uploads.
