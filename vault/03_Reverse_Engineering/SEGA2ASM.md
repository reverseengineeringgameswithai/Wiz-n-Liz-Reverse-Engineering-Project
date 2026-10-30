---
id: RE-SEGA2ASM
type: technical
status: partial
---
# sega2asm integration

Pinned upstream revision `78f37b0d71d27b43b960e24c01c5437bbef55404` was built and
run locally. The executable reports `sega2asm v1.0.0`; the commit, rather than
that version string, identifies the inspected source. Build, dry-run and
conservative raw split succeed. The upstream 68000 decoder emits incorrect
instructions in the reset fragment; the final configuration preserves that
fragment as binary and uses independent decoders for semantic analysis.
See [[03_Reverse_Engineering/findings/FIND-0002-sega2asm-defects]].

This is an analysis tool, never a native game runtime dependency. No third-party
source was copied into tracked project code. The MIT tool license grants no
rights over the ROM or generated content.

## Provenance and inspected source

Source: <https://github.com/hansbonini/sega2asm>, accessed 2026-10-02. Pin and exact
binary digest: `third_party/manifest.lock.json`. Local clone:
`local/tools/sega2asm-src`; executable: `local/tools/sega2asm`. Source tree is
unmodified. No local upstream patch is applied in this pass.

Inspected at the pin: `README.md`, `LICENSE`, `go.mod`, `go.sum`, `main.go`,
`types/config.go`, `types/rom.go`, `types/processor.go`, `types/hex.go`,
`example/alteredbeast.yaml`, `splitter/splitter.go`, the header/bin/m68k/gfx segment
handlers, `disasm/m68k/m68k.go`, and `compress/lzh_rnc.go`. Example addresses were
not reused. The module requires Go 1.21 and Cobra, pflag, YAML dependencies;
tested compiler is project-local Go 1.27.1 linux/amd64. The installed tool's
build information records the exact commit and `vcs.modified=false`.

Verified source and executable interfaces:

```text
sega2asm --version
sega2asm --dry-run -c <configuration.yaml>
sega2asm -c <configuration.yaml> -v
```

`types.LoadConfig` resolves input/symbol paths relative to the config file,
but not `base_path`. The wrapper therefore emits absolute paths, with JSON
quoting accepted by upstream's YAML parser. Apostrophes and spaces are tested.
No game timing inference is drawn from default `region` or PCM settings.

## Authoritative metadata and output

- ROM identity: `re/rom_manifest.json`.
- File-offset segmentation: `re/sega2asm/segments.json`.
- Symbols: `re/symbols.csv`, exported automatically to a per-run `symbols.txt`.
- Tool/reproducible-build pin: `third_party/manifest.lock.json`.
- Generated YAML, disassembly, raw bins and process logs: ignored
  `local/generated/sega2asm/<unique-run>/`.

Segments use `[start,end)` ROM file offsets:

| Range | Handler | Meaning |
| --- | --- | --- |
| `0x000000–0x000200` | header | vectors/header interpretation |
| `0x000200–0x00028E` | bin | known reset code fragment, kept raw due to decoder defects |
| `0x00028E–0x0002FA` | bin | observed inline initialization table |
| `0x0002FA–0x100000` | bin | unclassified remainder |

The wrapper rejects unsupported identities, nonpartitioning ranges, unreviewed
handlers, unsafe segment names and symlink redirects of output ancestors. It
verifies the binary hash, creates a fresh run directory, records the exact
argument array, version/exit status, timeout, configuration digest and output
digests, then rechecks the ROM. It treats warnings, missing/incorrect raw output,
and all upstream m68k output as partial extraction even if upstream exits zero.
The latter restriction is deliberate: the MOVEM bug can produce plausible but
wrong text without any invalid marker. The default configuration uses no m68k
handler. Its `classification` field preserves the independently established code
classification separately from the safe binary output handler.

The three bin files preserve exactly 1,048,064 bytes of the 1,048,576-byte input.
The remaining 512 bytes have generated header/vector views, not an assembled
round-trip proof. Upstream header formatting trims spaces/NULs, substitutes RAM
constants and emits unescaped apostrophes in title strings. No byte-identical
rebuild or assembly compatibility is claimed. Main assembly output is disabled.

## Reproduce

From the repository root, after the explicit local bootstrap below:

```bash
python3 tools/project.py split --dry-run
python3 tools/project.py split
python3 -m unittest discover -s tests -p test_sega2asm.py -v
```

All three commands pass with the final conservative configuration. Selecting an
m68k handler instead produces partial extraction, exit 2, until its decoder has
been independently repaired and validated. Independent reset analysis remains
available through `tools/reset_probe.py`; see
[[03_Reverse_Engineering/findings/FIND-0001-reset-path]].

Recorded local evidence:

- `local/generated/sega2asm/dry-run-ozxbl__a/run.json`: final dry-run exit 0.
- `local/generated/sega2asm/split-fnjkvvxs/run.json`: final split exit 0;
  header annotation and three raw slices, raw outputs checked exactly;
  original ROM size/SHA-256 unchanged.
