#pragma once

#include "sim/movement.hpp"

namespace wiz::sim {
struct AirborneParameters {
    MotionParameters motion;
    std::uint16_t acceleration = 12, contact_damping_count_minus_one = 11, gravity = 4;
};
struct AirborneInput {
    std::uint8_t boost{}, left{}, right{};
    std::uint16_t acceleration_gate{};
};
struct AirborneBudget { std::size_t horizontal = 1024, downward = 4096; };
struct AirborneResult {
    std::size_t horizontal_steps{}, settle_calls{}, landings{};
    // Idle initialization falls directly into its handler. This is a pending
    // same-call continuation, not a completed frame or a deferred next tick.
    bool immediate_continuation{}, horizontal_contact{};
};

std::size_t airborne_downward_count(std::uint16_t vertical_motion) noexcept;
void set_right_motion_reload(MotionState& state) noexcept;
void set_left_motion_reload(MotionState& state) noexcept;
AirborneResult resolve_landing(MotionState& state, const MotionParameters& parameters) noexcept;
AirborneResult step_airborne_left(const assets::SceneResource& scene, const assets::PatternBank& bank,
                                 MotionState& state, const AirborneParameters& parameters, TerrainScratch& scratch);
AirborneResult step_airborne_right(const assets::SceneResource& scene, const assets::PatternBank& bank,
                                  MotionState& state, const AirborneParameters& parameters, TerrainScratch& scratch);
AirborneResult step_airborne_horizontal(const assets::SceneResource& scene, const assets::PatternBank& bank,
                                       MotionState& state, const AirborneParameters& parameters,
                                       TerrainScratch& scratch, std::size_t max_steps = 1024);
// Executes only the delayed/falling airborne entries. Landing handlers remain
// explicit events. Unsupported handlers, budgets and resources fail atomically.
AirborneResult step_airborne(const assets::SceneResource& scene, const assets::PatternBank& bank,
                            MotionState& state, const AirborneParameters& parameters,
                            AirborneInput input, TerrainScratch& scratch, AirborneBudget budget = {});
} // namespace wiz::sim
