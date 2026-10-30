---
id: SESSION-2026-10-29-057
type: session
status: completed
---
# Public mirror of the reverse engineering project

Started clean at `1000146a0e4a7e159f80796e93d142c6e1bf44a7` on
`work/airborne-update` (session 056's banked checkpoint), with an empty index,
no stash and no merge/rebase/cherry-pick/revert operation. A side pass at the
user's request: no native code, ROM, capture or external tool was touched, and
session 056 stays the current native handoff.

Intended checkpoint: `Add the scrubbed public mirror of the project`.

## Request

The user asked for a second Git repository that tracks only the reverse
engineering of the game, keeping the Obsidian notes (including the modification
requirements), leaving out their mod and any commits or notes containing their
name, and named the public GitHub repository
`reverseengineeringgameswithai/Wiz-n-Liz-Reverse-Engineering-Project` (empty,
already logged in through `gh`). They then confirmed that no mod exists yet, so
the whole committed project is in scope.

## Findings that shaped the export

- All 58 private commits carry the user's name as author, so no private commit
  can be published; the mirror starts fresh history.
- The name occurs in 34 tracked files: home-directory paths in 17
  `re/*_validation.json` records and 17 notes (15 session handoffs,
  [[09_References/GENESIS_DEBUGGER]] and [[09_References/KEV]]), plus the local
  author name in two of those session notes. No recorded hash covers any of
  these files, so scrubbing them breaks no evidence chain. Dropping them would
  have lost those handoffs, references and records, so they are scrubbed.
- Tracked ROM-derived content is limited to small constants (for example a
  48-byte palette in two validation records) and addresses, as the project
  rules already require; no file matches the ROM's SHA-256 or exceeds 2 MiB.

## Work

Added `tools/public_mirror.py`, `tests/test_public_mirror.py` (six synthetic
cases) and [[02_Workflow/PUBLIC_MIRROR]]; recorded the authorization in
`START_HERE.md`, `README.md`, [[00_START_HERE]], [[01_Project/MASTER_BRIEF]] and
[[02_Workflow/GIT_RULES]]. A dry run into a scratch repository exported 526 files
from `1000146` with no identity term left; the changed lines are only `~`
paths and two `[author]` placeholders.

After this checkpoint, the mirror is created at ignored `local/public-mirror/`
with the account's noreply identity, exported from this checkpoint and pushed to
`main`; the result is reported to the user, not written here (the private
checkpoint cannot name a later commit).

## Validation

`check-vault`, `check-hygiene` and all Python tests are run on this checkpoint
before committing, and again inside the exported mirror. Native presets were not
rebuilt: no native source changed.
