---
id: TASK-0003
type: task
status: complete
deliverable: Bounded project-native C++20 RNC2 asset codec with independent differential cases and headless builds
acceptance: ["C++20 decoder rejects invalid reads, backreferences, sizes and unterminated streams without UB", "Authored fixtures cover literal, match, overlap, continuation and termination paths", "Verified first ROM block matches reference bytes, CRCs and exact consumption", "Headless CMake/Ninja debug and release builds plus Clang sanitizer tests pass", "No original CPU execution or reference decoder linked into native component", "Extraction can use the project codec with stable logical IDs and explicit limits"]
---
# First project-native asset codec — complete

Delivered `src/core/rnc2.hpp` / `.cpp`, static library, headless CLI, CMake presets,
build/provenance wrapper and native extraction backend. All six acceptance
criteria passed in [[08_Sessions/2026-10-02-003-native-rnc2]].

Independent authored cases were checked with the pinned reference before the
native decoder was implemented. All 49 cases and the first ROM block match;
debug/release/sanitize tests pass, including bounded malformed-input rejection.
No original CPU stream executes and no reference decoder is linked into the
project library. `rnc-validate --decode` defaults to the native component.

Evidence and format grammar:
[[03_Reverse_Engineering/findings/FIND-0006-native-rnc2]]. Canonical interfaces:
[[03_Reverse_Engineering/ASSET_FORMATS]], [[04_Native_Implementation/ARCHITECTURE]],
[[04_Native_Implementation/PORTING_MAP]], [[05_Validation/RESULTS]].

Limits: this is a native asset component, not gameplay or a mapped original
routine. Resource role/destination and the other 133 candidates remain unknown.
The separate GPL reference remains optional research tooling; this direct
inspection project is not clean-room work. No SDL/game window was introduced.

Prior: [[07_Tasks/TASK-0002-rnc-block]]. Next:
[[07_Tasks/TASK-0004-rnc-loader]].
