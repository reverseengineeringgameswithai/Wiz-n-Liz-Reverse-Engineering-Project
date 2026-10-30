---
id: FIND-0026
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# Level banner shares terrain scratch

ROM/file-offset identity is SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
Exact hashes, instruction boundaries, transfers and declared reference data are
in `re/level_banner.json`. Native code is `src/sim/banner.*` and its composition
in `src/sim/session.*`. Evidence: `re/banner_session_validation.json`.

## Writer and dataflow

The intervening scratch writer in ordinary movie `[700,1067)` is **63E2**, not
another terrain-query actor. `MOVE.W D1,FF4444` saves the banner row in shared
scratch Y. Native write callbacks report **63E8**, the next PC; pre-instruction
63E2/63E8 hooks establish the actual instruction. Scratch X is retained.
The caller at 17AA0 loads D1.W=6 and calls 63E2 at 17AA4, returning at 17AA8.

The 25-instruction scope `[63E2,644C)` consumes difficulty word FF13E2 (supported
0..3), stage word FF33C4 and row D1.W. It selects one of four ordinary/final
labels through tables at 644C/645C. Equality with final-stage words 7,15,31,55
chooses the final label; this is equality, not an upper-bound test. Both paths
write scratch Y first. Ordinary labels call centered text 17532 with pending
return 6422, reload the saved row, then tail-enter numeric renderer 175D0.
Final labels tail-enter 17532 directly. The original caller return remains
pending through either tail. There is no extra native actor invocation.

The initial tilemap address is E000 plus signed word `(row << 7)`. Numeric
columns add 56,52,54,58 bytes by difficulty, and the numeric argument is
`word(stage + 1)`. Native requests normalize destinations to the low 16 bits
consumed by the renderer. Row 256 crosses the signed-address boundary; row
65535 and stage 65535 retain their original word-wrap behavior.

Native `LevelBannerRequest` contains logical label ID `difficulty*2 + final`,
centered-text destination and an optional number/destination. Text precedes the
number. These are **requests**, not rendered text or pixels. The numeric renderer
is not implemented natively; values greater than 99 are retained as original
word arguments, without inventing decimal clamping. Unsupported difficulty
rejects before publishing scratch. The session returns banner and actor results
only after all phases succeed; actor, tracking, scratch, control and ordinal
roll back on a late unsupported service or budget failure.

## Restricted execution and scope

All 25 dispatcher instructions are compared. Musashi additionally executes 46
original centered-text/glyph/number instructions at `[17532,17558)` and
`[17568,175E8)`, reading only declared label/tables and the 256-byte font map.
Declared VDP writes are sunk, not emulated; no device reads are accepted.
The reference checks five word writes per glyph, lock restoration, scratch X
and D2..D7/A2..A6 preservation, real stack returns and a 2,048-instruction cap.
No callee is replaced with a fabricated RTS. The 46 rendering instructions are
**research-only**, not additional native mappings or pixel comparisons.

66,880 cases per debug/release/sanitize pass: a 65,536-case word sweep distributes
difficulty while covering every stage and row word; 1,344 crossed boundaries
exercise every difficulty, final-stage sides, number wrap and signed row shifts.
This is not the exhaustive Cartesian input space. Primary decoding, region
hashes, closed graph and four GNU instruction checks pass. GNU still ignores
CPU selection; original execution explicitly selects M68000.

One native mapping is added: FUNC-0109. New disjoint classified scope is 792
bytes: 106 native-dispatch code, 166 reference-only callee code and 520 bytes of
declared reference tables/text/font data. No proprietary bytes enter Git.

## Retained movie composition

The early session now schedules the banner before physical-input conversion
and the P1 wrapper. All state/resources/configuration are initialized once; the
35-field seed adds difficulty/stage/row to the existing 32-field seed. Each later
row contains only a held-button mask. Scratch is never reseeded between calls.
The original wrapper returns at **6986**, with SP advanced four bytes. Its
cadence is three conversions / four polls per video frame, unlike the later
six-conversion/eight-poll window. The inactive shared timer precedes the banner.

Writer guards pin scene collision data/addressing, parameters, gate, selector,
mailbox, transition state, difficulty, stage and multiplayer flag. The broad
action snapshot contains one unrelated byte FF33DE: 655A clears it to its
already-zero value each frame. Only that exact zero byte write is accepted;
snapshots must stay zero. This unrelated phase is observed, not reconstructed.
Every other scratch write must match a P1 query pair and its three exact
instruction checkpoints. Overflow/drops reject evidence. Managed and native
traces drain every frame to keep worker responses bounded.

367 early wrappers, 367 banners and twelve sound requests match from a single
seed. Fresh worker captures and independent unhooked endpoints support the
measured schedule; debug comparison can reuse a hash-verified completed capture
through `project.py session-compare`. A reused fixture is explicitly reported as
fresh native comparison, not another original-machine replay.

The movie is unchanged: SHA-256
`c1db675318d4e8b1527f8161fa4b782fe96f1ce4e47f173b66ae782a01b327fd`,
input digest `34434f0aa0b1ebc7dbf4e464cd044ac52436b944bf6a01cdc24c811e1f6c3a88`.
Frozen worker build ID remains
`6caddf552236e2538cef28557605012c6f18f00807e4d1dca9ec1b0c63db89c6`.
No RAM/register/input/ROM edits or controlled experiments were needed this pass.
Canonical endpoint hashes cover declared exposed state, not hidden device bits.

This is an initialized headless simulation slice. Renderer/audio, boot, pause,
up/down world actions, effect allocation and broader world scheduling remain
outside this session API. Their existing bounded components remain available.
Next integrate the measured reversal allocation/effect phase near movie frame
1067 using owned persistent slots/free-list state, without per-call object feeds.
[[07_Tasks/TASK-0010-grounded-controller]] stays in progress; **native playability: none**.
