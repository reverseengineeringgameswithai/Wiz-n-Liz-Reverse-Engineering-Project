---
id: FIND-0022
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# Tally bonus slot selection and partial completion

The 5266 path fills words in the associated control's tables. **It does not
allocate actor objects, use the reversal pool, or call a random-number generator.**
The preceding handoff's allocation/ownership language was a discovery lead,
resolved here. [[07_Tasks/TASK-0010-grounded-controller]] remains in progress;
native playability remains none. This extends
[[03_Reverse_Engineering/findings/FIND-0021-tally-palette]].

## Exact scope and state

`re/bonus_step.json` pins three new disjoint intervals, **150 bytes / 43 instructions**:

| Interval | Instructions | Contract |
| --- | --- | --- |
| `[5266,52A6)` | 16 | Request sample, set special gate, attempt up to five assignments |
| `[451A,4526)` | 5 | Scan assigned words from the beginning; stop at zero or negative |
| `[4770,47BA)` | 22 | D2=0: select an empty slot, advance/reset cursor, return source word and destination |

Existing `[52A6,52B0)` completion and ED6E6's mailbox request are reused without
duplicate coverage. **4770's nonzero-D2 branch at 47BA is still unsupported.**
Its full function end is not asserted.

| Associated control field | P1 effective RAM address | Meaning in this scope |
| --- | --- | --- |
| `+172` | `FF0802` | Assigned word table: zero empty; a negative scan result ends attempts |
| `+188` | `FF0818` | Source choice words, preserved exactly |
| `+19E` | `FF082E` | Unsigned selection count |
| `+1A0` | `FF0830` | Word cursor, mutable across calls |

The original adapter declares eleven words per table from the field extents.
This is not a verified gameplay capacity. At movie boundary 3403, count=6 and
cursor=1; assigned slots 0–4 are zero and slot 5 is FFFF. The first five source
words are 0042,004F,004E,0055,0053 (BONUS). Their consumers and visible/audible
meaning are outside this comparison.

451A retains TST's flags through RTS. Positive words continue its linear scan;
a zero permits selection; a negative ends the outer loop successfully. For each
selection, 4770 resets cursor only on equality with count, not on greater-than.
Otherwise it increments cursor with word wrap and selects
`uint16(old_cursor * 17 + 35) % count`. The high product/add bits are discarded
before division. Any nonzero assigned word is skipped, including a negative.
An empty slot receives the corresponding choice word, even if zero or negative.
Thus malformed counts/tables can make original selection nonterminating.

5266 is reached after coasting when remaining=0, skip=0, Start is nonzero,
special gate=0 and `(raw_buttons & 0x70)==0x10`. It saves D0–D3, requests existing
sample F0000 with count 200 and parameter F14, restores those registers, then
sets FF0104=FFFF. It attempts five assignments, or fewer if 451A returns negative.
It always completes via mode=3 on these successful paths. **Partial assignments
commit on a later negative sentinel; a full table still requests the sample and
sets the gate/mode.** Handler identity is retained. The existing logical sample
resource is shared with the up action; no new sound resource or playback claim.

## Same-call and return evidence

51C8's zero gate continues to 5222 and then 5266 in the same selected-handler
invocation. Relative to selected-handler stack pointer S:

| Boundary | Stack / pending return |
| --- | --- |
| A148 entry/return | S-4 / 522C |
| ED6E6 and ED714 | S-20 / 5282, with sixteen saved register bytes below caller |
| 5282 before restore | S-16; 528E after restore/gate is S / F906 |
| 451A and 4524 | S-4 / 5294; 5294 resumes at S / F906 |
| 4770 and 47B0 | S-6 / 529E, including the two-byte saved D7 |
| 529E before D7 restore | S-2; 52A0 assignment is S / F906 |
| 52A6 and 52AE | S / F906; full wrapper later returns to 7EC |

Selected traces validate these exact boundaries, scan order/flags, empty/source
selection and ordered destination writes. General inferred call/return trees
are not used as proof. Trace overflow rejects evidence.

## Native state and transactional failure

