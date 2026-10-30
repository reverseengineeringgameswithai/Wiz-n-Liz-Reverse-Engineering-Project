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
  held back by subject. Licensing: [[06_Decisions/ADR-0002-project-license]]
  (MIT; `LICENSE`, `NOTICE.md`, `CONTRIBUTING.md`).
- Nothing Git ignores: never `Original_Game/`, `local/` (extracted assets,
  disassembly, captures, recordings), builds or Obsidian workspace churn.
- Fresh history in the mirror, one commit per sync, authored by the
  `reverseengineeringgameswithai` account's noreply address.

## The user's name never reaches GitHub

The user requires that their name, handles and email never appear in the
public repository. Three independent layers enforce it:

1. **Export.** The home-directory path becomes `~`; this repository's Git name
   and email become `[author]` and `[email]`; every term in the local,
   multi-valued `mirror.forbid` setting becomes `[redacted]`. The export then
   refuses any remaining occurrence (case-insensitive, even inside a longer
   word, in paths or content), any file whose SHA-256 equals the ROM's and files
   over 2 MiB. Commits refuse an author or message containing a term.
2. **Pre-push hook.** `local/public-mirror/.git/hooks/pre-push` scans every
   commit a push would add (author, committer, message, every path and blob)
   and refuses the whole push on any term, however the push is started.
3. **Pinned account.** The mirror's local credential helper always
   authenticates as `reverseengineeringgameswithai`; the user's personal
   account is not a collaborator, so it could not push there anyway.

Blocked terms live only in this repository's untracked `.git/config`
(`git config --get-all mirror.forbid`). Never write them in a tracked file,
commit message or note: an export would redact them, and a substring would
block the sync. Add a term with `git config --local --add mirror.forbid <term>`.
The user should not comment, open issues or pull requests, or star the
repository from their personal GitHub account: that activity is public.

## Sync

The mirror working tree is the ignored `local/public-mirror/`, a separate
repository with its own `origin`, branch `main` and local mirror identity.
**Standing authorization (2026-10-29):** the user asked that this GitHub
repository be used going forward and that agents push whenever needed. After
every reviewed, committed checkpoint, sync and push as the last step of the
pass, once the export's checks pass; never push uncommitted or mid-review work.
This repository stays the working copy: its tools write home-directory paths
into evidence, and the export is what removes them.

Never force-push. A rejected push means someone changed GitHub directly (a web
edit or a merged pull request): fetch it, bring the change into this repository
as a reviewed commit, then sync again, because an export replaces the whole
mirror tree and would otherwise revert it.

Sync and push:

```sh
python3 -B tools/public_mirror.py local/public-mirror --commit "Sync: <checkpoint subject>"
git -C local/public-mirror show --stat HEAD
git -C local/public-mirror push origin main
```

`tools/public_mirror.py` exports with `git archive`, so uncommitted work never
reaches the mirror; it replaces the mirror's whole tree and stages it with
`git add --all`, which is safe only because the tool alone writes that tree.
The pinned helper borrows the account's token per push and never switches the
active `gh` account. Tests: `tests/test_public_mirror.py`.

## If the local mirror is missing

```sh
git init -q -b main local/public-mirror
git -C local/public-mirror remote add origin \
  https://github.com/reverseengineeringgameswithai/Wiz-n-Liz-Reverse-Engineering-Project.git
git -C local/public-mirror config user.name reverseengineeringgameswithai
git -C local/public-mirror config user.email \
  350059656+reverseengineeringgameswithai@users.noreply.github.com
git -C local/public-mirror config credential.https://github.com.helper ''
git -C local/public-mirror config --add credential.https://github.com.helper \
  '!f() { GH_TOKEN="$(gh auth token --user reverseengineeringgameswithai)" gh auth git-credential "$@"; }; f'
python3 -B tools/public_mirror.py local/public-mirror --install-hook
git -C local/public-mirror fetch origin && git -C local/public-mirror reset -q origin/main
```

The empty helper clears the global helpers for the mirror only. The final
`reset` (mixed, in the mirror only) adopts the published history without
touching files; then run the sync above. If `mirror.forbid` is also missing
(a new clone of this repository), ask the user for the terms to block before
any push; never guess them.
