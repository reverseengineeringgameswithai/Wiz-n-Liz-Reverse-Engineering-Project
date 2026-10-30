---
id: TASK-0004
type: task
status: complete
deliverable: Reproducible static identification of the original RNC2 decoder and one caller with source and destination dataflow
acceptance: ["Candidate decoder entry and one caller are corroborated with original-68000 decoding and header/stream accesses", "ROM identity, address spaces, source ranges, calls, reads and writes are recorded in a stable finding", "Relationship to rnc.unclassified.0001 is established or remains explicitly unknown with a precise next experiment", "Symbols/function metadata and bounded analysis tools regenerate the evidence", "No asset meaning or dynamic execution is claimed from signatures alone"]
---
# Original decoder and resource chain — complete

All acceptance criteria were met in [[08_Sessions/2026-10-02-004-rnc-loader]].
[[03_Reverse_Engineering/findings/FIND-0007-rnc-loader]] establishes decoder
`[0x19462,0x1959E)`, the PACK wrapper/caller at `0x3CFA`, descriptor-zero pointer
chain to the first compressed block, output RAM `0xFFFF8844`, and consumer
`0x3D46`. Its two loops exactly partition the 17,714-byte output into palette,
count, 442 32-byte patterns and 442 opaque eight-byte records.

`tools/rnc_loader_probe.py`, `re/rnc_loader.json`, catalog/CSV updates and nine
synthetic tests make this reproducible. Static CFG closure covers 147 decoder
instructions; 16 selected instructions have independent GNU corroboration.
No original CPU or game was run; resource runtime selection and pixel/collision
interpretations remain unverified. The native codec is a valid-format replacement,
not a reproduction of the unsafe original ABI/malformed-input behavior.

Prior: [[07_Tasks/TASK-0003-native-rnc2]]. Next:
[[07_Tasks/TASK-0005-native-pattern-bank]].
