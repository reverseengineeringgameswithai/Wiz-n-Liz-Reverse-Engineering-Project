#pragma once
#include "sim/reversal.hpp"
#include <optional>

namespace wiz::sim {
enum class PrivateUpdate { rising, gated_visibility };
struct PrivateGlobals {
    std::uint32_t rise_gate{};
    std::uint16_t flags_gate{}, hide_gate{};
    std::optional<std::uint16_t> table_loop_count{};
};
struct PrivateObject {
    PrivateUpdate update{};
    Position position;
    std::uint16_t flags{};
    MotionPresentation presentation;
    std::uint16_t target{}, countdown{};
    // 7808 loads this link but never dereferences it. Retain its logical
    // identity without requiring a live owner or importing an original address.
    ActorId control;
};
// 7808 / 7CA4, optionally preceded by the active/presentation phase and followed
// by the fixed return-only service. Any invoked callback rejects. Initializers,
// producers of shared gates and other services are outside this bounded API.
// Failure publishes no changes, including prior presentation changes.
void step_private_object(PrivateObject& object, const PrivateGlobals& globals, bool scheduled = false);
// F9E2 defaults followed by 7C26's stores for one gated-visibility member:
// first (287,152) frames 892..901, second (287,184) frames 902..911, both
// counter/reload 5, active mode 81, flags left cleared by F9E2.
PrivateObject make_visibility_pair_member(PairMember member, const InheritedObjectFields& inherited) noexcept;
// F9E2 defaults followed by 7772's stores for one rising member. Both store the
// caller's control (A5) and clear countdown, so only target is inherited.
// First: (158,262) frames 922..927. Second copies the first member's X+32
// (word wrap) and Y, frames 928..933. Both counter/reload 5, mode 81.
PrivateObject make_rising_pair_member(PairMember member, const InheritedObjectFields& inherited,
    ActorId control, Position first) noexcept;
} // namespace wiz::sim
