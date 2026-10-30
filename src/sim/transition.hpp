#pragma once

#include "sim/movement.hpp"

namespace wiz::sim {
// Logical resources. Retained curves are never dereferenced by this component;
// curve evaluation and device writes belong to a separate consumer.
enum class TransitionCurve { retained, exit_red_green, exit_blue, tally };
// Fixed 137CE call with bank index 2: sixteen source colors and sixteen
// blue/green/red intensity triplets. Other banks and palette rendering are separate.
struct PalettePreparation {
    std::array<std::uint16_t,16> colors{};
    std::array<std::array<std::uint8_t,3>,16> components{};
};
void prepare_tally_palette(PalettePreparation& palette) noexcept;
struct TransitionState {
    std::uint16_t direction{}, countdown{}, reload{}, level{};
    std::array<TransitionCurve,3> curves{};
    std::uint16_t dirty{}, palette_scope{};
    Position requested_position{}, saved_position{};
};
// A148: fixed initial pixel count, foot probe, optional Y decrement, then two
// damping operations per pixel. Zero speed performs no terrain query.
// Actor and persistent scratch commit together; the budget precedes all work.
std::size_t step_transition_coast(const assets::SceneResource& scene, const assets::PatternBank& bank,
                                MotionState& state, TerrainScratch& scratch, std::size_t max_steps = 1024);
void start_transition(TransitionState& state) noexcept;
void start_tally_transition(TransitionState& state) noexcept;
// 13294: 1324E's fade-out twin (direction 1, countdown 6, reload 0, palette scope
// 0, the 135EA curves); the level is kept, so the fade runs down from it.
void start_spell_fade_out(TransitionState& state) noexcept;
// 131C2: the fade-in (direction FFFF, level 0, countdown 6, reload 1, palette
// scope 0, the 1356A/1356A/135AA curves).
void start_fade_in(TransitionState& state) noexcept;
// One 1345A invocation, scheduled externally. Exact word countdown and +/-2
// arithmetic: malformed levels are not clamped. This does not render a palette.
void step_transition_timer(TransitionState& state) noexcept;
} // namespace wiz::sim
