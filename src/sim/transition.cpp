#include "sim/transition.hpp"

namespace wiz::sim {
std::size_t step_transition_coast(const assets::SceneResource& scene, const assets::PatternBank& bank,
                                MotionState& state, TerrainScratch& scratch, std::size_t max_steps) {
    const auto count = horizontal_step_count(state.horizontal_speed);
    if (count > max_steps) throw assets::BankError("transition coasting budget exhausted");
    auto next = state; auto terrain = scratch;
    const unsigned increment = state.horizontal_speed & 0x8000U ? 65535U : 1U;
    for (std::size_t i = 0; i < count; ++i) {
        next.position.x = static_cast<std::uint16_t>(next.position.x + increment);
        if (probe_contact(scene,bank,next.position,ContactProbe::foot,terrain).equal())
            next.position.y = static_cast<std::uint16_t>(next.position.y - 1U);
        damp_once(next); damp_once(next);
    }
    state = next; scratch = terrain; return count;
}
void start_transition(TransitionState& s) noexcept {
    s.direction = 1; s.level = 14; s.countdown = s.reload = 1;
    s.palette_scope = 0;
    s.curves = {TransitionCurve::exit_red_green,TransitionCurve::exit_red_green,TransitionCurve::exit_blue};
}
void prepare_tally_palette(PalettePreparation& p) noexcept {
    for (std::size_t i = 0; i < p.colors.size(); ++i) {
        const auto color = p.colors[i];
        p.components[i] = {static_cast<std::uint8_t>(((color >> 8U) & 14U) << 2U),
                           static_cast<std::uint8_t>(((color >> 4U) & 14U) << 2U),
                           static_cast<std::uint8_t>((color & 14U) << 2U)};
    }
}
void start_tally_transition(TransitionState& s) noexcept {
    s.direction = 0xffff; s.level = 0; s.countdown = 6; s.reload = 0;
    s.palette_scope = 0;
    s.curves.fill(TransitionCurve::tally);
}
void start_spell_fade_out(TransitionState& s) noexcept {
    s.direction = 1; s.countdown = 6; s.reload = 0;
    s.palette_scope = 0;
    s.curves.fill(TransitionCurve::tally);
}
void start_fade_in(TransitionState& s) noexcept {
    s.direction = 0xffff; s.level = 0; s.countdown = 6; s.reload = 1;
    s.palette_scope = 0;
    s.curves = {TransitionCurve::exit_red_green,TransitionCurve::exit_red_green,TransitionCurve::exit_blue};
}
void step_transition_timer(TransitionState& s) noexcept {
    if (!s.direction) return;
    if (s.countdown) { --s.countdown; return; }
    const bool negative = (s.direction & 0x8000U) != 0;
    s.dirty = 0xffff;
    if (s.level == (negative ? 14 : 0)) s.direction = 0;
    else {
        s.level = static_cast<std::uint16_t>(s.level + (negative ? 2U : 65534U));
        s.countdown = s.reload;
    }
}
} // namespace wiz::sim
