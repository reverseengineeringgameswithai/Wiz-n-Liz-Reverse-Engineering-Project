---
id: REFERENCE-REA
type: reference
status: evaluated
---
# REA (morluto/rea): evaluated, not adopted

User question, 2026-10-12: would `https://github.com/morluto/rea` help this
project continue? Its public README and docs were read on 2026-10-12 (installation,
CLI, raw-binary and native-investigation pages, commit list); nothing was
installed or run, and no project data was sent anywhere.

## What it is

REA ("Reverse Engineer Anything") is an MIT-licensed Node/TypeScript MCP server and
CLI (`rea-agents`) that drives an existing Ghidra 12.1.x, Hopper or IDA install and
returns pseudocode, assembly, strings, symbols and references as evidence
records. It also targets JavaScript, .NET, Go, WASM, APKs, firmware and host
runtime capture. It does not disassemble, decompile or emulate by itself.

## Fit for this project

- **No 68000 path.** Its only headerless route is Ghidra raw-binary mode for
  little-endian x86, x86-64, ARM and AArch64; the docs state that big-endian
  and other processor variants are unsupported. A raw Genesis ROM cannot be
  loaded through any documented path; m68k, Sega or ROMs are never mentioned.
- **No replacement for the evidence stack.** The pinned Musashi restricted
  harness, the BizHawk full-machine trace worker and `rasm2` remain the tools.
- **Data boundary.** REA itself calls no model API, but in MCP mode its results
  (disassembly, pseudocode, raw bytes) enter the agent's model context, which
  conflicts with the no-upload rule for ROM-derived content. CLI-only local JSON
  output would avoid that.
- **Reproducibility.** Installation resolves `@latest` and analysis profiles
  change often; any use would need an exact pinned version, and its setup must
  not rewrite Claude Code configuration without review.

Possible edge uses only: inspecting the project's own x86-64 native builds, and
its evidence/snapshot record-keeping as a design comparison (its showcased
"reconstruct, then verify against original cases" method matches this
project's). **Decision: not adopted**; revisit only if it gains a documented
big-endian 68000 raw-binary path that runs fully locally.
