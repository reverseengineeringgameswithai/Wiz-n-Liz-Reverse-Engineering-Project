---
id: WORKFLOW-PUBLIC-MIRROR
type: workflow
status: active
---
# Public mirror

Authorized by the user on 2026-10-29
([[08_Sessions/2026-10-29-057-public-mirror]]): the reverse engineering project
may be published to the public GitHub repository
`https://github.com/reverseengineeringgameswithai/Wiz-n-Liz-Reverse-Engineering-Project`.
This is the only authorized publication. It does not relax the ROM rules in
[[01_Project/MASTER_BRIEF]] or [[02_Workflow/GIT_RULES]]; this repository keeps
no remote and its private history is never pushed.

## What the mirror contains

- Every file committed at the exported revision: vault notes (including the
  brief's modding requirements), `re/` evidence, `src/`, `tests/`, `tools/`,
  `third_party/` manifests and the build files. No mod exists yet; nothing is
  held back by subject.
- Nothing Git ignores: never `Original_Game/`, `local/` (extracted assets,
  disassembly, captures, recordings), builds or Obsidian workspace churn.
- Fresh history in the mirror, one commit per sync, authored by the
  `reverseengineeringgameswithai` account's noreply address.

The local identity is scrubbed: the home-directory path becomes `~`, and this
repository's configured Git name and email become `[author]` and `[email]`.
The export refuses any remaining occurrence (case-insensitive, in paths or
content), any file whose SHA-256 equals the ROM's, and files over 2 MiB.

## Sync

The mirror working tree is the ignored `local/public-mirror/`, a separate
repository with its own `origin`, branch `main` and local mirror identity.
Sync only from a reviewed, committed checkpoint, and push only when the user
asks:

```sh
python3 -B tools/public_mirror.py local/public-mirror --commit "Sync: <checkpoint subject>"
git -C local/public-mirror show --stat HEAD
GH_TOKEN="$(gh auth token --user reverseengineeringgameswithai)" \
  git -C local/public-mirror -c credential.helper= \
  -c 'credential.helper=!gh auth git-credential' push origin main
```

`tools/public_mirror.py` exports with `git archive`, so uncommitted work never
reaches the mirror; it replaces the mirror's whole tree and stages it with
`git add --all`, which is safe only because the tool alone writes that tree.
The push borrows the account's token for one command and never switches the
active `gh` account. Tests: `tests/test_public_mirror.py`.

## If the local mirror is missing

```sh
git init -q -b main local/public-mirror
git -C local/public-mirror remote add origin \
  https://github.com/reverseengineeringgameswithai/Wiz-n-Liz-Reverse-Engineering-Project.git
git -C local/public-mirror config user.name reverseengineeringgameswithai
git -C local/public-mirror config user.email \
  350059656+reverseengineeringgameswithai@users.noreply.github.com
git -C local/public-mirror fetch origin && git -C local/public-mirror reset -q origin/main
```

The final `reset` (mixed, in the mirror only) adopts the published history
without touching files; then run the sync above.
