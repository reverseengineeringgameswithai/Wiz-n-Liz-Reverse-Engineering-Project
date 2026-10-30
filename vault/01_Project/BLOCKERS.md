---
id: PROJECT-BLOCKERS
type: project
status: active
---
# Blockers

Kev is an accepted research aid: [[09_References/KEV]]. Its measured errors
guide review and do not block practical use. It resolves no native
implementation blocker and adds no required dependency.

- **Native SDL platform build:** runtime 3.4.10 installed, `SDL3-devel` absent
  (rechecked 2026-10-05). Cached development packages are available; no
  privileged installation was attempted. Headless native builds/tests pass
  without it. [[06_Decisions/ADR-0001-presentation-shell]] (Godot instead) was
  rejected on 2026-10-23, so SDL3 stays; the first shell task needs
  `SDL3-devel` installed by the user or an authorized local pinned build.
- **Full-system reference resolved:** the isolated GPGX worker now provides
  reset-to-gameplay capture, selected instruction boundaries and replay checks.
  See [[09_References/GENESIS_DEBUGGER]]. Musashi remains an independent restricted
  function reference; no emulator enters the native runtime. Broader controller
  modes, hidden device state equivalence and complete scheduling remain open.
- **sega2asm semantic disassembly:** reproducible instruction errors at the pin;
  safe default exports the reset fragment as raw bytes and uses independent
  decoder evidence. See [[03_Reverse_Engineering/findings/FIND-0002-sega2asm-defects]].
- **sega2asm RNC2 decoder:** emits corrupt/short output without error. A pinned,
  sanitized independent reference successfully decodes the first block; see
  [[03_Reverse_Engineering/findings/FIND-0005-rnc-upstream-defect]].
- **GCC sanitizers:** libasan/libubsan runtime packages are absent; installed
  Clang22.1.7 compiler-rt runs both the native codec and reference ASan/UBSan checks.
- **Remaining asset semantics:** first bank's consumer and container layout are
  now known and natively parsed; normal pixel layout/channel bits are corroborated.
  One companion map now composes natively; exact display response, camera/layers,
  coordinate roles remain unvalidated. Eight-byte records now have verified
  terrain column/contact use; other consumers and full collision semantics remain
  open. Two of 134
  RNC signature candidates are validated; 132 remain unvalidated.

System Go is absent but no longer blocks sega2asm: verified Go 1.27.1 was
bootstrapped beneath ignored `local/tools/`. No global packages/config changed.

Resolved: the user supplied the Git email on continuation; name and email are
set only in this repository, allowing the foundation checkpoint commit.

Resolved in [[07_Tasks/TASK-0003-native-rnc2]]: default extraction now uses the
bounded project C++20 codec. The optional GPL reference remains isolated for
comparison; it is no longer required to extract the cataloged resource.
Resolved by [[07_Tasks/TASK-0004-rnc-loader]]: original decoder/caller linkage
and first-bank layout.
Resolved by [[07_Tasks/TASK-0005-native-pattern-bank]]: native structured loading,
source-corroborated pixels/channel bits and deterministic diagnostic atlas.
Resolved by [[07_Tasks/TASK-0006-companion-scene-resource]]: companion pointer,
format, native parser and diagnostic static map-plane reconstruction.
Resolved by [[07_Tasks/TASK-0007-terrain-query]]: isolated original CPU execution,
native map/record queries, contact probes and one-pixel settling, independently
compared across all presets. Native assets and headless simulation are unblocked.
Resolved by [[07_Tasks/TASK-0008-movement-step]]: paired actor/control ownership,
horizontal movement, damping, signed limits and all airborne-entry assignments.
Resolved by [[07_Tasks/TASK-0009-airborne-update]]: delayed/falling airborne
updates, vertical/horizontal contact, landing assignments and explicit immediate
idle continuation events.
Advanced in [[07_Tasks/TASK-0010-grounded-controller]]: supported idle/grounded,
turn/reversal/drop/jump actor invocation and same-call landing work are native.
Presentation scheduling and six callbacks now also execute natively and match
507 continuous calls from the user's movie. Fast reversal and owned effects now
also pass 92 actor calls and 24 effect updates. Up/down actions now pass 146,638
cases per preset, 184 original-route actor calls and 72 input-branch calls, with
separate intermediate presentation checks and a logical sample request. The
12646/AA50 integration and return-only +46/control-coordinate tail now pass
138,149 cases per preset and 191 ordinary / 72 branch wrapper calls.
710E/7126, A148/13208 and the shared transition timer now pass 306,528 cases per
preset plus 17 ordinary actor / 17 timer calls. The 630A/632A initializer and
coasting handler now pass 87,571 cases per preset plus one movie initializer
and 16 continuous calls. The bounded zero-gate 51C8 tally path now passes 231,475 cases per preset and
175 continuous movie calls with five sound requests. Nonzero-gate 51D0, 5204
and fixed palette preparation/initialization now pass 214,448 cases per preset
and 37 controlled-state wrapper calls. 5266 and 451A/4770 D2=0 now pass
160,680 cases per preset plus three controlled table-assignment experiments.
The bonus path uses control words, not object allocation. Bounded 5132/5188
now pass 348,668 cases per preset and 231 ordinary movie wrappers. 53F2 valid packed-decimal
score/reward behavior now passes 328,916 cases per preset and eleven controlled
wrappers. Native P1 session/input integration has since advanced as recorded
below; table consumers, broader world ownership and sound-request consumption
remain open. Physical ownership is verified for the captured
three-button producer; full controller/mode timing remains open.


