---
id: PROJECT-BRIEF
type: project
status: active
---
# Durable project brief

This condenses the user's 2026-10-02 project brief into lasting requirements.
The canonical pass workflow is [[00_START_HERE]]. The original brief authorizes
local analysis, implementation, tests, documentation and reviewed Git commits,
not publication, pushes, uploads or unrelated system changes. On 2026-10-29 the
user authorized one exception: the scrubbed [[02_Workflow/PUBLIC_MIRROR]] of
committed files, never the ROM or ignored research products.

## Intended result and terminology

Build a source-buildable, moddable native Wiz 'N' Liz implementation for the
actual Fedora Linux 44 host. Default stack: C++20, SDL3, CMake, Ninja, Python 3,
and project-local Go if the selected sega2asm revision requires it. Verify the
host architecture and installed versions. A different stack requires an ADR
with a concrete project advantage.

- **Disassembly:** original machine instructions and data represented as text.
- **Reconstructed source:** human-maintainable source derived from evidence;
  never claim it is the lost original source or a clean-room implementation.
- **Native implementation:** host-compiled gameplay with PC platform services.
- **Reference emulation:** observation, tracing, comparison and test tooling.
- **Temporary compatibility:** an explicitly reported transitional dependency
  with a replacement plan.

An emulator launcher, embedded ROM, hidden interpreter/dynamic translator,
screenshot display, look-alike platformer or raw-include ROM rebuild is not a
completed native port. Prefer incremental semantic reconstruction; do not start
by writing a universal Genesis recompiler. Whole-ROM round trips are useful
preservation checks, never gameplay-understanding measures or prerequisites to
porting a verified subsystem.

## Protect inputs, machine and history

Treat `Original_Game/Wiz 'N' Liz (USA).md` as a probable ROM until inspected.
Never modify, patch, rename, truncate, delete or chmod the original. Record size
and cryptographic hash before analysis and recheck after processing. Normalize
only into ignored `local/`, recording both identities, transformation, command
and reason. Filename, header and matching checksum are not provenance proofs.
Never invent hashes, maps, revisions, formats, counts or driver identities.

Never upload proprietary input or derived assets. Track recipes and evidence
metadata; ignore bulk disassembly, extracted assets, states, traces, Ghidra
databases, tool downloads, builds and caches. Record third-party commit, source,
license, build and local path before copying code. Tool licenses do not grant
rights to ROM content. Do not change SELinux, firewall, global Git/Python or
unrelated system settings. No remote install script piped to a shell. Use local
environments; privileged/package changes require applicable authorization.

See [[02_Workflow/GIT_RULES]]: explicit staging, preserve pre-existing work and
index, no blanket cleanup/staging/stash, no fabricated author, no history rewrite
or remotes/push without permission. A controlled tree and accurate vault must
describe the same checkpoint. Ignored research products need not be deleted.

## Knowledge and evidence

Open `vault/` in Obsidian. Plain Markdown must suffice; no plugin installation or
overwriting personal settings. Use vault-relative, explicit `[[path/NOTE]]`
links, and code-formatted repository paths outside the vault. Keep current truth
in canonical notes; history and failed experiments in session handoffs. Startup
reading order is [[00_START_HERE]].

Significant findings need stable ID, ROM identity, address space/ranges,
observations distinct from interpretation, confidence, versions/commands,
callers/callees/reads/writes/references, artifact location, related tasks/tests/
code, limitations and next validation. Confidence values: confirmed, probable,
hypothesis, unknown, rejected. State exactly what is confirmed. Never silently
promote a hypothesis. Preserve superseded reasoning and link corrections.
Use lightweight YAML frontmatter with real nulls for unknowns. Tasks need a
concrete deliverable and acceptance criteria. Keep one recommended next task.
Maintain a vault checker for links, IDs, fields and task relationships, ignoring
code examples appropriately.

## Analysis and extraction

Investigate and pin `https://github.com/hansbonini/sega2asm`. Read the selected
README, go.mod, command/config and segment handlers; verify actual --version,
--dry-run -c and -c ... -v forms. Build under `local/tools/`. Wrapper must locate
root, validate ROM identity, quote paths, use pinned executable, restrict output
to approved local directories, and record invocation, exit status and partial
output. Never report integration complete unless it ran. Start conservative;
unknown regions stay raw. Metadata is authoritative; generated disassembly is
not the sole record. Test RNC candidates using boundaries, lengths, decode and
integrity fields; a signature alone proves nothing. Default PCM rates are not
game playback evidence. Reproduce tool bugs, preserve patches and continue
independent work when blocked.

