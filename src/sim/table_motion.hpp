#pragma once
#include "sim/reversal.hpp"

namespace wiz::sim {
struct TableMotion {
    Position position;
    std::uint16_t flags{};
    MotionPresentation presentation;
    std::uint16_t target{}, countdown{};
    ActorId control; // Loaded by the original handler, never dereferenced.
    std::size_t cursor{}; // Logical word index in the 24-entry motion cycle.
    std::uint16_t delta_x{}, toggle{};
};
// 7A88, with optional active/presentation phase and fixed return-only service.
// loop_count is the DBRA initial word: even FFFF executes 65,536 iterations.
// The caller's budget bounds work. Consumed invalid cursors and invoked
// callback79B6 reject without publishing presentation or motion changes.
void step_table_motion(TableMotion& object, std::uint16_t loop_count,
    bool scheduled = false, std::size_t budget = 4096);
} // namespace wiz::sim
