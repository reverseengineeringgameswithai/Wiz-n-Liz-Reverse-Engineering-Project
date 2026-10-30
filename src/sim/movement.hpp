#pragma once

#include "sim/terrain.hpp"

namespace wiz::sim {
// Logical handler identities, never original code pointers. Only airborne and
// airborne_fall are executable by the bounded airborne component.
enum class MotionUpdate { retained, airborne, airborne_fall, ground_right, ground_left,
                          fast_right, fast_left, idle_right, idle_left,
                          turn_right, turn_left, reverse_left, reverse_right, jump_entry,
                          fast_reverse_left, fast_reverse_right,
                          up_hold, up_release, down_hold, down_release, return_only, transition_start, transition_wait, coast, tally, tally_wait, tally_palette_wait, exit_tally, exit_tally_wait };
struct MotionPresentation {
    std::uint8_t mode{};
    std::array<std::uint16_t, 3> words{}; // Original +6/+8/+A; rendering use pending.
    std::uint8_t counter{}, reload{};
};
struct MotionState {
    Position position;
    std::uint16_t horizontal_speed{}, vertical_motion{}, airborne_delay{};
    MotionPresentation presentation;
    MotionUpdate update = MotionUpdate::retained;
    std::uint16_t flags{}; // Original actor+0x12; bit 0x0800 selects facing.
};
struct MotionParameters {
    std::uint16_t positive_limit = 192, negative_limit = 0xff40;
    std::uint16_t damping_count_minus_one = 3;
};
struct MotionResult {
    std::size_t horizontal_steps{}, airborne_transitions{};
};

// Exact NEG.W/ASR.W/DBF count; zero speed delegates to settle_down instead.
// In particular 0x8000 yields 64513, not 1025. Host budget is explicit.
std::size_t horizontal_step_count(std::uint16_t speed) noexcept;
void damp_once(MotionState& state) noexcept;
void damp_horizontal(MotionState& state, const MotionParameters& parameters) noexcept;
void clamp_positive(MotionState& state, const MotionParameters& parameters) noexcept;
void clamp_negative(MotionState& state, const MotionParameters& parameters) noexcept;
void enter_airborne(MotionState& state) noexcept;
// Entire update is transactional: unsupported map access or exhausted budget
// leaves both state and terrain scratch unchanged. No per-frame timing implied.
MotionResult step_horizontal(const assets::SceneResource& scene, const assets::PatternBank& bank,
                             MotionState& state, const MotionParameters& parameters,
                             TerrainScratch& scratch, std::size_t max_steps = 1024);
MotionResult step_left(const assets::SceneResource& scene, const assets::PatternBank& bank,
                       MotionState& state, const MotionParameters& parameters, TerrainScratch& scratch);
MotionResult step_right(const assets::SceneResource& scene, const assets::PatternBank& bank,
                        MotionState& state, const MotionParameters& parameters, TerrainScratch& scratch);
} // namespace wiz::sim
