---
id: FIND-0021
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# Tally palette preparation and deferred waits

Scope: verified USA ROM, P1 actor/control association, fixed palette bank 2.
[[07_Tasks/TASK-0010-grounded-controller]] remains in progress. Native playability remains none. This extends
[[03_Reverse_Engineering/findings/FIND-0020-tally-handler]]; it does not implement
palette rendering or the bonus-allocation path at 5266.

## Exact new instruction scope

`re/palette_step.json` pins five disjoint intervals, **232 bytes / 56 instructions**:

| Interval | Instructions | Effect |
| --- | --- | --- |
| `[51D0,5204)` | 10 | Nonzero-gate entry: reload associated control, coast, wait for direction zero, prepare palette, initialize transition, assign 5204 and RTS |
| `[5204,5222)` | 6 | Coast, wait for direction zero, assign 5222 and RTS |
| `[1324E,13294)` | 9 | Initialize tally transition; retain dirty flag and position fields |
| `[137CE,137F6)` | 15 | Fixed bank-2 conversion wrapper; preserve A0/A1/D1 |
| `[1372C,13754)` | 16 | Sixteen big-endian color words to sixteen B/G/R byte triplets |

The caller fixes source A0=`FFFF0EA8` and D0.W=2. The wrapper computes the signed
word destination offset `(D0*3)<<4`, giving `FFFF0DC8`, then calls 1372C with
D0.W=15. Only this fixed disjoint source/destination/count contract is implemented;
arbitrary bank indices, aliasing and arbitrary DBRA counts are not claimed.

For each raw color word, output is blue `((word>>8)&14)<<2`, green
`((word>>4)&14)<<2`, red `(word&14)<<2`. Each byte lies in 0..56 in increments of
8; unused source bits are ignored. The source remains unchanged. Destination
extent is exactly 48 bytes ending at `FF0DF8`; source extent is 32 bytes ending
at `FF0EC8`. Original D2/D3 are scratch, not preserved. The restricted harness
checks D2's actual final green value when conversion ran and the old sentinel
otherwise. No general register-ABI or device timing parity is claimed.

1324E sets direction `FFFF`, level 0, countdown 6, reload 0 and palette scope 0.
All three curve identities become the logical tally resource (original 135EA).
Dirty, requested position and saved position are retained. The curve table is
identified but is not evaluated by this component. The existing 1345A timer
remains an explicitly separate invocation.

## Return and scheduling boundaries

51C8 still branches immediately to 5222 when FF33CE is zero, retaining its
selector. For a nonzero gate, A148 returns to 51DA; for 5204 it returns to 520E.
A busy direction takes the shared 4F8C RTS with the original selected-handler
return F906 pending. An idle direction at 51D0 calls 137CE, which returns to
51F4; 1324E returns to 51FA. Assignment at 51FA ends at 5202 RTS. **5204 executes
on a later actor invocation.** Its assignment at 5218 ends at 5220 RTS, so
**5222 also executes on a later invocation**. Neither assignment consumes a tally
unit now. This differs from 51CE's already implemented immediate branch.

The conversion's nested pending return is 137EE. Relative to selected-handler
SP, 137CE/its RTS use SP-4, 1372C/its RTS use SP-20, and 137EE uses SP-16 because
three saved registers remain. Exact hooks verify these positions and the actual
wrapper return, without relying on general inferred call-stack reconstruction.

## Native implementation and failure behavior

`PalettePreparation` holds sixteen raw words and sixteen typed B/G/R triplets.
`MotionUpdate::tally_palette_wait` is appended without changing older IDs;
`TransitionCurve::tally` identifies the new curve resource. Context flows through
handler, presentation, scheduled actor and complete wrapper transactions.
Actor, palette, transition, tally, tracking, scratch and logical effects commit
only on success, including after the late service check.

Nonzero-gate 51C8 requires transition state; it requires palette state only when
preparation actually runs. 5204 needs transition state but no tally/palette state.
Unknown services, missing required contexts, coasting/continuation budgets and
5266 reject transactionally. Runtime targets contain no CPU emulator or bus
addresses. The new research `--palette` transport has 131 bounded numeric fields;
`--palette-sequence` retains the destination and mutable tally counters alongside
actor/service/tracking. Source colors, shared transition timer, controls and
terrain scratch remain explicit world inputs. Destination drift rejects.

## Independent evidence

Static decoding, exact bytes/transfer checks and a closed dependency graph pass.
Four new GNU-decoder checks pass; the earlier presentation BCHG limitation is
unchanged. Restricted Musashi execution uses original unmodified code, a fixed
bank/source guard, exact readable/writable extents and bounded instruction work.

The corpus has **214,448 original/native cases per preset**, sixteen authored
goldens, all raw color words at each of sixteen slots, all direction words for
both initial/wait handlers, both facings, signed speed extremes, coordinate wrap,
repeated invocations, activity gating and authored/cataloged terrain. These are
separate exhaustive sweeps, not all combinations of all state. All 56 new
instructions execute. See `re/palette_validation.json` for pinned results.

Two **controlled RAM-edit experiments**, not ordinary gameplay, branch from the
unchanged movie at completed boundary 3403:

| Experiment | Exact edits | Continuous P1 calls | Observed order |
| --- | --- | --- | --- |
| Ready | FF33CE 0000→0001 | 17 at `[3403,3420)` | Prepare 3403; 5204 selects 5222 at 3417; count from 3418 |
| Initial wait | Same gate; FF0B90 0000→0001, FF0B92 0000→0003, FF0B96 000E→0000; fill 48 destination bytes with A5 | 20 at `[3403,3423)` | Initial handler waits at 3403–3405; prepare 3406; 5204 selects 5222 at 3420; count from 3421 |

Each pins complete input rows, start settings, loaded binary identity and old/new
edit bytes, validates complete selected returns and rejects trace overflow.
A fresh independent worker repeats the same edits and inputs without hooks;
both declared covered-state endpoints match. The source movie and ROM are never
edited. After a direct experiment edit, the script advances explicit rows rather
than seeking/exporting an unchanged replay timeline. Palette source and other
banks remain unchanged inside each actor invocation. Native destination persists
across calls; the poisoned destination demonstrates the preparation write.

The ordinary movie still takes the zero-gate path: its 175-call tally regression
passes with five sound requests and completion at 3577. Transition/coasting
movie contracts also pass freshly with independent unhooked equality. Older
actor/effect/movie-survey results retain their historical scopes.

## Remaining scope

51C8 and 5222 remain partial because their shared common path can reach
unsupported 5266. The new 5204 mapping is bounded and complete for its selected
handler scope. Four new bounded mappings bring totals to **87 bounded simulation
mappings plus two partial tally handlers / 98 indexed functions**. Classified
bytes become **23,995 / 1,048,576**; no duplicated A148/51C8-gate coverage.

Next: reconstruct **5266's bonus-allocation path**, starting with its ED6E6 sample
request, FF0104 gate, 451A/4770 helper calls and failure/partial-loop behavior.
The local 5266 disassembly is only a discovery lead; no new allocation contract
is claimed. Later recorded selectors 5132/5188, broader world ownership, palette
consumer/rendering, P2 scheduling and audio playback remain open.


Subsequent scope: [[03_Reverse_Engineering/findings/FIND-0022-bonus-slots]] now
implements 5266 and the D2=0 helper path. Its control-table assignments supersede
the earlier allocation lead and unsupported statement above. Earlier validation
counts remain historical; no original report is rewritten.
