#pragma once
#include "sim/reversal.hpp"
#include <optional>

namespace wiz::sim {
struct TrailRandom { std::uint32_t state{}, mirror{}; };
// E918's two-word recurrence, retained mirror and logical right-shift result.
std::uint32_t next_trail_random(TrailRandom& random) noexcept;
struct TrailParticle {
    Position position;
    std::uint16_t flags{};
    MotionPresentation presentation;
    std::uint16_t target{};
};
// Successful 5A9A allocation/initialization. Capacity is an explicit caller
// resource; this component does not own or emulate the general object pool.
TrailParticle make_trail_particle(Position position, bool allocation_available);
// Active gate, presentation/release, then fixed return-only handler/service.
bool step_trail_particle(TrailParticle& particle) noexcept;
// The pickup a 6D22 conversion copied into an emitter (FB06), as a later 6C00
// exchange swaps it: count (+10), logical FF447A record (+42) and extents
// (+1E/+20). 6D8C never reads them.
struct CarriedPickup {
    std::uint16_t count{};
    std::size_t record{};
    std::uint16_t x_extent{}, y_extent{};
    bool operator==(const CarriedPickup&) const = default;
};
struct TrailEmitter {
    Position position;
    std::uint16_t countdown{};
    std::array<Position,5> history{};
    MotionPresentation presentation;
    std::uint16_t target{}, flags{};
    ActorId owner;
    // Absent when not established (e.g. an emitter seeded without these bytes).
    std::optional<CarriedPickup> carried{};
};
// Handler 6D8C; optionally include its preceding active/presentation phase.
// The caller supplies the resolved owner position and allocation availability.
// RNG is consumed twice only on emission. All mutations roll back on failure.
// Initializer 6D22, generic callbacks/world scheduling and pool competition
// are outside this API. No original RAM addresses are used as native identities.
std::optional<TrailParticle> step_trail_emitter(TrailEmitter& emitter,
    TrailRandom& random, ActorId owner, Position position,
    bool allocation_available, bool scheduled = false);
} // namespace wiz::sim
