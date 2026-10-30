---
id: SESSION-2026-10-05-028
type: session
status: completed
---
# Reconstruct the 6D8C allocator client

Started clean at `15c1df21cb5e5207322672ca3d83e1258f4b91a3` on
`work/airborne-update`; empty index and no pending Git operation. Read actual
entry points, status/next/task, session 027/finding 0027, brief, Git rules,
relevant source and the debugger's capability/hook semantics. User explicitly
requested continuation onto 6D8C. No new movie or user action was needed.

Intended checkpoint: `Reconstruct the trail allocator client and particle lifetime`.

## Implemented

`src/sim/trail.*` reconstructs 6D8C's signed countdown, five-position history,
owner lookup, movement-dependent allocation and coordinate jitter. 5A9A's
successful particle initializer and E918's exact state/mirror recurrence are
native. Particle active/presentation/release behavior includes its return-only
handler/service on the release invocation. Handler and scheduled APIs keep their
boundaries explicit. Allocation, callback and late owner failures roll back
emitter and RNG together. No original RAM pointers are native identities.

New transport supports component corpora and retained emitter/RNG/particle
sequences; later state rows are ignored in sequence modes, tested with poisoned
seeds. Owner position and capacity availability remain explicit contextual
inputs. There is no shared world pool yet; native emission returns a typed
particle and release returns an event. See
[[03_Reverse_Engineering/findings/FIND-0028-trail-allocator-client]].

Three mappings add 288 bytes/62 instructions. Totals: **102 bounded simulation
mappings plus one partial / 112 indexed**. Classified bytes 25,897; unclassified
1,022,679. Two previously static service instructions also enter the restricted
execution corpus, giving 64 additional successful addresses and cumulative union
1,467. Fresh ten-corpus union is 1,118; unrelated historical scopes were not rerun.

## Fresh validation

- **209,082 original/native comparisons per debug/release/sanitize**, all 62 new
  instructions. Closed graph, exact hashes/transfers, primary decode and five
  GNU opcode checks pass. Original allocation, RNG and callbacks execute in the
  project-owned Musashi harness; no fabricated returns or native emulator.
- Fresh unchanged movie `[1066,1100)` and independent unhooked replay:
  `local/generated/trail-movie/run-_gh9gmsm/`. All native presets match **34
  retained emitter calls, eight spawns, sixteen RNG calls and 97 particle updates**.
  Four lifetimes complete; four are partial at the capture boundary. Six births
  wait until the next frame because their slots precede the emitter; two run
  immediately in later slots. Exact entry/return/stack and ordered phase checks
  distinguish these cases.
- 533 emitter writes and 64 RNG writes are audited; all RNG activity in this
  interval belongs to the emitter. 8,183 selected routine events and 52,895 native
  events drain per frame without drops/overflow. Hooked/unhooked exposed-state
  hashes agree. That hash does not cover hidden CPU/device state.
- Final native comparisons in every preset revalidate the saved raw capture;
  these are not additional original runs. Particle sequences start from native
  spawn output. Older 390-call P1/reversal session also passes all three native
  builds against its previously captured evidence, retaining its output digest.
- **187 Python tests, zero skips; 36/36 CTests per preset.** Authored RNG values,
  sign/wrap/history/equality branches, both particle rates, inactive gate,
  capacity/late-owner/callback failures and retained-seed transport checks pass.
- Nine sanitized regressions pass: input 1,024; banner 66,880; reversal 203,586;
  presentation 347,320; actor 152,093; dispatch 138,149; airborne 415,940;
  movement 282,233; terrain 614,436. Final comparison identities and report
  hashes are in `re/trail_validation.json`.

The reference harness was rebuilt locally after adding its strictly gated trail
mode. The external BizHawk source/runtime stayed read-only. Native source and
reference dependencies remain separately pinned. The final CLI usage-string
correction was followed by rebuilt presets and fresh trail comparisons/tests;
unchanged P1/regression binaries retain their recorded output evidence.

## Discovery errors and limitations

The first worker request supplied an array where the protocol's `registers`
option requires a Boolean. It rejected the request before collecting a trace;
that failed attempt is not evidence. A corrected discovery run and final capture
pass. Static probing initially used an incorrect inherited F76C instruction
count (52); primary decoding establishes 59. GNU rejects absolute EOR.W at E932;
five supported opcodes are corroborated, while E932 relies on primary decoding
and actual original execution. No native/reference semantic mismatch occurred.

Not rerun: eight other component corpora (actions, transition, coasting, tally,
palette, bonus, exit tally, score), other historical/controlled captures,
whole-movie selector survey, or SDL3 development availability. Initializer 6D22,
E948's alternate random routine, full shared pool/world schedule, rendering,
audio and native boot remain unimplemented. Native playability is **none**.

## Reproduction and handoff

```sh
python3 -B tools/build_terrain_reference.py
python3 -B tools/project.py build --preset debug
python3 -B tools/project.py trail-compare --preset debug
python3 -B tools/project.py trail-capture local/generated/capture-qb2htq3j/recording.json --preset debug
python3 -B tools/project.py trail-capture local/generated/capture-qb2htq3j/recording.json --preset release --fixture local/generated/trail-movie/run-_gh9gmsm/report.json
python3 -B tools/project.py test --rom --preset debug
python3 -B tools/project.py check-vault
python3 -B tools/project.py check-hygiene
```

Use each native preset for build/comparison/test. Captures, disassembly, states,
corpora and binaries remain ignored. Logs and discovery recipes are under
`local/generated/allocator-client-research/`; tracked capture/comparison tools
reproduce the final scope and refuse incomplete or changed evidence.

Next TASK-0010 pass: integrate P1, this retained emitter/RNG and both particle
kinds into a bounded mixed-object session with an ordered slot/free-list model.
Start from frame 1066's initial live objects; preserve release/reallocate order
and whether new slots lie before/after the current iterator. Audit other active
handlers 7CA4/7808/7A88 and service 78EE before claiming their stability or shared
capacity parity. Keep explicit unsupported behavior and combined rollback.
TASK-0010 stays in progress. No new recording or GUI action needed.


Final preservation check: ROM and BK2 hashes unchanged; worker and all 104 frozen
runtime binaries match the same build manifest. All owned reference workers are
closed. No changes to user GUI, Sonic19420, WL3PC or external source/runtime, and
no uploads/pushes. Vault validation passes (88 notes), hygiene and whitespace
checks pass. The initially empty index is preserved until explicit owned-path
staging; source, tests, metadata and synchronized notes form this checkpoint.
