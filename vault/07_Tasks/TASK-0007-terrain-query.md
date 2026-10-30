---
id: TASK-0007
type: task
status: complete
deliverable: Identify and reconstruct the original map-to-record terrain query with independently observed execution cases
acceptance: ["Validate boundaries and callers of the map lookup and record-byte lookup near 0x99F6 and 0x9A18 using the exact ROM identity", "Establish inputs, outputs, coordinate offsets, wrap rules and horizontal/vertical flag handling without guessing record meaning", "Run a narrowly scoped original-routine reference using a pinned and verified research CPU/debugger tool; keep it outside the native runtime", "Implement the verified terrain query in native C++ using SceneResource and preserved records with authored edge cases and differential expectations", "Document any unresolved collision response and keep gameplay/playability claims bounded", "Run sanitizers and complete Git/Obsidian checkpoint"]
---
# Move from reconstructed terrain graphics to native terrain behavior

Prior: [[07_Tasks/TASK-0006-companion-scene-resource]]. Read
[[03_Reverse_Engineering/findings/FIND-0009-companion-scene]],
[[03_Reverse_Engineering/ASSET_FORMATS]], `src/assets/scene.hpp`,
`src/assets/pattern_bank.hpp`, `re/scene_loader.json`, and current handoff.

The reconstructed map now links 578 patterns and their opaque records. Next
follow actual readers of effective RAM `0xFFFF4452` (map pointer) and
`0xFFFF444E` (record base adjusted for original pattern relocation).
A discovery scan found address operands at `0x99F8`, `0x9A26`, `0x9A44`, and
`0x5520`. These are **leads**, not automatically verified callers/functions.

Exploratory decode starting `0x9A18` suggests a word-indexed record address,
one byte selected by saved x modulo 8, and index reversal when bit 11 is set.
Do not infer heights, solidity, signed meaning or vertical-flip behavior solely
from this fragment. Validate the entry/callers and downstream consumers first.
The exploratory dump beginning `0x99E0` was misaligned and the end of another
slice was truncated; do not use those invalid boundaries. Evidence locations:
`local/generated/companion-research/terrain-candidate*.txt`.

Native code should query logical map cells/pattern records, not original RAM
pointers. Preserve verified arithmetic via narrow helpers where needed. Obtain
independent original-routine execution evidence, with inputs/state/ROM/tool pin
and exact commands recorded. Evaluate a project-local research CPU harness or
verified debugger-capable emulator; no hidden interpreter in the native game.
Normal builds must remain offline and no system installation is assumed.

If dynamic tooling is blocked, document the exact dependency/failure and complete
independent static/parser work without claiming the task's differential criterion.
Do not keep producing more asset galleries instead of advancing simulation.
After this query, follow real player movement/collision response and integrate
SDL3 input/rendering/audio toward a playable slice; no invented platformer.

Session 2026-10-02-007 expanded and completed the bounded deliverable with three
direct contact probes and the one-pixel downward settling step, supported by
independently executed cases. The reference harness remains research-only.

## Completed in session 2026-10-02-007

Validated entries are `0x99D4` (not the internal `0x99F6` map-pointer load) and
`0x9A18`. Native query, three contact probes and one-pixel settling are implemented
in `src/sim/terrain.cpp`. All 614,436 differential cases per preset pass, with 86/86
instruction addresses visited across six routines. 101 Python tests and 8/8
CTest targets pass in debug/release/sanitizer. Exact semantics, limits and
reproduction: [[03_Reverse_Engineering/findings/FIND-0010-terrain-query]].

Independent original execution criterion is met through pinned isolated Musashi;
no full game boot or native playability is claimed. Next:
[[07_Tasks/TASK-0008-movement-step]]. Handoff:
[[08_Sessions/2026-10-02-007-terrain-query]].
