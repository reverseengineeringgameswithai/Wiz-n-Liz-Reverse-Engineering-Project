# Licensing and legal notice

## This project's work

Unless a file says otherwise, everything in this repository is the project's own
work: source code, tools, tests, evidence records and the Obsidian notes in
`vault/`. It is released under the [MIT License](LICENSE). You may fork, modify,
redistribute and build on it, including commercially, as long as the copyright
notice and license text are kept.

One exception: `re/reference_scripts/rnc_reference_main.cpp` is licensed
GPL-3.0-or-later, as its SPDX header states, because the optional research
bootstrap links it with ScummVM's GPL RNC decoder. Its license text is
[`LICENSES/GPL-3.0-or-later.txt`](LICENSES/GPL-3.0-or-later.txt). It is a
comparison harness only; the native components in `src/` never link it.

## Third-party tools (not included)

This repository contains no third-party source code. Optional research tools are
downloaded only by explicit bootstrap commands into the ignored `local/`
directory, pinned by the manifests in `third_party/`, and keep their own licenses:

| Tool | Use here | License |
| --- | --- | --- |
| [Musashi](https://github.com/kstenerud/Musashi) | runs individual original routines for comparisons | MIT, with its bundled SoftFloat notice |
| [ScummVM](https://github.com/scummvm/scummvm) RNC decoder | independent RNC2 reference | GPL-3.0-or-later |
| [sega2asm](https://github.com/hansbonini/sega2asm) | conservative ROM segmentation | MIT (dependencies: Apache-2.0, BSD-3-Clause, MIT) |
| [Go](https://go.dev) toolchain | builds sega2asm | BSD-3-Clause |
| [MAME](https://github.com/mamedev/mame) | source reading only; nothing copied, linked or run | BSD-3-Clause files in a GPL-2.0 repository |

The BizHawk-based capture worker referenced in the notes is a separate tool
under its own license and is not part of this repository.

## The game

*Wiz 'N' Liz* (Sega Genesis / Mega Drive, 1993), including its program code,
graphics, sound, music, text, names and trademarks, belongs to its respective
rights holders. This is an unofficial project, not affiliated with or endorsed
by them. The MIT License covers only this project's own work and grants no
rights in the game.

- This repository contains no ROM, no extracted graphics, audio or text, and no
  bulk disassembly. Contributions must not add them; `.gitignore` and
  `python3 tools/project.py check-hygiene` guard the obvious cases.
- To use the tools, supply your own copy of the game, for example a dump of a
  cartridge you own. The tools check it against the SHA-256 recorded in
  `re/rom_manifest.json` and never modify it.
- The notes and evidence records cite addresses, small constants and
  descriptions of behavior as research findings, for interoperability and
  preservation.

Whether reverse engineering or using a game dump is lawful depends on where you
live. This notice is not legal advice.
