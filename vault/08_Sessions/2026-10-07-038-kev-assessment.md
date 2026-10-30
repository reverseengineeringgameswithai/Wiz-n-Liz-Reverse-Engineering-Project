---
id: SESSION-2026-10-07-038
type: session
status: completed
---
# Local Kev assessment using known project facts

Started clean at `77344706e0f7002827373a1ad63c4b5594b686f8` on
`work/airborne-update`, empty index and no merge/rebase/cherry-pick/revert.
User requested an assessment of `~/AI/Kev`, then resumed after changing the
execution permissions. Actual path is `~/AI/kev`. This pass adds a bounded
research recipe and notes; no native simulation or reference tool changed.
Intended checkpoint: `Assess local Kev against known WizNLiz evidence`.

## Delivered and measured

[[07_Tasks/TASK-0012-kev-assessment]] is complete. Canonical assessment:
[[09_References/KEV]]. `tools/kev_evidence_pilot.py` plus
`re/kev_evidence_pilot.json` prepare or submit 36 pre-labelled claims against
hashed evidence excerpts. Labels/rationales never enter the API. The client is
stdlib-only, localhost-only, proxy/redirect-free and uses the already-running
Kev-27B NVFP4 server; no package, model or external repository was modified.

First form: **35/36**, zero false-supported claims; other cyclic answer orders:
36/36 and 35/36; separate questions: 35/36. One interval-scope error changes
with option order, failing the predeclared unattended-use criterion. This is
36 repeated claims, not 144 independent cases and not native coverage. Nine
grouped questions take median 753 ms with a new state on the loaded server.
Usefulness is advisory evidence screening; no end-to-end time saving is proven.
Raw artifacts: `local/generated/kev-evidence-pilot/run-lrr6ldqg/`;
tracked summary: `re/kev_validation.json`. No prompt/label tuning or rerun.

## Verification and reproduction

```sh
python3 -B tools/kev_evidence_pilot.py
python3 -B tools/kev_evidence_pilot.py --run
python3 -B tools/project.py test
python3 -B tools/project.py rom-identify --verify
python3 -B tools/project.py check-vault
python3 -B tools/project.py check-hygiene
git diff --check
```

Prepare and 16 live API requests completed; all 144 response records have
matching IDs and finite normalized probability distributions. Payload inspection
verified the evaluator fields are absent. The existing synthetic suite passes
208 tests with zero skips. Vault/hygiene/whitespace checks pass. ROM SHA-256
before/after remains `d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.
Native builds/CTests, emulator captures and ROM-dependent differential corpora
were not rerun: no native or emulator code changed.

Initial attempts: uppercase path absent; the lowercase installation was found.
Sandbox denied the localhost socket and GPU query; the user enabled unrestricted
execution, and the existing server then responded. These were environment
restrictions, not model failures. The first vault check also caught a new-task ID
collision with the existing Genesis-reference TASK-0011; this assessment was
renumbered TASK-0012 and the links corrected. The classifier error above remains
recorded.

Kev stayed at `84847f0a883d900f7de5b7a57eaa341ca7f9a6b4`; its pre-existing
untracked INSTALL-local.txt, demo.sh, local/, start-server.sh and start.sh were
preserved. Its existing server stays running; no owned temporary process remains.
Original ROM, recordings, GUI, BizHawk, Sonic19420 and WL3PC were not modified.
Public documentation was read; no project evidence was sent off-host or pushed.

Explicit staging and review precede the local commit. Next task stays **783A
four-object initialization** under [[07_Tasks/TASK-0010-grounded-controller]].
TASK-0010 remains in progress, native playability none, and Musashi/GPGX remain
reference tools outside the native runtime. The Godot ADR remains proposed.

## User acceptance follow-up — 2026-10-07

After checkpoint `e11a187`, the user asked to bank the result and emphasized
that perfect accuracy is not expected. This documentation-only follow-up banks
Kev as an accepted research aid, evaluated by practical usefulness with suitable
review. The original measurements and experimental acceptance rule are preserved;
that rule does not block ordinary advisory use. Canonical assessment, task,
status, next actions and blockers now carry the user's preference.

Started clean on the same branch with no pending Git operation. Vault, hygiene,
whitespace and before/after ROM identity checks pass. No code or inference
changed, so model, Python, native and reference suites were not rerun. Reviewed
explicit staging precedes the checkpoint `Bank accepted practical use of Kev`.
Native playability, reference dependencies and the next 783A task are unchanged.