Advanced in [[03_Reverse_Engineering/findings/FIND-0025-p1-session]]: the scoped
physical-input converter and one-seed `[3100,3200)` session are native and pass
all presets. General world scheduling still blocks a playable slice. The earlier scratch gap is now resolved by
[[03_Reverse_Engineering/findings/FIND-0026-level-banner-session]]: 367 movie
calls retain scratch by scheduling the level-banner writer. That checkpoint’s next step is delivered by
[[03_Reverse_Engineering/findings/FIND-0027-retained-reversal-session]]: 390
wrappers with retained reversal allocation and effect lifetime now match. At that
checkpoint shared-pool competition was observational only: 38 foreign
allocations/36 releases. The client is now reconstructed in
[[03_Reverse_Engineering/findings/FIND-0028-trail-allocator-client]]: native
6D8C, 5A9A and E918 match 209,082 cases per preset and 34 retained emitter
calls/eight spawns/97 particle updates from one fresh ordinary capture. Owner
position/capacity remain per-call context at that checkpoint. The next step is now implemented by
[[03_Reverse_Engineering/findings/FIND-0029-mixed-object-pool]]: P1 and both
particle kinds share native ordered allocation, initial live objects and RNG,
matching 34 invocations with physical-only later inputs. That checkpoint retained thirteen
external reservations. FIND-0030 subsequently promoted four 7808/7CA4 objects;
[[03_Reverse_Engineering/findings/FIND-0031-table-motion]] promoted 7A88 with
retained FF31BC and bounded loops. FIND-0032 now integrates the 78EE miss service
and AC5E helper. FIND-0033 now retains all seven return-only objects, including
two dormant occupied slots; zero reservations remain in the measured interval.
This closes the omission of those object states, not general world scheduling.
P1 tracking is produced natively; other collision/shared inputs are fixed only
in that window. FIND-0034..0039 now reconstruct F9E2 allocation, the 7772, 7B9C
and 7C26 pairs, the 783A collision quad, the 6EC8/6EDC dormant objects, the 6A94
pickups and 6EB6 control links, and the whole `[6886,68BC)` setup prefix and tail
with verified inherited fields and the FF31B4/FF31B8/FF31C0/+1A2 identities. The
ordinary movie then reaches unsupported 6C00 pickup hits (780, 980), hit7910
(823) and 7AD6 (853), which bound native continuity of the tail, slot 63 and
slot 67. FIND-0040 adds the 7DB8 setup message (CB9A as a logical render request)
and the closed 6EF0 gate; FIND-0041 adds the four gated pair initializers of
`[68C4,68D4)` (lead handlers unsupported). FIND-0042 makes the 6C00 pickup hit
native for ordinary kinds (carry, swap, vanish/release, re-dress) with an explicit
`PickupWorld`; its 020D/0205/01FD family branches stay unsupported. FIND-0043
makes the 7910 probe hit native (the fruit delivery: sparkle, copy, dormant
link); FIND-0044 the first-ingredient paths of callback79B6 and 7AD6. The setup
after 68D4, the 6EF0 allocating path, other F9E2 callers, gate/activation
producers, pool resets, P2 and callback scheduling remain incomplete. FIND-0048
makes the second-ingredient paths of 79B6/7AD6, the anchor's 7B42 countdown and
the 7CC8 producer native; FIND-0049 the spell's completion (13294, 7B58/7B8A,
7E18 with recipe 8652, the sparkle, 6EF0's allocating path, the door and sign).
FIND-0050 makes entering the door native (7082, 4CA2) and runs P1's exit
handlers in the joined session to the level's end. FIND-0051 makes the scene
after the level native from its door setup (63A4, 60E6) to its end (6024);
FIND-0052 makes the scene change native (0x488, 16EA4's resets and fade-in,
9880, 63E2, 5ED4), so the level and the hub run as one native run from one P1
seed. The terrain switch uses the hub's captured resource, and what follows the
hub (0x4A4 onward, the second level) is not native. Keep the other 104 recipes,
9288/9182, the FF31A8 path, the 95EE gates, the two-player door paths, the
active-link entry path (70FE) and the overlap-hit FF31C0 readers unsupported
until separately verified. FIND-0045 runs the whole retained world (the setup and all 432 loops
to 1066) natively with one carried `PickupWorld`; FIND-0046 joins native P1 and
FIND-0047 schedules the level-start fade, so the joined run is native from 634.
General world services and rendering/audio still block playability. No user
input needed; SDL3 availability was not rechecked. See
[[03_Reverse_Engineering/findings/FIND-0033-return-only-objects]] and
[[03_Reverse_Engineering/findings/FIND-0034-pair-initializer]] and
[[03_Reverse_Engineering/findings/FIND-0035-visibility-pair]] and
[[03_Reverse_Engineering/findings/FIND-0036-rising-pair]] and
[[03_Reverse_Engineering/findings/FIND-0037-collision-quad]] and
[[03_Reverse_Engineering/findings/FIND-0038-setup-prefix]] and
[[03_Reverse_Engineering/findings/FIND-0039-setup-tail]] and
[[03_Reverse_Engineering/findings/FIND-0040-setup-message]] and
[[03_Reverse_Engineering/findings/FIND-0041-gated-pairs]] and
[[03_Reverse_Engineering/findings/FIND-0042-pickup-hit]] and
[[03_Reverse_Engineering/findings/FIND-0043-fruit-delivery]] and
[[03_Reverse_Engineering/findings/FIND-0044-first-ingredient]] and
[[03_Reverse_Engineering/findings/FIND-0045-retained-world]] and
[[03_Reverse_Engineering/findings/FIND-0046-world-session]] and
[[03_Reverse_Engineering/findings/FIND-0047-level-start-fade]].
