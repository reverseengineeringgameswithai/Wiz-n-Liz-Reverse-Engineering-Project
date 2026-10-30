---
id: TASK-0012
type: task
status: completed
deliverable: Assess the installed local Kev decision model against known WizNLiz facts and identify useful bounded applications
acceptance: ["Inspect the installed model and API without changing the Kev environment", "Register labelled evidence claims before inference and retain errors", "Measure answer-order and grouped-versus-separate stability", "Record a recommendation, reproduction recipe and limitations without promoting model guesses to game facts"]
---
# Assess Kev as a research aid

User-requested assessment, separate from the native implementation work in
[[07_Tasks/TASK-0010-grounded-controller]]. The existing 783A task remains the
next native change.

Run `tools/kev_evidence_pilot.py` with the preregistered
`re/kev_evidence_pilot.json`: 36 claims, balanced supported/contradicted/
insufficient, against selected verbatim sections of existing findings and
current status. Three cyclic answer orders and a separate-question request
check stability; all variants reuse the same 36 claims. Labels and rationales
are withheld from the API. Raw requests/responses stay in ignored `local/`.

Decision rule: any false-supported claim or label flip prevents unattended
acceptance. Even zero errors justifies only advisory use pending independent
workload evaluation. No model answer establishes unknown game behavior.

Completed in [[08_Sessions/2026-10-07-038-kev-assessment]]. First form 35/36,
rotations 36/36 and 35/36, separate questions 35/36; one interval-scope label
changes with answer order. All acceptance items were delivered; the model's
unattended-use condition failed. Recommendation and limitations:
[[09_References/KEV]]. Native implementation work remains TASK-0010.

User follow-up on 2026-10-07 accepted the assessment and asked to bank it.
Perfect accuracy is not required for useful research assistance. The strict
pilot criterion above remains historical; practical use with suitable review
is accepted as recorded in [[09_References/KEV]].
