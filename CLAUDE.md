# Agent entry point

Read `START_HERE.md` and `vault/00_START_HERE.md`, then follow the current
handoff through `vault/01_Project/PROJECT_STATUS.md` and
`vault/01_Project/NEXT_ACTIONS.md`. Read the files; paths alone are not context.

Preserve the immutable ROM and all pre-existing work. Complete a bounded,
verified pass, update Obsidian, and commit only reviewed changes you own.
The vault contains the canonical workflow and project brief.

After each reviewed commit, sync and push the scrubbed public mirror as
`vault/02_Workflow/PUBLIC_MIRROR.md` describes. The user's name, handles and
email must never reach it: never bypass its export, hook, credential gate or
GitHub audit.

Never write the user's name or personal handles anywhere: files, notes,
commit messages, branch names or replies. Call them "the user". Write paths
relative to the repository or with `~`, never the absolute home path. The
identity guard (`tools/identity_guard.py`, its Git hooks and `check-hygiene`)
enforces this; fix the text, never bypass it.
