#pragma once

#include "sim/actor.hpp"

namespace wiz::sim {
// F76C's bounded field update, before its optional callback. Returns whether
// the old frame triggered the target. Reused by actor and effect scheduling.
bool advance_presentation(MotionPresentation& presentation, std::uint16_t target) noexcept;
// One F76C presentation invocation. Byte countdown and word frame/cycle wrap
// are intentional. Returns whether the pre-advance target fired a callback.
// A retained/unknown callback is allowed until actually invoked, then rejects.
// Failure leaves all actor state unchanged.
bool step_presentation(ActorState& state);

// Contextual F76C: action-idle callback enters idle immediately, including its
// input, movement and effect paths. The context-free API rejects that callback.
ActorResult step_actor_presentation(const assets::SceneResource& scene, const assets::PatternBank& bank,
                                    ActorState& state, const ActorParameters& parameters,
                                    ActorInput input, TerrainScratch& scratch, ActorBudget budget = {},
                                    ReversalContext effects = {}, ActionGlobals* actions = nullptr, TransitionState* transition = nullptr, TallyState* tally = nullptr, PalettePreparation* palette = nullptr);

// Active-bit gate, presentation, then the handler selected AFTER presentation
// (F8F6 -> F906, or inactive exit F90C). The later +46 service, other objects,
// input production and frame scheduling are outside this contract.
// Presentation, movement, scratch and returned effects commit together.
ActorResult step_scheduled_actor(const assets::SceneResource& scene, const assets::PatternBank& bank,
                                 ActorState& state, const ActorParameters& parameters,
                                 ActorInput input, TerrainScratch& scratch, ActorBudget budget = {}, ReversalContext effects = {},
                                 ActionGlobals* actions = nullptr, TransitionState* transition = nullptr, TallyState* tally = nullptr, PalettePreparation* palette = nullptr);

// Control-record outputs (+42/+44), gated by exact word +1A6 == FFFF.
// Their downstream consumers and the meaning of other selector values remain separate.
struct ActorTracking {
    std::uint16_t selector{};
    Position position;
};
// 630A: initialize the explicitly associated actor and tracking selector.
// Retains tracking coordinates and all other actor fields; the selected coast
// handler executes only when a later caller invokes it. No shared timer change.
void begin_coasting(ActorState& state, ActorTracking& tracking) noexcept;
// 70D2..70F4 (705C's door entry): 630A's shape with handler 710E: tracking
// selector FFFF, mode 80, frame 021D, handler 710E (+4A stays the control).
void begin_exit_transition(ActorState& state, ActorTracking& tracking) noexcept;
// F8F6 through the wrapper's actual RTS: initial active gate, presentation,
// selected motion handler, selected +46 service, then control coordinates.
// Inactive actors still update tracking. Unknown invoked services reject.
// Actor, tracking, scratch, globals, effect storage and requests commit together.
ActorResult step_actor_dispatch(const assets::SceneResource& scene, const assets::PatternBank& bank,
                                ActorState& state, ActorTracking& tracking, const ActorParameters& parameters,
                                ActorInput input, TerrainScratch& scratch, ActorBudget budget = {},
                                ReversalContext effects = {}, ActionGlobals* actions = nullptr, TransitionState* transition = nullptr, TallyState* tally = nullptr, PalettePreparation* palette = nullptr);
} // namespace wiz::sim
