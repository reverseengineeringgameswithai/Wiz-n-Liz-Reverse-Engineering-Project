---
id: SESSION-20261002-011
type: session
status: complete
task: TASK-0010
---
# Implement supported grounded actor dispatch and same-call jumps

## Starting state and protected scope

Continued [[07_Tasks/TASK-0010-grounded-controller]] after reading the actual
AGENTS/START_HERE entry points, canonical vault workflow/brief/Git rules, both
handoff sessions, airborne finding, native code/transports/research metadata,
and the Genesis debugger README, verification, protocol, ABI, Python guide,
Wiz recipe and profile. Verified root `~/WizNLizPC`, clean tree and
empty index, branch `work/airborne-update`, HEAD
`45c947d1551117926cb583ad9de8145509700883`. No unrelated Wiz work was present.
No history rewrite, push, upload, package installation or global change.

Original ROM identity was checked before research, by every comparison/capture,
and at checkpoint review: 1,048,576 bytes, SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
No original bytes, permissions or filename changed. Bulk disassembly, captured
RAM, states, traces, binaries and extracted resources remain ignored locally.
BizHawk source/runtime program bytes and Sonic installation/port 19420 were
read-only. The existing worker launcher used only its usual ignored lock files;
new worker storage is in WizNLizPC/local. No reference-runtime rebuild occurred.
WL3PC was not used. Every owned worker has closed; no new persistent service.

Intended checkpoint subject: `Implement grounded actor dispatch and same-call jump transitions`.
No future commit hash is embedded in this note.

## Native delivery

`src/sim/actor.*` adds a transactional, bounded actor handler dispatcher and
explicit state/parameters/controls/effects. Idle, normal/fast grounded, idle turns,
normal reversal, terrain drop and jump paths execute with the original priority,
word wrap, signed comparisons, scratch and presentation assignments. Zero-speed
landing's idle continuation is consumed in the **same invocation**. Assignments
followed by RTS remain deferred. Jump executes its first airborne phase immediately
and returns ordered sound requests. Neither handler hits nor semantic invocations
are presented as completed game frames.

Seventeen bounded mappings bring the simulation total to 39, with two previous
idle initializer fragments retained. `re/actor_update.json` pins 315 additional
compared instructions over 1,542 bytes; six are the restricted original sound
guard/return. Only 1,426 bytes are newly classified because 116 idle bytes were
already static context. Full function ends remain empty where not proven.

`wiznliz-actor`, authored native units/transports, six Python evidence-contract
tests, `actor-probe`, `actor-compare` and `actor-capture` make the work reproducible.
Canonical semantics and exclusions:
[[03_Reverse_Engineering/findings/FIND-0013-actor-dispatch]].

## Original execution and reference capture

The separate Musashi harness executes all supported branches through RTS with
exact stack balance. It expands only declared code/state/argument ranges and
records all instruction visits and ordered sound request arguments. The original
FCB32 sound guard executes with selector zero, so both requests take actual
mismatch returns. No instruction patch, fake RTS or emulator code in native
libraries. Active audio driver execution is not part of that fixture.

The independent frozen GPGX worker performs ordinary routes from a fresh reset
and a gameplay checkpoint, plus two explicitly edited landing branches. Ordinary
inputs reach A27E, A6C8 and A88E. At F904/selected-handler/F906 the comparator
checks exact ordering, actor/control registers, stack and captured return address.
Eighteen actor/scratch fields and ordered sound requests agree. Both landing
experiments enter idle before the same F906 return. The ordinary frame-2013
A408 → AAEA → AB04 sequence remains observed.

All six hooked runs match unhooked replays from the same checkpoint and edits
using the declared covered-state hash. This is not hidden-state equivalence,
audio waveform parity, or a continuous native replay of the intervening animation
scheduler. Every native call is initialized from its captured entry. Full input
histories/settings, actual loaded binary identity, edits and artifact hashes are
retained. Trace overflow/errors reject evidence. See [[09_References/GENESIS_DEBUGGER]].

## Executed validation

- 117 Python tests pass, zero skips; all 14 CTest targets pass in debug, release
  and Clang ASan+UBSan. Seventeen independent actor goldens pass unchanged.
- 152,093 actor cases pass in **each** preset, 167,453 applied invocations per
  corpus. All outputs/digests agree across presets. Ten rejection checks per
  preset verify invalid terrain and four unsupported original branch addresses.
