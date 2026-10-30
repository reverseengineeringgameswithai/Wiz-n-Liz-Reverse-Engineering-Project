#include "sim/collision_probe.hpp"
#include "sim/presentation.hpp"

namespace wiz::sim {
bool overlaps_control(Position object, Position extents, Position control, std::uint16_t x_mask) noexcept {
    const auto x = static_cast<std::uint16_t>(object.x + extents.x - control.x) & x_mask;
    if (x > static_cast<std::uint16_t>(extents.x + 16U)) return false;
    const auto y = static_cast<std::uint16_t>(object.y + extents.y - control.y);
    return y <= static_cast<std::uint16_t>(extents.y + 12U);
}
namespace {
// 78EE and 6BD6 share this test: AC5E against FF0690, then FF0838 only behind
// the FF33E2 gate; the first overlap short-circuits.
PickupContact contact(Position position, Position extents, const CollisionInputs& inputs) {
    if (overlaps_control(position,extents,inputs.primary,inputs.config.x_mask)) return PickupContact::primary;
    if (inputs.config.secondary_gate) {
        if (!inputs.config.secondary) throw assets::BankError("secondary collision input unavailable");
        if (overlaps_control(position,extents,*inputs.config.secondary,inputs.config.x_mask)) return PickupContact::secondary;
    }
    return PickupContact::none;
}
// Only their unsupported hit targets differ.
void require_miss(Position position, Position extents, const CollisionInputs& inputs, const char* primary, const char* secondary) {
    const auto c = contact(position,extents,inputs);
    if (c == PickupContact::primary) throw assets::BankError(primary);
    if (c == PickupContact::secondary) throw assets::BankError(secondary);
}
// 6B44 frames and 6BB2 cadence, shared by 6AF0 and the 6CF4 re-dress.
std::array<std::uint16_t,3> pickup_frames(std::uint16_t kind) noexcept {
    if (static_cast<std::int16_t>(kind) < 14) {
        // MULU.W then ADDI.W: only the low word of kind*6 survives.
        const auto first = static_cast<std::uint16_t>(kind * 6U + 0x260U);
        return {first,first,static_cast<std::uint16_t>(first + 5U)};
    }
    if (kind == 0x20d) return {0x20d,0x20d,0x214};
    if (kind == 0x205) return {0x205,0x205,0x20c};
    return {0x1fd,0x1fd,0x204};
}
std::uint8_t pickup_cadence(std::uint16_t count) noexcept { return count == 2 ? 1 : 5; }
}
void step_collision_probe(CollisionProbe& object, const CollisionInputs& inputs, bool scheduled) {
    if (scheduled && !(object.presentation.mode & 0x80U)) return;
    auto next = object;
    if (scheduled && advance_presentation(next.presentation,next.target))
        throw assets::BankError("unsupported collision probe callback");
    require_miss(next.position,{next.x_extent,next.y_extent},inputs,
        "unsupported collision-hit7910 (primary)","unsupported collision-hit7910 (secondary)");
    object = next;
}
PickupContact walk_collision_probe(CollisionProbe& object, const CollisionInputs& inputs) {
    if (!(object.presentation.mode & 0x80U)) return PickupContact::none;
    auto next = object;
    if (advance_presentation(next.presentation,next.target)) throw assets::BankError("unsupported collision probe callback");
    const auto c = contact(next.position,{next.x_extent,next.y_extent},inputs);
    object = next; return c;
}
void step_pickup(Pickup& object, const CollisionInputs& inputs, bool scheduled) {
    if (object.phase != PickupPhase::collectable) throw assets::BankError("pickup is not collectable");
    if (scheduled && !(object.presentation.mode & 0x80U)) return;
    auto next = object;
    if (scheduled && advance_presentation(next.presentation,next.target))
        throw assets::BankError("unsupported pickup callback");
    require_miss(next.position,{next.x_extent,next.y_extent},inputs,
        "unsupported pickup-hit 6C00 (primary)","unsupported pickup-hit 6C00 (secondary)");
    object = next;
}
PickupWalk walk_pickup(Pickup& object, const CollisionInputs& inputs, std::optional<std::uint16_t> kind) {
    if (!(object.presentation.mode & 0x80U)) return {};
    auto next = object; PickupWalk out;
    if (advance_presentation(next.presentation,next.target)) {
        switch (next.phase) {
        case PickupPhase::collectable: throw assets::BankError("unsupported pickup callback");
        case PickupPhase::vanishing: // FAA4: clear the mode byte; the caller frees the slot.
            next.presentation.mode = 0; out.released = true; break;
        case PickupPhase::swapped_out: // 6CDA: 5964, then 2/2 and callback 6CF4.
            next.presentation = {0x87,{0x227,0x21e,0x227},2,2};
            next.target = 0x21e; next.flags &= 0x9fffU; next.phase = PickupPhase::swapped_in; break;
        case PickupPhase::swapped_in: { // 6CF4: mode 81, 6B44 from the kind, X + 8, 6BB2, service 6BD6.
            if (!kind) throw assets::BankError("pickup kind unavailable");
            const auto cadence = pickup_cadence(next.countdown);
            next.presentation = {0x81,pickup_frames(*kind),cadence,cadence};
            next.position.x = static_cast<std::uint16_t>(next.position.x + 8U);
            next.phase = PickupPhase::collectable; break;
        }
        }
    }
    // The handler and service are read after presentation, so a re-dressed
    // pickup is tested in the same walk.
    if (next.phase == PickupPhase::collectable) out.contact = contact(next.position,{next.x_extent,next.y_extent},inputs);
    object = next; return out;
}
void begin_pickup_vanish(Pickup& object, PickupPhase phase) noexcept {
    object.position.x = static_cast<std::uint16_t>(object.position.x - 8U);
    object.presentation = {0x85,{0x21e,0x21e,0x227},3,3};
    object.target = 0x227; object.flags &= 0x9fffU; object.phase = phase;
}
TrailEmitter carry_pickup(const Pickup& object, ActorId owner) noexcept {
    TrailEmitter e;
    e.position = object.position; e.countdown = 0;
    e.history.fill({0xff80,0xff80});
    e.presentation = object.presentation; e.target = object.target; e.flags = object.flags; e.owner = owner;
    e.carried = CarriedPickup{object.countdown,object.record,object.x_extent,object.y_extent};
    return e;
}
void exchange_carried(Pickup& object, TrailEmitter& link) {
    if (!link.carried) throw assets::BankError("emitter carried pickup unknown");
    auto& carried = *link.carried;
    std::swap(object.presentation.words,link.presentation.words);
    std::swap(object.presentation.reload,link.presentation.reload);
    std::swap(object.countdown,carried.count);
    std::swap(object.record,carried.record);
}
void step_delivered_pickup(DeliveredPickup& object) {
    if (!(object.presentation.mode & 0x80U)) return;
    auto next = object;
    if (advance_presentation(next.presentation,next.target)) throw assets::BankError("unsupported delivered pickup callback 79B6");
    object = next;
}
Delivery deliver_carried(const TrailEmitter& link, ActorId control) {
    if (!link.carried) throw assets::BankError("emitter carried pickup unknown");
    // 59AE's F9E2 clears +12 before 59BC's AND, so the sparkle's flags are 0.
    const TrailParticle sparkle{{static_cast<std::uint16_t>(link.position.x - 8U),static_cast<std::uint16_t>(link.position.y - 8U)},0,
        {0x85,{0x21e,0x21e,0x227},3,3},0x227};
    // +22/+26 take +08/+0A before 5964; the Y - 4 is overwritten by (00A4,00F6).
    const DeliveredPickup copy{{0xa4,0xf6},static_cast<std::uint16_t>(link.flags & 0x9fffU),{0x87,{0x227,0x21e,0x227},3,3},0x21e,control,
        {link.presentation.words[1],link.presentation.words[2]},*link.carried};
    // FB06 copies the link before CLR.B clears only its mode byte.
    auto presentation = copy.presentation; presentation.mode = 0;
    return {sparkle,copy,{copy.position,copy.flags,presentation,copy.target,copy.carried.count,control}};
}
Pickup make_pickup(const InheritedObjectFields& inherited, ActorId control, Position at,
        std::uint16_t kind, std::uint16_t count, std::size_t record) noexcept {
    const auto cadence = pickup_cadence(count);
    return {{at.x,static_cast<std::uint16_t>(at.y + 0x10U)},0,{0x81,pickup_frames(kind),cadence,cadence},
        inherited.target,count,control,0x10,0x10,record};
}
CollisionProbe make_quad_probe(const InheritedObjectFields& inherited, ActorId control) {
    if (!inherited.presentation) throw assets::BankError("collision quad inherits unknown presentation");
    const auto& p = *inherited.presentation;
    // F9E2 clears +12/+14; mode 80 has bit 0 clear, so the frame never advances.
    return {{0x96,0x106},0,{0x80,{0x390,p.words[0],p.words[1]},p.counter,p.reload},
        inherited.target,inherited.countdown,control,0x38,8};
}
} // namespace wiz::sim
