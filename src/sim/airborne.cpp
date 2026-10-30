#include "sim/airborne.hpp"

namespace wiz::sim {
namespace {
std::uint16_t word(unsigned value) noexcept { return static_cast<std::uint16_t>(value); }
int signed_word(std::uint16_t value) noexcept {
    return value < 32768U ? static_cast<int>(value) : static_cast<int>(value) - 65536;
}
void air_pixel(const assets::SceneResource& scene, const assets::PatternBank& bank,
               MotionState& state, const AirborneParameters& parameters, TerrainScratch& scratch, bool left) {
    state.position.x = word(state.position.x + (left ? 65535U : 1U));
    if (probe_contact(scene, bank, state.position, ContactProbe::upper, scratch).equal()) {
        state.position.y = word(state.position.y + 65535U);
        auto damping = parameters.motion;
        damping.damping_count_minus_one = parameters.contact_damping_count_minus_one;
        damp_horizontal(state, damping);
    }
}
AirborneResult air_horizontal(const assets::SceneResource& scene, const assets::PatternBank& bank,
                              MotionState& state, const AirborneParameters& parameters,
                              TerrainScratch& scratch, std::size_t max_steps) {
    const auto count = horizontal_step_count(state.horizontal_speed);
    if (count > max_steps) throw assets::BankError("airborne horizontal count exceeds explicit budget");
    AirborneResult result;
    if (!count) {
        result.horizontal_contact = settle_down(scene, bank, state.position, scratch).contact.equal();
        result.settle_calls = 1;
    } else {
        const bool left = (state.horizontal_speed & 0x8000U) != 0;
        for (std::size_t i = 0; i < count; ++i) air_pixel(scene, bank, state, parameters, scratch, left);
        result.horizontal_steps = count;
        // Original nonzero-speed paths force D0.W=FFFF and Z=0, even if speed
        // becomes zero or a terrain equality occurred during the loop.
    }
    return result;
}
AirborneResult pixel_transaction(const assets::SceneResource& scene, const assets::PatternBank& bank,
                                 MotionState& state, const AirborneParameters& parameters,
                                 TerrainScratch& scratch, bool left) {
    auto next = state; auto next_scratch = scratch;
    air_pixel(scene, bank, next, parameters, next_scratch, left);
    state = next; scratch = next_scratch;
    AirborneResult result; result.horizontal_steps = 1; return result;
}
} // namespace

std::size_t airborne_downward_count(std::uint16_t vertical_motion) noexcept {
    const auto value = signed_word(vertical_motion);
    return value < 0 ? static_cast<std::size_t>((-value + 7) / 8) : 0;
}
void set_right_motion_reload(MotionState& state) noexcept {
    const auto speed = signed_word(state.horizontal_speed);
    state.presentation.reload = speed < 32 ? 4 : speed < 64 ? 3 : speed < 96 ? 2 : 1;
}
void set_left_motion_reload(MotionState& state) noexcept {
    const auto speed = signed_word(state.horizontal_speed);
    state.presentation.reload = speed > -32 ? 4 : speed > -64 ? 3 : speed > -96 ? 2 : 1;
}
AirborneResult resolve_landing(MotionState& state, const MotionParameters& parameters) noexcept {
    AirborneResult result; result.landings = 1;
    const bool right = (state.flags & 0x0800U) != 0;
    const bool fast = right ? signed_word(state.horizontal_speed) > signed_word(parameters.positive_limit)
                            : signed_word(state.horizontal_speed) < signed_word(parameters.negative_limit);
    state.presentation.mode = 0x81;
    if (fast) {
        state.presentation.words = {6,12,17};
        state.presentation.counter = state.presentation.reload = 2;
        state.update = right ? MotionUpdate::fast_right : MotionUpdate::fast_left;
    } else {
        state.presentation.words = {0,0,5};
        state.update = right ? MotionUpdate::ground_right : MotionUpdate::ground_left;
        if (right) set_right_motion_reload(state); else set_left_motion_reload(state);
        if (!state.horizontal_speed) {
            state.presentation.mode = 0x80;
            state.presentation.words[0] = 2;
            state.update = right ? MotionUpdate::idle_right : MotionUpdate::idle_left;
            result.immediate_continuation = true;
        }
    }
    return result;
}
AirborneResult step_airborne_left(const assets::SceneResource& scene, const assets::PatternBank& bank,
                                 MotionState& state, const AirborneParameters& parameters, TerrainScratch& scratch) {
    return pixel_transaction(scene, bank, state, parameters, scratch, true);
}
AirborneResult step_airborne_right(const assets::SceneResource& scene, const assets::PatternBank& bank,
                                  MotionState& state, const AirborneParameters& parameters, TerrainScratch& scratch) {
    return pixel_transaction(scene, bank, state, parameters, scratch, false);
}
AirborneResult step_airborne_horizontal(const assets::SceneResource& scene, const assets::PatternBank& bank,
                                       MotionState& state, const AirborneParameters& parameters,
                                       TerrainScratch& scratch, std::size_t max_steps) {
    auto next = state; auto next_scratch = scratch;
    auto result = air_horizontal(scene, bank, next, parameters, next_scratch, max_steps);
    state = next; scratch = next_scratch; return result;
}
AirborneResult step_airborne(const assets::SceneResource& scene, const assets::PatternBank& bank,
                            MotionState& state, const AirborneParameters& parameters,
                            AirborneInput input, TerrainScratch& scratch, AirborneBudget budget) {
    if (state.update != MotionUpdate::airborne && state.update != MotionUpdate::airborne_fall)
        throw assets::BankError("unsupported airborne update handler; consume continuation explicitly");
    auto next = state; auto next_scratch = scratch;
    if (next.update == MotionUpdate::airborne) {
        next.airborne_delay = word(next.airborne_delay + 65535U);
        if (next.airborne_delay & 0x8000U) next.update = MotionUpdate::airborne_fall;
        else if (input.boost) next.vertical_motion = word(next.vertical_motion + 5U);
    }
    damp_horizontal(next, parameters.motion);
    if (!input.acceleration_gate) {
        if (input.left) {
            next.flags &= 0xf7ffU;
            next.horizontal_speed = word(next.horizontal_speed + 65536U - parameters.acceleration);
            clamp_negative(next, parameters.motion);
        } else if (input.right) {
            next.flags |= 0x0800U;
            next.horizontal_speed = word(next.horizontal_speed + parameters.acceleration);
            clamp_positive(next, parameters.motion);
        }
    }
    if (signed_word(next.vertical_motion) >= -48)
        next.vertical_motion = word(next.vertical_motion + 65536U - parameters.gravity);
    auto result = air_horizontal(scene, bank, next, parameters, next_scratch, budget.horizontal);
    if (next.vertical_motion & 0x8000U) {
        bool landed = result.horizontal_contact;
        if (!landed) {
            const auto count = airborne_downward_count(next.vertical_motion);
            if (count > budget.downward) throw assets::BankError("airborne downward count exceeds explicit budget");
            for (std::size_t i = 0; i < count; ++i) {
                ++result.settle_calls;
                if (settle_down(scene, bank, next.position, next_scratch).contact.equal()) { landed = true; break; }
            }
        }
        if (landed) {
            const auto landing = resolve_landing(next, parameters.motion);
            result.landings = landing.landings;
            result.immediate_continuation = landing.immediate_continuation;
        }
    } else {
        next.position.y = word(next.position.y + 65536U - ((next.vertical_motion >> 3U) + 1U));
    }
    state = next; scratch = next_scratch; return result;
}
} // namespace wiz::sim
