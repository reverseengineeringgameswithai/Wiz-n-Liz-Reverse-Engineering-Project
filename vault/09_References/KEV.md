---
id: REFERENCE-KEV
type: reference
status: evaluated
task: TASK-0012
---
# Kev as a local evidence-review assistant

Assessment: [[07_Tasks/TASK-0012-kev-assessment]], session
[[08_Sessions/2026-10-07-038-kev-assessment]]. **Accepted as a useful local
research aid, with review appropriate to the decision.** Native coverage,
playability and the next 783A implementation task are unchanged.

## User decision — 2026-10-07

The user accepted the assessment and asked to bank it: “it's not going to be
100% accurate for everything, nothing is.” Use Kev where it helps check claims
or prioritize investigation; judge it by practical value, error costs and time
saved. Perfect accuracy is not an adoption requirement. The pilot's strict
unattended-acceptance criterion is an experimental result, not a blanket blocker
on using the tool. Keep its measured errors as useful guidance and verify
consequential conclusions through the project's existing evidence workflow.
No additional approval or perfect benchmark is needed for ordinary local
advisory use within the authorized research scope.

## Installed capability

The actual path is `~/AI/kev` (lowercase). The existing server at
`127.0.0.1:8021` serves Kev-27B NVFP4 on the RTX 5090. Source commit:
`84847f0a883d900f7de5b7a57eaa341ca7f9a6b4`; community model revision:
`ba00fe3c9b43fa59ab3e76199f2292d5ca47e0c7`. The model ID is
`kev27b-af0e6d55-lh2048-w4a4-cutlass-20261003`; temperature 1.319507910772894.
The live API reports a 32,768-token state limit, truncation disabled, and one
cached state with an 8,192-token cache budget. These installed limits differ
from upstream's general 65,536-token claim. No limit stress test was run here.

Kev selects among caller-supplied choices, yes/no decisions or ordered ratings;
it does not generate disassembly, C++ implementations, explanations or missing
candidate answers. Its API does not retrieve the vault: the caller supplies
the relevant evidence. Sources: inspected `kev/api.py`, `kev/serve.py`, local
`INSTALL-local.txt`, model loader and live `/v1/models`; upstream
[Kev documentation](https://github.com/jaredpalmer/kev) and the quantization
publisher's [model card](https://huggingface.co/SVPG-Labs/kev-27b-NVFP4).
Local installation records report a 0.01238 grouped/separate probability
difference in an earlier check; BF16 parity is not assumed.

## Measured diagnostic

`re/kev_evidence_pilot.json` registers **36 claims** before inference: twelve
supported, twelve contradicted, twelve insufficient. Evidence is selected
verbatim sections of FIND-0034, FIND-0036, FIND-0032 and PROJECT_STATUS. Labels
and rationales are evaluator-only. Claims cover allocator ownership and
inheritance, rising-pair stores and provenance, collision semantics and scope,
and project readiness. This hand-authored sample measures reading supplied
facts, not discovering unlabelled routines or generating code.

| Request form | Correct / unique claims | Wrongly accepted claims | Label changes from first form |
| --- | --- | --- | --- |
| Original option order, grouped questions | 35 / 36 | 0 | 0 |
| Cyclic option order 1 | 36 / 36 | 0 | 1 |
| Cyclic option order 2 | 35 / 36 | 0 | 0 |
| Original order, separate questions | 35 / 36 | 0 | 0 |

These are the **same 36 claims repeated**, not 144 independent cases. The sole
error is `collision_08`: “FF33E2 is nonzero at frame 1500 of this recording.”
The evidence establishes zero only in `[1066,1100)`, so the correct label is
insufficient. Kev chose contradicted with probability 0.595 in the first form;
one option order changes the label to insufficient. Thus the predeclared
no-label-flips condition for unattended acceptance failed. No prompt or expected
label was changed after seeing the results.

Median wall time for nine grouped questions with a new evidence state was
**753 ms**; cached option-order repeats were 575/570 ms; the separate endpoint
took 1,028 ms per nine-question packet. Four packets are too few for a speed
benchmark. This excludes model loading, evidence retrieval and human review.
Maximum probability differences were 0.171 across the tested order changes and
0.0544 between grouped and separate forms. Probabilities are model scores, not
validated probabilities of a WizNLiz finding being true.

## Where it can help

- **Screen a proposed finding against a small evidence packet.** Flag claims
  that conflict with established register ownership, inherited fields or native
  support. Preserve the evidence path and scope alongside every decision.
- **Flag overclaims in handoffs.** The pilot correctly rejected a playable
  `project.py run`, supported callback79B6 and a fully mapped 121-routine claim.
  The frame-1500 error means interval scope still needs explicit review.
- **Explore candidate ranking later.** Supply a few plausible interpretations
  and an insufficient-evidence option, then use the ranking only to select an
  emulator experiment. Ranking unseen routines, code/data separation and trace
  anomaly detection were not tested; no productivity improvement is established.

For 783A, the useful input would be the existing F9E2 contract plus the exact
four-pop write audit, with questions about retained fields and supported scope.
The scheduled implementation and original/native comparisons remain the source
of truth. Deterministic scripts are better for address equality, hashes, write
counts and arithmetic already specified precisely. Kev cannot recover the
missing public disassembly merely by being given this knowledge base.

Do not fine-tune yet: this pilot does not establish a workload that needs it.
Before automatic use, evaluate a fresh, independently labelled collection of
real drafts, temporal-scope traps and missing-evidence cases; compare with a
simple deterministic baseline and measure reviewer time. Option-order stability
alone never establishes correctness. No new automatic workflow is enabled.

## Reproduce

```sh
python3 -B tools/kev_evidence_pilot.py        # prepare only; no server needed
python3 -B tools/kev_evidence_pilot.py --run  # existing localhost:8021 server
```

The stdlib client disables proxies and redirects, verifies evidence-section
hashes and the model ID, and refuses a truncating server. It starts no server,
installs nothing and writes only beneath ignored `local/generated/`. Evidence
changes require a reviewed new suite; do not silently update expected labels.
The original run is `local/generated/kev-evidence-pilot/run-lrr6ldqg/`:
requests, responses, suite snapshot, model metadata, timing, rows and summary.
Tracked results and hashes: `re/kev_validation.json`.
