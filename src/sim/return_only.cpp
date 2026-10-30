#include "sim/return_only.hpp"
#include "sim/presentation.hpp"

namespace wiz::sim {
void step_return_only_object(ReturnOnlyObject& object) {
    if (!(object.presentation.mode & 0x80U)) return;
    auto next=object;
    if (advance_presentation(next.presentation,next.target))
        throw assets::BankError("unsupported return-only object callback");
    object=next;
}
SpellStep step_spell_countdown(SpellCountdown& object, TransitionState* timer) {
    if (!(object.presentation.mode & 0x80U)) return SpellStep::none;
    auto next=object;
    if (advance_presentation(next.presentation,next.target))
        throw assets::BankError("unsupported spell countdown callback");
    auto step=SpellStep::none;
    if (next.phase==SpellPhase::countdown) {
        next.countdown=static_cast<std::uint16_t>(next.countdown-1U);
        if (next.countdown & 0x8000U) {
            // 7B48: JSR 13294, then +16 = 7B58.
            if (!timer) throw assets::BankError("spell transition timer unavailable");
            start_spell_fade_out(*timer);next.phase=SpellPhase::completion;
        }
    } else {
        // 7B58/7B8A: TST.W FF0B90; BNE to the RTS.
        if (!timer) throw assets::BankError("spell transition timer unavailable");
        if (!timer->direction) step=next.phase==SpellPhase::completion ? SpellStep::complete : SpellStep::revealed;
    }
    object=next;return step;
}
ReturnOnlyObject make_return_only_pair_member(PairMember member,
        const InheritedObjectFields& inherited) noexcept {
    // F9E2 clears +12/+14 and selects both RTS routines; 7B9C replaces mode,
    // all three frame words, position and counter/reload, then sets 0800 on
    // the second member only. +0E/+10/+4A are never written by either.
    const bool second=member==PairMember::second;
    const std::uint8_t cadence=second ? 5 : 4;
    return {{static_cast<std::uint16_t>(second ? 164 : 161),270},static_cast<std::uint16_t>(second ? 0x800 : 0),
        {0x81,{static_cast<std::uint16_t>(second ? 919 : 916),916,921},cadence,cadence},
        inherited.target,inherited.countdown,inherited.control};
}
ReturnOnlyObject make_quad_return_only(QuadMember member, const InheritedObjectFields& inherited, Position probe) {
    if (member == QuadMember::probe) throw assets::BankError("collision quad probe is not return-only");
    if (!inherited.presentation) throw assets::BankError("collision quad inherits unknown presentation");
    const auto& p = *inherited.presentation;
    const auto index = static_cast<std::uint16_t>(member);
    const bool right = member != QuadMember::below, below = member != QuadMember::right;
    const Position position{static_cast<std::uint16_t>(probe.x + (right ? 0x20U : 0U)),
                            static_cast<std::uint16_t>(probe.y + (below ? 0x20U : 0U))};
    return {position,0,{0x80,{static_cast<std::uint16_t>(0x390U + index),p.words[0],p.words[1]},p.counter,p.reload},
        inherited.target,inherited.countdown,inherited.control};
}
ReturnOnlyObject make_dormant(const InheritedObjectFields& inherited) {
    if (!inherited.presentation || !inherited.position) throw assets::BankError("dormant object inherits unknown position or presentation");
    const auto& p = *inherited.presentation;
    return {*inherited.position,0,{0,{0x21d,p.words[0],p.words[1]},p.counter,p.reload},
        inherited.target,inherited.countdown,inherited.control};
}
} // namespace wiz::sim
