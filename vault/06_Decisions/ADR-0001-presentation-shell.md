---
id: ADR-0001
type: decision
status: rejected
---
# ADR-0001: Presentation shell (Godot via GDExtension instead of SDL3)

- **Status:** **rejected on 2026-10-23**; see the Decision section. Proposed
  on 2026-10-05; not accepted then. The user asked for an
  engine analysis without changes and then asked for the findings to be
  recorded. Acceptance is the user's decision. Until then SDL3 remains the
  briefed default in [[01_Project/MASTER_BRIEF]].
- **Trigger status (2026-10-23):** the pool part of the trigger below is met:
  [[03_Reverse_Engineering/findings/FIND-0045-retained-world]] replays 432
  consecutive object loops of the user's recording natively from the level
  setup, with P1's tracking and position still supplied. The decision is now
  due; it remains the user's, and nothing was installed or scheduled.
- **Supersedes:** none. [[01_Project/MASTER_BRIEF]] requires an ADR with a
  concrete project advantage for any stack other than C++20, SDL3, CMake, Ninja.
- **Session:** [[08_Sessions/2026-10-05-037-engine-analysis]].

## Decision (2026-10-23)

**Rejected; SDL3 stays the presentation layer, as briefed.** The user delegated
the decision ("I'll let you take care of the decision for me … I just want the
end result to be the same where it is a recompilation effort"). Reasons:

- The user's goal is the briefed outcome: a native, source-buildable
  reimplementation of the game (what the user calls a recompilation effort).
  The C++20 simulation is that product; the shell only draws, plays sound and
  reads input, which SDL3 covers without a second engine.
- One language, one CMake build and one toolchain; no godot-cpp dependency, no
  GDExtension boundary across which exceptions must be translated, and no pinned
  engine download.
- The concrete advantage this ADR claimed was reusing patterns from the user's
  separate WL3PC project. The user asked on the same day to keep that project
  fully separate ([[02_Workflow/PROJECT_BOUNDARIES]]), which removes it.
- The Genesis-specific work (tile/sprite/plane rendering, YM2612/PSG audio) is
  project work under either shell.

Consequences: [[01_Project/MASTER_BRIEF]]'s stack stands; no Godot build,
godot-cpp or engine work is planned. An SDL3 application still needs SDL3
development files (`SDL3-devel` absent; [[01_Project/BLOCKERS]]), which the
first shell task must obtain with the user's authorization. The sections below
are the 2026-10-05 analysis, kept as history.

## Question

Should WizNLizPC switch to Godot, now or later, and for which layer?

## Observations (facts, 2026-10-05)

Observed on this Fedora 44 x86_64 host at commit
`f703da0e1ea2ac022680d742ab2556a41be7811b`. Commands are in the session note.

- **No platform code exists.** `grep -rli sdl src tools tests CMakeLists.txt`
  matches only the environment probe in `tools/doctor.py` and one comment in
  `tests/native_rnc2.py`. `CMakeLists.txt` has no `find_package(SDL3)`. Every
  `#include` under `src/` is a project header or the C++ standard library.
- **SDL3 development files are still absent:** `pkg-config --modversion sdl3`
  fails; runtime `SDL3-3.4.10-1.fc44` is installed. Unchanged since
  [[02_Workflow/ENVIRONMENT]].
- **Native size:** `src/` is 2,657 lines (sim, assets, core); `tools/native/`
  is 1,107 lines of CLI transports; Python tools 9,811 lines; `tests/` 6,915
  lines. The debug CTest suite (46 tests) passed in 0.92 s on the existing build.
  Error handling uses C++ exceptions (117 `throw` sites), which matters for any
  foreign-function boundary.
- **Engine-independent verification.** Python drives the native transports over
  stdin/stdout and compares them with a pinned Musashi harness and isolated GPGX
  workers ([[09_References/GENESIS_DEBUGGER]]). None of it depends on a window,
  audio device, or engine.
- **Coverage** ([[03_Reverse_Engineering/COVERAGE]], [[01_Project/PROJECT_STATUS]]):
  26,749 of 1,048,576 ROM bytes classified; 121 function entries indexed;
  1,628 cumulative executed instructions; no frame loop, world scheduler, boot
  path, renderer or audio driver; native playability none. 36 commits between
  2026-10-02 and 2026-10-05, all on `work/airborne-update`; no `main` branch.
- **Godot on this machine.** `~/.local/bin/godot` is a wrapper for the Godot
  4.7.2 stable **.NET** build (`4.7.2.stable.mono.official.ed1daf0bf`). The
  user's sibling project `~/WL3PC` pins the **standard** 4.7.2 build under its
  own ignored `local/toolchain/godot-4.7.2` with recorded SHA-512s.
- **Sibling project WL3PC** (read only; same user, same evidence-based port
  method): Wario Land 3 in Godot 4.7.2 with typed GDScript split into
  `scripts/sim`, `scripts/content`, `scripts/present`; 95 scripts, 57,429
  lines; 178 commits from 2026-10-01 to 2026-10-05; milestone M3 with a playable
  level, map, golf and clear screens; headless tests via
  `godot --headless -s res://tests/run_tests.gd`; PyBoy as oracle; data-only
  mods, content packs and a Linux export. Its ADR-0001 records that a
  byte-identical public disassembly (ElectroDeoxys) with about 81% named labels
  exists for that game, and names GDScript performance as the risk to watch,
  with GDExtension C++ as the escape hatch for hot paths.
- **godot-cpp** (README on `master`, accessed 2026-10-05; a `4.7` branch does
  not exist): versioned independently from v10 onward, targets Godot 4.3 or
  later through an `api_version` parameter, extensions built for an earlier
  minor run on later minors but not the reverse. The README shows SCons only;
  CMake support, minimum C++ standard and license were **not** confirmed from
  that page.

## Interpretation

- **The engine is not the bottleneck.** Wiz 'N' Liz has no public disassembly.
  Every routine here is discovered from raw bytes, executed in Musashi, then
  reconstructed; WL3PC translates named source. A Godot rewrite would still start
  at 2.6% ROM understanding with no frame loop. Comparing commit counts between
  the two projects measures disassembly availability, not engine choice.
- **There is nothing SDL-specific to lose.** The whole native investment is a
  headless library plus harnesses that survive any shell choice unchanged.
- **Concrete project advantage of a Godot shell:** the user already has working
  patterns for a compatibility renderer with integer scaling, headless
  selftests, content packs, data-only mods and a verified Linux export. Those
  map directly onto the brief's M3, M5 and M6 goals (playable slice, mods and
  enhancements beyond original restrictions, reproducible user build and
  modding docs). An SDL3 shell would hand-build a tile and palette renderer,
  mixer, input mapping, scaling, packaging and mod loading from scratch.