- 283 GPGX actor comparisons pass: 281 ordinary calls and two controlled landings.
  Eighteen fields plus eight ordered sound requests match; six unhooked replays
  agree. A27E/A6C8/A88E have 1/17/27 captured hits respectively.
- Fresh sanitized regressions pass 415,940 airborne, 282,233 movement and 614,436
  terrain cases. Across the four corpora all 647 scoped instructions are visited.
- The supplied previous damping fixture passes a fresh 135/135 scalar recheck.
  The 33 historical physical-input observations were read, not rerun here.
- Static range/transfer/graph checks, 68000 sentinel and seven GNU checks pass.
  Original ROM and source/executable provenance are verified. The vault, explicit
  staged metadata, hygiene and whitespace are checked for the final checkpoint.

Exact report locations and counts: [[05_Validation/RESULTS]]. Tracked summary:
`re/actor_validation.json`. Exact command argv/status/duration/logs and cross-preset
summary: `local/logs/grounded-controller/`. Key reproduction commands:

```sh
python3 -B tools/build_terrain_reference.py
python3 -B tools/project.py build --preset debug
python3 -B tools/project.py build --preset release
python3 -B tools/project.py build --preset sanitize
python3 -B tools/project.py test --rom --preset debug
ctest --preset release
ctest --preset sanitize
python3 -B tools/project.py actor-probe --disassemble
python3 -B tools/project.py actor-compare --rom --preset debug
python3 -B tools/project.py actor-compare --rom --preset release
python3 -B tools/project.py actor-compare --rom --preset sanitize
python3 -B tools/project.py actor-capture --preset debug
python3 -B tools/project.py airborne-compare --rom --preset sanitize
python3 -B tools/project.py movement-compare --rom --preset sanitize
python3 -B tools/project.py terrain-compare --rom --preset sanitize
python3 -B tools/project.py genesis-compare ~/BizHawkOpenSource/Tools/GenesisDebug/local/wiz/scenarios-jbc97cle/routine-fixture.json --preset debug
python3 -B tools/project.py split --dry-run
python3 -B tools/project.py check-vault
python3 -B tools/project.py check-hygiene
python3 -B tools/project.py rom-identify --verify
```

## Checkpoint review

Explicitly staged and reviewed all 31 owned source/test/metadata/vault paths;
there were no unrelated changes or pre-existing staged files. Vault validation
passes for 56 notes, hygiene passes for 173 indexed files, and staged whitespace
checks pass. All seven native executable provenance checks pass in each preset;
the restricted reference and final comparison report digests also verify.
The final field-name cleanup leaves the three sanitized regression executable
hashes identical to the bytes used by their recorded successful runs. No bulk
capture, extracted asset, ROM, binary or external source is staged. The local
review record is `local/logs/grounded-controller/checkpoint-review.json`.

## Corrections and limits

Initial generated cases included Python Boolean text, which scanf correctly
rejected; the case constructor now emits integer fields. Under the original
sandbox, LeakSanitizer could not inspect a traced process and the owned-worker
launcher could not open its normal lock files. Approved execution resolved both;
later the user enabled unrestricted local access. A six-byte GNU disassembly
probe was inconclusive in its short buffer; the final corroboration uses the
four-byte source load/store, while the full-range decode/hash and actual execution
still cover the six-byte instruction. These failures remain in ignored artifacts.

The first expanded rejection checks incorrectly expected a memory error for
unsupported branches. The reference actually reached a forbidden instruction.
Its diagnostics now distinguish the exact unsupported PC from instruction-budget
exhaustion, and final tests check those PCs. No expected native state output was
changed to conceal divergence; all authored goldens and semantic comparisons
passed. There is no unresolved final failure within the implemented scope.

**Native playability: none. TASK-0010 remains in progress.** Presentation callback
scheduling, allocating fast reversal, up/down actions, audio request consumption,
full physical input/frame scheduler, SDL3 app, mods/saves and native gameplay
replay remain open. Unsupported paths reject atomically. Audio is explicit
requests only. Codec/image differential corpora were not rerun, while their
normal CTest targets passed; prior results remain historical.

Exact next pass: trace and reconstruct F76C before the F904 handler call,
including A2E8/A380/A50E/A654 and A774/A93A callbacks. Then validate continuous
native presentation/motion sequences across invocations. Fast reversal requires
A818/A9DE and allocator F994; up/down requires 9C56/9D4E and their called effects.
Current task details: [[07_Tasks/TASK-0010-grounded-controller]].
