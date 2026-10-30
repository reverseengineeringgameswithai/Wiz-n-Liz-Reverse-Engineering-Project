#include "sim/spell.hpp"
#include "sim/presentation.hpp"

namespace wiz::sim {
const std::array<Recipe,105> recipes{{
    {6,6,0x908c},{6,5,0x8652},{6,4,0x879e},{6,3,0x8af4},{6,1,0x9132},{5,5,0x9276},{5,4,0x8ee2},{5,3,0x86fe},
    {5,1,0x8cea},{4,4,0x8c38},{4,3,0x8de2},{4,1,0x9400},{3,3,0x911e},{3,1,0x882e},{1,1,0x8760},{7,6,0x8bae},
    {7,5,0x87f2},{7,4,0x87c8},{7,3,0x86aa},{7,1,0x9288},{7,7,0x88bc},{2,6,0x8d84},{2,5,0x8810},{2,4,0x8c8c},
    {2,3,0x8e3a},{2,1,0x8df8},{2,7,0x8e50},{2,2,0x868e},{0,6,0x9412},{0,5,0x8752},{0,4,0x88cc},{0,3,0x8fe0},
    {0,1,0x8a4a},{0,7,0x8f22},{0,2,0x916e},{0,0,0x8ea6},{8,6,0x9196},{8,5,0x86d4},{8,4,0x8ab0},{8,3,0x86f0},
    {8,1,0x9424},{8,7,0x871a},{8,2,0x8b56},{8,0,0x9036},{8,8,0x90e8},{13,6,0x8f02},{13,5,0x8c02},{13,4,0x8736},
    {13,3,0x92ac},{13,1,0x8a28},{13,7,0x8e0e},{13,2,0x9264},{13,0,0x88b4},{13,8,0x8f8a},{13,13,0x8b74},{10,6,0x8bd8},
    {10,5,0x869c},{10,4,0x8a8e},{10,3,0x92be},{10,1,0x8680},{10,7,0x8744},{10,2,0x88dc},{10,0,0x9436},{10,8,0x8ec4},
    {10,13,0x8b16},{10,10,0x870c},{12,6,0x945a},{12,5,0x8d2a},{12,4,0x8c62},{12,3,0x88a4},{12,1,0x89b4},{12,7,0x88c4},
    {12,2,0x8e88},{12,0,0x9252},{12,8,0x86e2},{12,13,0x915a},{12,10,0x946c},{12,12,0x86b8},{11,6,0x88ac},
    {11,5,0x8ca8},{11,4,0x92d0},{11,3,0x9146},{11,1,0x9394},{11,7,0x88d4},{11,2,0x9182},{11,0,0x8e24},{11,8,0x9382},
    {11,13,0x9448},{11,10,0x947e},{11,12,0x8a6c},{11,11,0x90b2},{9,6,0x8b38},{9,5,0x8a04},{9,4,0x884c},{9,3,0x8728},
    {9,1,0x8ad2},{9,7,0x9490},{9,2,0x86c6},{9,0,0x91aa},{9,8,0x89dc},{9,13,0x8e6a},{9,10,0x92e2},{9,12,0x886a},
    {9,11,0x8b92},{9,9,0x8f42}
}};
std::optional<std::uint32_t> recipe_effect(std::uint16_t a, std::uint16_t b) noexcept {
    for (const auto& r:recipes)
        if ((r.first==a && r.second==b) || (r.first==b && r.second==a)) return r.effect;
    return std::nullopt;
}
std::uint16_t ingredient_fruit(std::uint16_t frame) noexcept {
    return static_cast<std::uint16_t>(static_cast<std::uint16_t>(frame-0x260U)/6U);
}
SpellSparkle make_spell_sparkle(Position position) noexcept {
    SpellSparkle s{{position.x,static_cast<std::uint16_t>(position.y+4U)},0,{},0,0x40,0x10,0x10};
    s.presentation.mode=0x80;s.presentation.words[0]=0x21d;return s;
}
SparkleStep step_spell_sparkle(SpellSparkle& sparkle, TrailRandom& random, bool allocation_available) {
    if (!(sparkle.presentation.mode & 0x80U)) return {};
    auto next=sparkle;auto rng=random;SparkleStep out;
    if (advance_presentation(next.presentation,next.target)) throw assets::BankError("unsupported spell sparkle callback");
    next.countdown=static_cast<std::uint16_t>(next.countdown-1U);
    if (next.countdown & 0x8000U) { next.presentation.mode=0;sparkle=next;out.released=true;return out; }
    // 7F80: CMPI.W #73 on the low byte, then BGT.
    if ((next_trail_random(rng) & 0xffU) <= 0x73U) {
        const auto y=static_cast<std::uint16_t>((next_trail_random(rng) & 0x1fU) - 0x10U + next.position.y);
        const auto x=static_cast<std::uint16_t>((next_trail_random(rng) & 0x1fU) - 0x10U + next.position.x);
        out.particle=make_trail_particle({x,y},allocation_available);
        if (next_trail_random(rng) & 1U) out.particle->flags=0x4000;
    }
    sparkle=next;random=rng;return out;
}
DoorSign make_door_sign() noexcept {
    DoorSign s;s.presentation.mode=0x80;s.presentation.words[0]=0x21d;return s;
}
void raise_door_sign(DoorSign& sign, Position door) noexcept {
    sign.presentation.mode=0x80;sign.position={door.x,static_cast<std::uint16_t>(door.y-0x24U)};
    sign.presentation.words[0]=0xd2;sign.cursor=0;sign.bobbing=true;
}
void step_door_sign(DoorSign& sign) {
    if (!(sign.presentation.mode & 0x80U)) return;
    auto next=sign;
    if (advance_presentation(next.presentation,next.target)) throw assets::BankError("unsupported door sign callback");
    if (next.bobbing) {
        constexpr std::array<int,14> bob{1,1,2,1,1,0,0,-1,-1,-2,-1,-1,0,0};
        if (next.cursor>=bob.size()) throw assets::BankError("door sign cursor outside table");
        next.position.y=static_cast<std::uint16_t>(next.position.y+bob[next.cursor]);
        if (++next.cursor==bob.size()) next.cursor=0;
    }
    sign=next;
}
ExitDoor make_exit_door(Position position, ActorId control, EffectId sign) noexcept {
    ExitDoor d;d.position={static_cast<std::uint16_t>(position.x-8U),static_cast<std::uint16_t>(position.y+0x18U)};
    d.presentation.mode=0x80;d.presentation.words[0]=0x21d;d.countdown=0x1e;d.control=control;d.sign=sign;return d;
}
DoorStep step_exit_door(ExitDoor& door, const CollisionInputs* inputs, bool two_player) {
    if (!(door.presentation.mode & 0x80U)) return {};
    auto next=door;bool dressed=false;
    if (advance_presentation(next.presentation,next.target)) {
        if (next.phase!=DoorPhase::appearing) throw assets::BankError("unsupported exit door callback");
        // 6FCA (sound 95 is the caller's request).
        next.position={static_cast<std::uint16_t>(next.position.x+8U),static_cast<std::uint16_t>(next.position.y-8U)};
        next.presentation.words={0xb0,0xa8,0xb7};next.presentation.counter=next.presentation.reload=3;
        next.x_extent=0x10;next.y_extent=0x20;next.presentation.mode=0x81;next.phase=DoorPhase::open;dressed=true;
    }
    if (next.phase==DoorPhase::waiting) {
        next.countdown=static_cast<std::uint16_t>(next.countdown-1U);
        if (next.countdown & 0x8000U) {
            // 5964, then +1A = 6FCA.
            next.presentation={0x87,{0x227,0x21e,0x227},3,3};next.target=0x21e;next.flags&=0x9fffU;next.phase=DoorPhase::appearing;
        }
    }
    if (next.phase==DoorPhase::open) {
        // 705C: AC5E with FF0690, then FF0838 only with FF33E2 set.
        if (!inputs) throw assets::BankError("exit door collision inputs unavailable");
        if (overlaps_control(next.position,{next.x_extent,next.y_extent},inputs->primary,inputs->config.x_mask)) { door=next;return {dressed,true}; }
        if (two_player) throw assets::BankError("unsupported two-player door service");
    }
    door=next;return {dressed,false};
}
TrailParticle vanish_exit_door(const ExitDoor& door) noexcept {
    return {{static_cast<std::uint16_t>(door.position.x-8U),static_cast<std::uint16_t>(door.position.y+8U)},static_cast<std::uint16_t>(door.flags & 0x9fffU),
            {0x85,{0x21e,0x21e,0x227},3,3},0x227};
}
} // namespace wiz::sim
