#include "sim/trail.hpp"
#include "sim/presentation.hpp"

namespace wiz::sim {
std::uint32_t next_trail_random(TrailRandom& random) noexcept {
    const auto previous = random.state;
    const auto low = ((previous >> 8U) ^ (previous >> 15U)) & 0xffffU;
    random.state = (previous << 16U) | low;
    random.mirror = random.state;
    return random.state >> 1U;
}
TrailParticle make_trail_particle(Position position, bool allocation_available) {
    if (!allocation_available) throw assets::BankError("trail allocation exhausted");
    return {position,0,{0x85,{227,227,234},3,3},234};
}
bool step_trail_particle(TrailParticle& particle) noexcept {
    if (!(particle.presentation.mode & 0x80U)) return false;
    const bool released = advance_presentation(particle.presentation,particle.target);
    if (released) particle.presentation.mode = 0;
    return released;
}
std::optional<TrailParticle> step_trail_emitter(TrailEmitter& emitter,
        TrailRandom& random, ActorId owner, Position position,
        bool allocation_available, bool scheduled) {
    if (scheduled && !(emitter.presentation.mode & 0x80U)) return {};
    auto next = emitter; auto rng = random; std::optional<TrailParticle> particle;
    if (scheduled && advance_presentation(next.presentation,next.target))
        throw assets::BankError("unsupported trail emitter callback");
    next.countdown = static_cast<std::uint16_t>(next.countdown - 1U);
    if (next.countdown & 0x8000U) {
        next.countdown = 3;
        const auto a = next.history[0], b = next.history[1];
        if (a.x != b.x || a.y != b.y) {
            particle = make_trail_particle(next.position,allocation_available);
            particle->position.x = static_cast<std::uint16_t>(particle->position.x + (next_trail_random(rng) & 7U) - 4U);
            particle->position.y = static_cast<std::uint16_t>(particle->position.y + (next_trail_random(rng) & 7U) - 4U);
            particle->presentation.counter = particle->presentation.reload = 2;
        }
    }
    // Original resolves the linked actor after allocation/random calls. Keep
    // that ordering, while publishing none of those changes on a late failure.
    if (!owner.value || owner != next.owner) throw assets::BankError("trail owner unavailable");
    next.position = next.history.back();
    for (std::size_t i=next.history.size()-1;i>0;--i) next.history[i]=next.history[i-1];
    next.history[0] = {static_cast<std::uint16_t>(position.x + 4U),position.y};
    emitter = next; random = rng;
    return particle;
}
} // namespace wiz::sim
