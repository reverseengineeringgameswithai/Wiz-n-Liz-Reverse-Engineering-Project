---
id: SESSION-2026-10-05-037
type: session
status: completed
---
# Engine analysis: should the project switch to Godot?

Started clean at `f703da0e1ea2ac022680d742ab2556a41be7811b` on
`work/airborne-update`, with an empty index, no stash and no merge/rebase/
cherry-pick/revert operation. No user changes, workers, emulator or GUI
processes. The user asked for a read-only analysis of whether to switch the
project to Godot, then asked for the findings to be recorded in Obsidian.
This is a documentation-only pass by explicit user request; no source, test,
build, tool or external file changed. No subagent touched the repository; one
web-fetch agent read the public godot-cpp README. No pushes or uploads.

Intended checkpoint: `Record the engine analysis and propose a Godot shell ADR`.

## Delivered scope

[[06_Decisions/ADR-0001-presentation-shell]] (status `proposed`): facts,
interpretation, options, recommendation, trigger and consequences. Summary:
keep the C++20 simulation; plan Godot through GDExtension as the presentation
shell instead of SDL3; decide formally at the first native frame loop or on the
user's acceptance. The engine is not what limits progress; the absence of a
public disassembly is.

Pointer updates: [[01_Project/PROJECT_STATUS]], [[01_Project/NEXT_ACTIONS]],
[[01_Project/BLOCKERS]], [[04_Native_Implementation/ARCHITECTURE]],
[[02_Workflow/ENVIRONMENT]], [[09_References/SOURCES]] and the navigation list
in [[00_START_HERE]]. The next task is unchanged.

## What was read

Entry points, status, next actions, master brief, blockers, environment,
architecture, coverage, test strategy, Genesis debugger reference, session 036,
`CMakeLists.txt`, `CMakePresets.json`, `README.md`, every header under `src/`,
`src/sim/movement.cpp`, `tools/native/terrain_main.cpp`, `tools/project.py`,
`tools/doctor.py`. Read only, outside this repository: `~/WL3PC` (README,
`AGENTS.md`, `docs/00-home.md`, current state, roadmap, workflow, ADR-0001 to
ADR-0003, architecture overview, `Makefile`, `game/project.godot`,
`toolchain.lock.json`, script line counts, Git log) and `~/.local/bin/godot`.

## Observations

- Zero SDL usage in native code or CMake; SDL3-devel still absent.
- All native code is a headless library with CLI transports; Python owns the
  differential comparisons against Musashi and GPGX. Nothing depends on an
  engine, window or audio device.
- `~/.local/bin/godot` runs the Godot 4.7.2 .NET build; WL3PC pins the standard
  build locally. Two other Godot projects exist on the machine.
- WL3PC: 178 commits in five days, 57,429 lines of typed GDScript, playable
  level at M3, built on a byte-identical public disassembly with about 81% named
  labels. WizNLizPC: 36 commits in four days, 2,657 native lines, 2.6% of ROM
  bytes classified, no public disassembly, no frame loop.
- Process weight differs: this vault holds about 118,000 words across 109 notes
  for 36 commits, and every pass re-verifies preservation of the GUI, BizHawk,
  Sonic19420 and WL3PC. WL3PC runs on a short agent file and a Makefile. This is
  an observation for the user, not a change made here.
- godot-cpp `master` README: v10 targets Godot 4.3+ via `api_version`; SCons
  shown; CMake, C++ standard and license not stated on that page.

## Validation

- ROM identity verified before and after:
  `d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`,
  1,048,576 bytes, header checksum matches.
- Existing debug CTest run on the pre-existing build: 46/46 passed in 0.92 s
  (observation only; no build was reconfigured).
- `check-vault`: 106 notes checked, no errors. `check-hygiene`: 419 indexed
  files checked, no errors.
- `project.py test` (synthetic Python only, no preset): 208 tests passed in
  1.13 s, zero skips. Native CTest and ROM-dependent tests were not requested
  because no code changed.
- `git diff --check` clean; no tabs or trailing whitespace in the new notes.

## Attempts, failures and skips

- Fetching `godot-cpp` on a `4.7` branch and `cmake/README.md` returned 404 on
  both `4.7` and `master`; only the `master` README was read. CMake support is
  therefore recorded as unverified.
- Not run: native rebuilds, release/sanitize presets, reference captures,
  movie survey, SDL3 or Godot builds. Nothing in this pass required them.

## Reproduction

```sh
git -C ~/WizNLizPC status --short --branch
python3 -B tools/project.py rom-identify --verify
grep -rli sdl src tools tests CMakeLists.txt
grep -rh '^#include' src | sort | uniq -c | sort -rn
find src -type f | xargs wc -l | tail -1
find tools/native -type f | xargs wc -l | tail -1
pkg-config --modversion sdl3 || echo "no sdl3 pkg-config"
~/.local/bin/godot --version
git -C ~/WL3PC log --format='%ad' --date=short | sort | uniq -c
find ~/WL3PC/game -name '*.gd' -not -path '*/.godot/*' | xargs wc -l | tail -1
python3 -B tools/project.py check-vault
python3 -B tools/project.py check-hygiene
python3 -B tools/project.py test
```

## Handoff

Next task is unchanged: **reconstruct the 783A four-object initializer** under
[[07_Tasks/TASK-0010-grounded-controller]]; see [[01_Project/NEXT_ACTIONS]].
The ADR waits for the user's acceptance or the frame-loop trigger; no shell
work is scheduled. TASK-0010 is **in progress**; native playability is **none**.
Original ROM, BK2/recording, GUI, Sonic19420, BizHawk sources/runtime and
WL3PC were only read. Explicit staged review precedes the local checkpoint
commit. No pushes/uploads.
