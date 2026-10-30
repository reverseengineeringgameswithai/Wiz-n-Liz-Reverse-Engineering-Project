#include "sim/reversal.hpp"
#include "sim/presentation.hpp"
#include <limits>

namespace wiz::sim {
namespace {
bool from_right(ReversalSide side) {
    if (side != ReversalSide::from_right && side != ReversalSide::from_left)
        throw assets::BankError("unsupported reversal effect side");
    return side == ReversalSide::from_right;
}
}
ReversalEffect make_reversal_effect(ActorId owner, Position position, ReversalSide side) {
    if (!owner.value) throw assets::BankError("reversal effect requires an owner");
    const bool right = from_right(side);
    position.x = static_cast<std::uint16_t>(position.x + (right ? 22U : 65530U));
    position.y = static_cast<std::uint16_t>(position.y + (right ? 15U : 16U));
    return {owner,position,{0x85,{215,215,220},2,2},220,
            static_cast<std::uint16_t>(right ? 0x800 : 0),side};
}
bool step_reversal_effect(ReversalEffect& effect, ActorId owner, Position position) {
    if (!(effect.presentation.mode & 0x80U)) return false;
    if (!owner.value || owner != effect.owner) throw assets::BankError("reversal effect owner unavailable");
    const bool right = from_right(effect.side);
    auto next = effect;
    const bool released = advance_presentation(next.presentation,next.target);
    if (released) next.presentation.mode = 0;
    // Both observed object loops load +16 after the callback without retesting
    // activity. The last follow therefore runs after the release callback too.
    next.position.x = static_cast<std::uint16_t>(position.x + (right ? 22U : 65530U));
    effect = next;
    return released;
}
ReversalEffects::ReversalEffects(std::size_t capacity) {
    if (capacity > 4096) throw assets::BankError("reversal storage budget exceeded");
    slots_.resize(capacity); free_.reserve(capacity);
    for (std::size_t i=0;i<capacity;++i) free_.push_back(i);
}
EffectId ReversalEffects::spawn(ActorId owner, Position position, ReversalSide side) {
    if (free_.empty()) throw assets::BankError("reversal allocation exhausted");
    const auto effect = make_reversal_effect(owner,position,side);
    const auto index = free_.back(); auto& slot = slots_[index];
    if (slot.generation == std::numeric_limits<std::uint64_t>::max())
        throw assets::BankError("reversal identity exhausted");
    slot.effect = effect; ++slot.generation; free_.pop_back();
    return {index,slot.generation};
}
const ReversalEffect& ReversalEffects::at(EffectId id) const {
    if (id.slot >= slots_.size() || !id.generation || slots_[id.slot].generation != id.generation)
        throw assets::BankError("stale reversal effect identity");
    return slots_[id.slot].effect;
}
bool ReversalEffects::step(EffectId id, ActorId owner, Position position) {
    auto next = at(id);
    const bool released = step_reversal_effect(next,owner,position);
    // Publish the free entry before mutating the slot, so an allocation failure
    // after copying a pool still preserves its previous state.
    if (released) free_.push_back(id.slot);
    slots_[id.slot].effect = next;
    return released;
}
std::vector<EffectUpdate> ReversalEffects::step_active(ActorId owner, Position position, std::size_t budget) {
    auto next = *this;
    std::vector<EffectUpdate> updates;
    for (std::size_t i=0;i<next.slots_.size();++i) {
        const auto& slot = next.slots_[i];
        if (!(slot.effect.presentation.mode & 0x80U)) continue;
        if (updates.size() >= budget) throw assets::BankError("reversal phase work budget exhausted");
        const EffectId id{i,slot.generation};
        const bool released = next.step(id,owner,position);
        updates.push_back({id,next.at(id),released});
    }
    *this = std::move(next);
    return updates;
}
} // namespace wiz::sim
