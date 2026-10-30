---
id: SESSION-2026-10-05-024
type: session
status: completed
---
# Secondary tally, packed score and bounded reward thresholds

Started clean on `work/airborne-update` at
`187f43ed769c6bdb30aa5b6928e3a10704e861a5`, with empty index and no pending Git
operation. Read actual repository entry points, current status/next/task, session
023, finding 0023, durable brief, Git rules, source, static leads and debugger
protocol/capability semantics. The user authorized continuing the next bounded
pass. No new movie, GUI action or user input was needed.

Intended checkpoint: `Reconstruct secondary tally and packed score rewards`.

## Implemented result

The 5132 secondary gate now reaches native 53F2 behavior. Start/countdown rules
match the existing tally, but the consumed secondary unit adds packed 00010000
(decimal 10,000) to the score. A strict score > threshold check requests one
reward, then advances threshold until sufficient. The loop returns to AE36,
after AF28: it does not award for every crossed threshold. The counter stops
only at exactly 9; other words increment and FFFF wraps to zero. The final tally
sound is followed by countdown=3 and a return, even after the last unit. A later
actor invocation can start transition setup.

`ScoreState` contains packed score, threshold, increment, persistent arithmetic
scratch and reward word. Native decimal addition wraps after eight digits.
Invalid digits reject when consumed by addition; unused fields remain opaque.
The reference harness uses the same explicit input-domain guard before ADF4/AE4C,
not an invented original-game malformed-input check. A 4,096-advance default
budget bounds threshold loops. All new state and requests participate in the
actor transaction and roll back after malformed data, budget failure or a later
unsupported service. There is no native emulator dependency.

A logical `score_reward` sample identity maps through the research adapter to
F25EA/count 230/parameter 20E4, observed mailbox `(230,20E4,A5EA,30)`. Playback,
audible meaning and the broader reward-counter role are not established. Exact
stack boundaries distinguish the tail into 53F2, the called score helper and its
nested sample/threshold helpers. Full CPU flags and dead stack scratch are not
native gameplay fields.

Research transport now offers 77-field `--score` / `--score-sequence`. The latter
retains/asserts score, threshold, increment, rewards, arithmetic scratch and
secondary count alongside previous actor/tally state. Gates, equality keys,
controls, transition/world context and terrain scratch remain explicit feeds.

## Fresh validation

- **280 new disjoint bytes / 71 instructions**, plus the previously classified
  four-byte transfer at 5166 now successfully compared. Static byte/transfer/
  closed-graph checks and four new GNU checks pass, including ABCD and both BHI
  branches. Earlier decoder limitations remain; no new limitation in this scope.
- **328,916 original/native cases in each preset**, identical output hashes,
  20 independent goldens and all 72 scoped instructions visited. Groups:
  313,556 flat/state, 4,608 authored-terrain, 10,752 cataloged-terrain. Separate
  full-word and valid-score sweeps are not a Cartesian proof. ADF4's original
  source operand here is fixed to 00010000; other helper amounts have authored
  native arithmetic tests, not new direct original-entry comparisons.
- Five expected negative cases reject without output in each transport:
  invalid consumed score, threshold and increment; zero threshold increment;
  and a threshold cycle. Native tests verify exact budget boundaries and
  late-service rollback after both score and motion updates.
- **Four controlled RAM/input branches / eleven complete wrappers** from movie
  boundary 4934. The eight-call branch consumes two units and advances thresholds
  four then one times, with two sample requests; its second reward sees counter=9
  and leaves it there. Single-call branches cover equality without a reward,
  score overflow and reward-counter overflow. Totals: **five tally sounds,
  three sample requests, six threshold advances**. Native mutable state persists.
  Four independent unhooked workers repeat identical edits/neutral inputs and
  match covered-state endpoints. No trace overflow. These are not ordinary hits.
- **174 Python tests, zero skips; 32/32 CTest targets per preset.** Trace tests
  reject missing boundaries, wrong stack/sample ABI, unintended writes, truncated
  snapshots and overflow. Existing default sample/control contracts remain strict.
- Fresh replay regressions: **231 ordinary exit-tally wrappers / two sounds**,
  **one controlled equality wrapper**, **175 ordinary tally wrappers / five
  sounds**, **191 ordinary / 72 input-branch wrappers**, **17 transition actor /
  17 timer calls**, **one coasting initializer / 16 calls**, **37 controlled
  palette wrappers**, **three controlled bonus wrappers**. Independent unhooked
  endpoint checks all pass. Counts overlap between contracts and are not a sum
  of distinct frames.
