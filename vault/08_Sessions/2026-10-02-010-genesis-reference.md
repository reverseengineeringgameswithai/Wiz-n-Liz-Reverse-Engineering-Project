---
id: SESSION-20261002-010
type: session
status: complete
task: TASK-0011
---
# Integrate independent Genesis capture with native routine comparison

Completed [[07_Tasks/TASK-0011-genesis-reference]]. Started with clean
`c0a67bd2014011975d23f07d1762788aa7ab1372` on `work/airborne-update`.
Read all entry points, canonical workflow/brief, latest airborne handoff,
grounded task, routine metadata and native/reference transports before editing.
No pre-existing Wiz changes or Git operation were present. BizHawkOpenSource's
extensive unrelated dirty work and the live Sonic installation were preserved
by the owning integrator. WL3PC remained strictly read-only.

The emulator/tool implementation lives in BizHawkOpenSource. WizNLizPC receives
only `tools/genesis_reference.py`, the `project.py genesis-compare` dispatch
and canonical notes. Native simulation sources, libraries, resources and
Musashi transport are unchanged. Exact results and commands are in
[[09_References/GENESIS_DEBUGGER]], backed by the external tracked
`Tools/GenesisDebug/wiz/evidence.json` and ignored full artifacts.

Original gameplay was reached from a recorded power-on route. Eight scenario
effect checks pass across 136 gameplay frames, with 135 matched damping calls
agreeing with existing native code. Eleven checkpoint branches validate 33
physical pad-producer observations. A second independent unhooked replay and
save/load replay match the scoped canonical checkpoint hash. Actual reset,
input, settings, binary hashes, stack boundaries and experimental-edit lists
are retained; all lists of edits are empty in these captures.

The initial exploratory probe also matched 101 calls, but its runtime lacked
the build-manifest file; it is not the promoted reproducibility artifact.
The final scripted capture uses complete build ID
`6caddf552236e2538cef28557605012c6f18f00807e4d1dca9ec1b0c63db89c6` and its
exact binary/source manifest. No states are assumed portable across future builds.

Validation PASS: 10 external fixture-consumer tests, 33 pinned metadata
regions plus three new static ranges, all eight scenario-effect checks,
135/135 actual native damping comparisons, 33 physical-producer observations,
independent unhooked and save/load replay equality, and the end-to-end
`project.py genesis-compare` CLI. Existing Wiz regression also passes all
111 Python tests with zero skips and 12/12 debug CTest targets. Exact
regression log: `/tmp/wiz-genesis-integration/regression.log`. Vault check
passes 54 notes; indexed hygiene and whitespace are checked before commit.
No unresolved failure or skipped requested test remains within this narrow
reference-integration scope; debugger-wide limitations are documented externally.

ROM identity is rechecked before/after
the wrapper and capture. No original modifications, system installation,
global changes, publication or new persistent user-facing process occurred.
Commit subject: `Integrate isolated Genesis reference captures with native comparisons`.

**Native playability remains none.** This is new full-machine reference evidence,
not native gameplay replay. Only damping speed is compared dynamically here;
existing scoped Musashi corpora remain the wider semantic reference. The next
native task remains [[07_Tasks/TASK-0010-grounded-controller]], starting from
same-call idle and grounded transitions. Broaden scheduling/pad-mode coverage
after consuming the now-observed producer and dispatcher evidence.
