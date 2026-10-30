---
id: FIND-0027
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# Retained P1 reversal ownership and effect phase

Task: [[07_Tasks/TASK-0010-grounded-controller]].

The native session now matches ordinary movie **[700,1090)** from one initial
seed and physical held sets only: 390 P1 wrappers, 390 banner requests, twelve
sound requests, one reversal allocation and twelve effect updates through
release. Debug/release/sanitize produce the same output digest. One fresh
instrumented original replay and one independent unhooked replay agree at their
covered-state endpoint. This is a bounded actor/effect session, not whole-frame,
global allocation, rendered output or audio equivalence.

ROM SHA-256:
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
Static context: `re/effect_session.json`; results/provenance:
`re/effect_session_validation.json`. Existing allocator/reversal semantics remain
in `re/reversal_step.json` and [[03_Reverse_Engineering/findings/FIND-0015-fast-reversal]].

## Measured order

After P1 returns at 6986, 69A4 initializes A6=FFFF1B50. The loop visits all 68
78-byte slots in ascending address order, ending at FFFF3008. Each active slot
executes F76C presentation, then the newly loaded +16 handler, then its +46
service. Exact instruction hooks establish these boundaries:

| Address/range | Behavior |
| --- | --- |
| `[69A4,69AA)` | Initialize slot address; one instruction |
| `[69AA,69BC)` | Existing active gate, F76C and +16 dispatch fragment |
| `[69BC,69CE)` | Load +46, call it, advance 78 bytes, compare end, loop; five instructions |
| `12646` | Existing return-only service; pending return 69C2 and four-byte stack restoration |
| `[B126,B12A)` | Later rendering bookkeeping clears word +14; one instruction |

The ordinary left-to-right reversal allocates physical object FFFF2C12 at
frame 1067 through A9DE/F994 and updates it later in that same frame. Native
logical identity is slot 0/generation 1, owner 1; original RAM addresses do not
enter native runtime state. Its X follows P1's final X minus six with word wrap;
spawn Y remains unchanged. It releases at frame 1078. F76C tail-calls FAA4,
which clears mode and pushes the free pointer. The loop then still executes
AA40 and the return-only +46 service: it does not retest the active bit.
The actor's A9DA completion occurs later, at frame 1085.

All twelve effect updates include exact caller/return/SP checks. All 82 writes
to the physical object during its P1 lifetime belong to initialization,
presentation, release, X-follow or the measured zero clear. The later B126 write
has callback PC B12A; +14 is already zero and is not consumed by native effect
logic. It is audited as an observed no-op, not silently modeled as rendering.
Actor and scratch remain unchanged during these effect phases. Native write
traces also retain the prior fixed input/resource guards.

## Shared pool boundary

There are **38 foreign allocations and 36 foreign releases** in this window.
Observed free pointers range from 47 to 53. FF3008 is a zero sentinel; the
available count is `(head - FFFF300C) / 4`, excluding that sentinel. The first
capture report counted it (48..54). Current validation of the unchanged raw
chunks corrects this observation and retains the earlier capture source hash.
Native outputs never depended on that count and are unchanged.

The native pool is deliberately a dedicated, bounded P1 reversal store. It
retains allocation/release and LIFO reuse, but does not reproduce competition,
capacity or physical order of the game's general pool. Physical FFFF2C12 can
belong to another object before/after P1's measured lifetime. Initial RAM must
contain no active P1 reversal; otherwise this empty-pool seed contract rejects.
This is not a claim that an original physical slot was reserved at frame 700.

A concrete next allocator client is A6=FFFF2B76, whose observed handler is 6D8C,
service 12646 and F994 pending return 5AA0 at frame 1069. These are investigation
leads, not a reconstructed handler. Follow its caller, spawned object and release
before claiming a shared native pool or replacing the dedicated capacity model.

## Native contract and validation

`P1SessionState::effects` optionally owns `ReversalEffects`. The session runs
banner, physical input conversion, full P1 wrapper, then active reversal slots
in ascending logical order. Objects born in the wrapper are included immediately.
Results include stable handles and final effect snapshots, including the release
update. Later inactive updates emit no effect request. Owner mismatch, exhausted
capacity or phase budget, unsupported actor work and later failures roll back
actor/control/tracking/scratch/ordinal and pool together. Publication uses a
nothrow move after all work succeeds. Native storage is capped at 4096 slots;
the default effect work budget is 64 active updates.

`wiznliz-session --reversal-session` accepts a 36-field seed: the existing
35 banner-session fields plus dedicated native capacity. Subsequent lines are
only U/D/L/R/A/B/C/Start held masks. No effect state, free-stack or environmental
state is supplied per call. Its output appends capacity, spawned handles and
15 fields per effect update. Older modes keep their existing transport.

- Authored C++/transport checks cover both facings, birth in the same invocation,
  retained Y, release/final follow, inactive skipping, slot order, LIFO generation
  reuse, multiple slots, capacity/work-budget failures and late owner rejection.
- Fresh restricted original comparisons: **203,586 reversal cases per preset**,
  all 119 declared new component instructions. Eight other sanitized corpora
  pass; combined fresh restricted scope is 1,054 instructions. Historical union
  stays 1,403. Seven new static/observed context instructions are not added to
  the restricted-execution count. Four GNU checks corroborate selected opcodes.
- **184 Python tests, zero skips; 34 CTests per preset.** Evidence guards reject
  changed/unhashed fixtures, wrong initial ownership and mismatched endpoints.
- `effect-session --fixture` rechecks raw chunks, artifact hashes, input/loaded
  identities and endpoints, then compares a fresh native build. It records both
  current and original validator identities; dependency changes reject reuse.

Native playability remains **none**. Pause, up/down world scheduling, transitions,
tally and other world objects are not integrated into this session; their bounded
components retain their separate contracts. Fresh ordinary effect evidence is
for one facing; authored tests and restricted execution cover both. No external
runtime rebuild, experimental state edit, GUI interaction or new movie needed.
