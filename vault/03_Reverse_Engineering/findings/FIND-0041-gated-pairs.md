---
id: FIND-0041
type: finding
status: active
rom_id: ROM-LOCAL-0001
address_space: rom_file_offset_and_m68000_effective_address
confidence: confirmed
task: TASK-0010
---
# 7FBE, 7154, 735E and 7568: the gated pairs of `[68C4,68D4)`

Task: [[07_Tasks/TASK-0010-grounded-controller]]. ROM SHA-256:
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`. Scope/hashes:
`re/setup_pairs_step.json`; validation: `re/setup_pairs_validation.json`.
Source: `src/sim/gated_pair.*`, `src/sim/mixed_pool.*`. Evidence:
`tools/pair_initializer_compare.py --variant setup-pairs`,
`tools/genesis_pair_initializer.py`. Continues
[[03_Reverse_Engineering/findings/FIND-0040-setup-message]].

## Static ranges and contract

| Half-open range | Instructions | Contract |
| --- | --- | --- |
| `[68C4,68D4)` | 4 | BSR 7FBE, BSR 7154, BSR 735E, BSR 7568 (fragment) |
| `[7FBE,8040)` | 28 | Return unless FF3172 is set. MOVEM A5/A6; two BSR F9E2 pops ordered by address; partner (FF80,FF80); lead +36 = partner, countdown 003C, handler 8040, +4A = caller A5, then from FF0838 +3C/+3E: X − 8, Y − FFE8; restore A5/A6 |
| `[7154,71CE)` | 26 | Return unless FF3174 is set. Two JSR F9E2 pops ordered by address; partner (0,0); A5 = FF0690 (left set); lead (0318,0098) − (8,FFE8), countdown 001E, handler 71CE, +4A = A5 |
| `[735E,73D8)` | 26 | As 7154 with gate FF3176, lead (03A4,004E) and handler 73D8 |
| `[7568,75E2)` | 26 | As 7154 with gate FF3178, lead (023C,0060) and handler 75E2 |

Ordering is `LEA (A6),A4` after the first pop, `CMPA.L A6,A4`, `BLT`, `EXG`:
the lower address (A4) is the **partner** and the higher (A6) the **lead**.
Both members get mode 80 and frame 021D; the partner keeps F9E2's 12646 handler
and service, the lead keeps the 12646 service. Neither writes +08..+0D or +0E,
and the partner's +10/+4A are not written, so those bytes are inherited. Lead
positions use word arithmetic: (0310,00B0), (039C,0066), (0234,0078) for the
fixed three. 512 bytes / 110 instructions, none previously classified.

Not reconstructed: the lead handlers. 71CE/73D8/75E2 count +10 down (`SUBQ`,
`BPL`); on expiry they call 5964 (mode 87, frames 0227/021E/0227, target 021E,
counter/reload 3/3, both selectors 12646, callback FAA4, +12 AND 9FFF) and then
replace the callback with 71E2/73EC/75F6, which by static reading re-dresses the
lead, places the partner through 4C08, links it at +3A and sets mode 81 and a
new service (728A for 7154, 7494 for 735E); 8040 is similar with a Y − 4 step.

## Native implementation

`GatedLead` (pool variant 10) carries the pair kind, position, presentation,
target, countdown, control and the partner identity (+36). Stepping an active
lead rejects (`unsupported gated-pair lead handler`); the partner is an ordinary
`ReturnOnlyObject`. `MixedPool::initialize_gated_pair` pops two slots through the
shared F9E2 template, compares the slots' (address-ordered) indices, and fills
the lead's partner after both commit; both slots need verified inherited
presentation. `initialize_gated_pairs(state, GatedPairInputs)` runs `[68C4,68D4)`
with explicit inputs whose producers are not native: the four gate words, the
FF0838 control's +3C/+3E (required only behind FF3172), the caller's A5 (7FBE's
+4A) and the logical FF0690 control. All pops commit together or not at all.
`wiznliz-return-only --pairs` and `--pairs-pool` expose it.

## Restricted original comparison

`--setup-pairs` executes `[68C4,68D4)`, all four initializers and F9E2 from 68C4,
stopping at 68D4 or at FA1E. Each case gives the stack depth, A5, gate words,
the P2 +3C/+3E words, eight member slots and per-member residue; the harness
checks D0–D7/A1–A3 preserved, A0 by outcome, A4/A6/A5 at return, the head, the
selectors, each lead's handler and +36, and every byte outside each member's
contracted set. **8,941 cases per debug/release/sanitize** pass: every stack
depth with all gates open (the original stops at FA1E after each of 0..7 pops),
all sixteen gate combinations with both pop orders, wrapped P2 origins, varied
inherited fields and unrepresentable residue. Native creates 6,269 cases
byte-identically and otherwise rejects at the first failing pop (1,272 exhausted,
1,400 unknown inheritance). All 110 new instructions execute. GNU corroborates
the BSR, MOVEM, CMPA.L/BLT/EXG and register-store forms.

## Ordinary recording evidence

A fresh hooked replay of frames 0..1066 with an independent unhooked endpoint
(`3f66b79f…`, equal) verifies one `[68C4,68D4)` run at frame 629, at the message
step's stack and with A5 = FF0690 (7DB8 had selected MIX THOSE FRUIT). Each
initializer is entered at SP − 4 and returns at once: FF3172..FF3178 are all zero.
The step's only writes are the four BSR return pushes; no F9E2 call occurs, the
52-entry free stack (slots 0..51) is unchanged, no register changes and no
interrupt frame interleaves. Over the whole replay no F9E2 call returns into
these initializers and no open path runs; the gates are still zero at 1066. The
P2 control's +3C/+3E read (0100,00E0) is observed but not consumed. Native
`--pairs-pool` from the 68C4-entry inputs allocates nothing and leaves the same
stack. All earlier comparisons and bounds (780, 823, 853) reproduce; release and
sanitize reuse the capture with twelve matched comparisons each. **The open paths
are therefore compared only by the restricted corpus.**

## Limits and next validation

Newly mapped: 7FBE, 7154, 735E and 7568 (bounded) and the fragment. The lead
handlers 8040/71CE/73D8/75E2 with 5964, their callbacks and 4C08, the gate
producers, the meaning of FF0838 +3C/+3E, the 6EF0 allocating path, the setup
after 68D4 (9874 with AA90A, FCB94, globals), the 6C00 pickup hit, 6D22/FB06,
7AD6/callback79B6 and hit7910 remain unreconstructed or unsupported.
TASK-0010 remains in progress; **native playability: none**.
