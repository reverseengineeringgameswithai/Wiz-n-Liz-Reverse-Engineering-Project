---
id: RE-COVERAGE
type: coverage
status: active
---
# Current coverage

ROM denominator: **1,048,576 bytes**, identity [[03_Reverse_Engineering/ROM_IDENTITY]].
All intervals below are file offsets and half-open. Full-game function, asset
and scenario totals are unknown; do not replace unknown denominators with zero.

| Measure | Actual evidence / denominator |
| --- | --- |
| Segmentation assigned | 1,048,576 / 1,048,576 bytes across four segments; mostly unknown bin |
| Raw-output byte preservation | 1,048,064 / 1,048,576 bytes, verified bin slice equality |
| Whole-ROM assembled round trip | 0 runs; not attempted, no identity claim for assembly exports |
| Structural header/vector region | 512 / 1,048,576 bytes, format observation, vectors not all semantic handlers |
| Static instruction fragment | 142 / 1,048,576 bytes at `[0x200,0x28E)` |
| Referenced inline table | 108 / 1,048,576 bytes at `[0x28E,0x2FA)` |
| Raw remainder in sega2asm segmentation | 1,047,814 / 1,048,576 bytes at `[0x2FA,0x100000)`; includes separately cataloged RNC block |
| Integrity-validated RNC2 blocks | 16,497 / 1,048,576 bytes: base `[0x348B2,0x372F7)` plus companion `[0x48FD8,0x4A604)` |
| Resource code, first descriptor and PACK tag | 900 / 1,048,576 additional disjoint bytes; six routine ranges (862), first descriptor (34), tag (4) |
| Companion code/tag | 476 / 1,048,576 additional disjoint bytes: consumer 288, helper 44, column fragment 140, PACK tag 4 |
| Terrain query/contact code | 348 additional disjoint bytes: six bounded routines (304 bytes), duplicate contact fragment (44 bytes) |
| Movement/ownership code | 650 additional disjoint bytes: eight routine mappings in nine fragments (260), six static-only context fragments (390) |
| Airborne/landing code | 706 additional disjoint bytes: eight routine mappings (654), two bounded idle initializer fragments (52) |
| Grounded actor code and request boundary | 1,426 additional classified bytes; 1,542 pinned bytes overlap 116 previously static idle bytes |
| Presentation/callback code and dispatch phase | 364 additional disjoint bytes, seven routine mappings plus a bounded caller fragment |
| Fast reversal/effect execution | 576 new disjoint bytes / 119 instructions, including two bounded effect-dispatch phases |
| Up/down actions and mailbox service | 412 new disjoint bytes / 81 instructions; twelve bounded mappings in thirteen ranges |
| Return-only selector and actor-wrapper tail | 52 new disjoint bytes / 15 instructions; one mapping and extension of existing actor phase |
| Transition actors, coasting and shared timer | 342 new disjoint bytes / 68 instructions; seven bounded mappings |
| Deferred coasting entry/handler | 42 new disjoint bytes / eight instructions; two bounded mappings; A148 reused |
| Bounded tally paths | 210 new disjoint bytes / 48 instructions; three helper mappings and two partial handlers |
| Tally palette preparation/wait | 232 new disjoint bytes / 56 instructions; four bounded mappings and extension of partial 51C8 |
| Bonus slot selection/completion | 150 new disjoint bytes / 43 instructions; promote two tally handlers, add bounded scan and partial D2=0 selector |
| Exit tally and wait | 150 classified bytes / 32 instructions; initial 31-instruction comparison extended by secondary tally to consume the remaining branch |
| Secondary tally / score | 280 new disjoint bytes / 71 instructions plus one previously classified transfer now compared; promote 5132, add five bounded helpers |
| Physical pad conversion | 214 new disjoint bytes / 54 instructions; one stateless input mapping |
| Level banner and reference callees/data | 792 new disjoint bytes: native 106/25 instructions; research-only callees 166/46 instructions; tables/labels/font 520 |
| Effect-loop/service and render bookkeeping context | 28 new disjoint static/observed bytes / seven instructions; no added function or restricted execution count |
| Trail client, particle initializer and RNG | 288 new disjoint bytes / 62 instructions; three bounded mappings; two previously static service instructions additionally executed |
| Mixed-pool private-object audit | 308 new disjoint static bytes: 260 code / 67 instructions and 48 table bytes; no new native function or restricted execution count |
| Private handlers promoted to native | 86 previously classified bytes / twenty instructions at 7808 and 7CA4; two new mappings, zero new classified bytes |
| Table motion and input writers | 78 preclassified handler bytes / nineteen native instructions promoted; 52 new research bytes / nine writer instructions, table already classified |
| Collision helper and miss service promoted | 96 preclassified bytes / 28 native instructions; one bounded helper and one partial service, zero new classified bytes |
| Return-only object composition | Existing 67-instruction dispatch/presentation/RTS graph; 42 supported successful instructions exercised; zero added functions, instructions or classified bytes |
| F9E2 allocator and 7B9C pair initializer | 216 new disjoint bytes / 40 decoded instructions; two bounded mappings; 37 executed, three exhaustion-loop instructions static only |
| 7C26 gated-visibility pair initializer | 126 new disjoint bytes / 21 instructions; one bounded mapping; all 21 executed |
| 7772 rising pair initializer | 150 new disjoint bytes / 27 instructions; one bounded mapping; all 27 executed |
| 783A collision quad initializer | 180 new disjoint bytes / 31 instructions; one bounded mapping; all 31 executed |
| 6EC8/6EDC dormant initializers and `[6886,68A4)` setup fragment | 70 new disjoint bytes / 15 instructions; two bounded mappings and one mapped fragment; all 15 executed |
| 6A94/6AF0/6B44/6BB2/6EB6 and `[68A4,68BC)` setup fragment | 364 new disjoint bytes / 92 instructions; five bounded mappings and one mapped fragment; all 92 executed |
| 7DB8/CB72, CB9A, 6EF0 gate, 6BD6, two message strings and `[68BC,68C4)` | 373 new disjoint bytes / 82 instructions; two bounded and two partial mappings, one mapped fragment; all 82 executed (CB9A's 32 research-only rendering) |
| 7FBE/7154/735E/7568 gated pairs and `[68C4,68D4)` | 512 new disjoint bytes / 110 instructions; four bounded mappings and one mapped fragment; all 110 executed |
| 6C00 pickup hit, 6D22, 6CDA, 6CF4, 59BC, 5964, FB06 | 564 new disjoint bytes / 115 instructions; six bounded and one partial mapping, 6BD6 promoted to bounded; all 115 executed |
| 7910 probe hit (fruit delivery), 59AE | 180 new disjoint bytes / 40 instructions; two bounded mappings; all 40 executed (7A56, already classified with the 7A46 writer fragment, executes too) |
| callback79B6 and 7AD6, first-ingredient paths | 154 new disjoint bytes / 29 instructions; two partial mappings (their FF31AC-nonzero paths reject); all 29 executed, with the already classified `[7A46,7A58)` tail |
| Second ingredient, spell countdown and 7CC8 producer | 318 new disjoint bytes / 73 instructions; 79B6 and 7AD6 promoted to bounded, 7CC8 bounded (its already classified 34-byte writer gate now native), 7B42 partial (13294 rejects); all 73 executed |
| The spell's completion: 13294, 7B58/7B8A, 7E18/7ED6, recipe 8652, 7F08/7F6A, 6F02's door path, 6FB6/6FCA/705C, 4C08/4C34, 95EE, the recipe and sign tables | 1,671 new disjoint bytes: 1,012 code / 219 instructions, 631 recipe-table and 28 sign-table bytes; 7B42 promoted to bounded, nine bounded and five partial mappings added, 6EF0's partial extended; all 219 executed |
| Entering the exit door: 7082 and 4CA2 | 152 new disjoint bytes / 29 instructions; 4CA2 bounded, 705C's partial extended; all 29 executed (59BC, FAA4 and the 7152 RTS already classified) |
| The scene after the level: 63A4, 60E6/611E/6334, 61F6/621A/623C, 17298, FA8C, FAC4, the 639A table and three hub fragments | 876 new disjoint bytes: 866 code / 185 instructions and the 10-byte number table; nine bounded and one partial mapping, three mapped fragments (`[5E86,5E8E)`, `[5F5E,5F76)`, `[6024,6040)`); all 185 executed |
| After the hub: 14E3C, the hint loop's test, E2A's anchor clear, 118C's FF33D8 and 9952 re-entry, FF33E0 = 0013 (five fragments) | 182 new disjoint bytes / 38 instructions; one bounded mapping (14E3C) and five fragments; all 38 executed in the debug corpus (E918, 13208, 9880/9952 and 16EA4's pieces already classified) |
| The scene change: 17024, F850/F872/F940, 131C2, 9880/98DE/9952, five fragments and four research-only callees (1720C, 1737E, 446C, 17284) | 692 new disjoint bytes of 966 / 190 instructions (274 bytes, 54 instructions previously static-only in FIND-0011's movement fragments); five bounded and three partial mappings; all 190 executed |
| Remaining unclassified bytes | 1,015,539 / 1,048,576 after disjoint classified ranges |
| Function entries indexed | 184 / unknown game total; 162 bounded simulation mappings and 13 partial mappings, eight resource mappings and partial reset; two idle initializers, four setup, three hub, five scene-change and five second-level fragments and one actor and two effect-dispatch phases remain fragments |
| Static semantic understanding | Resource/scene layout, terrain/contact, paired actor ownership and horizontal/airborne movement, landing and presentation scheduling; full controller/device timing unknown |
| Original routines mapped to a native replacement | 1 RNC2 format replacement, 4 partial resource/palette/map mappings and 162 bounded simulation mappings plus 13 partial mappings, two initializer fragments, four setup, three hub, five scene-change and five second-level fragments and one actor and two effect-dispatch phases / unknown total; full ABI/device effects excluded |
| Gameplay-related functions reconstructed natively | 162 bounded simulation mappings plus 13 partial mappings, two initializer fragments, four setup, three hub, five scene-change and five second-level fragments and one actor and two effect phases / unknown total; no complete player controller |
| Original game functions differentially tested | 162 bounded simulation mappings plus 13 partial mappings, nineteen fragments and one actor and two effect phases / unknown total; 2,876 cumulative scoped successful instructions, including six sound-gate, 78 rendering (46 banner, 32 CB9A) and nine writer-fragment research-only instructions; twenty-six-corpus union 1,787 (session 046, the `[7A46,7A58)` tail in the ingredient corpus) plus the spell corpora's 73 new and the six 7CC8 writer instructions they now execute the completion corpora's 219, the door entry's 29, the hub corpora's 185, the scene change's 190 (41 research-only: 1720C, 1737E, 446C with its 5D6A glue and 17284) and the second level's 38: 2,527 by composition (all corpora were not rerun together) |
| Native codec components | 1 RNC2 decoder mapped to original `0x19462`; 49 synthetic + 2 ROM comparison cases, not a function-coverage denominator |
| Decoded resource blobs | 2 / 134 header candidates; candidate count is not a proven asset total |
| Assets with understood container/consumer role | 2 / unknown total: base bank (442 patterns) and companion scene (136 patterns, coordinates, map); coordinate roles pending; per-column terrain contact use verified |
| Native asset/map components | 3: RNC2 codec, pattern bank/atlas, companion scene/parser/compositor; not gameplay coverage |
| Native static scenes | 1 map plane / unknown total; all 4096 cells and 262,144 pixels checked against an independent source-derived model |
| Original gameplay reference exercised | Fresh `[1066,1100)` mixed capture: 34 retained P1/emitter calls, 136 trail/twelve reversal/136 private/34 table/34 collision/170 return-only updates, nine allocations/releases; 565 spawn/update/release events plus 68 inactive observations; full free-stack order matches all native presets from one seed. Zero external reservations in this measured window; all eighteen initially occupied entries typed, including two dormant. One independent unhooked replay; same capture reused for native comparisons. Older 390-call P1 fixture freshly rerun; no whole-world/frame parity. Fresh frames 0..1066: 65 F9E2/32 F994 calls, the `[6886,68D4)` setup (prefix, tail, message step with MIX THOSE FRUIT shown at VRAM E00E, and the gated-pair step with all four gates closed) both ordinary 6C00 hits (780, 980) with all 62 hit-pickup walks to their releases, all nine 7910 hits (823 delivers; 824..831 return) with all 60 later walks of the sparkle and the copy to 853, and the copy's 853 first-ingredient walk with all 213 later walks of slot 67 as the table object (6EC8, 6EDC, 7772, 783A, 6A94 and two 6EB6 runs) plus two 7B9C and two 7C26 runs with exact write audits, sixteen setup slots (67..52) followed through 432 walks; native comparisons stop before unsupported paths: the 783A probe after 189 walks (hit7910 at 823), slot 67 after 219 (7AD6 copy at 853), the tail after 146 (6C00 pickup hit at 780, which also converts link 53); twelve slots reach the 1066 seed; the mixed seed carries the FF31C0 anchor. The retained world (session 047) then runs the whole setup and all 432 object loops (634..1065) natively in one pool: 5,732 walk updates, 33 births, both hits, the delivery and the first ingredient, with supplied P1 tracking/owner position, external E918 counts and message-producer updates; no whole-machine parity. Session 049 joins native P1 from 669: a fresh P1 capture matches all 397 P1 calls and 397 joined loops with P1's own tracking and position (634..668 still supplied during the level-start fade). Session 050 schedules that fade: a fresh P1 capture of 634..1066 matches all 432 timer states, P1 calls and object loops with no supplied loops. Session 051 extends it with fresh P1 and world replays of 634..1433: all 799 timer states, P1 calls and object loops match natively through P1's reversal effect (1067), the second delivery (1103), the second ingredient (1133) and 299 7CC8 calls with 46 exchanges. Session 052 extends it to 634..1515: all 881 timer states, P1 calls and object loops through 13294, the completion (recipe 8652), the sparkle's 31 particles and the door's puff and opening. Session 053 extends it to 634..1533: P1 enters the door at 1515 and its exit fade ends the level at 1532 (FF33E0 = 7); all 899 timer states, P1 calls and object loops match. Session 054 runs the scene after the level from its door setup: a fresh capture of 1562..1759 matches the setup's 24 objects, all 196 P1 calls, timer states and pool images (P1 entering door 0 at 1742, the scene's end at 1758) from one P1 seed. Session 055 makes the scene change native: one native run from the level's setup through the scene change and the hub matches 1,095 P1 calls and loops from one P1 seed at 634, P1 never reseeded (compared offline first, then by session 056's fresh all-in-one capture and its fixtures on every preset) |
| Audio driver / sequencer reconstructed | 0; processor/format/timing not established |

The structurally classified prefix is 762 bytes. With both disjoint RNC blocks
(16,497 bytes), the prior 900 resource bytes, 476 companion code/tag bytes,
348 terrain code bytes, 650 movement/context bytes, 706 airborne/landing bytes
and 1,426 newly classified actor bytes, 364 presentation/dispatch bytes and
576 reversal/effect bytes, 412 action/mailbox bytes, 52 return-only/wrapper-tail
bytes, 342 transition bytes, 42 coasting entry/handler bytes, 210 tally bytes, 232 palette bytes, 150 bonus bytes, 150 exit-tally bytes, 280 secondary-score bytes, 214 input-conversion bytes and 792 banner/reference bytes plus 28 effect-loop/render-context bytes and 288 trail-client/particle/RNG bytes plus 308 mixed-pool private-context bytes plus 52 table-input writer-fragment bytes plus 216 F9E2/7B9C bytes plus 126 7C26 bytes plus 150 7772 bytes plus 180 783A bytes plus 70 6EC8/6EDC/setup-prefix bytes plus 364 setup-tail bytes plus 373 setup-message/pickup-service bytes plus 512 gated-pair/setup-step bytes plus 564 pickup-hit bytes plus 180 delivery bytes plus 154 ingredient bytes plus 318 spell bytes plus 1,671 completion bytes plus 152 door-entry bytes plus 876 hub bytes plus 692 scene-change bytes, **32,855 / 1,048,576 bytes** have scoped structural evidence;
its categories carry different evidence strengths. Raw preservation does
not imply understanding. The final split keeps the 142-byte code fragment raw
because the upstream decoder failed review; independent reset decoding supplies
annotation, not a complete function map or proof of correct reassembly.

Native codec, graphics-bank, scene, terrain/contact and movement components exist. No
temporary emulated runtime exists. Default extraction uses the project codec.
Research uses static decoders, sega2asm, isolated ScummVM codec comparison and
pinned Musashi executing the declared original routine scopes and independent
GPGX workers booting the game with its devices/sound driver. Native behavior needs
no CPU interpreter. Actual game execution and bounded physical producer evidence
now exist; no original hardware run, native sound driver or complete gameplay
equivalence is claimed. See [[09_References/GENESIS_DEBUGGER]].
See [[03_Reverse_Engineering/CONTROL_FLOW]], [[03_Reverse_Engineering/SEGA2ASM]],
[[04_Native_Implementation/ARCHITECTURE]], and [[05_Validation/RESULTS]].

The RNC2 CFG's 147/147 instructions statically reachable from its entry is a
closure check, not executed coverage. All 17,714 decoded bytes are partitioned
by the consumer-derived schema; decoded byte counts are not added to ROM-range
coverage. See [[03_Reverse_Engineering/findings/FIND-0007-rnc-loader]].


TASK-0005 adds no ROM byte ranges or function boundaries to the denominator.
It checks every pixel of one decoded bank against an independently encoded
bitplane/palette specification model, not an executed original frame. The
normal-mode display scale is diagnostic. Synthetic 1000/65536-pattern imports
prove parser/storage bounds only, not a verified increase over an original
hardware capacity. See [[03_Reverse_Engineering/findings/FIND-0008-native-pattern-bank]].


TASK-0006 adds exactly 6152 disjoint ROM bytes to classified coverage: 5676 block,
4 tag and 472 code. Its 13,700 decoded bytes are not added to ROM byte coverage.
The static preview uses 578 available patterns, 561 referenced distinct indices;
the first bank count 442 is not a capacity. Two coordinate lists and map words
are parsed. That pass did not execute entity simulation, collision response or
an original frame. See [[03_Reverse_Engineering/findings/FIND-0009-companion-scene]].

TASK-0007 adds the 348 code bytes above and six native terrain/contact mappings.
614,436 cases per preset comprise 221,220 authored relocated-state cases and
393,216 real-resource cases. These include every pixel position of the known
map plus three contact probes/one-pixel settling. All 86 routine instruction
addresses are executed; inputs are not an exhaustive multidimensional state
space, and no cycle/full-register ABI equivalence is claimed. Three malformed
address cases explicitly fail in both native tests and the reference. The native
library constitutes the first bounded M2 behavior checkpoint; playability stays
none. See [[03_Reverse_Engineering/findings/FIND-0010-terrain-query]].

TASK-0008 adds 650 disjoint classified bytes and eight native movement mappings.
Its 282,233 cases per preset include every signed speed word for damping/clamps,
26 hand-worked goldens, slopes/empty records and actual terrain sequences. All
74 new instructions execute; the movement corpus visits 149 of the combined
160 instructions, and the terrain regression covers the remaining lower probe.
Static ownership/caller fragments are not counted as executed functions. Actor
pairs were identified statically in that pass; airborne/landing was still pending
then and is covered below. Physical inputs and game boot were unverified in that
pass; the later Genesis reference supplies scoped evidence, not full scheduling. See
[[03_Reverse_Engineering/findings/FIND-0011-movement-step]].

TASK-0009 adds 706 disjoint bytes / 172 instructions: eight routine mappings
and two bounded idle initializer fragments. All new instructions execute across
415,940 cases per preset; outputs include explicit immediate idle continuations
at 0xA1BE/0xA246. That component stops before the handlers; the actor dispatcher below now consumes them. The airborne corpus
visits 246 instruction addresses; the three simulation corpora together visit
332. Sweeps cover all delay/vertical words, both landing directions and reload
helpers, not the exhaustive Cartesian state space. Native playability remains
none. See [[03_Reverse_Engineering/findings/FIND-0012-airborne-update]].


TASK-0010's first implemented pass adds seventeen bounded actor mappings and
315 newly compared instructions: 309 actor instructions plus six sound-selector
mismatch instructions executed only by the restricted reference. The 1,542-byte
actor scope includes 116 idle bytes previously classified as static callers, so
only 1,426 bytes are newly classified. The four simulation corpora visit all 647
scoped instructions. 152,093 actor cases per preset and 283 GPGX invocation
comparisons are distinct validation denominators. Presentation scheduling was
open at that checkpoint and is now implemented below. Broader frame scheduling,
allocating fast reversal, up/down actions and audio playback remain open. Full native playability remains none. See
[[03_Reverse_Engineering/findings/FIND-0013-actor-dispatch]].

TASK-0010's presentation pass adds seven routine mappings and the separately
bounded active-dispatch phase: 364 disjoint bytes / 90 instructions. 347,320
cases per preset pass, including 24 authored goldens. Fresh regressions and the
new corpus visit all 737 scoped instructions. In three ordinary user-movie
windows, 507 continuous actor outputs and 507 intermediate presentation outputs
match, with ten observed callbacks and 16 sound requests. This is continuous
actor-state parity with sampled environment inputs, not native world/frame
parity. The complete-movie selected-PC survey contributes 4,139 active P1 call
observations and zero native comparisons. Evidence:
[[03_Reverse_Engineering/findings/FIND-0014-presentation-scheduler]].


TASK-0010's fast-reversal pass adds twelve mappings and two bounded object
phases: 576 new bytes / 119 instructions. Native owner IDs and generation-checked
LIFO storage model only reversal objects. Original success/release and the active
object phases are directly executed in Musashi; exhaustion stops before F9D0.
203,586 cases pass per preset and the six fresh corpora cover 856 scoped
instruction addresses. The ordinary movie contributes 92 actor / 24 complete
effect comparisons with hooked/unhooked agreement. The older 507-call windows
were rerun successfully; source windows overlap, so counts are not unique frames.
Up/down actions, general world services and native playability remain open:
[[03_Reverse_Engineering/findings/FIND-0015-fast-reversal]].


TASK-0010's action pass adds twelve bounded mappings in thirteen ranges:
412 bytes / 81 instructions. All 146,638 cases pass per preset; seven freshly
executed corpora cover 937 scoped instructions, including six reference-only
sound guards. Up/down hold/release, deferred jumps, contextual idle callback and
shared-global/sample-mailbox effects are now native. The movie supplies 184
continuous actor calls and intermediate checks, plus 72 of each from two explicit
input branches with no state edits. Actor state persists; shared world inputs
remain external. Older up/down-outstanding statements describe earlier scopes.
That pass identified the 12646/AA50 gap and later +46 service, now resolved
for the scoped return-only wrapper by the following pass. General sound consumption and native playability remain open. See
[[03_Reverse_Engineering/findings/FIND-0016-up-down-actions]].


TASK-0010's wrapper pass adds one return-only mapping and extends the bounded
actor phase through actual RTS: 52 bytes / 15 instructions, with no duplicate
coverage for the existing AA50 initializer. 138,149 cases pass per preset;
eight fresh corpora cover 952 scoped instructions. Active gating, presentation,
selected handler/service and control-coordinate writes are now native through
F938, with unsupported-service rollback. The movie supplies 191 ordinary and
72 input-branch wrapper comparisons, with two intermediate checks per call and
four fresh unhooked endpoint matches. A fresh full-recording survey observes
4,139 return-only service selections, contributing zero native comparisons.
At that checkpoint 710E/7126 remained unimplemented; the following pass resolves them.
[[03_Reverse_Engineering/findings/FIND-0017-actor-wrapper]].


TASK-0010's transition pass adds seven mappings: 342 disjoint bytes / 68
instructions. 306,528 original/native cases pass per preset, including sixteen
authored goldens and every new instruction. Nine fresh corpora visit 1,020 scoped
instructions. The ordinary recording supplies 17 continuous wrapper calls and
17 separate timer calls at [1516,1533), with exact caller/stack checks and
independent unhooked equality. World palette conversion, preceding actor entry
and subsequent mode scheduling remain open. Fresh wrapper regression also
passes 191 ordinary / 72 branch calls. Older 507/92/24 movie contracts above are
historical for this pass. At that checkpoint the next selector was 632A at 1743–1758; resolved below.
[[03_Reverse_Engineering/findings/FIND-0018-actor-transition]].


TASK-0010's coasting pass adds two mappings: 42 bytes / eight instructions.
All 87,571 original/native cases pass per preset, including eleven goldens.
Ten fresh corpora visit 1,028 scoped instructions, with no duplicate coverage
for reused A148. The ordinary recording supplies one P1 initializer at 1742
and sixteen continuous wrapper calls at 1743–1758, with an independent unhooked
match. Initialization defers motion and tracking-coordinate writes. P2 entry
is observed but not compared. Both prior transition (17 actor / 17 timer) and
wrapper (191 ordinary / 72 branch) movie contracts pass freshly. Native
playability remains none. At that checkpoint 51C8 was next; its bounded tally path is covered below.
[[03_Reverse_Engineering/findings/FIND-0019-coasting-handler]].


The tally pass adds **three bounded helpers and two partial handlers**, with
210 bytes / 48 instructions in six disjoint ranges. Unreconstructed 51C8/5222 branches are not added to classified bytes;
the function index records entry fragments and leaves overall ends unknown.
231,475 comparisons pass per preset; eleven fresh corpora visit 1,076 scoped
instructions. The ordinary movie supplies 175 continuous P1 wrappers, five sound
requests and mode completion at 3577, matching independent unhooked replay.
Mutable tally counters persist natively. At that checkpoint 51D0 and 5266 were
explicit rejected exits; 51D0 is now covered below. Earlier coasting/transition/wrapper movie contracts pass freshly; older
507/92/24 windows remain historical. Native playability remains none.
The next palette scope is now implemented below.
[[03_Reverse_Engineering/findings/FIND-0020-tally-handler]].


The palette pass adds **232 bytes / 56 instructions and four bounded mappings**,
extending partial 51C8 without duplicating its gate or A148. Fixed bank-2
conversion, tally transition initialization and deferred 5204/5222 assignments
pass 214,448 comparisons per preset. Twelve fresh corpora visit 1,132 scoped
instructions, including six reference-only sound guards. Two RAM-edited movie
experiments supply 37 continuous wrappers with independent unhooked equality;
they are not ordinary-game observations. Ordinary tally, transition and coasting
movie contracts pass freshly. Source/destination conversion is not palette
consumer/rendering parity. At that checkpoint 5266 was unsupported and both
tally handlers remained partial; resolved below. Native playability remains none.
[[03_Reverse_Engineering/findings/FIND-0021-tally-palette]].


The bonus pass adds **150 bytes / 43 instructions**: two tally mappings become
bounded, 451A is a bounded scan and 4770 is partial for D2=0 only. Thirteen fresh
corpora visit **1,175 scoped instructions**. All 160,680 new comparisons pass in
each preset, including sixteen goldens and all new instructions. Three controlled
RAM/input experiments from movie boundary 3403 compare five, partial and zero
assignments; independent unhooked endpoints match. Ordinary tally, transition,
coasting and 191/72 wrapper regressions, plus 37 palette experiment wrappers,
pass freshly. These are control-table writes, not object allocation. Table
consumers, 4770's alternate mode and whole-world timing remain open. Native
playability remains none. [[03_Reverse_Engineering/findings/FIND-0022-bonus-slots]].


The exit-tally pass adds **150 classified bytes / 32 instructions**, of which
**146 bytes / 31 instructions** have successful original/native comparisons.
The remaining four-byte transfer at 5166 reaches explicitly rejected 53F2 and
is not counted as a successful native instruction. One new bounded mapping and
one partial mapping bring totals to 91 bounded / two partial / 102 indexed.
348,668 comparisons pass per preset; fourteen fresh corpora visit 1,206 scoped
successful instructions. The ordinary recording supplies 231 continuous wrappers
and two sound requests; one controlled equality experiment supplies a further
wrapper. All declared endpoints match independent unhooked runs. A fresh complete
survey sees zero unregistered P1 handler addresses across 4,139 calls, but supplies
zero native comparisons. Secondary-score behavior and full native playability
remain open. [[03_Reverse_Engineering/findings/FIND-0023-exit-tally]].


Secondary tally adds **280 new bytes / 71 instructions** and executes the existing
5166 transfer, bringing the successful corpus union to **1,278 instructions**
across fifteen corpora. Native/original score comparisons: 328,916 per preset.
Four controlled branches compare eleven wrappers, three sample requests and six
threshold advances; independent unhooked endpoints agree. No ordinary score hit,
full-frame parity or playability is claimed. 5132 is promoted and five helpers
added: **97 bounded simulation mappings / one partial / 107 indexed functions**.
[[03_Reverse_Engineering/findings/FIND-0024-secondary-score]].


Physical input/session integration adds **214 new bytes / 54 instructions**,
one bounded mapping, and a native composition of the existing wrapper. All
256 raw input bytes with four prior fills compare in every preset. Fresh
six-corpus regressions plus conversion visit 864 instructions; the cumulative
session-024 union plus conversion is 1,332, not all rerun this pass.

The unchanged movie `[3100,3200)` drives a native session using one initial seed
and 100 physical held sets, zero per-call world feeds. Actor/control/tracking/
scratch and four requests match in every preset. Independent unhooked endpoints
agree. All 892 scratch writes belong to P1; immutable terrain/shared-input guards
are enforced with per-frame write traces. Other world phases and rendering/audio
remain outside scope. **98 bounded mappings + one partial / 108 indexed**;
native playability none. [[03_Reverse_Engineering/findings/FIND-0025-p1-session]].


TASK-0010's banner/session pass adds one native mapping (25 instructions), plus
46 reference-only renderer instructions and declared tables/data. New bytes
are 792 disjoint; see `re/level_banner.json`. All 71 execute in restricted
comparison, but only request arguments/shared scratch are compared natively.
66,880 cases per preset, 367 earlier one-seed wrappers per preset, 367 banner
requests and twelve sounds pass. The seven sanitized regressions plus banner
have a fresh union of 935 instructions. Cumulative 1,403 includes earlier corpora
not rerun here. No function or frame completeness inferred from these unions.


Latest session composition: [[03_Reverse_Engineering/findings/FIND-0027-retained-reversal-session]].
The 28 new static context bytes extend the early effect loop through its +46
service/slot walk and identify a no-op rendering clear. They are not a new native
function or additional restricted comparison coverage. Fresh reversal corpus is
203,586 per preset; input/banner/dispatch/presentation/actor/airborne/movement/
terrain run in sanitize. Fresh union is 1,054; cumulative 1,403 remains historical.
Dedicated P1 allocation is implemented; general shared-pool capacity/order is not.


The trail-client pass adds **288 disjoint bytes / 62 instructions / three
bounded mappings** at 6D8C, 5A9A and E918. 5AE2 is the initializer's return tail,
not an additional disjoint function. Original execution also visits previously
classified 69BC and 69C0; cumulative successful scope becomes **1,467
instructions**, while ten freshly run corpora cover **1,118**. No whole-ROM
instruction denominator is known. 209,082 cases pass per preset; an ordinary
34-frame movie interval supplies 34 retained emitter updates, eight allocations,
sixteen random calls and 97 newborn particle updates. All three presets reuse
one fresh capture and independent unhooked replay; four lifetimes complete,
four partial. Existing live particles and shared-pool scheduling are not native
world parity. Totals are 102 bounded mappings plus one partial / 112 indexed;
4770 remains partial. See
[[03_Reverse_Engineering/findings/FIND-0028-trail-allocator-client]].


The mixed-pool pass adds no native function mapping: **102 bounded plus one
partial / 112 indexed** remain. Five exact static audit ranges classify 260
additional code bytes / 67 instructions, plus a 48-byte private-motion table.
These are omitted-object context, not restricted-original comparison coverage.
The cumulative executed union stays 1,467; ten fresh corpora cover 1,118. Native
composition newly compares full shared free-stack order, seeded live particles,
P1 owner position and RNG over 34 physical-only subsequent inputs. All 136 trail
updates include the initial four particles' 39 updates; twelve reversal updates
and nine allocations/releases match. Thirteen external reservations retain
occupancy only and remain an explicit parity exclusion. See
[[03_Reverse_Engineering/findings/FIND-0029-mixed-object-pool]].


The private-object pass promotes **86 already classified bytes / twenty
instructions** at 7808/7CA4 into two native mappings: **104 bounded plus one
partial / 114 indexed**. Byte totals remain 26,205 classified / 1,022,371
unclassified. 277,232 comparisons pass in each preset; eleven freshly run
corpora visit 1,138 instructions, cumulative successful scope becomes 1,487
(partly historical). The ordinary mixed comparison adds 136 private updates,
bringing ordered events to 327; all gate writers are absent in this window.
Four reservations become native, nine remain. Nonzero gate branches are covered
by restricted execution, not ordinary movie observation. See
[[03_Reverse_Engineering/findings/FIND-0030-private-object-updates]].


Session 031 ([[03_Reverse_Engineering/findings/FIND-0031-table-motion]]) promotes
7A88's 78 preclassified bytes / nineteen instructions to one bounded native
mapping, with its already classified 48-byte table. The input reset and increment
fragments add 52 disjoint research bytes / nine executed instructions; they do
not implement callback79B6 or the wider 7CC8 producer. Current totals: 105 bounded
plus one partial / 115 indexed; 26,257 classified / 1,022,319 unclassified bytes.
Fresh twelve-corpus instruction union is 1,157, plus nine writer instructions;
1,515 cumulative includes historical corpora not rerun this pass. All 406,634 table
cases per preset and 34 retained table updates / 361 total mixed events pass.
Eight reservations remain. No whole-world/frame/render/audio parity or native
playability is claimed.


## Current collision checkpoint

Session 032 ([[03_Reverse_Engineering/findings/FIND-0032-collision-miss]]) promotes
AC5E and the partial 78EE miss path: 96 already classified bytes / 28 instructions.
No new classified bytes; 26,257 classified / 1,022,319 unclassified. Current
function totals are 106 bounded plus two partial / 117 indexed. Cumulative
scoped instruction execution is 1,543; fresh thirteen-corpus union is 1,185
plus nine research writer instructions (1,194). Historical counts above belong
to their recorded passes.

478,345 new component comparisons per preset and 34 collision updates / 395
ordered movie events match. All mask/gate/P2 inputs are fixed only in the
measured window; 68 P1 tracking writes come from the native wrapper. Seven
external return-only reservations remain, including inactive occupied slots.
Hit7910 and callback79B6 remain unsupported. Native playability none.


## Current return-only checkpoint

Session 033 ([[03_Reverse_Engineering/findings/FIND-0033-return-only-objects]])
composes existing active/presentation/RTS routines into retained return-only
state, including dormant occupancy. No new original function, executed instruction
or classified byte is added. Totals remain 106 bounded plus two partial / 117
indexed; 26,257 classified / 1,022,319 unclassified bytes; cumulative 1,543
scoped instructions. Fresh fourteen-corpus union is 1,185, or 1,194 including
nine research writer instructions.

286,848 original/native composition cases per preset pass. The current ordinary
pool has no external reservations and matches 633 records: 565 normal pool events
plus 68 explicit inactive observations. This does not establish initializer,
activation-producer, whole-world, rendering/audio or playability coverage.
Callback79B6 and hit7910 remain unsupported. Next F9E2/7B9C initialization.


## Current pair-initializer checkpoint

Session 034 ([[03_Reverse_Engineering/findings/FIND-0034-pair-initializer]]) adds
`[7B9C,7C26)` (23 instructions), `[F9E2,FA1E)` (14) and the static exhaustion
loop `[FA1E,FA30)` (3): **216 new classified bytes**, none previously classified.
FUNC-0118 and FUNC-0119 are bounded mappings: **108 bounded plus two partial /
119 indexed**; 26,473 classified / 1,022,103 unclassified bytes. 37 successful
instructions are newly executed in restricted original comparison, giving 1,580
cumulative; the fresh fifteen-corpus union is 1,222, or 1,231 with nine writer
instructions. FA1E..FA30 is decoded and graph-closed but never executed.

8,714 pair cases per preset pass. The ordinary frames 0..1066 replay and the
34-call mixed window are behavior evidence, not whole-world, rendering/audio or
playability coverage. Level setup, 7C26, other F9E2 callers, FA30, pool resets,
7AD6/callback79B6, overlap-hit FF31C0 readers and hit7910 remain outside scope.


## Current visibility-pair checkpoint

Session 035 ([[03_Reverse_Engineering/findings/FIND-0035-visibility-pair]]) adds
`[7C26,7CA4)`: **126 new classified bytes / 21 instructions**, one bounded
mapping (FUNC-0120). Totals: **109 bounded plus two partial / 120 indexed**;
26,599 classified / 1,021,977 unclassified bytes; 1,601 cumulative executed
instructions. The fresh sixteen-corpus union is 1,243, or 1,252 with nine writer
instructions. The ordinary frames 0..1066 replay is behavior evidence, not
whole-world, rendering/audio or playability coverage.


## Current rising-pair checkpoint

Session 036 ([[03_Reverse_Engineering/findings/FIND-0036-rising-pair]]) adds
`[7772,7808)`: **150 new classified bytes / 27 instructions**, one bounded
mapping (FUNC-0121). Totals: **110 bounded plus two partial / 121 indexed**;
26,749 classified / 1,021,827 unclassified bytes; 1,628 cumulative executed
instructions. The fresh seventeen-corpus union is 1,270, or 1,279 with nine
writer instructions. Ordinary replay evidence is not whole-world, rendering/audio
or playability coverage.


## Current collision-quad checkpoint

Session 039 ([[03_Reverse_Engineering/findings/FIND-0037-collision-quad]]) adds
`[783A,78EE)`: **180 new classified bytes / 31 instructions**, one bounded
mapping (FUNC-0122). Totals: **111 bounded plus two partial / 122 indexed**;
26,929 classified / 1,021,647 unclassified bytes; 1,659 cumulative executed
instructions. The fresh eighteen-corpus union is 1,301, or 1,310 with nine
writer instructions. The ordinary replay's unsupported 7910 hits are observed
behavior, not coverage; ordinary replay evidence is not whole-world,
rendering/audio or playability coverage.


## Current setup-prefix checkpoint

Session 040 ([[03_Reverse_Engineering/findings/FIND-0038-setup-prefix]]) adds
`[6EC8,6EF0)` and the `[6886,68A4)` fragment: **70 new classified bytes / 15
instructions**, two bounded mappings (FUNC-0123/0124) and one mapped fragment.
Totals: **113 bounded plus two partial / 124 indexed**; 26,999 classified /
1,021,577 unclassified bytes; 1,674 cumulative executed instructions. The fresh
nineteen-corpus union is 1,316, or 1,325 with nine writer instructions. The
unsupported 7AD6 copy and 7910 hits are observed behavior, not coverage.


## Current setup-tail checkpoint

Session 041 ([[03_Reverse_Engineering/findings/FIND-0039-setup-tail]]) adds
`[6A94,6BD6)`, `[6EB6,6EC8)` and the `[68A4,68BC)` fragment: **364 new classified
bytes / 92 instructions**, five bounded mappings (FUNC-0125..0129) and one mapped
fragment. Totals: **118 bounded plus two partial / 129 indexed**; 27,363
classified / 1,021,213 unclassified bytes; 1,766 cumulative executed
instructions. The fresh twenty-corpus union is 1,408, or 1,417 with nine writer
instructions. The 6BD6 miss path is native but not counted until a restricted
corpus covers it; the unsupported 6C00/7910/7AD6 events are observations, not coverage.


## Current setup-message checkpoint

Session 042 ([[03_Reverse_Engineering/findings/FIND-0040-setup-message]]) adds
`[7DB8,7E18)`, `[CB72,CC18)`, `[6EF0,6F02)`, `[6BD6,6C00)`, the two message
strings and the `[68BC,68C4)` fragment: **373 new classified bytes / 82
instructions**, two bounded mappings (FUNC-0130/0131), two partial (FUNC-0132
6EF0 gate, FUNC-0133 6BD6 miss path) and one mapped fragment. CB9A's 32
instructions are research-only rendering. Totals: **120 bounded plus four partial
/ 133 indexed**; 27,736 classified / 1,020,840 unclassified bytes; 1,848 cumulative
executed instructions. The fresh twenty-two-corpus union is 1,490, or 1,499 with
nine writer instructions.
