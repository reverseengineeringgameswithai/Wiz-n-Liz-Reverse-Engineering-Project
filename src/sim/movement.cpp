#include "sim/movement.hpp"

namespace wiz::sim {
namespace {
std::uint16_t word(unsigned value) noexcept { return static_cast<std::uint16_t>(value); }
int signed_word(std::uint16_t value) noexcept {
    return value < 32768U ? static_cast<int>(value) : static_cast<int>(value) - 65536;
}
MotionResult single_step(const assets::SceneResource& scene, const assets::PatternBank& bank,
                         MotionState& state, const MotionParameters& parameters,
                         TerrainScratch& scratch, bool left) {
    state.position.x = word(state.position.x + (left ? 65535U : 1U));
    if (probe_contact(scene, bank, state.position, ContactProbe::foot, scratch).equal()) return {1,0};
    if (probe_contact(scene, bank, state.position, ContactProbe::upper, scratch).equal()) {
        state.position.y = word(state.position.y + 65535U);
        return {1,0};
    }
    state.position.y = word(state.position.y + 1U);
    if (probe_contact(scene, bank, state.position, ContactProbe::foot, scratch).equal()) return {1,0};
    state.horizontal_speed = word(state.horizontal_speed + (left ? 65532U : 4U));
    if (left) clamp_negative(state, parameters); else clamp_positive(state, parameters);
    enter_airborne(state);
    return {1,1};
}
MotionResult transactional_step(const assets::SceneResource& scene, const assets::PatternBank& bank,
                                MotionState& state, const MotionParameters& parameters,
                                TerrainScratch& scratch, bool left) {
    auto next = state; auto next_scratch = scratch;
    const auto result = single_step(scene, bank, next, parameters, next_scratch, left);
    state = next; scratch = next_scratch;
    return result;
}
} // namespace

std::size_t horizontal_step_count(std::uint16_t speed) noexcept {
    if (!speed) return 0;
    const auto magnitude = (speed & 0x8000U) ? word(0U - speed) : speed;
    const auto shifted = static_cast<unsigned>(magnitude >> 5U) | (magnitude & 0x8000U ? 0xf800U : 0U);
    return shifted + 1U;
}
void damp_once(MotionState& state) noexcept {
    if (state.horizontal_speed)
        state.horizontal_speed = word(state.horizontal_speed + (state.horizontal_speed & 0x8000U ? 1U : 65535U));
}
void damp_horizontal(MotionState& state, const MotionParameters& parameters) noexcept {
    // Each original iteration moves one unit toward zero and then stays there.
    const unsigned count = static_cast<unsigned>(parameters.damping_count_minus_one) + 1U;
    const auto value = signed_word(state.horizontal_speed);
    if (value < 0) {
        const auto magnitude = static_cast<unsigned>(-value);
        state.horizontal_speed = count >= magnitude ? 0 : word(0U - (magnitude - count));
    } else {
        const auto magnitude = static_cast<unsigned>(value);
        state.horizontal_speed = count >= magnitude ? 0 : word(magnitude - count);
    }
}
void clamp_positive(MotionState& state, const MotionParameters& parameters) noexcept {
    if (signed_word(state.horizontal_speed) > signed_word(parameters.positive_limit))
        state.horizontal_speed = parameters.positive_limit;
}
void clamp_negative(MotionState& state, const MotionParameters& parameters) noexcept {
    if (signed_word(state.horizontal_speed) < signed_word(parameters.negative_limit))
        state.horizontal_speed = parameters.negative_limit;
}
void enter_airborne(MotionState& state) noexcept {
    state.presentation = {0x81,{0x3a,0x3c,0x3d},6,6};
    state.vertical_motion = 0;
    state.airborne_delay = 0xffff;
    state.update = MotionUpdate::airborne;
}
MotionResult step_horizontal(const assets::SceneResource& scene, const assets::PatternBank& bank,
                             MotionState& state, const MotionParameters& parameters,
                             TerrainScratch& scratch, std::size_t max_steps) {
    const auto count = horizontal_step_count(state.horizontal_speed);
    if (count > max_steps) throw assets::BankError("horizontal step count exceeds explicit budget");
    auto next = state; auto next_scratch = scratch;
    MotionResult result;
    if (!count) settle_down(scene, bank, next.position, next_scratch);
    const bool left = (state.horizontal_speed & 0x8000U) != 0;
    for (std::size_t i = 0; i < count; ++i) {
        const auto step = single_step(scene, bank, next, parameters, next_scratch, left);
        result.horizontal_steps += step.horizontal_steps;
        result.airborne_transitions += step.airborne_transitions;
        // Original DBF continues even after speed/state-handler changes.
    }
    state = next; scratch = next_scratch;
    return result;
}
MotionResult step_left(const assets::SceneResource& scene, const assets::PatternBank& bank,
                       MotionState& state, const MotionParameters& parameters, TerrainScratch& scratch) {
    return transactional_step(scene, bank, state, parameters, scratch, true);
}
MotionResult step_right(const assets::SceneResource& scene, const assets::PatternBank& bank,
                        MotionState& state, const MotionParameters& parameters, TerrainScratch& scratch) {
    return transactional_step(scene, bank, state, parameters, scratch, false);
}
} // namespace wiz::sim
