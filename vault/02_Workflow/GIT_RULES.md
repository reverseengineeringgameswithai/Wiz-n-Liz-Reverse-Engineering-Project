---
id: WORKFLOW-GIT
type: workflow
status: active
---
# Git rules

Start by checking actual root, branch/HEAD, recent history, staged/unstaged/
untracked paths and in-progress merge/rebase/cherry-pick. Record pre-existing
changes. Initialize only in the project directory when no repository exists.
Use a local task branch when useful. Never change remotes or push without
permission. This repository has no remote; the only authorized publication is
the separate scrubbed [[02_Workflow/PUBLIC_MIRROR]], pushed after each reviewed
checkpoint under the user's standing authorization. Preserve all original
input and user work.

No `git reset --hard`, `git clean -fd`, `git clean -fdx`, `git add .`, `git add -A`,
automatic stash or blanket cleanup. Stage explicit owned paths/reviewed hunks.
Inspect the staged diff before committing. If unrelated content is staged,
isolate the workflow safely or record the commit blocker; never include it or
disturb the user's index. Do not invent identity or alter global Git config.

Never write the user's name or personal handles in tracked files, commit
messages or branch names, nor the absolute home path (use repository-relative
paths or `~`). The blocked terms are `git config --get-all mirror.forbid`.
`tools/identity_guard.py --install` adds pre-commit and commit-msg hooks that
refuse them, and `check-hygiene` fails on them; fix the text, never bypass.

Track source, synthetic tests, recipes, metadata, meaningful notes, schemas and
dependency manifests. Keep ROMs, rebuilt ROMs, bulk disassembly/assets/traces/
states, tool downloads, environments, caches, builds and personal Obsidian churn
out of normal history. Use scoped ignores; never ignore all Markdown. Verify
both ignore behavior and tracked paths. Do not rewrite history to fix exposure
without permission; report and avoid publication.

At end, commit reviewed owned code/tests/docs together if substantive and safe.
Inspect final status and record preserved dirt accurately. Ignored artifacts
are allowed. Never write a commit's own future hash into its files. The final
handoff and canonical state must agree with committed reality.
