---
id: SESSION-2026-10-23-048
type: session
status: completed
---
# Stack decision and project boundaries

Started clean at `7a30372` on `work/airborne-update` (session 047's checkpoint,
made earlier in this conversation), with an empty index, no stash and no
merge/rebase/cherry-pick/revert operation. Documentation-only pass, done at the
user's request; no code, tool, ROM or external tool was touched.

Intended checkpoint: `Decide the presentation stack and fence off other projects`.

## Requests

After session 047 reported that ADR-0001's trigger was met, the user wrote: "I'll
let you take care of the decision for me because I'm not too sure what the Thing
is here I just want the end result to be the same where it is a recompilation
effort". They also asked that WL3PC (their Wario Land 3 port, which earlier
passes had baselined read-only) be segmented properly so future agents need not
deal with it, and documented in Obsidian.

## Decisions

- [[06_Decisions/ADR-0001-presentation-shell]] is **rejected**: SDL3 stays the
  presentation layer, as briefed. The simulation is the product; one language
  and build; no godot-cpp or GDExtension boundary; the ADR's claimed advantage
  was reuse of WL3PC patterns, which the boundary request removes. The first
  SDL3 shell task will need `SDL3-devel` with the user's authorization.
- New [[02_Workflow/PROJECT_BOUNDARIES]]: this project is the repository and the
  verify-only GenesisDebug worker plus the user's recording; the BizHawk GUI
  install and its Sonic bridge are never touched; every other home-directory
  project (WL3PC included) is out of scope: never read, searched, `git`-queried,
  baselined, hashed or reported. [[00_START_HERE]] and
  [[02_Workflow/PASS_CHECKLIST]] link it.

Clarification for the record: WL3PC never interfered with this project's code
or results. Earlier passes' preservation scripts recorded its Git HEAD as a
read-only check, so its owner's commits showed up in reports. Those entries stay
in older session notes and validation files as history; from this session they
are not collected.

Updated: ADR-0001 (status and Decision section), PROJECT_STATUS, NEXT_ACTIONS,
BLOCKERS, ARCHITECTURE, ENVIRONMENT, SOURCES, FIND-0045 and TASK-0010.

## Validation

ROM SHA-256 `d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`
verified before and after; `check-vault`, `check-hygiene` and `git diff --check`
pass; the Python suite passes. No native build, capture or comparison was needed.

## Handoff

Next: **join the native P1 session to the retained world**
([[01_Project/NEXT_ACTIONS]]), continued in the same conversation. TASK-0010 is
in progress; native playability is **none**.
