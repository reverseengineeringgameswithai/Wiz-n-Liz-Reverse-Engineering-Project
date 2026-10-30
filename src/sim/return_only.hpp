#pragma once
#include "sim/reversal.hpp"
#include "sim/transition.hpp"

namespace wiz::sim {
// Typed 12646 handler + 12646 service. Occupancy is independent of activity;
// dormant instances are retained and cannot be allocated over. The verified
// initializers are the 7B9C pair, 783A's last three members and the 6EC8/6EDC
// dormant objects below; no activation producer, release or callback is
// implied by this type.
struct ReturnOnlyObject {
    Position position;
    std::uint16_t flags{};
    MotionPresentation presentation;
    std::uint16_t target{}, countdown{};
    ActorId control; // Preserved, never dereferenced by either RTS.
};
// Active gate, presentation, then the two fixed RTS invocations. Any invoked
// callback rejects transactionally, including an original null callback.
void step_return_only_object(ReturnOnlyObject& object);
// The FF31C0 anchor after 7AD6's second-ingredient path (7AE6): handler 7B42
// with the delivering control at +4A and +10 counting down from 012C, then
// 7B58 (the spell's completion, after the fade-out) and 7B8A (after the fade-in).
enum class SpellPhase : std::uint8_t { countdown, completion, reveal };
struct SpellCountdown {
    Position position;
    std::uint16_t flags{};
    MotionPresentation presentation;
    std::uint16_t target{}, countdown{};
    ActorId control;
    SpellPhase phase = SpellPhase::countdown;
};
enum class SpellStep : std::uint8_t { none, complete, revealed };
// One walk: active gate, presentation (a callback rejects), then the handler.
// 7B42: SUBQ.W #1,+10 and BPL; a negative result runs 13294 on `timer` and
// selects 7B58. 7B58 and 7B8A return while FF0B90 is nonzero; once it is zero
// they report `complete` (the caller posts D269, runs 7E18 and 1324E and selects
// 7B8A) or `revealed` (the caller installs the 12646 RTS handler). A missing
// timer rejects. Only the returned work remains for the caller.
SpellStep step_spell_countdown(SpellCountdown& object, TransitionState* timer);

// F9E2 defaults followed by 7B9C's stores for one member of the pair:
// first (161,270) frames 916..921 counter/reload 4; second (164,270) starting
// at frame 919, counter/reload 5, flags 0800. Both active mode 81.
ReturnOnlyObject make_return_only_pair_member(PairMember member,
    const InheritedObjectFields& inherited) noexcept;
// F9E2 defaults followed by 783A's stores for one of its three return-only
// members: mode 80, frame 913/914/915 and the probe's position plus 32 in X,
// Y or both (word wrap). Everything else F9E2 leaves, including +08..+0D, the
// target, countdown and control link, is inherited; absent presentation rejects.
ReturnOnlyObject make_quad_return_only(QuadMember member, const InheritedObjectFields& inherited, Position probe);
// F9E2 defaults followed by 6EC8/6EDC's only store, mode 0: the object stays
// dormant with frame 021D, flags 0 and both RTS selectors. Position, +08..+0D,
// target, countdown and link are inherited; absent position or presentation
// rejects.
ReturnOnlyObject make_dormant(const InheritedObjectFields& inherited);
} // namespace wiz::sim
