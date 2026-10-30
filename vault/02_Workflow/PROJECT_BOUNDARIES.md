---
id: WORKFLOW-BOUNDARIES
type: workflow
status: active
---
# Project boundaries

Set with the user on 2026-10-23
([[08_Sessions/2026-10-23-048-stack-decision-and-boundaries]]): this project is
the Git repository `WizNLizPC/` and nothing else in the home directory. Follow
this note on every pass; [[00_START_HERE]] links it.

## In scope

- This repository: `src/`, `tools/`, `tests/`, `re/`, `third_party/`, `vault/`
  and the ignored `local/` research products.
- The original ROM in `Original_Game/` (immutable; see
  [[03_Reverse_Engineering/ROM_IDENTITY]]).
- The reference tooling this project's capture tools drive, **verify only,
  never edit**: the isolated worker under `../BizHawkOpenSource/Tools/GenesisDebug`
  (its runtime manifest, 104 runtime binaries and 59 sources are hashed against
  a pass-start baseline), and the user's recording and BK2 under
  `local/generated/capture-qb2htq3j/`. See [[09_References/GENESIS_DEBUGGER]].

## Never touched, never a dependency

- The user's BizHawk GUI installation `~/BizHawk-2.11.1-linux-x64`, its Sonic
  bridge on port 19420 and any running EmuHawk session: do not deploy into,
  connect to, stop or restart them. Capture uses only owned isolated workers.

## Out of scope

- Every other project in the home directory, specifically the user's other
  ports such as `~/WL3PC` (Wario Land 3). They are separate projects with their
  own histories and agents.
- Do not read, search, build, run, `git`-query, hash, baseline or report them;
  do not cite them as evidence or design input. Their activity (commits, edits,
  running processes) is never a preservation event or a note in this project.
- Search inside this repository with explicit paths under its root; never sweep
  the home directory. When the user mentions another project, treat it as
  conversation context only.

## History

Up to session 047, pass-start baselines also recorded WL3PC's HEAD and status as
a read-only check, and the proposed ADR-0001 drew comparison figures from it.
Those entries remain in older session notes and `re/*_validation.json` files as
history and are not repeated. [[06_Decisions/ADR-0001-presentation-shell]] is
rejected; the stack stays as briefed in [[01_Project/MASTER_BRIEF]].
