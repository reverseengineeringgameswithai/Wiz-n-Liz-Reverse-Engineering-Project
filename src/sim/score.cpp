#include "sim/score.hpp"
#include "assets/pattern_bank.hpp"

namespace wiz::sim {
std::uint32_t add_packed_score(std::uint32_t value, std::uint32_t amount) {
    std::uint32_t result = 0;
    unsigned carry = 0;
    for (unsigned shift = 0; shift < 32; shift += 4) {
        const auto a = (value >> shift) & 15U, b = (amount >> shift) & 15U;
        if (a > 9 || b > 9) throw assets::BankError("unsupported packed score digit");
        const auto sum = a + b + carry;
        carry = sum >= 10 ? 1U : 0U;
        result |= (sum - 10U * carry) << shift;
    }
    return result; // Eight-digit overflow is discarded by the original four byte writes.
}
ScoreResult add_score(ScoreState& state, std::uint32_t amount, std::size_t max_advances) {
    auto next = state;
    next.value = add_packed_score(next.value,amount);
    next.scratch = amount;
    ScoreResult result;
    if (next.value > next.threshold) {
        result.reward = true;
        // AF28 tests equality with nine, not an upper clamp.
        if (next.rewards != 9) next.rewards = static_cast<std::uint16_t>(next.rewards + 1U);
        do {
            if (result.threshold_advances >= max_advances)
                throw assets::BankError("score threshold budget exhausted");
            ++result.threshold_advances;
            next.threshold = add_packed_score(next.threshold,next.increment);
            next.scratch = next.increment;
        } while (next.value > next.threshold);
    }
    state = next;
    return result;
}
} // namespace wiz::sim
