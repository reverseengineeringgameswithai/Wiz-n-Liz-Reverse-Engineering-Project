#pragma once

#include "sim/movement.hpp"
#include <optional>

namespace wiz::sim {
// Stable native identities, never original RAM addresses or host pointers.
struct ActorId { std::uint64_t value{}; bool operator==(const ActorId&) const = default; };
enum class ReversalSide { from_right, from_left };
struct ReversalEffect {
    ActorId owner;
    Position position;
    MotionPresentation presentation;
    std::uint16_t target{}, flags{};
    ReversalSide side = ReversalSide::from_right;
};
ReversalEffect make_reversal_effect(ActorId owner, Position position, ReversalSide side);
// Active gate, presentation/release callback, then X follow even on the release
// invocation. Y is retained. Returns true exactly when the slot is released.
// Missing/wrong ownership rejects atomically; inactive objects do nothing.
bool step_reversal_effect(ReversalEffect& effect, ActorId owner, Position position);

struct EffectId {
    std::size_t slot{};
    std::uint64_t generation{};
    bool operator==(const EffectId&) const = default;
};
// Original +08/+0A presentation words and +0C/+0D counter/reload. F9E2 and the
// pair initializers overwrite them; 783A does not, so its members keep them.
struct InheritedPresentation {
    std::array<std::uint16_t, 2> words{};
    std::uint8_t counter{}, reload{};
    bool operator==(const InheritedPresentation&) const = default;
};
// Represented fields that the F9E2 allocator and the initializers built on it
// never write. The original keeps the slot's previous contents there; native
// callers supply verified values and never receive defaults. Unrepresented
// private bytes are outside this type and must be established as zero.
struct InheritedObjectFields {
    std::uint16_t target{}, countdown{};
    ActorId control;
    // Absent unless verified; an initializer that keeps these bytes rejects.
    std::optional<InheritedPresentation> presentation{};
    // Original +02/+04. Only the 6EC8/6EDC dormant initializers keep them.
    std::optional<Position> position{};
};
// Inherited parts an initializer keeps beyond target, countdown and link.
struct InheritanceNeeds { bool presentation{}, position{}; };
enum class PairMember { first, second };
struct ObjectPair { EffectId first, second; };
// One logical FF447A record: the 6AF0 object and its FF312C/FF314C entry index.
struct PickupRecord {
    EffectId object;
    std::size_t entry{};
    bool operator==(const PickupRecord&) const = default;
};
// 783A pop order: the probe, then return-only members at (+32,0), (0,+32)
// and (+32,+32) from the probe's position.
enum class QuadMember { probe, right, below, diagonal };
struct ObjectQuad { std::array<EffectId, 4> members; };
struct EffectUpdate {
    EffectId id;
    ReversalEffect state;
    bool released{};
};
// Bounded native storage with LIFO reuse, not the original fixed RAM pool.
// Only reversal objects live here. A future world service must account for
// competition with other object types before claiming original capacity parity.
class ReversalEffects {
public:
    explicit ReversalEffects(std::size_t capacity);
    EffectId spawn(ActorId owner, Position position, ReversalSide side);
    const ReversalEffect& at(EffectId id) const;
    bool step(EffectId id, ActorId owner, Position position);
    // Ascending logical slot order. Includes objects spawned before this phase,
    // and the final follow on release. All slots/requests roll back on failure.
    // These objects have the fixed return-only +46 service assigned at spawn.
    std::vector<EffectUpdate> step_active(ActorId owner, Position position, std::size_t budget);
    std::size_t available() const noexcept { return free_.size(); }
private:
    struct Slot { ReversalEffect effect; std::uint64_t generation{}; };
    std::vector<Slot> slots_;
    std::vector<std::size_t> free_;
};
struct ReversalContext { ReversalEffects* effects{}; ActorId owner{}; };
} // namespace wiz::sim
