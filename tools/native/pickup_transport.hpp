#pragma once
#include "pair_transport.hpp"

namespace wiz::transport {
// The eleven shared fields of a pool object, with `count` as its +10 word.
template<class T> void print_hit_fields(const T& o, std::uint16_t count) {
    const auto& p=o.presentation;
    for(auto v:std::array<unsigned,11>{o.position.x,o.position.y,o.flags,p.mode,p.words[0],p.words[1],p.words[2],p.counter,p.reload,o.target,count})std::cout<<' '<<v;
}
// A control link from 26 row fields at j: a dormant return-only object (kind
// 0: the eleven fields and +4A), or a carrying 6D8C emitter (kind 1: also +36,
// ten history words, extents and record).
inline sim::PoolObject authored_link(const std::vector<std::uint32_t>& f, std::size_t j, bool emitter) {
    auto w=[&](std::size_t i){if(f[i]>65535)throw assets::BankError("link word outside range");return static_cast<std::uint16_t>(f[i]);};
    auto b=[&](std::size_t i){if(f[i]>255)throw assets::BankError("link byte outside range");return static_cast<std::uint8_t>(f[i]);};
    const sim::MotionPresentation presentation{b(j+3),{w(j+4),w(j+5),w(j+6)},b(j+7),b(j+8)};
    if(f[j+25]>15) throw assets::BankError("link record outside range");
    if(!emitter) return sim::ReturnOnlyObject{{w(j),w(j+1)},w(j+2),presentation,w(j+9),w(j+10),{f[j+22]}};
    sim::TrailEmitter e;e.position={w(j),w(j+1)};e.flags=w(j+2);e.presentation=presentation;e.target=w(j+9);e.countdown=w(j+11);
    for(std::size_t h=0;h<5;++h) e.history[h]={w(j+12+2*h),w(j+13+2*h)};
    e.owner={f[j+22]};e.carried=sim::CarriedPickup{w(j+10),f[j+25],w(j+23),w(j+24)};
    return e;
}
// The link's kind and fields in authored_link's order (a dormant link prints
// only the eleven fields and +4A).
inline void print_link(const sim::PoolObject& o) {
    if(const auto* d=std::get_if<sim::ReturnOnlyObject>(&o)) {std::cout<<" 0";print_hit_fields(*d,d->countdown);std::cout<<' '<<d->control.value;return;}
    const auto& e=std::get<sim::TrailEmitter>(o);
    if(!e.carried) throw assets::BankError("emitter lost its carried pickup");
    std::cout<<" 1";print_hit_fields(e,e.carried->count);std::cout<<' '<<e.countdown;
    for(const auto& h:e.history)std::cout<<' '<<h.x<<' '<<h.y;
    std::cout<<' '<<e.owner.value<<' '<<e.carried->x_extent<<' '<<e.carried->y_extent<<' '<<e.carried->record;
}
// Authored 6BD6/6C00 walks shared with the restricted original (115 fields):
// pickup x y flags mode w06 w08 w0a c0c r0d target count, control, extents,
// record; slots s l1 l2; link kinds (0 dormant return-only, 1 carrying
// emitter); per link the eleven fields, +36, ten history words, owner,
// extents, record; sixteen FF312C kinds; sixteen record entries (16 = absent);
// p1x p1y mask gate present p2x p2y; free depth; walks; the walk after which
// both trackers leave (Y + 4000, 0 = never); the starting phase. An emitter's
// record names it, the pickup's record the pickup, and every other record the
// lowest slot outside s/l1/l2. Success prints "1 released", the
// pickup (with control, extents, record and phase), both links (kind, fields;
// an emitter adds +36, ten history words, owner, extents and record, a dormant
// link its control), sixteen (holder, entry) records, the sound requests, the
// free depth and the released slot (99 when none). The 6E32/6E5E/6E8A family
// stop prints "0 1" and a collectable callback "0 2".
inline void authored_pickup_hit(const std::vector<std::uint32_t>& f) {
    constexpr std::size_t link=20,width=26,slots=pair_pool_slots;
    if(f.size()!=115) throw assets::BankError("invalid pickup hit case");
    auto w=[&](std::size_t i){if(f[i]>65535)throw assets::BankError("pickup hit word outside range");return static_cast<std::uint16_t>(f[i]);};
    auto b=[&](std::size_t i){if(f[i]>255)throw assets::BankError("pickup hit byte outside range");return static_cast<std::uint8_t>(f[i]);};
    auto presentation=[&](std::size_t j){return sim::MotionPresentation{b(j+3),{w(j+4),w(j+5),w(j+6)},b(j+7),b(j+8)};};
    const std::size_t s=f[15],l1=f[16],l2=f[17];
    if(s>=slots || l1>=slots || l2>=slots || s==l1 || s==l2 || l1==l2 || f[18]>1 || f[19]>1 || f[14]>15) throw assets::BankError("pickup hit slots invalid");
    if(f[108]>1 || f[111]>64 || !f[112] || f[112]>64 || f[113]>64 || f[114]>3) throw assets::BankError("pickup hit context invalid");
    std::size_t other=0;while(other==s || other==l1 || other==l2)++other;
    std::vector<sim::PoolObject> objects(slots,sim::ExternalReservation{});std::vector<std::size_t> free;
    for(std::size_t i=0;i<slots && free.size()<f[111];++i) if(i!=s && i!=l1 && i!=l2 && i!=other) {objects[i]=std::monostate{};free.push_back(i);}
    objects[s]=sim::Pickup{{w(0),w(1)},w(2),presentation(0),w(9),w(10),{f[11]},w(12),w(13),f[14],static_cast<sim::PickupPhase>(f[114])};
    const std::array<std::size_t,2> links{l1,l2};
    for(std::size_t k=0;k<2;++k) objects[links[k]]=authored_link(f,link+width*k,f[18+k]);
    sim::MixedPool pool(std::move(objects),free);
    auto id=[&](std::size_t slot){return sim::EffectId{slot,pool.slots()[slot].generation};};
    sim::PickupWorld world;world.controls={sim::ActorId{0xffff0690U},sim::ActorId{0xffff0838U}};world.links={id(l1),id(l2)};
    for(std::size_t k=0;k<16;++k) world.kinds[k]=w(72+k);
    for(std::size_t r=0;r<16;++r) {
        if(f[88+r]>16) throw assets::BankError("pickup hit record entry outside range");
        if(f[88+r]==16) continue;
        const auto holder=(f[18] && r==f[link+25]) ? l1 : (f[19] && r==f[link+width+25]) ? l2 : r==f[14] ? s : other;
        world.records[r]=sim::PickupRecord{id(holder),f[88+r]};
    }
    sim::CollisionInputs inputs{{w(104),w(105)},{w(106),w(107),{}}};
    if(f[108]) inputs.config.secondary=sim::Position{w(109),w(110)};
    else if(f[109] || f[110]) throw assets::BankError("unconsumed secondary coordinates");
    bool released=false;
    try {
        for(unsigned n=0;n<f[112];++n) {
            if(f[113] && n==f[113]) {
                inputs.primary.y=static_cast<std::uint16_t>(inputs.primary.y+0x4000U);
                if(inputs.config.secondary) inputs.config.secondary->y=static_cast<std::uint16_t>(inputs.config.secondary->y+0x4000U);
            }
            released|=pool.walk_pickup(id(s),inputs,world);
        }
    } catch(const assets::BankError& e) {
        const std::string_view reason=e.what();
        if(reason=="unsupported pickup-hit 6C00 family") {std::cout<<"0 1";return;}
        if(reason=="unsupported pickup callback") {std::cout<<"0 2";return;}
        throw;
    }
    const auto& p=std::get<sim::Pickup>(pool.slots()[s].object);
    std::cout<<"1 "<<released;print_hit_fields(p,p.countdown);
    std::cout<<' '<<p.control.value<<' '<<p.x_extent<<' '<<p.y_extent<<' '<<p.record<<' '<<static_cast<unsigned>(p.phase);
    for(auto l:links) print_link(pool.slots()[l].object);
    for(const auto& r:world.records) {
        unsigned holder=0;
        if(r) {const std::array<std::size_t,4> by{s,l1,l2,other};for(unsigned k=0;k<4;++k)if(r->object.slot==by[k])holder=k+1;}
        std::cout<<' '<<holder<<' '<<(r ? r->entry : 16);
    }
    std::cout<<' '<<world.sounds.size();
    for(const auto& q:world.sounds)std::cout<<' '<<q.id<<' '<<q.priority<<' '<<q.parameter<<' '<<q.selector;
    std::cout<<' '<<pool.available()<<' '<<(released ? pool.free_stack().back() : 99);
}
} // namespace wiz::transport
