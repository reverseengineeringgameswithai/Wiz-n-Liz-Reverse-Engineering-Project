---
id: FIND-0005
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset
confidence: confirmed
task: TASK-0002
---
# Pinned sega2asm RNC2 output fails independent integrity checks

Task: [[07_Tasks/TASK-0002-rnc-block]]. ROM-LOCAL-0001, 1,048,576 bytes, SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
The tested source range is `[0x348B2,0x372F7)`, including its 18-byte header.
Correct bounded reference results are [[03_Reverse_Engineering/findings/FIND-0004-first-rnc-block]].

## Observation and cause

Pinned sega2asm commit `78f37b0d71d27b43b960e24c01c5437bbef55404`, Go1.27.1
linux/amd64, `compress.DecompressLZHRNC2` returns **25 bytes without an error**
for a header declaring 17,714. Actual output CRC is `0xAF60`, not stored
`0xAF73`. Output SHA-256:
`d9e14b6c254fc2a7d195d20a29de6fb97589a76fd8c0c2ea6b0987ba96c53f6f`.
The packed input CRC is independently valid (`0x3673`).

An authored 21-byte fixture encodes one literal `A` and termination:

```text
524e4302000000010000000330c0565000011e4100
```

Its control byte `0x1E`, literal `0x41`, and terminator byte `0x00` are accepted
by the independent sanitized reference, which consumes all three payload bytes
and emits `A`. Stored CRCs are packed `0x5650`, unpacked `0x30C0`.
The pinned Go decoder instead emits `G` (`0x47`), still with no error and the
correct length. Its CRC is `0x3240`. Checking output length alone is insufficient.

Source inspection finds an LSB-first shared bit reader and simplified raw/
distance commands in the pinned method-2 implementation. The working reference
uses MSB-first control bits interleaved with direct raw-byte reads. This explains
the demonstrated disagreement; it is not a complete audit of either decoder.

## Implementation and verification

`re/reference_scripts/rnc_sega2asm_probe.go` imports the unmodified pinned MIT
upstream source. `tools/rnc_upstream_probe.py` builds this adapter offline with
Go network access disabled. The source checkout must be clean and at the pin.
Inputs are bounded to 1 MiB, and declared extents must match the isolated block.
The decoder child has a 2 GiB address-space limit, five-second CPU/wall limits,
1 MiB output-file limit, and Go's 64 MiB soft memory limit. Every invocation,
build, exit status, output digest and independently calculated CRC is recorded.

Wrapper outcome is `rejected_output`, exit **2**, for both real and synthetic
cases. It never promotes these bytes into validated extracted assets. No local
upstream patch is applied. The smaller authored fixture is a useful future
repair/regression case. Tests intentionally reproduce the pinned defect; do not
edit their expectations without reviewing an upstream update.

```sh
python3 tools/rnc_upstream_probe.py
# Expected exit 2: rejected output, with a local report path.
python3 -m unittest discover -s tests -p test_rnc_upstream.py -v
```

The optional `--input <exact-block.rnc>` path supports ROM-free synthetic probes.
Three tests pass, including six malformed-input cases and proof that this path
does not access the original ROM. Evidence:
`local/generated/rnc-sega2asm/run-m3446ji5/report.json` (real block),
`run-97s1199t/report.json` (literal fixture), and the latest report linked from
`local/logs/rnc-pass/sega-rnc-rejected.log`. Original ROM and source checkout
were unchanged after execution.

This confirms the defect only at the pinned revision/cases. It does not prove
all RNC methods or all other compression handlers are wrong. Do not add RNC
segments to the canonical sega2asm configuration; use the independently checked
path in [[03_Reverse_Engineering/ASSET_FORMATS]]. No game code was executed.
