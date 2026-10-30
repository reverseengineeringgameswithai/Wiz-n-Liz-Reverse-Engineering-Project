---
id: SESSION-2026-10-05-027
type: session
status: completed
---
# Retained reversal allocation and effect lifetime

Started clean at `7cdf6e9bf7aa006affe53ec432288f8e8903b16a` on
`work/airborne-update`, empty index and no pending operation. Read actual entry
instructions, status/next/task, latest session/finding, brief/Git rules, relevant
native/research code and debugger protocol. Continued the user's authorized
local work; no new user action or movie was required.

Intended checkpoint: `Retain reversal effects across the native P1 session`.

## Delivered

The one-seed physical-input session now covers **[700,1090)**, extending through
frame 1067's allocating reversal and its twelve-update lifetime. It owns native
reversal slots/free-list and runs the effect phase after P1, including newly
spawned objects and the final X-follow after release. Banner, input, actor,
tracking, scratch, ordinal and effects commit together. Budget/ownership/capacity
failures preserve all caller state. Both facings and multi-slot failures have
authored tests. Transport adds an optional 36-field seed; later rows remain held
masks only. No emulator enters native targets.

Fresh writes reveal ongoing unrelated shared-pool activity. The implemented
pool therefore retains P1 ownership as a bounded projection, not general world
allocation parity. No foreign writer changes the effect during its owned life.
Its observed +46 service returns normally even on release. Rendering later
clears its already-zero +14 field; this audited no-op remains outside native
rendering. See [[03_Reverse_Engineering/findings/FIND-0027-retained-reversal-session]].

Three static context ranges add 28 classified bytes/seven instructions; four
GNU checks pass. They extend understanding of the existing effect phase and
render bookkeeping, not the original/native instruction corpus or mapping
count. **99 bounded simulation mappings + one partial / 109 indexed** remain.
Classified total is 25,609 bytes, with 1,022,967 unclassified.

## Fresh runs

- Fresh unchanged ordinary movie capture: `local/generated/effect-session/run-6gklchzd`.
  All 390 wrappers/390 banners/twelve sounds, one spawn/twelve effect updates/one
  release match; independent unhooked replay reaches the same exposed state.
- Current raw-chunk validation and native comparisons pass in debug/release/
  sanitize: respectively `run-fhe51vb6`, `run-s1rdwy4b`, `run-ra6yk38i`, under
  `local/generated/effect-session/`. These reuse the one original capture;
  they are not three new emulator runs. Common native output SHA-256:
  `8c738e9a85ad89630327f17f9a973add730f96a7ee29555ce55267a51558577b`.
- Per original window: 390 wrappers, 1,170 producer conversions, 1,560 polls,
  390 inactive timers and 5,350 scratch writes. 102,510 selected routine events
  and 610,828 native events, drained per frame without overflow/drop. P1 effect
  has 82 writes, twelve verified service tails. Foreign pool activity is 38
  allocations/36 releases, observed rather than reproduced.
- **203,586 reversal comparisons per preset**, all 119 component instructions.
  Eight sanitized regressions: input 1,024; banner 66,880; dispatch 138,149;
  presentation 347,320; actor 152,093; airborne 415,940; movement 282,233;
  terrain 614,436. Fresh restricted instruction union 1,054; cumulative 1,403
  remains partly historical. The new static context is not added to that union.
- **184 Python tests, zero skips; 34/34 CTests in each preset.** No native/reference
  mismatch or final test failure. Explicit malformed/unsupported cases reject
  as expected. No reference harness or external runtime rebuild was needed.

During audit development the initial free count included the FF3008 zero sentinel
(48..54). The final validator excludes it (47..53) using the same unchanged raw
capture. It also verifies the complete owned service tail, initial empty-owner
contract and fixture hashes/identities. Earlier source identity remains recorded;
no trace or original report was overwritten to hide the correction. Native
output did not depend on this observation. A preceding 14-frame owned discovery
also matched actor/effect outputs; final claims above use the full window.

Not rerun: eight other component corpora (actions, transition, coasting, tally,
palette, bonus, exit tally, score), other historical/controlled movie captures,
whole-movie selector survey or SDL3 development availability. Rendering/audio,
whole-pool/world/frame parity, native boot and playability remain absent.

## Reproduce and continue

```sh
python3 -B tools/project.py build --preset debug
python3 -B tools/project.py effect-session-probe
python3 -B tools/project.py effect-session local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py effect-session local/generated/capture-qb2htq3j/recording.json --preset release --fixture local/generated/effect-session/run-6gklchzd/report.json
python3 -B tools/project.py reversal-compare --rom --preset debug
python3 -B tools/project.py test --rom --preset debug
python3 -B tools/project.py check-vault
python3 -B tools/project.py check-hygiene
```

Build/test/reversal and current saved-capture comparisons were run in all three
presets. Exact report/native/reference/source identities are pinned in
`re/effect_session_validation.json`. Discovery, preservation manifest and logs
are ignored under `local/generated/effect-session-research/`.

Next bounded TASK-0010 pass: reconstruct the competing allocator client observed
at **A6=FFFF2B76, handler 6D8C, F994 return 5AA0** and its spawned object's lifetime.
Derive exact ranges/dependencies, compare restricted original execution, and
measure its writes/order relative to P1 before integrating a shared native pool.
Keep this session's dedicated-pool limitation until competition is implemented.
No new movie or GUI action is needed. TASK-0010 stays in progress; **native
playability is none**.

Final preservation checks confirm unchanged ROM/BK2, worker, build identity and
all 104 runtime binaries. No owned reference workers remain. External source/
runtime, user GUI, Sonic19420 and WL3PC were untouched; no upload/push. Initial
vault validation found a missing explicit task link in the new finding; it was
corrected and all 86 notes now pass. The pass began clean, with no unrelated
work to preserve or include. Checkpoint review covers 23 explicitly owned paths;
protected generated/input artifacts remain ignored.
