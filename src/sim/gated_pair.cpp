#include "sim/gated_pair.hpp"

namespace wiz::sim {
void step_gated_lead(GatedLead& lead) {
    if (!(lead.presentation.mode & 0x80U)) return;
    throw assets::BankError("unsupported gated-pair lead handler");
}
ReturnOnlyObject make_gated_partner(GatedPair pair, const InheritedObjectFields& inherited) {
    if (!inherited.presentation) throw assets::BankError("gated pair partner inherits unknown presentation");
    const auto& p = *inherited.presentation;
    // 7FBE: MOVE.W #FF80 to +02 and +04; the others CLR.W both.
    const std::uint16_t at = pair == GatedPair::p2_placed ? 0xff80 : 0;
    return {{at,at},0,{0x80,{0x21d,p.words[0],p.words[1]},p.counter,p.reload},
        inherited.target,inherited.countdown,inherited.control};
}
GatedLead make_gated_lead(GatedPair pair, const InheritedObjectFields& inherited, ActorId control, Position p2_origin) {
    if (!inherited.presentation) throw assets::BankError("gated pair lead inherits unknown presentation");
    const auto& p = *inherited.presentation;
    constexpr std::array<Position,4> fixed{{{0,0},{0x318,0x98},{0x3a4,0x4e},{0x23c,0x60}}};
    const bool placed = pair == GatedPair::p2_placed;
    const auto origin = placed ? p2_origin : fixed[static_cast<std::size_t>(pair)];
    // SUBQ.W #8 on X and SUBI.W #FFE8 on Y, both word arithmetic.
    const Position position{static_cast<std::uint16_t>(origin.x - 8U),static_cast<std::uint16_t>(origin.y - 0xffe8U)};
    return {pair,position,0,{0x80,{0x21d,p.words[0],p.words[1]},p.counter,p.reload},
        inherited.target,static_cast<std::uint16_t>(placed ? 0x3c : 0x1e),control,{}};
}
} // namespace wiz::sim
