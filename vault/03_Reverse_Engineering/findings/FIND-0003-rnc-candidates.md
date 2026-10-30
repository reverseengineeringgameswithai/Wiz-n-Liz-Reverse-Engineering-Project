---
id: FIND-0003
type: finding
status: partially_validated
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset
confidence: hypothesis
task: TASK-0002
---
# RNC2 header candidates

Update: the first candidate is now verified by
[[03_Reverse_Engineering/findings/FIND-0004-first-rnc-block]]. The remaining 133
are still header hypotheses. Original scan observations follow.

Observed on ROM-LOCAL-0001, size 1,048,576 bytes, SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
There are 134 `RNC` occurrences. Each has method byte 2 and a declared packed
extent within this file. This is confirmed header/signature observation only;
the interpretation as valid compressed resources is a **hypothesis**.

The first candidate's 18-byte header starts at file `0x348B2`. Fields declare
17,714 unpacked bytes, 10,803 packed bytes, unpacked CRC `0xAF73` and packed CRC
`0x3673`. Its candidate interval is `[0x348B2,0x372F7)`, and the next signature
starts at `0x372FC`. These are file ranges, not native resource identifiers.

At the initial scan no CRC or decoder had been checked. Those checks now pass
for the first block only; no asset role, caller/decompressor routine or references
are established. Do not infer a count
of 134 graphics/audio/level resources or classify the remainder of the ROM as
compressed data. Static reset work is independent of these candidates.

Evidence metadata: `local/generated/sega2asm/rnc-candidates.json`, with offsets,
sizes, declared CRC fields and in-file checks, marked
`unvalidated_header_candidates`. Pinned sega2asm's README supplies the lead;
`compress/lzh_rnc.go` supplies the candidate header layout but omits CRC checks.
Revision/tool provenance: [[03_Reverse_Engineering/SEGA2ASM]] and
`third_party/manifest.lock.json`. Scanner used Python 3.14.6.

Reproduce the count and first header without writing extracted bytes:

```sh
python3 - <<'PY'
import json, sys
sys.path.insert(0, 'tools')
from rom import DEFAULT_ROM, inspect_file, verify_expected
verify_expected(inspect_file())
data = DEFAULT_ROM.read_bytes()
rows, cursor = [], 0
while (offset := data.find(b'RNC', cursor)) != -1:
    cursor = offset + 1
    header = data[offset:offset + 18]
    if len(header) != 18:
        raise ValueError('truncated candidate header')
    packed = int.from_bytes(header[8:12], 'big')
    rows.append({'offset': offset, 'method': header[3],
                 'unpacked': int.from_bytes(header[4:8], 'big'),
                 'packed': packed, 'end': offset + 18 + packed,
                 'unpacked_crc': int.from_bytes(header[12:14], 'big'),
                 'packed_crc': int.from_bytes(header[14:16], 'big')})
print(json.dumps({'count': len(rows), 'first': rows[0],
                  'next_offset': rows[1]['offset'],
                  'all_method2_in_bounds': all(r['method'] == 2 and r['end'] <= len(data) for r in rows)}, indent=2))
verify_expected(inspect_file())
PY
```

The follow-up [[07_Tasks/TASK-0002-rnc-block]] completed the initial next step: verify
the packed CRC and attempt bounded method-2 decoding of one candidate, then
check length/unpacked CRC and consumed boundary. Preserve failures rather than
silently accepting a tool's success status. No native code mapping exists yet.
