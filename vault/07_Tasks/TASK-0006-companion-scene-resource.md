---
id: TASK-0006
type: task
status: complete
deliverable: Resolve one companion resource selected through A1 and reconstruct its first verified placement or map structure with a bounded native parser
acceptance: ["Trace the A1 selection feeding 0x3CB6 and consumer 0x3E14 from checked instruction boundaries", "Resolve at least one supported source pointer and exact decode/field extents against the recorded ROM identity", "Document field reads and meanings with uncertainty and independent decoder or execution corroboration", "Implement the verified structure as a bounded native resource with authored semantic and malformed tests; preserve unknown fields", "Connect any established pattern references to rnc.unclassified.0001 and record whether a native static scene can be composed", "Update porting map, coverage, handoff and reviewed Git checkpoint without claiming gameplay equivalence"]
---
# Follow the companion bank into placement and scene data

Prior: [[07_Tasks/TASK-0005-native-pattern-bank]]. Read
[[03_Reverse_Engineering/findings/FIND-0007-rnc-loader]],
[[03_Reverse_Engineering/findings/FIND-0008-native-pattern-bank]],
[[03_Reverse_Engineering/CONTROL_FLOW]], `re/rnc_loader.json`, and the verified
six-range disassembly under `local/generated/rnc-loader/`.

At `0x18E0` the dispatcher loads the companion into A1 independently of the
first bank. The pair loader at `0x3CB6` preserves it, optionally decompresses it,
and feeds consumer `0x3E14`. Follow this actual path; do not assume descriptor
zero alone fixes the companion pointer, or copy another game's table layout.
The consumer end, format, scene identity and complete selection bounds are
unknown. Resolve them from code/data evidence before publishing catalog entries.

Use the native RNC2 codec only after validating another compressed block's
header, lengths and integrity, with independent reference comparison. Preserve
unknown decoded bytes. The existing pattern bank provides native indexed pixels
and opaque records; do not infer collision heights from eight-byte shape alone.
Implement the first proven placement/map structure and connect established tile
references through the stable resource ID. Compose a static scene if the evidence
supports it; never substitute an invented map to pass acceptance.

Keep this bounded to one resource/consumer, not a whole-engine rewrite. Record
why composition remains blocked if the first verified structure does not yet
provide it. Afterward select a movement/collision routine and acquire independent
reference execution evidence; SDL3 input/rendering and audio are still needed
for a playable slice. No generic platformer or screenshot-based stand-in.


## Completed

[[03_Reverse_Engineering/findings/FIND-0009-companion-scene]] resolves descriptor 0 /
slot 0 conditionally to `scene.companion.0001`, with exact decoded ranges and
independent codec agreement. Native parsing preserves coordinates, state starts,
additional patterns, map attributes and opaque records; it composes a checked
1024x256 static map plane. All six native targets pass debug/release/sanitizer.
No original gameplay was executed. Next: [[07_Tasks/TASK-0007-terrain-query]].
Handoff: [[08_Sessions/2026-10-02-006-companion-scene]].