- `local/generated/sega2asm/split-fnjkvvxs/process.log`: exact upstream output.
- `local/generated/sega2asm/split-nuhwxko6/run.json`: earlier m68k attempt,
  partial extraction due to invalid decoder size, retained as failure evidence.
- First `split-z0vtx3nw/run.json` predates the invalid-size check; its `complete`
  label meant only expected artifacts existed. It is superseded by the stricter
  checks and the final raw configuration, not evidence of correct disassembly.

Nine wrapper tests pass, including two synthetic executions of the actual pinned
tool demonstrating swallowed write failures and wrong decode. Without the local
tool those two probes are explicitly skipped. `go test ./...` compiled all 11
upstream packages, but all reported `[no test files]`; this is no decoder test
coverage. No native gameplay, graphics extraction, dynamic run, sound extraction
or assembler round trip was performed by this integration.

## Explicit bootstrap, outside normal build commands

These were the tested host-specific dependencies: Linux x86_64/Go linux-amd64.
For a different host, review the compiler artifact and record a new binary pin.
The commands below are for absent local tool directories, from repository root;
inspect existing tool work before replacing anything. No privileged installation
or global environment modification is required. Network downloads occur only
in this explicitly requested bootstrap, never `split` or normal build commands.

```bash
mkdir -p local/tools
git clone https://github.com/hansbonini/sega2asm.git local/tools/sega2asm-src
git -C local/tools/sega2asm-src checkout --detach 78f37b0d71d27b43b960e24c01c5437bbef55404
curl -fL --max-time 60 https://dl.google.com/go/go1.27.1.linux-amd64.tar.gz -o local/tools/go1.27.1.linux-amd64.tar.gz
python3 - <<'PY'
import hashlib
from pathlib import Path
import tarfile
p = Path('local/tools/go1.27.1.linux-amd64.tar.gz')
assert hashlib.sha256(p.read_bytes()).hexdigest() == '63d339f0da5ab53635a56f2490a7984dfe12dfcff22ad749f63edaf590168445'
with tarfile.open(p) as archive:
    archive.extractall('local/tools', filter='data')
PY
GOTOOLCHAIN=local GOCACHE="$PWD/local/tools/go-cache" GOPATH="$PWD/local/tools/go-work" GOMODCACHE="$PWD/local/tools/go-modcache" local/tools/go/bin/go -C local/tools/sega2asm-src build -trimpath -o ../sega2asm .
local/tools/sega2asm --version
sha256sum local/tools/sega2asm
local/tools/go/bin/go version -m local/tools/sega2asm
```

Expected binary SHA-256:
`1b53f26764c1a117033d035431a5e22b2f9806a5b477c2eab4e4b8304b5d9ea4`.
Go archive checksum was independently obtained from the official download API
<https://go.dev/dl/?mode=json>. Original attempted Python urllib fetch stalled;
that owned process was stopped, and bounded curl worked. No remote script was
executed. Tool archives/caches remain ignored and useful for continuation.

## RNC: first block validated through a separate reference

The pinned README associates this title with RNC. A local signature/header scan
found 134 `RNC` occurrences, each followed by method byte 2, each declaring a
packed payload that fits within this ROM. This confirms candidate headers only.
The original scan alone established no successful decoding. TASK-0002 now
validates the first block with independent packed/unpacked CRCs and a separate
reference decoder. The other 133 candidates, resource roles and callers remain
unvalidated. See [[03_Reverse_Engineering/findings/FIND-0004-first-rnc-block]].
The pinned sega2asm RNC2 decoder fails both this block and an authored literal
fixture; see [[03_Reverse_Engineering/findings/FIND-0005-rnc-upstream-defect]].

First candidate: file offset `0x348B2`, packed size 10,803, unpacked size 17,714,
18-byte header; candidate payload ends at `0x372F7`. Stored fields are unpacked
CRC16 `0xAF73`, packed CRC16 `0x3673`. Next signature is at `0x372FC`, five bytes
after that candidate end. Upstream RNC handlers explicitly omit CRC checks;
their README alone is not evidence that they decode this ROM correctly.

Metadata artifact: `local/generated/sega2asm/rnc-candidates.json`. Reproduce
the first actionable candidate without generating assets:

```bash
python3 - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, 'tools')
from rom import inspect_file, verify_expected
p = Path("Original_Game/Wiz 'N' Liz (USA).md")
verify_expected(inspect_file(p))
b = p.read_bytes()
offset = b.find(b'RNC')
h = b[offset:offset + 18]
print(hex(offset), h.hex(), int.from_bytes(h[4:8], 'big'), int.from_bytes(h[8:12], 'big'))
verify_expected(inspect_file(p))
PY
```

The RNC validation task checked both integrity fields and exact consumed end
for this first candidate using a pinned independent method-2 implementation. Do not yet classify all remaining ROM data as RNC.
Stable hypothesis and complete count-reproduction command:
[[03_Reverse_Engineering/findings/FIND-0003-rnc-candidates]].

Related: [[07_Tasks/TASK-0001-foundation]], [[03_Reverse_Engineering/ROM_IDENTITY]].
