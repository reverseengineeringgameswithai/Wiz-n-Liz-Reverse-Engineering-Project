#include "sim/bonus.hpp"

namespace wiz::sim {
BonusResult allocate_bonus(BonusSlots& slots, std::size_t max_probes) {
    if (slots.assigned.empty() || slots.assigned.size() > 4096 || slots.choices.size() > 4096)
        throw assets::BankError("bonus table extent outside supported bounds");
    auto next = slots; BonusResult result;
    auto probe = [&] {
        if (result.probes == max_probes) throw assets::BankError("bonus selection budget exhausted");
        ++result.probes;
    };
    for (unsigned attempt = 0; attempt < 5; ++attempt) {
        std::size_t scan = 0;
        for (;;) {
            probe();
            if (scan >= next.assigned.size()) throw assets::BankError("bonus availability scan escaped table");
            const auto value = next.assigned[scan++];
            if (value & 0x8000U) { slots = std::move(next); return result; }
            if (!value) break;
        }
        if (!next.count || next.count > next.assigned.size() || next.count > next.choices.size())
            throw assets::BankError("bonus selection count outside table");
        for (;;) {
            probe();
            const auto cursor = next.cursor;
            if (cursor == next.count) { next.cursor = 0; continue; }
            next.cursor = static_cast<std::uint16_t>(cursor + 1U);
            // MULU then ADDI.W, ANDI.L and DIVU: discard product high word
            // before the unsigned remainder. Reset is equality, not >=.
            const auto numerator = static_cast<std::uint16_t>(unsigned(cursor) * 17U + 35U);
            const auto index = std::size_t(numerator % next.count);
            if (next.assigned[index]) continue;
            next.assigned[index] = next.choices[index];
            result.assignments.push_back({index,next.choices[index]});
            break;
        }
    }
    slots = std::move(next); return result;
}
} // namespace wiz::sim
