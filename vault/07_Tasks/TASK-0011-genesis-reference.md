---
id: TASK-0011
type: task
status: complete
deliverable: Consume isolated full-machine Genesis captures without adding emulator code to the native runtime
acceptance: ["Version ROM-specific labels and recipes with explicit confidence", "Capture a reset-reachable input sequence and compare an implemented native routine at matched entry/return boundaries", "Check deterministic independent and checkpoint replay plus actual input production", "Preserve original inputs, keep bulk artifacts ignored, and update canonical Git/Obsidian handoff honestly"]
---
# Independent Genesis reference integration

Delivered the narrow WizNLizPC `genesis-compare` client and external versioned
profile/capture/fixture workflow in BizHawkOpenSource. Actual 135-call damping
comparison, 136-frame scenarios, physical pad production and independent plus
checkpoint replays pass. See [[09_References/GENESIS_DEBUGGER]] and
[[08_Sessions/2026-10-02-010-genesis-reference]] for commands, exact identity,
evidence hashes, scope and limitations.

This completed task concerns reference integration only. It does not complete
every advanced emulator feature, native gameplay, the full controller or
scheduler. The next native task remains
[[07_Tasks/TASK-0010-grounded-controller]].
