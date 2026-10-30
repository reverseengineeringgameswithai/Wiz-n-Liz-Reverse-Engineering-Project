#pragma once
#include "sim/reversal.hpp"
#include "sim/return_only.hpp"
#include "sim/trail.hpp"
#include <optional>

namespace wiz::sim {
// AC5E uses unsigned inclusive comparisons after word wrap. Only X is masked.
// Extents are the original operands, not normalized geometric half sizes.
bool overlaps_control(Position object, Position extents, Position control, std::uint16_t x_mask) noexcept;
struct CollisionConfig {
    std::uint16_t x_mask{}, secondary_gate{};
    // The component accepts a supplied secondary tracker. Its producer and
    // two-player scheduling are outside this bounded service.
    std::optional<Position> secondary;
};
struct CollisionInputs { Position primary; CollisionConfig config; };
struct CollisionProbe {
    Position position;
    std::uint16_t flags{};
    MotionPresentation presentation;
    std::uint16_t target{}, countdown{};
    ActorId control; // Preserved; 78EE selects the two controls independently.
    std::uint16_t x_extent{}, y_extent{};
};
// Fixed RTS handler, then 78EE's miss-only service. Scheduled calls include
// active/presentation first. Hit7910, invoked callbacks and missing consumed
// secondary input reject without publishing any earlier presentation changes.
void step_collision_probe(CollisionProbe& object, const CollisionInputs& inputs, bool scheduled = false);
enum class PickupContact { none, primary, secondary };
// One scheduled probe walk: active gate, presentation, then 78EE's test. The
// contact is returned for the caller's 7910. An invoked callback or missing
// consumed P2 input rejects with no change.
PickupContact walk_collision_probe(CollisionProbe& object, const CollisionInputs& inputs);
// F9E2 defaults followed by 783A's first-member stores: mode 80, the caller's
// control (A5), (150,262), frame 912, service 78EE and extents 0038/0008.
// +08..+0D, +0E and +10 are never written, so they come from verified
// inheritance; absent inherited presentation rejects.
CollisionProbe make_quad_probe(const InheritedObjectFields& inherited, ActorId control);

// A pickup's stage. Collectable pickups run the 6BD6 service. A 6C00 hit
// starts 59BC's mode-85 vanish (frames 021E/021E/0227, target 0227, 3/3, +12
// AND 9FFF, both selectors RTS): `vanishing` ends in the FAA4 release,
// `swapped_out` (after an exchange) in 6CDA, which runs 5964's mode-87 frames
// 0227/021E/0227 (target 021E), sets 2/2 and leaves it `swapped_in`; 6CF4 then
// re-dresses it from its record's kind as collectable again.
enum class PickupPhase : std::uint8_t { collectable, vanishing, swapped_out, swapped_in };
// 6AF0 pickup: fixed 12646 handler and, while collectable, the 6BD6 service,
// whose miss path has 78EE's shape (P1, then P2 only behind the FF33E2 gate).
// `record` is the logical index of its FF447A record (+42); `countdown` (+10)
// is the FF314C count and selects the cadence.
struct Pickup {
    Position position;
    std::uint16_t flags{};
    MotionPresentation presentation;
    std::uint16_t target{}, countdown{};
    ActorId control;
    std::uint16_t x_extent{}, y_extent{};
    std::size_t record{};
    PickupPhase phase = PickupPhase::collectable;
};
// Active gate and presentation, then 6BD6's miss service, for a collectable
// pickup. Hits, invoked callbacks and missing consumed P2 input reject without
// publishing changes; a hit's 6C00 work belongs to the pool (MixedPool).
void step_pickup(Pickup& object, const CollisionInputs& inputs, bool scheduled = false);
struct PickupWalk { bool released{}; PickupContact contact = PickupContact::none; };
// One scheduled walk: active gate, presentation and the phase's callback (FAA4
// release, 6CDA, or 6CF4 re-dressing from `kind`, the FF312C word its record
// names), then 6BD6's miss test when the pickup is collectable afterwards. The
// contact is returned for the caller's 6C00. A collectable callback, a missing
// kind or missing consumed P2 input reject with no change.
PickupWalk walk_pickup(Pickup& object, const CollisionInputs& inputs, std::optional<std::uint16_t> kind);
// 6C00's pickup side after its link work: X - 8, then 59BC and the phase.
void begin_pickup_vanish(Pickup& object, PickupPhase phase) noexcept;
// 6D22: FB06 copies the pickup into the dormant link, which becomes a 6D8C
// trail emitter owned by the touching control: countdown (+36) 0, all ten
// history words FF80, +46 RTS; it carries the pickup's count, record and extents.
TrailEmitter carry_pickup(const Pickup& object, ActorId owner) noexcept;
// 6C50..6CB4: an active emitter link and the touched pickup swap frame words
// (+06/+08/+0A), reload (+0D), count (+10) and record (+42). An emitter whose
// carried bytes are not established rejects.
void exchange_carried(Pickup& object, TrailEmitter& link);
// 7910's FB06 copy of a carrying emitter link: 5964's mode 87 (frames
// 0227/021E/0227, target 021E, 3/3, +12 AND 9FFF, both selectors RTS) at
// (00A4,00F6) with callback 79B6. `frames` (+22/+26) keep the emitter's +08/+0A
// from before 5964, `control` (+4A) is the touching control, and the carried
// count, record and extents are the emitter's. The emitter's other history
// words and +36 are copied too; nothing reads them before 79B6.
struct DeliveredPickup {
    Position position;
    std::uint16_t flags{};
    MotionPresentation presentation;
    std::uint16_t target{};
    ActorId control;
    std::array<std::uint16_t,2> frames{};
    CarriedPickup carried;
};
// Active gate and presentation, then the fixed RTS handler and service. The
// 79B6 callback is not native and rejects with no change.
void step_delivered_pickup(DeliveredPickup& object);
// 7910's object work for an active carrying emitter link, as the pool applies
// it: the 59AE sparkle (placed at the emitter's position - (8,8), then 59BC; it
// has the 5A9A particle's shape with frames 021E..0227), the copy and the link
// left dormant (mode 0) with the copy's other represented fields. An emitter
// whose carried bytes are not established rejects.
struct Delivery { TrailParticle sparkle; DeliveredPickup copy; ReturnOnlyObject link; };
Delivery deliver_carried(const TrailEmitter& link, ActorId control);
// F9E2 defaults followed by 6AF0 and its 6B44/6BB2 helpers for one table
// entry: mode 81 at (x, y + 16) (word wrap), extents 0010/0010, frames from the
// kind (signed kind < 14: kind*6 + 0260 by unsigned word arithmetic, end +5;
// else 020D, 0205 or 01FD families), countdown = count, counter/reload 1/1 when
// count is 2 else 5/5, caller control at +4A. Only the target is inherited.
Pickup make_pickup(const InheritedObjectFields& inherited, ActorId control, Position at,
    std::uint16_t kind, std::uint16_t count, std::size_t record) noexcept;
} // namespace wiz::sim
