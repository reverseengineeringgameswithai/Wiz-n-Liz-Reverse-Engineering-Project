---
id: SESSION-2026-10-28-056
type: session
status: in_progress
---
# After the hub: session 055's validation and the second level's entry

Started clean at `d8f3059061e9f5b14dbd0eefb3c8a0d191039e87` on
`work/airborne-update` (session 055's checkpoint), with an empty index, no stash
and no merge/rebase/cherry-pick/revert operation. The user asked to start the
next task. The user's BizHawk GUI (a Sonic session) was running and was left
untouched. Authorized local implementation, validation, vault sync and reviewed
local commits; no pushes/uploads. No subagents; no external tool changes;
[[02_Workflow/PROJECT_BOUNDARIES]] observed. The preserved recording sufficed.

Preservation baseline at pass start
(`local/generated/second-level-research/preservation.json`): ROM, BK2/recording,
worker/build manifest, 104 runtime binaries and 59 GenesisDebug sources verify.

## Session 055's validation, completed

With the unchanged tools and builds: the fresh all-in-one `game-session`
capture (`local/generated/game-session/run-s49_3nc8`) matches all 1,095 P1
calls and loops from one seed with session 055's offline digests (seed
`bc8e1384…`, output `8fab99e3…`); fresh standalone `world-session` and
`hub-session` captures reproduce session 054's digests; all nine fixtures
match on debug, release and sanitize. `re/scene_change_validation.json` is now
the full record (its `completed_in` names this session). The BizHawk source
tree's status differs from session 055's baseline outside Tools/GenesisDebug
(84 paths, not this project's; not recorded); the worker verifies unchanged.

## Survey after the hub

See [[03_Reverse_Engineering/findings/FIND-0053-second-level-entry]]: the hint
screen (1959E, 1758..2067, 301 loops), E2A (2067..2106), 754's head (2106) and
the second level's loop from 2107 (FF33E0 = 0013). 6664 is not reached; the
plan's order was corrected.

## Native work (second checkpoint, banked for a user restart)

The user asked to bank the work before restarting. Implemented and compared as
far as [[03_Reverse_Engineering/findings/FIND-0053-second-level-entry]] states:
the hint screen and the second level's entry (library, transports, reference
modes 14/15, `re/second_level_step.json`, FUNC-0184); 10,625 restricted cases
match in debug; the offline joined comparison matches the level, hub, 301 hint
loops, the entry's P1 and timer and 29 second-level P1 calls, rejects exactly at
2136, but E918's state at the entry is two draws behind. The session validator
learned the second level's fade cadence (`FADE_CONVERSIONS`, four polls), which
changes the source contract of the world, hub, mixed, effect and early/late P1
fixtures: they need fresh captures (as session 054 did).

Builds: debug current; release and sanitize must be rebuilt. Not yet run:
release/sanitize corpora, the fresh all-in-one capture, the fresh regression
captures and fixtures, the full test suite, the validation summary
(`local/generated/second-level-research/summarize.py`, which writes
`re/second_level_validation.json`).

## Resume

```sh
python3 -B tools/project.py build --preset debug   # and release, sanitize
python3 -B tools/project.py hub-compare --preset debug
```

1. Find the two uncounted E918 draws: count E918 calls (with callers) over
   1532..1758 (the scene change and the hub) and between the level's last
   counted world draw and 1532; add them to the joined run's counted draws
   (likely the scene change's inputs or the hub's loops), then rerun
   `python3 -B local/generated/second-level-research/offline_second.py
   local/generated/second-level-research/offline-0fbd1vt2` (no new capture).
2. `local/generated/second-level-research/captures.sh game` and
   `captures.sh rest`, then `fixtures.sh`, `corpora.sh`, `verify_end.py` and
   `summarize.py`; update FIND-0053, RESULTS, status and coverage; commit.

Failed attempts so far are in `local/generated/second-level-research/failures.json`
(a helper shadowing Python's `dis`; the validator's cadence; parking native
edits until 055's fixtures ran; tracing the wait-loop tops 19676/0x792; a test
name clash; external paths in 055's preservation note).

Second checkpoint commit: `Enter the second level natively (checkpoint)`.