`BonusSlots` holds host-sized assigned/choice vectors, count and cursor.
`allocate_bonus` returns ordered `BonusAssignment` events and a probe count.
Optional `TallyState::bonus` is required only on the selected special branch;
other paths keep their old context requirements. All tables, gate, sample request,
actor, tracking, terrain scratch and prior contexts participate in the same
outer transaction, including a failure in the later service. Native targets
contain no emulator, bus pointers or ROM requirement.

The host bound is 4096 words per vector. Every availability read and selection
loop entry consumes the explicit `bonus_probes` budget (default 4096). Escaped
scans, exhausted work, missing context and a reached selection count of zero or
beyond either vector reject atomically. Count is validated only if selection is
reached: an initial negative sentinel can return without any division or choice
access. These checked failures are host policies, not claims of reproducing
original malformed-memory behavior. The original research adapter additionally
limits selection/scan to its declared eleven-word fields. A 100-slot native test
checks logical storage, not original capacity or memory-alias semantics.

`--bonus` and `--bonus-sequence` extend the tally transport to 91 numeric fields
and a 1024-byte line bound. The sequence asserts/retains actor/service/tracking,
mutable tally counters, assigned words, cursor and special gate. Source choices,
count, palette routing, controls and shared environment remain explicit feeds.
Outputs include exact ordered assignments, including writes of zero. Existing
transports retain their old shapes and reject 5266 without a bonus context.

## Independent validation

**160,680 original/native cases pass in each of debug, release and sanitize**:
145,320 flat/state, 4,608 authored-terrain and 10,752 cataloged-terrain cases.
Sixteen authored goldens, every cursor word, every source value, counts 1–11,
positive/zero/negative prefixes, both handlers/facings, all raw button bytes,
Start/skip/gate combinations, repeated calls and activity/arithmetic boundaries
are covered. These separate sweeps are not the full Cartesian state space.
All 43 new instructions execute. Zero divisor, outside count, escaped scan and
nontermination reject in both transports with no published row. Static exact-byte,
transfer/closure checks and four new GNU checks pass; the inherited presentation
BCHG limitation remains.

Three **controlled RAM/input experiments**, not ordinary movie hits, each run
one P1 wrapper at `[3403,3404)` after replaying the same unchanged movie prefix.
All set remaining FF0714, skip FF0F0E and special gate FF0104 to zero, then apply
genuine P1 A+C+Start through the verified input producer:

| Experiment | Additional edits | Ordered assignments |
| --- | --- | --- |
| Five | None | 4:S, 3:U, 2:N, 1:O, 0:B |
| Partial-reset | Fill slots 0–2 from source; cursor=6 | 4:S, 3:U, then negative sentinel |
| Exhausted | Fill slots 0–4 from source | None; negative sentinel immediately |

Each compares all modeled native wrapper outputs, table words, cursor, probe
count and request order. Independent unhooked workers repeat the identical RAM
edits and input row; all declared covered-state endpoints match. Edits, old/new
bytes, receipts, inputs, loaded identity and artifacts are pinned. An initial
exploratory B+C+Start input produced raw 4F and did not select 5266; A+C+Start
produces raw 1F. No initial failed branch selection is counted as bonus evidence.

Fresh ordinary tally, transition/coasting and 191 ordinary / 72 input-branch
wrapper regressions pass; the 37 controlled palette wrappers also pass.
All twelve prior corpora pass freshly under sanitizers. Thirteen corpora visit
**1,175 scoped instructions**, including six reference-only sound guards.
**164 Python tests, zero skips and 28/28 CTest targets per preset** pass.
Pinned reports and output/build/source hashes: `re/bonus_validation.json`.

## Remaining scope

Both tally handlers now have bounded native mappings; 4770 remains a partial
mapping for D2=0 only. Totals are **90 bounded simulation mappings plus one
partial selector / 100 indexed functions**. Classified bytes become
**24,145 / 1,048,576**. Table consumers, shared world/P2 scheduling, palette
rendering and audio playback remain open. Next: recorded selectors 5132/5188,
including 5132's separately gated 53F2 lead; see [[01_Project/NEXT_ACTIONS]].


Subsequent scope: [[03_Reverse_Engineering/findings/FIND-0023-exit-tally]] adds
bounded 5132/5188 behavior and 231 continuous ordinary wrappers. Its remaining
53F2 secondary-score branch is explicit; the bonus counts above stay historical.
