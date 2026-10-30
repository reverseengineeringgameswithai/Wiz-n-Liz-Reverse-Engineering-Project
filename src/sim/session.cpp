#include "sim/session.hpp"
#include <type_traits>

namespace wiz::sim {
P1SessionResult step_p1_session(const assets::SceneResource& scene, const assets::PatternBank& bank,
                           P1SessionState& state, const P1SessionConfig& config, ThreeButtonPad held) {
    if (state.invocations >= config.max_invocations)
        throw assets::BankError("P1 session invocation budget exhausted");
    auto next = state;
    P1SessionResult result;
    if (next.transition) { step_transition_timer(*next.transition);result.transition=next.transition; }
    if (config.banner) result.banner = request_level_banner(*config.banner,next.scratch);
    next.control = produce_pad_control(held);
    if (next.control.start || next.control.up || next.control.down)
        throw assets::BankError("P1 session pause/up/down world scheduling unsupported");
    result.actor = step_actor_dispatch(scene,bank,next.actor,next.tracking,config.parameters,
        actor_input(next.control,config.acceleration_gate),next.scratch,config.actor_budget,
        {next.effects ? &*next.effects : nullptr,config.owner});
    if (next.effects)
        result.effects = next.effects->step_active(config.owner,next.actor.motion.position,config.effect_budget);
    ++next.invocations; // The bound above also prevents uint64 overflow.
    static_assert(std::is_nothrow_move_assignable_v<P1SessionState>);
    state = std::move(next);
    return result;
}
} // namespace wiz::sim
