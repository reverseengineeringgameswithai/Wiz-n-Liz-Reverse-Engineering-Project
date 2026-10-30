#pragma once
#include <cstddef>
#include <cstdint>

namespace wiz::sim {
// Eight packed decimal digits. Invalid digits in consumed addition operands
// are explicitly unsupported; unconsumed fields remain opaque.
// Scratch is shared arithmetic storage; it retains the last addition operand.
struct ScoreState {
    std::uint32_t value{}, threshold{}, increment{}, scratch{};
    std::uint16_t rewards{};
    bool operator==(const ScoreState&) const = default;
};
struct ScoreResult { bool reward{}; std::size_t threshold_advances{}; };
std::uint32_t add_packed_score(std::uint32_t value, std::uint32_t amount);
// AE1A: at most one reward per invocation, even across several thresholds.
// Equality does not award. All state commits together, including on budget failure.
ScoreResult add_score(ScoreState& state, std::uint32_t amount, std::size_t max_advances = 4096);
} // namespace wiz::sim
