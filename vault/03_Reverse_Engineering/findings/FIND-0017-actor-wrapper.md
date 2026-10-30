---
id: FIND-0017
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# Return-only selectors, airborne callback and the actor-wrapper tail

The observed 12646/AA50 gap is closed. Native execution now also reaches the
wrapper's actual return, including its selected +46 service and control-record
coordinate writes. This is a bounded actor contract, not a complete game frame.
[[07_Tasks/TASK-0010-grounded-controller]] remains in progress; native playability
is none. Prior action boundaries remain valid narrower APIs.

## Identity and instruction evidence

USA ROM, 1,048,576 bytes, SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
`re/dispatch_step.json` adds two disjoint ranges: `[12646,12648)` is one RTS;
`[F906,F938)` contains fourteen instructions / fifty bytes. All fifteen new
instructions execute in the restricted original corpus. Six new GNU instruction
corroborations and the existing original-68000 closed-graph checks pass. AA50's
`[AA50,AA88)` ten-instruction initializer was already mapped by FUNC-0021; its
new callback role does not add duplicate byte/function coverage.

FUNC-0080 maps the return-only selector, giving **80 indexed functions / 71
bounded simulation mappings**, plus two idle initializer fragments, one actor
phase and two effect phases. The actor phase now spans `[F8F6,F938)` through its
RTS. Original entry F8F2 first loads A6 from control+0; native ownership is supplied
explicitly at the API boundary. It is not a universal original-pointer dispatcher.

## Exact behavior and ordering

- 12646 is an actual RTS, used here as both actor+16 handler and actor+46 service.
  Native `MotionUpdate::return_only` and `ActorService::return_only` are distinct
  logical identities. Unknown selectors do not acquire this behavior.
- AA50 writes mode 81; frame/begin/end 58/60/61; counters 6/6; vertical motion 0;
  delay FFFF; and handler AAEA. It retains position, speed, facing, target,
  cycles, callback and service. Its RTS returns to F900 when used as a callback.
  It performs no terrain query or immediate airborne integration itself.
- F900 loads the handler after presentation. F904 invokes it, returning to F906.
  Thus movie frame 1614 runs AA50 initialization followed by AAEA -> AB04 inside
  one wrapper invocation. Frame 1608–1613's selected handler simply returns.
- F906 loads actor+46 after movement. F90A invokes it with F90C pending. The
  verified return-only service leaves captured state unchanged.
- F90C compares control+1A6 to **exact word FFFF**. For any other word, it writes
  wrapped actor X+4 and Y+6 to control+42/+44. For FFFF, it writes FF80 to both.
  Coordinate values are confirmed; their downstream display/gameplay consumers
  and the meaning of other selector values are not established by this pass.
- The active bit is tested once at F8F6. Inactive actors bypass presentation,
  handler and service but still execute the coordinate tail. There is no second
  activity test after a callback changes mode.

Native `step_actor_dispatch` wraps the prior scheduler, selected service and
`ActorTracking` output in one transaction. Unknown invoked services, unknown
callbacks/handlers, missing context or exhausted work budgets leave actor,
tracking, scratch, action globals and reversal storage unchanged. Authored tests
force service failure after sample requests and after effect allocation. The
successful path publishes requests only after the full wrapper succeeds.

`step_presentation` now supports AA50 without movement context. A196 remains a
contextual callback that executes idle before returning; these callbacks must
not be conflated. Trace validation distinguishes AA50 used inside movement from
AA50 selected by presentation.

## Original/native comparison

**138,149 cases pass per debug/release/sanitize preset**, with identical native
output hashes: 135,585 wrapper/word/mode boundary cases, four callback-only
cases, 768 authored-terrain and 1,792 cataloged-terrain cases. Thirteen independent
goldens cover return-only retention, inactive gating, coordinate wrap/sentinel,
both facings, callback-only initialization, same-call landing and sample requests.
All 65,536 coordinate/selector words and all 256 mode × 256 countdown combinations
are exercised. Two invoked-unknown-selector cases reject in both implementations.