- Fourteen sanitized prior corpora: **348,668 exit tally, 160,680 bonus,
  214,448 palette, 231,475 tally, 87,571 coasting, 306,528 transition, 138,149
  wrapper, 146,638 actions, 347,320 presentation, 152,093 actor, 203,586 reversal,
  415,940 airborne, 282,233 movement, 614,436 terrain**. Fifteen corpora together
  visit **1,278 scoped successful instructions**, including six reference-only
  sound guards and the newly consumed 5166 transfer.

No original/native semantic mismatch or final test failure. During review,
introducing scoped control writes was found to require preserving the prior
snapshot-length equality check; it was tightened and a truncation negative added.
All affected captures and the full test matrix were rerun afterward. Earlier
capture artifacts are superseded by the final evidence index. Full-movie address
survey and older 507 actor/presentation and 92 actor / 24 effect movie contracts
were not rerun. No undocumented skipped tests. The first vault check caught a
missing explicit task link in the new finding; adding that link resolved it.

Evidence: `re/score_validation.json`. Final controlled capture:
`local/generated/score-experiments/run-00x74dfm/report.json`. Logs, static
instruction text and preservation manifest remain ignored under
`local/generated/score-research/`.

```sh
python3 -B tools/project.py score-probe --disassemble
python3 -B tools/project.py score-compare --rom --preset debug
python3 -B tools/project.py score-compare --rom --preset release
python3 -B tools/project.py score-compare --rom --preset sanitize
python3 -B tools/project.py score-capture local/generated/capture-qb2htq3j/recording.json --preset sanitize
python3 -B tools/project.py exit-tally-capture local/generated/capture-qb2htq3j/recording.json --preset sanitize
python3 -B tools/project.py exit-tally-capture local/generated/capture-qb2htq3j/recording.json --preset sanitize --equal-marker-experiment
python3 -B tools/project.py dispatch-capture local/generated/capture-qb2htq3j/recording.json --preset sanitize
python3 -B tools/project.py test --rom --preset debug
python3 -B tools/project.py test --rom --preset release
python3 -B tools/project.py test --rom --preset sanitize
python3 -B tools/project.py check-vault
python3 -B tools/project.py check-hygiene
```

The other prior corpus/capture commands and exact report paths are pinned in
`re/score_validation.json`; ignored `regress.py` and `captures.py` show this pass's
batch recipes. Normal native builds remain independent of Musashi and Genesis.
The project-owned restricted harness was rebuilt locally from its pinned sources;
the external Genesis reference runtime was not rebuilt or modified.

## Preservation and handoff

Original ROM and BK2 hashes remain unchanged. All 104 pinned runtime binaries and
the independent worker match their previous hashes. Frozen build ID remains
`6caddf552236e2538cef28557605012c6f18f00807e4d1dca9ec1b0c63db89c6`.
Movie input digest remains
`34434f0aa0b1ebc7dbf4e464cd044ac52436b944bf6a01cdc24c811e1f6c3a88`.
No external source/runtime write, GUI/Sonic manipulation, installation, upload or
push. Owned workers close normally. Only owned code/tests/metadata/vault enter
this checkpoint; bulk artifacts stay ignored.
All 35 explicitly staged files were reviewed and matched the working files.
Final vault validation covers 80 notes and hygiene covers 303 indexed files;
both pass, along with the staged whitespace check. No unrelated paths are staged.

Current totals: **97 bounded simulation mappings plus one partial / 107 indexed
functions**, **24,575 / 1,048,576 classified ROM bytes**. 5132 is promoted;
4770's alternate mode remains partial. **TASK-0010 remains in progress; native
playability remains none.**

Exact next task: **a bounded native P1 session with measured input conversion and
invocation order**. Use an already compared movement/jump window, seed scene/
actor/control state once, then replace per-call control feeds with a derived
native three-button producer and measured stepping. Identify shared writers and
frame cadence before integrating timers/effects; preserve phase boundaries and
same-call continuations. Report remaining environment feeds rather than claiming
full-frame parity. This is the planned change in emphasis toward a playable
slice after closing 53F2, not another unrelated helper expansion.
See [[01_Project/NEXT_ACTIONS]] and
[[03_Reverse_Engineering/findings/FIND-0024-secondary-score]].