Define file/68000/RAM/Z80/device address spaces and interval conventions. Start
control-flow investigation at validated vectors/entry points; distinguish data,
inline constants, copied code and indirect tables. Use original-68000 decoding,
independent checks and dynamic evidence where available. Evaluate Ghidra and a
debugger-capable emulator (e.g. MAME), verifying actual flags/commands and keeping
reference runs separate from the native runtime. Record version/configuration,
ROM, initial conditions, inputs and synchronization boundaries.

Investigate actual menus, modes, movement, rescue, collectibles, words/spells,
fruit/cauldron, timers, progression, special encounters, multiplayer, demos and
persistence; this is a checklist, not assumed features. Connect original code/
data to behavior, native implementation and validation. Deterministically
extract structured assets where available, with stable IDs, ranges, procedures,
dimensions/layout/palette/transparency, hashes and confidence. Bound parsing,
reject malformed inputs and write atomically. Preserve all bytes on round trips
and report byte preservation separately from semantic coverage.

## Native architecture, audio and modding

Small explicit boundaries: deterministic headless simulation; assets; rendering;
audio sequencing/mixing; input/platform; saves/config; mods; narrow compatibility
helpers; reference comparisons. Introduce components as evidence demands, not a
large generic engine/editor. Maintain many-to-many uncertain-capable PORTING_MAP.
For each routine document state/dependencies, independently derived cases,
explicit arithmetic semantics, compare edge cases/traces, then refactor. Handle
width/wrap, signedness, endianness, flags, shifts, fixed point, ordering, timing,
aliasing and RNG without C++ UB. Never use host pointers as original addresses
or let compatibility helpers become a hidden CPU emulator. Unknown behavior
must diagnose failure or be explicitly experimental.

Keep `original` regression and `enhanced` intentional changes separate. Native
resources use stable logical IDs, host-sized containers and documented safety
limits rather than permanent ROM offsets/pools. Separate simulation stepping
from presentation and measure original timing. Enhanced graphics need not keep
legacy tile/palette/sprite/VRAM restrictions. Widescreen, worlds, cameras and
capacity changes need tests; removing a cap proves little.

Audio must identify driver processor, communication, formats, devices, timing,
sequencing and sample rates. PCM extraction is not a complete soundtrack. Prefer
native sequencing/decoding. Chip synthesis can be a documented backend, distinct
from executing an original CPU driver. Any unreconstructed driver execution is
a reported temporary dependency. Validate sequencing separately from waveforms,
with justified resampling/latency tolerances and replacement audio resources.

Start a simple JSON/TOML mod layer when useful: versioned manifest, deterministic
override order, stable IDs, schema/errors, profiles, disable-all-mods reference
mode, bounded parsing/path containment, examples, versioned saves/config. Add
scripting only by ADR with an explicit trust model. Eventually demonstrate a
real gameplay parameter change, authored asset replacement and tested increase
beyond a verified original restriction, all in native code without ROM patches.

## Interfaces, validation and milestones

Grow `python3 tools/project.py <command>` honestly: doctor, rom-identify, split,
extract, configure, build, test, run, reference-test, check-vault, check-hygiene.
Unimplemented commands must fail, not succeed as no-ops. No implicit downloads
or OS changes on normal build. Provide headless tests and an SDL3 app as code
becomes available, CMake debug/release/sanitizer presets where supported; verify
actual SDL3 API and Fedora44 execution. Final runtime consumes extracted
resources and native logic, not a raw ROM as a CPU program.

Keep synthetic ROM-independent tests separate from local ROM tests,
independently observed differential tests, deterministic canonical-state replays
and runtime/sanitizer/manual checks. Record input/state/synchronization and
justified ignored fields. Never generate every expectation from the function
under test or edit goldens to hide regressions. Report failures/skips accurately.
Track separate denominators for preserved/classified bytes, identified/
understood/native/differential functions, assets, scenarios and compatibility
dependencies. Booting or generated line counts are not gameplay coverage.

- M0: protected, identified input; Git/entry points/vault; audited environment;
  tested non-destructive inspector; safe continuation.
- M1: repeatable pinned analysis, conservative segmentation, entry points and
  at least one substantive reproducible finding.
- M2: useful native verified behavior with independent edge-case evidence.
- M3: playable native slice with assets/input/simulation/render/audio comparison.
- M4: documented coverage of observed modes, progression and special cases.
- M5: tested enhancements/mods beyond verified hardware/content restrictions.
- M6: reproducible Fedora44 user build, extraction, maintenance and modding docs.

Milestones may overlap. Each pass must deliver useful reproducible progress;
documentation-only passes after setup require a specific reason. Delegate
bounded independent tasks where useful; one integrator owns shared status and
commits. Finish with validation, ROM recheck, current notes, task/blocker/next
updates and a session handoff with exact commands, failed approaches, evidence,
starting Git state and outstanding limitations.
