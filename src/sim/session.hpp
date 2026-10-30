#pragma once

#include "sim/input.hpp"
#include "sim/presentation.hpp"
#include "sim/banner.hpp"

namespace wiz::sim {
struct P1SessionState {
    ActorState actor;
    ActorTracking tracking;
    TerrainScratch scratch;
    PadControl control;
    std::uint64_t invocations{};
    // Dedicated native P1 reversal budget; not a mirror of the shared game pool.
    std::optional<ReversalEffects> effects;
    // The shared 1345A timer (FF0B90..), run once per call before the banner as
    // the original frame does; absent, the timer is the observed inactive no-op.
    // In a mixed session P1's exit handlers (710E/7126) restart and read it;
    // its palette consumers are not native.
    std::optional<TransitionState> transition;
    // FF33E0/FF33D8/FF33DA, given to the actor's handlers in a mixed session
    // (7126's completion writes mode 7); absent, those handlers reject.
    std::optional<ActionGlobals> actions;
};
struct P1SessionConfig {
    ActorParameters parameters;
    std::uint16_t acceleration_gate{};
    std::uint64_t max_invocations = 600;
    ActorBudget actor_budget;
    std::optional<LevelBannerConfig> banner;
    ActorId owner{1};
    std::size_t effect_budget = 64;
};
struct P1SessionResult {
    ActorResult actor;
    std::optional<LevelBannerRequest> banner;
    std::vector<EffectUpdate> effects;
    // The timer just after this call's 1345A step (a world phase may restart it later).
    std::optional<TransitionState> transition;
    // P1's actor and tracking as the wrapper returned them, set by a mixed
    // session (its world phase may hand P1 to another handler afterwards).
    std::optional<ActorState> wrapper_actor;
    std::optional<ActorTracking> wrapper_tracking;
};
// Bounded movement session: the transition timer when present, then one
// physical held set -> input conversion -> full P1 actor wrapper. Caller pins
// scene, parameters and shared gate once. Actor, tracking, scratch, control,
// timer and invocation count persist and commit together.
// Optional level-banner phase precedes input and the wrapper. Its scratch write
// and requests commit with the actor. No per-invocation environment reseeding.
// Optional owned reversal storage executes after P1, including new objects in
// this invocation. Other world objects, pause, up/down actions and transition/
// tally contexts are unsupported. No external reseeding or global-pool parity.
P1SessionResult step_p1_session(const assets::SceneResource& scene, const assets::PatternBank& bank,
                           P1SessionState& state, const P1SessionConfig& config, ThreeButtonPad held);
} // namespace wiz::sim