- **Costs of a Godot shell:** a GDExtension binding layer and build; exceptions
  must be caught at the boundary; a second toolchain to pin; godot-cpp as a new
  third-party dependency with lock-manifest provenance; CMake support still to
  verify. Audio is a wash: neither engine supplies YM2612/PSG synthesis, so the
  audio backend is project work in either case.

## Options

1. **Godot shell, C++20 simulation kept and bound through GDExtension.** Keeps
   every verified routine and the 600k-case-per-preset corpora at native speed;
   CTest and Python remain the simulation's verification; Godot headless tests
   cover presentation and content only.
2. **Godot with the simulation rewritten in typed GDScript (WL3PC style).**
   Discards verified code, requires re-verification through a new transport,
   runs the differential corpora far slower, and loses ASan/UBSan coverage of
   the arithmetic claims.
3. **SDL3 as briefed.** Viable; single language and build. Buys simplicity and
   nothing else the brief needs.
4. **Defer.** No shell work is useful until a native frame loop exists.

## Recommendation (pending the user's acceptance)

Option 1, decided formally at the trigger below. Options 1 and 4 agree on the
next several passes, so nothing is lost by deciding when the first thing worth
drawing exists.

**Trigger:** the first native frame loop over the retained mixed pool that
replays a window of the user's recording (see [[07_Tasks/TASK-0010-grounded-controller]]
and [[01_Project/NEXT_ACTIONS]]), or earlier if the user accepts this ADR.

## Consequences if accepted

- Set this note's status to `accepted` and supersede the SDL3 statements in
  [[04_Native_Implementation/ARCHITECTURE]] and `README.md`; the brief itself
  stays as the user's record, with this ADR as the authorized deviation.
- Pin the standard Godot 4.7.2 build and export templates under ignored
  `local/tools/`, with hashes, following WL3PC's lock pattern; never the user's
  .NET build. No system package or `sudo`.
- Record godot-cpp (revision, license, hashes, build command) in
  `third_party/manifest.lock.json` before copying or building it; verify its
  CMake path and C++20 compatibility on this host first.
- Give the simulation one tick-step entry point the shell can call, with all
  exceptions converted to explicit results at the boundary.
- Replace the `SDL3-devel` requirement in `tools/doctor.py` with the Godot and
  godot-cpp checks; keep the doctor read-only.
- Godot tests exercise drawing, input mapping and content loading only; the
  simulation's evidence remains CTest, the Python corpora and the reference
  comparisons.

## Limitations

No Godot project, GDExtension build or SDL3 application was built in this
analysis. GDExtension CMake support, Godot 4.7.2 headless behavior on this host
and export reproducibility are unverified claims to test at adoption time. The
WL3PC figures describe that repository as found on 2026-10-05 and were not
rebuilt or rerun.
