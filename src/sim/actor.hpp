#pragma once

#include "sim/airborne.hpp"
#include "sim/reversal.hpp"
#include "sim/transition.hpp"
#include "sim/bonus.hpp"
#include "sim/score.hpp"
#include <optional>

namespace wiz::sim {
// Callback assignments are logical identities. The animation scheduler that
// invokes them is separate (step_presentation / step_scheduled_actor).
enum class PresentationCallback { retained, turn_right, turn_left, reverse_left, reverse_right, fast_jump_right, fast_jump_left,
                                  fast_reverse_left, fast_reverse_right, action_hold, action_idle, enter_airborne };
// Only the verified RTS service is supported. Unknown selectors stay explicit.
enum class ActorService { unsupported, return_only };
struct ActorState {
    MotionState motion;
    std::uint16_t presentation_target{}, presentation_cycles{}; // Original +E/+10.
    PresentationCallback callback = PresentationCallback::retained;
    ActorService service = ActorService::unsupported; // Original +46, separate from motion +16.
};
struct ActorParameters {
    AirborneParameters airborne;
    std::uint16_t ground_acceleration = 8, jump_impulse = 28, jump_delay = 10;
};
struct ActorInput {
    std::uint8_t jump{}, drop{}, up{}, down{}, left{}, right{};
    std::uint16_t acceleration_gate{};
    std::uint8_t raw_buttons = 0xff; // Observed producer +14; action uses bit 6 directly.
    std::uint8_t start{}; // Producer +21, separately sampled from raw buttons.
};
// Shared action gates, not actor-owned timers. External world scheduling may
// change these between invocations; this component never invents a countdown.
struct ActionGlobals {
    std::uint16_t mode{}, cooldown{}, interval{}; // Original FF33E0/D8/DA.
};
// 5132/5188 associated control and shared equality keys. The separately gated
// secondary-score path at 53F2 additionally requires ScoreState.
struct ExitTallyState {
    std::uint16_t secondary_gate{}, secondary_remaining{}, marker{}, selection{}, target_selection{};
};
// Explicit tally contexts. The world owns shared gates; associated control
// owns remaining units, bonus tables and score. Optional paths require context.
struct TallyState {
    std::uint16_t palette_gate{}, remaining{}, skip{}, countdown{}, credit{}, special_gate{};
    std::optional<BonusSlots> bonus{};
    std::optional<ExitTallyState> exit_state{};
    std::optional<ScoreState> score{};
};
// Logical sample identities; up_action is also requested by the tally bonus.
enum class ActionSample { up_action, score_reward };
struct SampleRequest {
    ActionSample sample = ActionSample::up_action;
    std::uint16_t count = 200, parameter = 0x0f14;
};
// Exact ordered request ABI at FCB32; output is a request, not synthesized sound
// or a claim of audio-driver parity. Requests publish only with successful state.
struct SoundRequest {
    std::uint16_t id{}, priority{}, parameter{}, selector{};
};
struct ActorBudget {
    std::size_t continuations = 32, horizontal = 1024, downward = 4096, bonus_probes = 4096, score_advances = 4096;
};
struct ActorResult {
    std::size_t handler_entries{}, horizontal_steps{}, settle_calls{}, landings{};
    std::vector<SoundRequest> sound_requests;
    std::vector<EffectId> spawned_effects;
    // ED6E6's deferred mailbox write. The resource adapter resolves sample IDs;
    // sound consumption, bank switching and playback are outside this phase.
    std::vector<SampleRequest> sample_requests;
    std::vector<BonusAssignment> bonus_assignments;
    std::size_t bonus_probes{}, score_advances{};
};
// One selected handler invocation (F904 -> F906), not a game frame. Consumes
// same-call continuations; handler assignments followed by RTS remain deferred.
// Fast reversal requires an explicit owned effect store. Actor, scratch, store
// and returned effects commit together. Unknown actions/resources/budgets fail.
ActorResult step_actor(const assets::SceneResource& scene, const assets::PatternBank& bank,
                       ActorState& state, const ActorParameters& parameters,
                       ActorInput input, TerrainScratch& scratch, ActorBudget budget = {}, ReversalContext effects = {},
                       ActionGlobals* actions = nullptr, TransitionState* transition = nullptr, TallyState* tally = nullptr, PalettePreparation* palette = nullptr);
} // namespace wiz::sim
