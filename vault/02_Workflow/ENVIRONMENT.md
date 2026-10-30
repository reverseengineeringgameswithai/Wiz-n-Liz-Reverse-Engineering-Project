---
id: WORKFLOW-ENVIRONMENT
type: workflow
status: active
---
# Environment audit

Observed locally on 2026-10-02. This is the user's actual Fedora machine, not a
container claim inferred from the project brief. Re-run the doctor before relying
on this snapshot. System tools were inspected without installing packages or
changing system configuration.

| Component | Observed state |
| --- | --- |
| OS | Fedora Linux 44 (Workstation Edition), `/etc/os-release` |
| CPU architecture | `x86_64`, `uname -m` |
| Kernel | `7.0.11-200.fc44.x86_64` |
| GCC / g++ | `16.1.1-2.fc44.x86_64`; compiler reports 16.1.1 |
| Clang | `22.1.7-1.fc44.x86_64` |
| Python | `3.14.6-1.fc44.x86_64` |
| CMake | `4.3.0-1.fc44.x86_64` |
| Ninja | `1.13.2-2.fc44.x86_64` |
| pkg-config | 2.5.1 |
| SDL3 runtime | `3.4.10-1.fc44`, both x86_64 and i686 installed |
| SDL3 development files | `SDL3-devel` absent; `pkg-config --modversion sdl3` fails |
| Go | System `go` absent from PATH; `golang` RPM not installed |
| radare2 | `5.9.8-9.fc44.x86_64`; `r2 -v` reports 5.9.8 |
| Java | OpenJDK 25.0.3; RPM `java-25-openjdk-25.0.3.0.9-2.fc44.x86_64` |
| GNU binutils | `2.46-3.fc44.x86_64`; installed `objdump -i` has no m68k target |
| MAME | No `mame` on PATH; RPM not installed |
| Ghidra | No `ghidraRun` / `analyzeHeadless` on PATH; RPM not installed |
| Other RE tools | `rizin`, `m68k-linux-gnu-objdump`, `clownassembler` absent from PATH |

PATH absence does not prove no manually installed tool exists elsewhere. Searches
of `/usr/include`, `/usr/lib64/cmake`, `/usr/local/include`, `/usr/local/lib`,
`/opt`, and `~/.local` found no SDL3 headers/CMake config or Ghidra launcher.
Project-local research tools are recorded separately in
`third_party/manifest.lock.json`; the doctor does not assume they are on PATH.

## Read-only doctor

`tools/doctor.py` uses standard-library Python, explicit subprocess argument
lists, a 10-second limit per probe, and retains at most 8192 characters per
command result. It does not install, download, build, run an emulator, or contact
package repositories. Missing tools are explicit JSON observations. An audit
exit of zero means the audit completed; it does not mean all dependencies exist.

```sh
python3 tools/doctor.py
python3 tools/doctor.py --require-native
```

The second command returns 1 on this snapshot because SDL3 development files
are unavailable. Its `build_verified: false` field is deliberate: package
availability alone cannot verify a native build. The Python function
`collect_report(root=None)` supports the project dispatcher.

Evidence: `local/logs/environment/doctor.json` (ignored, regenerable). No
environment-variable or credential dump is collected.

## Package candidates, without installation

This exact read-only command completed successfully using existing local
repository metadata:

```sh
dnf --cacheonly repoquery --available SDL3-devel golang mame ghidra
```

It listed SDL3-devel `3.4.0-3.fc44` and `3.4.16-1.fc44` for x86_64/i686,
Go `1.26.1-1.fc44` and `1.26.8-2.fc44` for x86_64, and MAME `0.286-2.fc44`
and `0.289-1.fc44` for x86_64. No Ghidra candidate appeared. These are cached
candidate versions, not installed versions or a guarantee of mirror availability.

Future user/system package action, **not executed**:

```sh
sudo dnf install SDL3-devel
```

This is the immediate development dependency for a distribution-based SDL3
application. Go and MAME may be installed separately if those workflows require
system packages; this pass uses a separate explicit project-local tool bootstrap
where recorded. No ordinary build command may silently install any dependency.

## C++20 compilation check

Both `g++` and `clang++` compiled and executed an original tiny C++20 program
using `std::span` and `std::rotl`: both compilation and program exit codes were
zero with `-Wall -Wextra -Werror`. This validates these compiler features on the
host, not the game, SDL3, sanitizer integration, or graphics/audio devices.
Evidence: `local/logs/environment/cxx20_probe.json` and
`build/environment/cxx20_probe.cpp`.

Recreate the probe from repository root:

```sh
mkdir -p build/environment
cat > build/environment/cxx20_probe.cpp <<'CPP'
#include <array>
#include <bit>
#include <cstdint>
#include <span>
static_assert(std::rotl(std::uint32_t{1}, 31) == 0x80000000u);
int main() {
    const std::array values{1, 2, 3};
    const std::span<const int> view{values};
    return view.size() == 3 && view[2] == 3 ? 0 : 1;
}
CPP
g++ -std=c++20 -Wall -Wextra -Werror build/environment/cxx20_probe.cpp -o build/environment/gpp_probe
build/environment/gpp_probe
clang++ -std=c++20 -Wall -Wextra -Werror build/environment/cxx20_probe.cpp -o build/environment/clangpp_probe
build/environment/clangpp_probe
```

