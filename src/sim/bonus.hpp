#pragma once

#include "sim/movement.hpp"

namespace wiz::sim {
// Associated control tables, not actor objects. Negative assigned words stop
// the availability scan; zero means empty. Source values remain uninterpreted.
struct BonusSlots {
    std::vector<std::uint16_t> assigned, choices;
    std::uint16_t count{}, cursor{};
};
struct BonusAssignment {
    std::size_t slot{};
    std::uint16_t value{};
    bool operator==(const BonusAssignment&) const = default;
};
struct BonusResult {
    std::vector<BonusAssignment> assignments;
    std::size_t probes{};
};
// Up to five assignments, preserving partial success on a negative sentinel.
// Only 4770's D2=0 path is modeled. Invalid extents/counts or exhausted work
// reject atomically; a source zero or negative word is preserved exactly.
BonusResult allocate_bonus(BonusSlots& slots, std::size_t max_probes = 4096);
} // namespace wiz::sim
