---
id: FIND-0002
type: finding
status: confirmed
rom_id: ROM-LOCAL-0001
address_space: m68000
confidence: confirmed
task: TASK-0001
---
# Pinned sega2asm decode and error-reporting defects

## Observation

ROM-LOCAL-0001 is 1,048,576 bytes, SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
At these low ROM addresses the CPU address equals the file offset, under the
initial linear cartridge mapping described in
[[03_Reverse_Engineering/ROM_IDENTITY]]. No game execution was observed.

Pinned sega2asm `78f37b0d71d27b43b960e24c01c5437bbef55404`, built with Go 1.27.1
linux/amd64, emits incorrect instructions in the statically validated reset
fragment:

| File/CPU address | Opcode bytes | sega2asm output | Independent interpretation |
| --- | --- | --- | --- |
| `0x000218` | `4cdd 1f00` | `movem.l (a5)+,d3/d4/d5/d6/d7` | `movem.l (a5)+,a0-a4` |
| `0x000288` | `46fc 2700` | `not.? #$2700` | `move.w #$2700,sr` |

The MOVEM register mask implementation tests bit `15-i` while enumerating
registers D0 through A7, reversing the nonpredecrement ordering. Group-4 decoding
treats all `0x46xx` opcodes as NOT and omits the MOVE-to-SR special case. These
source observations explain the outputs; they are not assumptions that all
other instructions decode correctly.

Capstone's original-68000 configuration and a separate GNU decoder agree on the
correct operands; original Motorola instruction documentation agrees with the
mask and MOVE-to-SR interpretation. Evidence and hardware implications belong
to [[03_Reverse_Engineering/findings/FIND-0001-reset-path]]. These
instructions initialize hardware address registers and SR in that startup
fragment; wrong MOVEM text would corrupt any reconstruction based on it.

A separate synthetic probe makes one `bin` output's parent a regular file.
Upstream logs `[WARN]   error:`, still prints `[OK] sega2asm`, and exits 0.
`splitter/splitter.go` handles segment processor errors with a warning and
`continue`, not a propagated failure.

## Interpretation and confidence

**Confirmed tool defects at the exact revision and cases above.** This does not
establish a complete inventory of decoder bugs. A zero exit status or plausible
assembly text is not semantic validation. Invalid-size marker detection catches
one demonstrated error but cannot catch every incorrect operand.

## Implementation and verification

`tools/sega2asm.py` validates output existence, raw-bin equality and warnings;
it returns partial extraction, exit 2 for errors or any upstream m68k output.
An earlier version only checked invalid `.?` markers, but that cannot catch the
plausible MOVEM error. The default configuration now preserves the reset code
fragment as binary while retaining its separate static code classification.
It keeps generated evidence and the exact command/exit status. No upstream
source patch is applied. `tools/reset_probe.py` uses independently checked
decoding for current reset work; sega2asm output must not be the authority for
instruction semantics.

`tests/test_sega2asm.py` contains original synthetic fixtures: eight opcode
bytes following a zero-filled 512-byte prefix, and an intentionally unwritable
single-bin output. No proprietary fixture is needed. Tests demonstrate both
upstream defects and the wrapper's failure handling. The tests intentionally
assert the pinned defects; updating the upstream pin requires revisiting these
expectations rather than silently accepting changed output.

## Reproduction and evidence

```bash
python3 -m unittest discover -s tests -p test_sega2asm.py -v
python3 tools/project.py split --dry-run
python3 tools/project.py split
```

Nine tests passed locally; both split commands pass using the final raw
configuration. Historical failed m68k-run artifacts are
`local/generated/sega2asm/split-nuhwxko6/run.json`,
`local/generated/sega2asm/split-nuhwxko6/asm/m68k/reset_fragment.asm`, and
`local/generated/reset/decoder-evidence.json`. Raw slices compare equal and the
ROM size/hash remains unchanged. The final successful raw split is recorded in
`local/generated/sega2asm/split-fnjkvvxs/run.json`. Bootstrap/provenance:
[[03_Reverse_Engineering/SEGA2ASM]].

Known limitations: no sega2asm whole-ROM disassembly, assembler round trip,
dynamic reference run or gameplay reconstruction was performed. The next useful
validation is a narrowly tested upstream patch or continued independent decode;
neither blocks using the verified reset finding or studying one RNC candidate.

Task: [[07_Tasks/TASK-0001-foundation]].
