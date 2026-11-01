---
id: SESSION-2026-11-01-059
type: session
status: completed
---
# Reclaiming local storage

Started clean at `af17d92` on `work/airborne-update`. A side pass at the
user's request ("reduce the space used here"): no native code, ROM, capture
content or external tool changed; session 056 stays the native handoff. The
user's BizHawk GUI and its bridge were running and were left untouched; no
process had files open under `local/`.

Intended checkpoint: `Share identical local captures to reclaim disk space`.

## Survey

The repository used 77 GB, almost all in ignored `local/generated/` (76 GB in
2,170 `run-*` directories; `build/` 429 MB, `local/tools/` 531 MB). Tracked
notes and evidence cite 1,343 of those runs by path (62 GB); the other 827
(12 GB) are uncited reruns. A SHA-256 scan of `local/` found 8,330 groups of
byte-identical files holding 73.7 GB, of which 63.2 GB were repeat copies:
each regression rerun writes the same deterministic traces (five 718 MB copies
of one effect trace, seven 126 MB copies of one session trace), states and
corpora again.

## Decision

Deleting cited runs would break the evidence trail, and once copies share
storage, deleting every uncited run would free only about 0.86 GB more. So
nothing was deleted. `/home` is btrfs (`compress=zstd:1`), so identical files
now share extents through the kernel's FIDEDUPERANGE ioctl: copy-on-write,
with each path keeping its inode, permissions and contents, and the kernel
comparing both ranges before sharing. Hard links were rejected because a
write through one path would change every copy. The reusable tool is
`tools/dedupe_local.py`; usage is in [[02_Workflow/REPRODUCIBILITY]] (local
storage).

## Result

All 8,330 groups now share extents: 63.18 GB of repeat copies, zero failures,
zero mtimes changed or restored, nothing deleted. Free space on `/home` rose
from 310.45 GB to 319.30 GB (about 8.9 GB; `df` is filesystem-wide, so other
processes can move it slightly). The disk saving is far smaller than the
logical 63 GB because btrfs already stored these traces and corpora
zstd-compressed, at roughly 7:1. `du` still reports 77 GB for the logical
copies.

A later report with the committed tool rehashed every file and found the same
8,330 digests, with every scanned path holding its recorded SHA-256. The only
extra paths were two `rnc-sega2asm` probe runs that this pass's own test run
had created after the scan (the pinned sega2asm probes write a run each). The
tool's `--apply` shared their 10.3 MB, and the remaining report shows
nothing reclaimable.

## Validation

- ROM identity verified before and after:
  `d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
- A trial on one five-file group, then the full run; mtimes were checked on
  every file in every group.
- `tests/test_dedupe_local.py`: four synthetic tests (grouping, apply keeps
  paths/contents/inodes/mtimes, report-only, CLI). They pass on tmpfs (no
  extent sharing: reported, nothing changed) and, run ad hoc with `TMPDIR` on
  btrfs, share extents; a second pass then reports them already shared.
- All 267 Python tests pass with no skips; `check-vault`, `check-hygiene` and
  `git diff --check`. Native presets were not rebuilt: no native source
  changed.

## Limitations

`du` still counts every copy, so `du -sh local` is unchanged; free space
(`df`) shows the saving. Exact compressed usage (`compsize`) needs root and was
not measured. Snapshots of `/home`, if any, would keep old extents; none were
checked (that needs root). Future reruns add new copies until the tool is run
again.