Restricted Musashi executes original bytes through the actual RTS, with explicit
read/write ranges for control+1A6 and +42/+44. No patch, stub or fabricated return
is used. The prior scheduler mode still stops before F906/F90C. New transport
modes `--dispatch` / `--dispatch-sequence` take 47 fields: action mode's 43 plus
service identity, tracking selector and coordinates. Outputs append those four
fields. Sequence mode retains actor/service/tracking coordinates and asserts
subsequent columns; controls, parameters, globals, mailbox, terrain scratch and
the tracking selector remain explicit environment inputs.

The transport lacks reversal storage and rejects allocation; the C++ wrapper
supports both action and reversal contexts. Their combined original/native
movie contract is still separate work. No audio playback or shared-world replay
is implied. Fresh regression totals, exact reports/hashes and commands are in
`re/dispatch_validation.json` and [[05_Validation/RESULTS]].

## Full-machine execution from the user's recording

Frozen worker build:
`6caddf552236e2538cef28557605012c6f18f00807e4d1dca9ec1b0c63db89c6`.
Original BK2 SHA-256:
`c1db675318d4e8b1527f8161fa4b782fe96f1ce4e47f173b66ae782a01b327fd`.
5298-row input digest:
`34434f0aa0b1ebc7dbf4e464cd044ac52436b944bf6a01cdc24c811e1f6c3a88`.

`tools/genesis_dispatch_capture.py` validates **191 ordinary calls** in
[1608,1690) and [3230,3339), plus **72 calls in the two explicit input branches**
from the previous action pass. There are zero RAM/register/ROM edits. Each call
also passes intermediate presentation and selected-handler comparisons; those
checks are phases of the same call, not additional game frames. Actor and tracking
outputs persist across each native sequence.

All 263 selected services return through F90C. The first ordinary window returns
to 5F3A (call at 5F34); level gameplay and the branches return to 07EC (call at
07E6). Both call F8F2. Capture hooks the exact caller return and checks SP+4,
owner registers, selected service A0, F90C stack word, tail order, uncontracted
writes and continuity. Overflow, missing phases and unknown services reject.

All four endpoints match fresh independent unhooked workers:

| Boundary | Covered-state SHA-256 |
| --- | --- |
| Ordinary 1690 | `1baf0e12950348021cfa0a44d71a70728f9c9a324532058198a141fb1791db2f` |
| Ordinary 3339 | `0b457909f71de875506844ea091199f66492e77c5767b8af272683a365008fbb` |
| Sample/down-jump branch 3318 | `f2aaba7fd7ab1459b42deb9433b5cc616e38c3f2adedc26696e6747abb2114a0` |
| Up-jump branch 3270 | `4fe1d86467ef6a156f342ebf710912e94787adbef3ec609952d276dc22941737` |

These are exposed-state hashes, not hidden-device equivalence. The movie windows
contain active P1 actors with selector zero; inactive/sentinel evidence comes
from authored tests and restricted original execution. Terrain endpoints agree;
no all-transient-terrain-write claim is made. Final report:
`local/generated/dispatch-movie/run-zefqb8xw/report.json`.

## Remaining selectors and next task

A fresh complete recording survey observes **4,139 F90A service selections**, all
12646, and matches the recorded unhooked final baseline. This is selected-PC
discovery, **zero additional native comparisons**, and does not establish other
modes/multiplayer schedules. Report:
`local/generated/movie-survey/run-gxfthj5e/report.json`.

Unimplemented selected handlers remain: 710E at 1516, 7126 at 1517–1532, 632A at
1743–1758, 51C8 at 3403–3577, 5132 at 4807–5021 and 5188 at 5022–5037. Every
observed presentation callback identity is now mapped, but this is not complete
controller coverage.

**Next bounded task: reconstruct 710E/7126 at frames 1516–1532**, starting with
A148 and the tail at 13208, FF0B90, control+A2/+A4 and mode FF33E0. The static lead
`local/generated/scheduler-research/710e.txt` is discovery only; derive complete
called effects and transition boundaries before implementing it. General world
allocation/owner destruction, shared timers, request consumption, rendering and
sound remain open. No further user recording is needed.
