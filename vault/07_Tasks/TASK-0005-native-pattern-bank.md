---
id: TASK-0005
type: task
status: complete
deliverable: Native structured pattern-bank loader with independently checked pixel and palette representation and deterministic local atlas output
acceptance: ["C++20 parser consumes the verified palette/count/pattern/opaque-record ranges with explicit safety limits", "Native parsing and palette conversion have authored malformed and semantic tests independent of implementation output", "Pixel layout and color representation are corroborated with primary hardware documentation or independent reference evidence before claiming image fidelity", "The 442-pattern bank loads through stable resource IDs and produces a deterministic local inspection atlas without ROM CPU execution", "Original opaque records remain lossless and explicitly uninterpreted until their consumer is traced", "Headless sanitizer tests and Git/Obsidian checkpoint pass"]
---
# Turn the verified resource into a native graphics asset

Prior: [[07_Tasks/TASK-0004-rnc-loader]]. Read
[[03_Reverse_Engineering/findings/FIND-0007-rnc-loader]],
[[03_Reverse_Engineering/ASSET_FORMATS]], `re/rnc_blocks.json`,
`re/rnc_loader.json`, `src/core/rnc2.hpp`, and `tools/rnc_loader_probe.py`.

Implement a small resource type with 16 palette inputs, host-sized pattern
storage, and preserved eight-byte companion records. Source ROM offsets stay
in extraction metadata; runtime resources use the existing stable logical ID.
Reuse the proven 32+2+count*40 layout. Keep explicit parsing/resource limits;
442 is the observed bank size, not a hardcoded universal maximum.

The original palette routine at `0x13754` transforms input pair `[a,b]` into
`[b & 15, (b & 240) | (a & 15)]`. Preserve those arithmetic semantics; establish
display scaling and pixel order from evidence before writing an atlas renderer.
Earlier attempts to fetch complete Sega hardware manuals were blocked by
mirror/TLS/size errors; indexed excerpts alone did not establish pixel layout.
Record a usable primary reference or actual independent observation.

Emit the atlas deterministically beneath ignored `local/` as a research artifact,
not a screenshot-based game implementation. This must exercise the native
asset code. A headless image writer avoids waiting for SDL3-devel; do not choose
another game framework. No generic editor or plugin system is needed.

After this task, the next route toward playability is the companion resource
at descriptor-selected A1, consumed by `0x3E14`: scene data, placement and map
consumers, then independently observed player movement/collision behavior.
Do not replace those systems with a generic platformer or declare a tile atlas
playable. Audio and a debugger reference remain separate outstanding work.


## Completed

See [[03_Reverse_Engineering/findings/FIND-0008-native-pattern-bank]] and
[[08_Sessions/2026-10-02-005-native-pattern-bank]]. The native parser, palette
conversion and atlas now work with authored boundary/semantic tests and an
independent source-derived bitplane model. Debug/release/sanitizer PNG outputs
are identical. Opaque records stay lossless; original display response is not
claimed. Next: [[07_Tasks/TASK-0006-companion-scene-resource]].
