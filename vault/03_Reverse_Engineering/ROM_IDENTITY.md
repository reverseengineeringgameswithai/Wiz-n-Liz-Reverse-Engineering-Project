---
id: ROM-LOCAL-0001
type: rom_identity
status: observed
---
# Original input identity

| Field | Observed value |
| --- | --- |
| Immutable path | `Original_Game/Wiz 'N' Liz (USA).md` |
| Size | 1,048,576 bytes (`0x100000`) |
| SHA-256 | `d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161` |
| Encoding | Linear big-endian bytes with `SEGA` at file `0x100` |
| Normalization | None; normalized identity and transformation are null |
| Console field | `SEGA GENESIS` |
| Copyright field | `(C)T-1131993.NOV` |
| Domestic / overseas title | `WIZ 'N' LIZ IN THE FRANTIC WABBIT WESCUE` |
| Product code | `GM T-113026` |
| Region field | `JUE` (filename says USA; no independent revision/region provenance) |
| Header ROM range | `0x00000000..0x000FFFFF` inclusive |
| Header RAM range | `0x00FF0000..0x00FFFFFF` inclusive; header observation, not complete map |
| Stored / calculated checksum | `0xC0DE` / `0xC0DE` |
| Initial SP raw longword | `0xFFFF0100` |
| Reset PC raw longword | `0x00000200` |

Classification: binary ROM image, not Markdown. Confirmed means these local
bytes were inspected, not that a trusted dump database or original cartridge
provenance was established. A matching header checksum is a weak consistency
observation. SHA-256 identifies this exact input, not semantic correctness.

## Reproduce

```sh
python3 tools/project.py rom-identify --verify
python3 tools/project.py test --rom
sha256sum "Original_Game/Wiz 'N' Liz (USA).md"
```

`tools/rom.py` bounds reads to 32 MiB, requires at least 512 bytes and an even
length for this linear format, extracts fixed-size fields and all 64 vector-area
longwords. It reports rather than trusts declared ranges. `--verify` compares
size/hash to authoritative `re/rom_manifest.json`. Synthetic tests cover checksum
wrap, malformed lengths, truncation, unsupported signatures, byte-swap/prefix
hints, non-ASCII fields, raw vs low-24-bit addresses, and immutable file reads.
Probable swapped/prefixed inputs are rejected with diagnostics; no automatic
normalization is implemented. Interleaved/SMD format detection is not claimed.

Evidence: first pre-analysis observation and later reports agree; full local JSON
is `local/logs/rom-identity.json` (regenerate by redirecting the identity command).
Toolchain: Python 3.14.6, inspector schema 1. Only metadata is tracked.

## Initial-vector caution

Entries 2–9 contain raw values beginning `0x0220800C`, `0x0320800C`, ...,
`0x0920800C`. Their low 24 bits are `0x20800C`, outside this ROM image. Do not
treat these raw longwords as direct file offsets or infer callable handlers.
Several later entries contain `0x0000EC06`, but those targets have not yet been
validated as complete handlers. The reset target is even and lies in the image;
its narrow static investigation is [[03_Reverse_Engineering/findings/FIND-0001-reset-path]].

See [[03_Reverse_Engineering/MEMORY_MAP]] for address conventions and
[[03_Reverse_Engineering/COVERAGE]] for honest limits. Next useful identity work
is independent dump provenance if needed, not changing this established hash.
