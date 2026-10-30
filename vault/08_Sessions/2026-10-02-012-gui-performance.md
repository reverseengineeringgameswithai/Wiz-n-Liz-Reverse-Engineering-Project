---
id: SESSION-20261002-012
type: session
status: complete
task: TASK-0010
---
# Restore normal interactive reference speed and preserve the movie

User requested launching the original game for recording, then reported roughly
two frames per second even at 100% speed. Started clean at
`ed04d7db31797938ce4cc504374c8a826f409d1e` on `work/airborne-update`.
This is an interactive reference setup correction; native TASK-0010 stays in
progress with no new native implementation or native playability claim.

## Diagnosis and applied change

The isolated Genesis GUI installer had selected `DispMethod: 1` (GDI+).
Two owned temporary GUIs using the same frozen runtime, ROM, bridge and 100%
speed settings isolated the renderer variable. Over approximately three seconds,
GDI+ advanced seven frames (2.332 FPS); OpenGL advanced 181 (60.143 FPS).
Both were unpaused with no input overrides or active control lease. Both test
processes were closed afterward. Test bridge port was 19422; Sonic/19420 was
untouched. Configurations, exact measurements and logs are under ignored
`local/logs/gui-performance/`; reproduction script is `compare_gui.py` there.

Set only the isolated runtime's local GUI configuration to OpenGL, retained the
user's controls/settings, and enabled FPS/frame display. The application requires
a restart for the renderer change. Source and all 104 manifest-listed program
binaries remain unchanged; no runtime rebuild or installer execution occurred.
Build ID remains `6caddf552236e2538cef28557605012c6f18f00807e4d1dca9ec1b0c63db89c6`.

Initial live inspection found a pause indicator and little CPU use. The user
clarified continuous crawling; that observation alone did not diagnose the cause.
Speed-reset and GUI automation attempts did not establish a fix. The controlled
renderer comparison above resolved the issue. OpenGL startup emitted a transient
Mono/X11 coordinate warning, but replay, rendering and state save completed.

## Recording preservation and recovery

Requested normal application close via WM_DELETE_WINDOW, after checking the
frontend's close path saves changed movies and stops on save errors. The original
user process was not killed. BizHawk saved:
`~/BizHawkOpenSource/Tools/GenesisDebug/local/runtime/Movies/wiznliz-gameplay-2026-10-02.bk2`.
An immutable-for-this-pass copy is retained locally as
`local/logs/gui-performance/original-wiznliz-gameplay-2026-10-02.bk2`, SHA-256
`e25732bf092a98a06872ed9d291289ad3c6e84b6ed74418ca0494e450571f101`.
The previous quicksave and full pre-change GUI configuration were also copied
into that ignored directory before replacement/restart.

Reopened the same runtime with OpenGL and the saved movie. A bounded local Lua
script replayed the original input log to its exact end, then restored speed 100%,
read/write recording mode and paused. Recorded completion:
`frame=1764 target=1764 mode=RECORD readonly=false paused=true`.
The script saved a fresh GUI checkpoint at
`local/logs/gui-performance/resumed-recording.State`, SHA-256
`6ca6a0a506fe42813c7413c45c69518a544ed6b3d2c18c88db4e596d78e4ff6c`.
No gameplay input was authored by the recovery script. This is movie recovery,
not an assertion of a whole-state differential comparison to the closed process.

The interactive GUI is intentionally left open for the user; the completed Lua
console and unused bridge are closed. Resume with the Pause key. Recording can
continue in the same `.bk2`; the saved original copy remains available. Bulk
movies, screenshots, states, settings and logs stay ignored and are not uploaded.
The original ROM still has SHA-256
`d65718df893f16cc5114b2d94944f5005d0ec2e471b74dd6dcee371bed11a161`.

## Checkpoint and next task

Only three vault notes change; their explicit staged diff was reviewed. Vault
validation passes for 57 notes, hygiene passes for 174 indexed files, and staged
whitespace checks pass. Native tests are not rerun because native code and data
are unchanged. Native playability
remains none. Continue [[07_Tasks/TASK-0010-grounded-controller]] at F76C
presentation scheduling and its callback boundaries after the user's recording.
