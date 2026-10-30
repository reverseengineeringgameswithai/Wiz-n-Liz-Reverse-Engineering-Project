---
id: WORKFLOW-CHECKLIST
type: workflow
status: active
---
# Pass checklist

Follow [[00_START_HERE]]; this checklist is an execution aid, not another policy.

- [ ] Read entry points, current status/next actions, latest handoff and task.
- [ ] Confirm root, branch/HEAD, staged/unstaged/untracked paths and operation state.
- [ ] Stay inside [[02_Workflow/PROJECT_BOUNDARIES]]: no reads, queries or
      baselines of other home-directory projects.
- [ ] Record pre-existing work and ROM identity before processing.
- [ ] Select a bounded deliverable with concrete acceptance criteria.
- [ ] Implement/research with reproducible evidence and scoped outputs.
- [ ] Recheck original identity; run relevant tests and distinguish skips/failures.
- [ ] Review changed code/metadata and `git diff --check`.
- [ ] Run `check-vault` and `check-hygiene`; inspect actual indexed paths.
- [ ] Promote findings; update status, tasks, blockers and short next actions.
- [ ] Write a session handoff with commands, starting state, failed approaches,
      limitations and intended commit subject.
- [ ] Stage explicit owned paths; inspect staged diff and protected-content checks.
- [ ] Commit when safe/configured; do not include another person's staged work.
- [ ] Verify final Git status and stop temporary processes.
- [ ] Report completed work, evidence/tests/skips, native playability, reference
      dependencies, commits/tree state, notes and the exact next task.
