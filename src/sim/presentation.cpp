#include "sim/presentation.hpp"
#include <optional>

namespace wiz::sim {
namespace {
void complete_turn(ActorState& a, bool right) noexcept {
    auto& s = a.motion;
    s.presentation = {0x81,{2,0,5},4,4};
    s.flags = static_cast<std::uint16_t>(right ? s.flags | 0x0800U : s.flags & 0xf7ffU);
    s.update = right ? MotionUpdate::ground_right : MotionUpdate::ground_left;
    // Original initializers retain target, cycles and callback identity.
}
void callback(ActorState& a) {
    switch (a.callback) {
    case PresentationCallback::enter_airborne: enter_airborne(a.motion); return; // AA50 ends with RTS.
    case PresentationCallback::action_hold: a.motion.presentation.mode = 0x80; return;
    case PresentationCallback::turn_right:
    case PresentationCallback::fast_reverse_right:
    case PresentationCallback::reverse_right: complete_turn(a,true); return;
    case PresentationCallback::turn_left:
    case PresentationCallback::fast_reverse_left:
    case PresentationCallback::reverse_left: complete_turn(a,false); return;
    case PresentationCallback::fast_jump_right:
    case PresentationCallback::fast_jump_left:
        a.presentation_cycles = static_cast<std::uint16_t>(a.presentation_cycles - 1U);
        if (a.presentation_cycles) a.motion.presentation.words[0] = a.motion.presentation.words[1];
        else a.motion.presentation = {0x81,{24,24,29},2,2};
        return;
    default: throw assets::BankError("unsupported presentation callback");
    }
}
} // namespace

bool advance_presentation(MotionPresentation& p, std::uint16_t target) noexcept {
    if (!(p.mode & 1U)) return false;
    p.counter = static_cast<std::uint8_t>(p.counter - 1U);
    if (p.counter) return false;
    p.counter = p.reload;
    const auto previous = p.words[0];
    const bool fire = (p.mode & 4U) && previous == target;
    const bool reverse = (p.mode & 2U) != 0;
    p.words[0] = static_cast<std::uint16_t>(previous + (reverse ? 65535U : 1U));
    if (previous == p.words[reverse ? 1 : 2]) {
        if (p.mode & 8U) { p.mode ^= 2U; p.words[0] = previous; }
        else p.words[0] = p.words[reverse ? 2 : 1];
    }
    return fire;
}
bool step_presentation(ActorState& state) {
    auto next = state;
    const bool fire = advance_presentation(next.motion.presentation,next.presentation_target);
    // The comparison used the OLD frame, but the callback sees the advanced
    // frame (including looping/bouncing). The tail jump keeps the caller RTS.
    if (fire) callback(next);
    state = next;
    return fire;
}

namespace {
ActorResult actor_phase(const assets::SceneResource& scene, const assets::PatternBank& bank,
                        ActorState& state, const ActorParameters& parameters, ActorInput input,
                        TerrainScratch& scratch, ActorBudget budget, ReversalContext effects,
                        ActionGlobals* actions, TransitionState* transition, TallyState* tally, PalettePreparation* palette, bool scheduled) {
    if (scheduled && !(state.motion.presentation.mode & 0x80U)) return {};
    auto next = state; auto terrain = scratch; ActorResult result;
    std::optional<ReversalEffects> objects;
    if (effects.effects) objects = *effects.effects;
    std::optional<ActionGlobals> globals;
    if (actions) globals = *actions;
    std::optional<TransitionState> fade;
    if (transition) fade = *transition;
    std::optional<TallyState> totals;
    if (tally) totals = *tally;
    std::optional<PalettePreparation> prepared;
    if (palette) prepared = *palette;
    auto invoke = [&] {
        auto step = step_actor(scene,bank,next,parameters,input,terrain,
            {budget.continuations - result.handler_entries,budget.horizontal - result.horizontal_steps,budget.downward,budget.bonus_probes - result.bonus_probes,budget.score_advances - result.score_advances},
            {objects ? &*objects : nullptr,effects.owner},globals ? &*globals : nullptr,fade ? &*fade : nullptr,totals ? &*totals : nullptr,prepared ? &*prepared : nullptr);
        result.handler_entries += step.handler_entries;
        result.horizontal_steps += step.horizontal_steps;
        result.settle_calls += step.settle_calls; result.landings += step.landings;
        result.sound_requests.insert(result.sound_requests.end(),step.sound_requests.begin(),step.sound_requests.end());
        result.spawned_effects.insert(result.spawned_effects.end(),step.spawned_effects.begin(),step.spawned_effects.end());
        result.sample_requests.insert(result.sample_requests.end(),step.sample_requests.begin(),step.sample_requests.end());
        result.bonus_assignments.insert(result.bonus_assignments.end(),step.bonus_assignments.begin(),step.bonus_assignments.end());
        result.bonus_probes += step.bonus_probes;
        result.score_advances += step.score_advances;
    };
    if (advance_presentation(next.motion.presentation,next.presentation_target)) {
        if (next.callback == PresentationCallback::action_idle) {
            // A196 branches by the retained facing bit into A1A4/A22C; those
            // initializers FALL THROUGH into idle with the F76C return pending.
            auto& m = next.motion;
            m.presentation.mode = 0x80; m.presentation.words[0] = 2;
            m.update = (m.flags & 0x0800U) ? MotionUpdate::idle_right : MotionUpdate::idle_left;
            invoke();
        } else callback(next);
    }
    // F900 selects +16 again even when a callback already executed a handler.
    if (scheduled) invoke();
    if (objects) *effects.effects = std::move(*objects);
    if (globals) *actions = *globals;
    if (fade) *transition = *fade;
    if (totals) *tally = *totals;
    if (prepared) *palette = *prepared;
    state = next; scratch = terrain; return result;
}
} // namespace

ActorResult step_actor_presentation(const assets::SceneResource& scene, const assets::PatternBank& bank,
                                    ActorState& state, const ActorParameters& parameters,
                                    ActorInput input, TerrainScratch& scratch, ActorBudget budget,
                                    ReversalContext effects, ActionGlobals* actions, TransitionState* transition, TallyState* tally, PalettePreparation* palette) {
    return actor_phase(scene,bank,state,parameters,input,scratch,budget,effects,actions,transition,tally,palette,false);
}
ActorResult step_scheduled_actor(const assets::SceneResource& scene, const assets::PatternBank& bank,
                                 ActorState& state, const ActorParameters& parameters,
                                 ActorInput input, TerrainScratch& scratch, ActorBudget budget,
                                 ReversalContext effects, ActionGlobals* actions, TransitionState* transition, TallyState* tally, PalettePreparation* palette) {
    return actor_phase(scene,bank,state,parameters,input,scratch,budget,effects,actions,transition,tally,palette,true);
}

void begin_coasting(ActorState& state, ActorTracking& tracking) noexcept {
    tracking.selector = 0xffff;
    state.motion.presentation.mode = 0x80;
    state.motion.presentation.words[0] = 0x21d;
    state.motion.update = MotionUpdate::coast;
}
void begin_exit_transition(ActorState& state, ActorTracking& tracking) noexcept {
    begin_coasting(state,tracking);
    state.motion.update = MotionUpdate::transition_start;
}

ActorResult step_actor_dispatch(const assets::SceneResource& scene, const assets::PatternBank& bank,
                                ActorState& state, ActorTracking& tracking, const ActorParameters& parameters,
                                ActorInput input, TerrainScratch& scratch, ActorBudget budget,
                                ReversalContext effects, ActionGlobals* actions, TransitionState* transition, TallyState* tally, PalettePreparation* palette) {
    auto next = state; auto terrain = scratch; auto tracked = tracking; ActorResult result;
    std::optional<ReversalEffects> objects;
    if (effects.effects) objects = *effects.effects;
    std::optional<ActionGlobals> globals;
    if (actions) globals = *actions;
    std::optional<TransitionState> fade;
    if (transition) fade = *transition;
    std::optional<TallyState> totals;
    if (tally) totals = *tally;
    std::optional<PalettePreparation> prepared;
    if (palette) prepared = *palette;
    // The original tests activity once, before presentation. Do not recheck
    // after a callback changes the mode; the service still follows the handler.
    if (next.motion.presentation.mode & 0x80U) {
        result = step_scheduled_actor(scene,bank,next,parameters,input,terrain,budget,
            {objects ? &*objects : nullptr,effects.owner},globals ? &*globals : nullptr,fade ? &*fade : nullptr,totals ? &*totals : nullptr,prepared ? &*prepared : nullptr);
        if (next.service != ActorService::return_only)
            throw assets::BankError("unsupported actor service");
    }
    if (tracked.selector == 0xffffU) tracked.position = {0xff80,0xff80};
    else tracked.position = {static_cast<std::uint16_t>(next.motion.position.x + 4U),
                             static_cast<std::uint16_t>(next.motion.position.y + 6U)};
    if (objects) *effects.effects = std::move(*objects);
    if (globals) *actions = *globals;
    if (fade) *transition = *fade;
    if (totals) *tally = *totals;
    if (prepared) *palette = *prepared;
    state = next; scratch = terrain; tracking = tracked; return result;
}
} // namespace wiz::sim