## Deferred checks

No native game/application target, CMake presets, SDL3 window/audio smoke,
sanitizer target, Ghidra project, or MAME reference run was built or run during
this environment task. SDL3 API implementation validation belongs to the first
actual platform component. See [[04_Native_Implementation/ARCHITECTURE]],
[[01_Project/BLOCKERS]], and [[09_References/SOURCES]].

## RNC reference follow-up (session 2026-10-02-002)

A real isolated C++20 decompression reference was compiled and run with Clang
22.1.7 ASan/UBSan. `rpm -q libasan libubsan compiler-rt` reports libasan/libubsan
absent and `compiler-rt-22.1.7-1.fc44.x86_64` installed. GCC's sanitizer link fails
on missing `/usr/lib64/libasan.so.8.0.0`; installed Clang compiler-rt works.
This updates the earlier unrun-sanitizer observation for the reference harness
only. No native game target or SDL application is built.

Reproduce with `python3 tools/build_rnc_reference.py` using already verified
local source downloads. Provenance is in `third_party/rnc_reference.lock.json`
and `local/tools/rnc-reference/build.json`. The failed GCC attempt remains in
`local/tools/rnc-reference/build-6wdgky1_/build.json`. No package was installed.

## Native codec build (session 2026-10-02-003)

The actual Fedora44 x86_64 machine builds/runs the C++20 RNC2 component with
GCC16.1.1 debug/release and Clang22.1.7 ASan/UBSan. CMake4.3.0 and Ninja1.13.2
configure/build both CTest targets. No SDL or additional system package is needed
for these headless targets. All final presets use Python3.14.6 via the project
wrapper's explicit `Python3_EXECUTABLE`; initial direct CMake discovery selected
another installed Python3.12.13 before this was made explicit.

`configure/build/test --preset {debug,release,sanitize}` are now real interfaces.
Exact commands and results: [[08_Sessions/2026-10-02-003-native-rnc2]],
`local/logs/native-rnc2/commands.json`. The earlier deferred CMake/sanitizer
observations are superseded for the codec only. SDL/gameplay, Ghidra and MAME
remain unrun. No package, global configuration or operating-system setting changed.

## Session 2026-10-02-007: isolated original CPU execution

Pinned Musashi `313ebf1bd9f4d0d93341eb5ce21fd8a119e9dbdd` is now built under
`local/tools/terrain-reference/` using installed Clang22.1.7 ASan/UBSan. The
initial inspected checkout remains at `local/tools/musashi-src/`; all compiled
sources are individually pinned in `third_party/terrain_reference.lock.json`.
Builder uses 68000 only, explicit instruction hook and restricted fixture memory.
Six original terrain/contact routines execute and compare with native C++.
This resolves the function-level reference blocker; MAME/Ghidra and full-game
capture remain absent. No privileged/package/global changes occurred. SDL3-devel
is still missing. Native simulation builds without SDL3 or Musashi.

## Session 2026-10-02-008: movement reference extension

The same pinned local Musashi source and Clang sanitizers now support eight
additional movement routines through the restricted `--movement` harness mode.
The reference was rebuilt with changed harness/lock provenance; no source
download, package installation or global configuration change occurred. All
five native transports and ten CTest targets build in debug/release/sanitize.
SDL3-devel, a full-system game capture and physical input/frame evidence remain
outstanding. See [[08_Sessions/2026-10-02-008-movement-step]].

## Session 2026-10-02-009: bounded airborne execution

The existing pinned Musashi source/Clang ASan+UBSan build now supports restricted
`--airborne` execution and exact immediate-idle stop boundaries. Reference
harness/lock provenance was rebuilt; no external download, package installation
or global setting changed. All six native transports and twelve CTest targets
build/run in debug, release and sanitizer presets. SDL3-devel and full-system
reference capture remain absent. See
[[08_Sessions/2026-10-02-009-airborne-update]].

## Session 2026-10-05-037: engine analysis snapshot

Observed without installing or changing anything. `pkg-config --modversion
sdl3` still fails; `rpm -qa` lists `SDL3-3.4.10-1.fc44` (x86_64 and i686) and
`mingw64-SDL3-3.4.12-1.fc44`, no `SDL3-devel`. `~/.local/bin/godot` is a shell
wrapper that sets `DOTNET_ROOT=~/.dotnet` and runs the Godot 4.7.2 stable .NET
build from `~/Applications`; `godot --version` reports
`4.7.2.stable.mono.official.ed1daf0bf`. No `godot4` on PATH and no Godot RPM.
That analysis also looked at another of the user's projects for its Godot pin;
since 2026-10-23 such projects are out of scope
([[02_Workflow/PROJECT_BOUNDARIES]]) and
[[06_Decisions/ADR-0001-presentation-shell]] is rejected.
The existing debug build's 46 CTests passed in 0.92 s without reconfiguring.
