---
id: ADR-0002
type: decision
status: accepted
---
# ADR-0002: Project license (MIT)

- **Status:** **accepted on 2026-10-29** by the user, who asked for proper
  licensing so others can legally fork and continue the work.
- **Supersedes:** none.
- **Session:** [[08_Sessions/2026-10-29-058-licensing]].

## Context

The project is published through [[02_Workflow/PUBLIC_MIRROR]]. It had no
license, so nobody could lawfully reuse it. Every tracked file is the project's
own work: third-party tools are downloaded only into ignored `local/` and pinned
by `third_party/*.lock.json`. The one file already carrying another license,
`re/reference_scripts/rnc_reference_main.cpp`, is a GPL-3.0-or-later research
harness because it links ScummVM's RNC decoder; the native `src/` never links it.

## Options offered

MIT (recommended), GPL-3.0-or-later (forks must stay open; could be relaxed to
MIT later) and CC0 public domain.

## Decision

**MIT** for the project's own code, tools, tests, evidence records and notes,
held by "The Wiz 'N' Liz Reverse Engineering Project contributors" (no personal
name, per [[08_Sessions/2026-10-29-057-public-mirror]]). The harness stays
GPL-3.0-or-later, with the GPL text from the pinned, hash-verified ScummVM
`COPYING` (SHA-256 `3972dc97…6986`) in `LICENSES/GPL-3.0-or-later.txt`.

- `LICENSE`: the standard MIT text.
- `NOTICE.md`: license scope, the GPL exception, third-party tool licenses (not
  included), and the game notice: no rights in Wiz 'N' Liz are granted, no ROM
  or extracted content is included, users supply their own copy, not legal advice.
- `CONTRIBUTING.md`: contributions take the license of the files they change;
  no game content; the project's checks.
- `README.md`: an AI-assistance disclaimer at the top, at the user's request,
  and a License section.

## Consequences

MIT grants are irrevocable for every published version. The license gives no
rights to the ROM or game content; the ROM rules in [[01_Project/MASTER_BRIEF]]
are unchanged.
