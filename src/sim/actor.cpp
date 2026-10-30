#include "sim/actor.hpp"
#include <optional>
#include <algorithm>

namespace wiz::sim {
namespace {
std::uint16_t word(unsigned v) noexcept { return static_cast<std::uint16_t>(v); }
int signed_word(std::uint16_t v) noexcept { return v < 32768U ? int(v) : int(v) - 65536; }
void facing(MotionState& s, bool right) noexcept {
    s.flags = word(right ? s.flags | 0x0800U : s.flags & 0xf7ffU);
}
void idle(MotionState& s, bool right) noexcept {
    s.presentation.mode = 0x80; s.presentation.words[0] = 2;
    facing(s,right); s.update = right ? MotionUpdate::idle_right : MotionUpdate::idle_left;
}
void ground_entry(MotionState& s, bool right) noexcept {
    s.presentation = {0x81,{2,0,5},4,4}; facing(s,right);
    s.update = right ? MotionUpdate::ground_right : MotionUpdate::ground_left;
}
void turn_entry(ActorState& a, bool right, bool reverse) noexcept {
    auto& s = a.motion;
    s.presentation = reverse ? MotionPresentation{0x87,{23,19,23},3,3}
                             : MotionPresentation{0x87,{47,42,47},3,3};
    a.presentation_target = reverse ? 19 : 42;
    if (!reverse) facing(s,right);
    a.callback = reverse ? (right ? PresentationCallback::reverse_right : PresentationCallback::reverse_left)
                         : (right ? PresentationCallback::turn_right : PresentationCallback::turn_left);
    s.update = reverse ? (right ? MotionUpdate::reverse_right : MotionUpdate::reverse_left)
                       : (right ? MotionUpdate::turn_right : MotionUpdate::turn_left);
}
void action_entry(ActorState& a, bool up) noexcept {
    a.motion.presentation = up ? MotionPresentation{0x85,{30,30,35},3,3}
                               : MotionPresentation{0x85,{36,36,41},3,3};
    a.presentation_target = up ? 34 : 40;
    a.callback = PresentationCallback::action_hold;
    a.motion.update = up ? MotionUpdate::up_hold : MotionUpdate::down_hold;
}
void consume_tally_unit(TallyState& t, ActorInput input, ActorResult& result) {
    // 537C can be called or tail-entered. Its caller decides what follows RTS.
    if (!t.skip && input.start) t.skip = 0xffff;
    else if (!(t.countdown & 0x8000U)) { --t.countdown; return; }
    --t.remaining;
    t.credit = std::min<std::uint16_t>(word(t.credit + 3U),180);
    t.countdown = 3;
    result.sound_requests.push_back({140,6,192,1});
}
void jump(ActorState& a, const ActorParameters& p, ActorResult& result, bool fast, bool right) {
    auto& s = a.motion;
    if (fast) {
        s.presentation = {0x85,{62,62,63},2,2};
        a.presentation_target = 63; a.presentation_cycles = 2;
        a.callback = right ? PresentationCallback::fast_jump_right : PresentationCallback::fast_jump_left;
    } else s.presentation = {0x81,{58,60,61},6,6};
    result.sound_requests.push_back({60,1,192,1});
    result.sound_requests.push_back({107,1,192,2});
    s.airborne_delay = p.jump_delay; s.vertical_motion = p.jump_impulse;
    s.update = MotionUpdate::airborne;
}
} // namespace

ActorResult step_actor(const assets::SceneResource& scene, const assets::PatternBank& bank,
                       ActorState& state, const ActorParameters& parameters,
                       ActorInput input, TerrainScratch& scratch, ActorBudget budget, ReversalContext effects,
                       ActionGlobals* actions, TransitionState* transition, TallyState* tally, PalettePreparation* palette) {
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
    auto& s = next.motion; const auto& motion = parameters.airborne.motion;
    auto horizontal = [&] {
        const bool settles = !s.horizontal_speed;
        const auto r = step_horizontal(scene,bank,s,motion,terrain,budget.horizontal - result.horizontal_steps);
        result.horizontal_steps += r.horizontal_steps;
        result.settle_calls += settles ? 1U : 0U;
    };
    auto accelerate = [&](bool right) {
        s.horizontal_speed = word(s.horizontal_speed + (right ? unsigned(parameters.ground_acceleration)
                                      : 65536U - parameters.ground_acceleration));
        if (right) clamp_positive(s,motion); else clamp_negative(s,motion);
    };
    for (;;) {
        if (result.handler_entries >= budget.continuations)
            throw assets::BankError("actor continuation budget exhausted");
        ++result.handler_entries;
        const auto handler = s.update;
        if (handler == MotionUpdate::return_only) break; // Verified 12646 RTS, not an unknown selector.
        if (handler == MotionUpdate::airborne || handler == MotionUpdate::airborne_fall) {
            const auto r = step_airborne(scene,bank,s,parameters.airborne,
                {input.jump,input.left,input.right,input.acceleration_gate},terrain,
                {budget.horizontal - result.horizontal_steps,budget.downward});
            result.horizontal_steps += r.horizontal_steps; result.settle_calls += r.settle_calls;
            result.landings += r.landings;
            // Only zero-speed landing falls through. All other landings RTS.
            if (r.immediate_continuation) continue;
            break;
        }
        if (handler == MotionUpdate::tally && !totals)
            throw assets::BankError("tally handler requires tally state");
        if (handler == MotionUpdate::tally_palette_wait ||
            (handler == MotionUpdate::tally && totals->palette_gate)) {
            if (!fade) throw assets::BankError("tally palette path requires transition state");
            result.horizontal_steps += step_transition_coast(scene,bank,s,terrain,budget.horizontal - result.horizontal_steps);
            if (fade->direction) break;
            if (handler == MotionUpdate::tally_palette_wait) s.update = MotionUpdate::tally_wait;
            else {
                if (!prepared) throw assets::BankError("tally palette path requires palette preparation state");
                prepare_tally_palette(*prepared);
                start_tally_transition(*fade);
                s.update = MotionUpdate::tally_palette_wait;
            }
            // Both assignments end in RTS. Neither new handler executes now.
            break;
        }
        if (handler == MotionUpdate::tally || handler == MotionUpdate::tally_wait) {
            if (!totals) throw assets::BankError("tally handler requires tally state");
            auto& t = *totals;
            // 51CE -> 5222 is an immediate branch, without replacing +16.
            result.horizontal_steps += step_transition_coast(scene,bank,s,terrain,budget.horizontal - result.horizontal_steps);
            if (t.remaining) {
                consume_tally_unit(t,input,result);
            } else if (t.skip || input.start) {
                if (!t.skip && !t.special_gate && !(input.raw_buttons & 0x40U)
                    && (input.raw_buttons & 0x10U) && !(input.raw_buttons & 0x20U))
                {
                    if (!t.bonus) throw assets::BankError("bonus allocation path requires slot state");
                    result.sample_requests.push_back({ActionSample::up_action,200,0x0f14});
                    t.special_gate = 0xffff;
                    const auto allocated = allocate_bonus(*t.bonus,budget.bonus_probes - result.bonus_probes);
                    result.bonus_probes += allocated.probes;
                    result.bonus_assignments.insert(result.bonus_assignments.end(),allocated.assignments.begin(),allocated.assignments.end());
                }
                if (!globals) throw assets::BankError("tally completion requires shared action globals");
                globals->mode = 3;
            }
            break;
        }
        if (handler == MotionUpdate::exit_tally || handler == MotionUpdate::exit_tally_wait) {
            result.horizontal_steps += step_transition_coast(scene,bank,s,terrain,budget.horizontal - result.horizontal_steps);
            if (handler == MotionUpdate::exit_tally) {
                if (!totals) throw assets::BankError("exit tally requires tally state");
                auto& t = *totals;
                if (t.remaining) {
                    consume_tally_unit(t,input,result);
                    if (!t.remaining) t.countdown = 60;
                    break; // Even consuming the last unit cannot start the transition now.
                }
                if (!t.exit_state) throw assets::BankError("exit tally requires exit state");
                if (t.exit_state->secondary_gate && t.exit_state->secondary_remaining) {
                    if (!t.score) throw assets::BankError("secondary tally requires score state");
                    if (!t.skip && input.start) t.skip = 0xffff;
                    else if (!(t.countdown & 0x8000U)) { --t.countdown; break; }
                    --t.exit_state->secondary_remaining;
                    const auto scored = add_score(*t.score,0x00010000U,budget.score_advances - result.score_advances);
                    result.score_advances += scored.threshold_advances;
                    if (scored.reward) result.sample_requests.push_back({ActionSample::score_reward,230,0x20e4});
                    result.sound_requests.push_back({140,6,192,1});
                    t.countdown = 3;
                    break; // Tail-entered 53F2 returns to the wrapper, even on the last unit.
                }
                if (!t.skip && !input.start) break;
                if (!fade) throw assets::BankError("exit tally requires transition state");
                s.update = MotionUpdate::exit_tally_wait;
                start_transition(*fade); // 13208 tail executes now; 5188 remains deferred.
            } else {
                if (!fade) throw assets::BankError("exit tally wait requires transition state");
                if (fade->direction) break;
                if (!totals || !totals->exit_state) throw assets::BankError("exit tally wait requires exit state");
                if (!globals) throw assets::BankError("exit tally completion requires shared action globals");
                fade->saved_position = fade->requested_position;
                auto& e = *totals->exit_state;
                if (e.selection == e.target_selection) e.marker = 0;
                globals->mode = 1;
            }
            break;
        }
        if (handler == MotionUpdate::coast) {
            // 632A tail-jumps to A148 with the handler caller's return pending.
            result.horizontal_steps += step_transition_coast(scene,bank,s,terrain,budget.horizontal - result.horizontal_steps);
            break;
        }
        if (handler == MotionUpdate::transition_start || handler == MotionUpdate::transition_wait) {
            if (!fade) throw assets::BankError("transition handler requires transition state");
            result.horizontal_steps += step_transition_coast(scene,bank,s,terrain,budget.horizontal - result.horizontal_steps);
            if (handler == MotionUpdate::transition_start) {
                s.update = MotionUpdate::transition_wait;
                start_transition(*fade); // Tail JMP returns to the actor caller; wait is deferred.
            } else if (!fade->direction) {
                if (!globals) throw assets::BankError("transition completion requires shared action globals");
                fade->saved_position = fade->requested_position;
                globals->mode = 7;
            }
            break;
        }
        if (handler == MotionUpdate::jump_entry) { jump(next,parameters,result,false,false); continue; }
        if (handler == MotionUpdate::up_release || handler == MotionUpdate::down_release) break;
        if (handler == MotionUpdate::up_hold || handler == MotionUpdate::down_hold) {
            // 9D44/9DC4 only replace the handler and RTS. Jump executes later.
            if (input.jump) { s.update = MotionUpdate::jump_entry; break; }
            const bool up = handler == MotionUpdate::up_hold;
            if (up) {
                if (!globals) throw assets::BankError("up action requires shared action globals");
                if (globals->mode == 19 && signed_word(globals->cooldown) < 0 && !(input.raw_buttons & 0x40U)) {
                    const auto delay = word(globals->interval - 10U);
                    // SUBI.W then BPL uses the wrapped N flag, not signed BLT.
                    globals->cooldown = signed_word(delay) < 0 ? 0 : delay;
                    result.sample_requests.push_back({ActionSample::up_action,200,0x0f14});
                    globals->interval = word(globals->interval + 3U);
                }
            }
            if (up ? input.up != 0 : input.down != 0) break;
            s.presentation.mode = 0x87;
            next.presentation_target = word(s.presentation.words[1] + 1U);
            s.presentation.counter = s.presentation.reload = 2;
            s.update = up ? MotionUpdate::up_release : MotionUpdate::down_release;
            next.callback = PresentationCallback::action_idle;
            break;
        }
        const bool is_idle = handler == MotionUpdate::idle_right || handler == MotionUpdate::idle_left;
        const bool is_ground = handler == MotionUpdate::ground_right || handler == MotionUpdate::ground_left;
        const bool is_fast = handler == MotionUpdate::fast_right || handler == MotionUpdate::fast_left;
        if (is_idle || is_ground || is_fast) {
            // A1FA may remove its caller return. Query map bit 15, not the
            // contact byte; above-map queries preserve the previous scratch.
            if (input.drop && !(query_terrain(scene,bank,word(s.position.x+12U),
                                            word(s.position.y+23U),terrain).map_word & 0x8000U)) {
                s.position.y = word(s.position.y+2U); enter_airborne(s); continue;
            }
            const bool right = handler == MotionUpdate::idle_right || handler == MotionUpdate::ground_right
                               || handler == MotionUpdate::fast_right;
            const bool same = right ? input.right != 0 : input.left != 0;
            const bool opposite = right ? input.left != 0 : input.right != 0;
            if (is_idle) {
                // Same-facing direction wins over the other direction and jump.
                if (same) { ground_entry(s,right); break; }
                if (opposite) { turn_entry(next,!right,false); break; }
                if (input.jump) { jump(next,parameters,result,false,right); continue; }
                damp_horizontal(s,motion);
                if (!s.horizontal_speed && (input.up || input.down)) {
                    action_entry(next,input.up != 0); continue; // Up wins; no terrain settling on this path.
                }
                horizontal(); break;
            }
            // A546 checks reversal before the jump gate. A408 and both fast
            // entries check jump first. Do not symmetrize these priorities.
            if (is_ground && !right && opposite) { turn_entry(next,true,true); continue; }
            if (!input.acceleration_gate && input.jump) { jump(next,parameters,result,is_fast,right); continue; }
            if (opposite) {
                if (is_fast) {
                    if (!objects) throw assets::BankError("unsupported fast reversal without effect storage");
                    s.presentation = {0x85,{52,52,57},3,3}; facing(s,right);
                    next.presentation_target = 57;
                    next.callback = right ? PresentationCallback::fast_reverse_left : PresentationCallback::fast_reverse_right;
                    s.update = right ? MotionUpdate::fast_reverse_left : MotionUpdate::fast_reverse_right;
                    result.spawned_effects.push_back(objects->spawn(effects.owner,s.position,
                        right ? ReversalSide::from_right : ReversalSide::from_left));
                    continue; // Allocation returns into the reversal handler now.
                }
                turn_entry(next,false,true); continue;
            }
            damp_horizontal(s,motion);
            if (is_ground && same && (right ? signed_word(s.horizontal_speed)>144 : signed_word(s.horizontal_speed)<-144)) {
                s.presentation.words = {6,12,17}; s.presentation.counter = s.presentation.reload = 2;
                s.update = right ? MotionUpdate::fast_right : MotionUpdate::fast_left;
                horizontal(); break;
            }
            if (same) accelerate(right);
            if (is_fast) {
                if (right ? signed_word(s.horizontal_speed)<=144 : signed_word(s.horizontal_speed)>=-144) {
                    s.presentation.words = {0,0,5}; s.presentation.counter = s.presentation.reload = 1;
                    s.update = right ? MotionUpdate::ground_right : MotionUpdate::ground_left;
                }
                horizontal(); break;
            }
            if (right) set_right_motion_reload(s); else set_left_motion_reload(s);
            if (!s.horizontal_speed) { idle(s,right); continue; }
            horizontal(); break;
        }
        if (handler == MotionUpdate::fast_reverse_left || handler == MotionUpdate::fast_reverse_right) {
            const bool from_right = handler == MotionUpdate::fast_reverse_left;
            // These entries reload the actor's control owner and ignore the
            // acceleration gate for jump. They never run the drop helper.
            if (input.jump) { jump(next,parameters,result,true,from_right); continue; }
            damp_horizontal(s,motion);
            if (from_right ? input.left != 0 : input.right != 0) accelerate(!from_right);
            horizontal(); break;
        }
        const bool turn_right = handler == MotionUpdate::turn_right;
        const bool turn_left = handler == MotionUpdate::turn_left;
        const bool reverse_left = handler == MotionUpdate::reverse_left;
        const bool reverse_right = handler == MotionUpdate::reverse_right;
        if (!(turn_right || turn_left || reverse_left || reverse_right))
            throw assets::BankError("unsupported actor update handler");
        if (turn_left) damp_horizontal(s,motion); // A384 damps even on jump.
        if (input.jump) {
            if (reverse_right && input.acceleration_gate) { horizontal(); break; }
            if (reverse_left || !input.acceleration_gate) { jump(next,parameters,result,false,false); continue; }
        }
        if (!turn_left) damp_horizontal(s,motion);
        const bool right = turn_right || reverse_right;
        if (right ? input.right != 0 : input.left != 0) accelerate(right);
        horizontal(); break;
    }
    if (objects) *effects.effects = std::move(*objects);
    if (globals) *actions = *globals;
    if (fade) *transition = *fade;
    if (totals) *tally = *totals;
    if (prepared) *palette = *prepared;
    state = next; scratch = terrain; return result;
}
} // namespace wiz::sim
