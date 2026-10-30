#pragma once
#include "sim/return_only.hpp"

namespace wiz::sim {
// The four level-setup pair initializers called from [68C4,68D4), each behind
// its own gate word: 7FBE (FF3172), 7154 (FF3174), 735E (FF3176) and 7568
// (FF3178). 7FBE places its lead from the P2 control record; the other three
// use fixed positions.
enum class GatedPair : std::uint8_t { p2_placed, first_fixed, second_fixed, third_fixed };
// The higher-addressed member of an open pair: handler 8040 (7FBE) or 71CE /
// 73D8 / 75E2, F9E2's fixed 12646 service, and +36 naming the lower-addressed
// partner. Its handler counts the countdown down, then re-dresses the lead
// through 5964 and a presentation callback that also places the partner. None
// of that is native: stepping an active lead rejects.
struct GatedLead {
    GatedPair pair{};
    Position position;
    std::uint16_t flags{};
    MotionPresentation presentation;
    std::uint16_t target{}, countdown{};
    ActorId control;
    EffectId partner;
};
struct GatedPairIds { EffectId partner, lead; };
// Active gate, then the unsupported handler. An inactive lead does nothing.
void step_gated_lead(GatedLead& lead);
// F9E2 defaults followed by the initializer's stores for the lower-addressed
// member: mode 80, frame 021D, both RTS selectors, position (FF80,FF80) for
// 7FBE and (0,0) for the others. +08..+0D, target, countdown and link are
// inherited; absent inherited presentation rejects.
ReturnOnlyObject make_gated_partner(GatedPair pair, const InheritedObjectFields& inherited);
// F9E2 defaults followed by the stores for the higher-addressed member: mode 80,
// frame 021D, countdown, handler and `control`. 7FBE places it at
// (+3C - 8, +3E + 18) of the FF0838 control record (`p2_origin`, word wrap) with
// countdown 60; 7154 / 735E / 7568 at (0310,00B0), (039C,0066) and (0234,0078)
// with countdown 30, ignoring `p2_origin`. +08..+0D and the target are
// inherited; absent inherited presentation rejects. The partner identity is
// the caller's to fill once both pops are known.
GatedLead make_gated_lead(GatedPair pair, const InheritedObjectFields& inherited, ActorId control, Position p2_origin);
} // namespace wiz::sim
