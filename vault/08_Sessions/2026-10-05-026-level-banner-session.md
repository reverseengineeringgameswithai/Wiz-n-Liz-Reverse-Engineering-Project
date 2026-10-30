---
id: SESSION-2026-10-05-026
type: session
status: completed
---
# Banner scratch and a longer retained P1 session

Started clean at `26faee93bb257ca7ad25afc2541d520192aa5fce` on
`work/airborne-update`, empty index and no pending Git operation. Read the actual
entry/handoff, status/next/task, session 025/finding 0025, durable brief, Git rules,
native/research code and debugger protocol. Latest user instruction authorized
continued work. No user recording, GUI action or external change was needed.

Intended checkpoint: `Integrate level banner into the retained P1 session`.

## Implemented progress

The session now covers ordinary movie `[700,1067)` with a single seed and
physical input rows. Its missing scratch writer is a banner routine: 63E2
stores row=6 in shared terrain scratch Y before input/P1. Native code selects
logical ordinary/final difficulty labels and optional wrapped number requests.
It preserves scratch X, word arithmetic, final-stage equality and text-before-
number order. Rendering remains outside the request contract. Original text/
glyph/number callees execute in research with a declared write sink and real
returns; no fabricated callee RTS or emulator enters the native runtime.

Session config optionally enables this pre-input phase. Banner and actor
results commit together after successful completion; unsupported later services
and exhausted budgets roll back all state and requests. The early transport
accepts one 35-field seed, then only held masks. The old 32-field session stays
supported. `session-compare` revalidates a completed capture's hashes, source
provenance and frame evidence before comparing a fresh native build, avoiding
unnecessary repeat instrumented replays.

Native mapping FUNC-0109 adds 106 bytes / 25 instructions. The additional 166
code bytes / 46 rendering instructions and 520 table/text/font bytes are
reference-only. New classified total 25,581 bytes; 1,022,995 remain unclassified.
Totals: **99 bounded simulation mappings + one partial / 109 indexed**.
Exact semantics: [[03_Reverse_Engineering/findings/FIND-0026-level-banner-session]].

## Fresh evidence

- **66,880 banner cases per debug/release/sanitize**, equal output hashes and
  all 71 declared original instructions. Native semantics cover 25 of those;
  46 are rendering callees executed only in research. Boundary sweeps, all word
  values distributed over difficulty, final branches and preserved fields pass.
- **367 early native wrappers per preset**, 367 banner requests/twelve sounds.
  Release/sanitize each have fresh unchanged movie captures and independent
  unhooked covered-state equality. Debug freshly revalidates the release
  capture; it is not a third worker replay. Common native output hash:
  `ba92d3030b033d90cfb53feba321d9b06ac8a64644a458c8128b3bb2ab0182c1`.
- Per early capture: 1,101 conversions, 1,468 polls, 367 inactive timer calls,
  5,205 scratch writes (367 banner + 4,838 query writes). Exact instruction hooks
  corroborate callback-time PCs. All fixed shared inputs/resources are guarded.
  Unused FF33DE permits only its observed zero clear; snapshots stay zero.
- Later `[3100,3200)` debug replay: 100 wrappers/four sounds and unhooked endpoint
  match, retaining output hash
  `a905ffb5327afbaea35a345d510674a50f01f81452065be474f390710835672f`.
- **181 Python tests, zero skips; 34/34 CTest targets per preset**. Native tests
  cover label branches, row/number wrap, unsupported difficulty, both retained
  session modes, late rollback and existing movement/jump/landing sequences.
  Two fixture checks reject a failed reference and a changed artifact as expected.
- Seven sanitized regressions: input 1,024; dispatch 138,149; presentation 347,320;
  actor 152,093; airborne 415,940; movement 282,233; terrain 614,436. Fresh union
  plus banner 935 instructions. Historical union plus new scope is 1,403.
- Static primary decode, byte hashes, transfers/closed graph and four GNU checks
  pass. GNU's CPU-selection limitation remains explicitly scoped.

Not rerun: nine other prior corpora (score, exit tally, bonus, palette, tally,
coasting, transition, actions, reversal), other historical/controlled captures,
whole-movie selector survey and SDL3 availability. No native rendering/audio,
boot or general world/frame equivalence claimed. Native playability is none.

## Failures resolved and limits preserved

The exploratory combined managed drain exceeded the worker response-size limit.
That attempt is not complete evidence. Final capture tooling drains both streams
per frame, checks every chunk for overflow/drops and preserves all events.
A preliminary debug capture failed an equal-SP assertion between 17AA0 and
63E2: the JSR at 17AA4 pushes four bytes. Static decoding and exact hooks corrected
the contract; fresh captures pass. No original/native mismatch was observed.

Save/load, PC/SR-write, reverse-navigation and hash-scope limits remain as recorded
in [[09_References/GENESIS_DEBUGGER]]. ROM/BK2, worker and all 104 runtime binaries
retain their hashes. Only the project-owned Musashi harness was rebuilt. No
external source/runtime, user GUI, Sonic19420 or WL3PC changes; no push/upload.

## Reproduction and handoff

```sh
python3 -B tools/build_terrain_reference.py
python3 -B tools/project.py build --preset debug
python3 -B tools/project.py banner-compare --preset debug
python3 -B tools/project.py session-capture local/generated/capture-qb2htq3j/recording.json --preset release --window early
python3 -B tools/project.py session-compare local/generated/session-movie/run-ego_8hqt/report.json --preset debug
python3 -B tools/project.py session-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py test --rom --preset debug
python3 -B tools/project.py check-vault
python3 -B tools/project.py check-hygiene
```

Build/banner/test were run in all presets; early capture also in sanitize.
Exact report/build/source identities: `re/banner_session_validation.json`.
Ignored research: `local/generated/world-session-research/`. Final early original
captures: `local/generated/session-movie/run-ego_8hqt` (release), `run-dinf5ps1`
(sanitize); late debug `run-p2uvtr0c`. Debug fixture comparison:
`local/generated/session-comparison/run-7dp51vrc`. Inputs and bulk traces remain
ignored. Reviewed 28 explicitly staged owned code/test/metadata/vault files.
Final vault check passes 84 notes; indexed hygiene passes 325 files; staged
whitespace checks pass. Initial finding-frontmatter errors were corrected. The
pass began clean with no unrelated user work to include.

Continue TASK-0010, still in progress: extend this retained session beyond frame
1067 by owning reversal slots/free-list state and executing the measured effect
phase/lifetime. Existing ordinary capture
`local/generated/reversal-movie/run-2ipv5ma3/1048-1090/trace.json` confirms F994
at frame 1067; use it as a lead, then collect fresh writer/ownership evidence.
Keep physical-only later rows and combined rollback. Full native playability
remains **none**; the broader world/platform/render/audio work is still open.
