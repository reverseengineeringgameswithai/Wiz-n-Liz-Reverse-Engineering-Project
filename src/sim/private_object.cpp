#include "sim/private_object.hpp"
#include "sim/presentation.hpp"

namespace wiz::sim {
void step_private_object(PrivateObject& object, const PrivateGlobals& globals, bool scheduled) {
    if (scheduled && !(object.presentation.mode & 0x80U)) return;
    auto next = object;
    if (scheduled && advance_presentation(next.presentation,next.target))
        throw assets::BankError("unsupported private object callback");
    switch (next.update) {
    case PrivateUpdate::rising:
        if (!globals.rise_gate) {
            next.position.y = 0x106;
            next.countdown = 8;
        } else if (next.position.y != 0xf6) {
            next.countdown = static_cast<std::uint16_t>(next.countdown - 1U);
            if (next.countdown & 0x8000U) {
                next.position.y = static_cast<std::uint16_t>(next.position.y - 1U);
                next.countdown = 8;
            }
        }
        break;
    case PrivateUpdate::gated_visibility:
        if (globals.flags_gate) next.flags = 0x2000;
        if (globals.hide_gate) next.position = {0xff80,0xff80};
        break;
    default: throw assets::BankError("unsupported private object handler");
    }
    object = next;
}
PrivateObject make_visibility_pair_member(PairMember member, const InheritedObjectFields& inherited) noexcept {
    // Neither F9E2 nor 7C26 writes +0E/+10/+4A; 7C26 also leaves +12 cleared.
    const bool second = member == PairMember::second;
    const std::uint16_t first_frame = second ? 902 : 892;
    return {PrivateUpdate::gated_visibility,{287,static_cast<std::uint16_t>(second ? 184 : 152)},0,
        {0x81,{first_frame,first_frame,static_cast<std::uint16_t>(first_frame + 9U)},5,5},
        inherited.target,inherited.countdown,inherited.control};
}
PrivateObject make_rising_pair_member(PairMember member, const InheritedObjectFields& inherited,
        ActorId control, Position first) noexcept {
    const bool second = member == PairMember::second;
    const Position position = second ? Position{static_cast<std::uint16_t>(first.x + 0x20U),first.y} : Position{0x9e,0x106};
    const std::uint16_t frame = second ? 928 : 922;
    return {PrivateUpdate::rising,position,0,{0x81,{frame,frame,static_cast<std::uint16_t>(frame + 5U)},5,5},
        inherited.target,0,control};
}
} // namespace wiz::sim
