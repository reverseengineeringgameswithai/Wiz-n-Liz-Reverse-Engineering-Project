#pragma once
#include "pickup_transport.hpp"

namespace wiz::transport {
// Authored 78EE/7910 probe walks shared with the restricted original (86
// fields): probe x y flags mode w06 w08 w0a c0c r0d target count, control,
// extents; slots s l1 l2; link kinds and per link the 26 --pickup-hit fields;
// FF31B0 as two words; p1x p1y mask gate present p2x p2y; free depth, the top
// free slot and the one below it (other entries are ascending slots); walks;
// the walk after which P1, and after which P2, leaves (Y + 4000, 0 = never).
// Success prints "1", the probe (eleven fields, control, extents), both links
// (print_link), the objects created in order (kind 0 sparkle: ten fields
// without +10; kind 1 copy: eleven fields, control, frames, extents, record),
// the sound requests and the free depth. Exhaustion prints "0 1" and an invoked
// probe callback "0 3".
inline void authored_probe_hit(const std::vector<std::uint32_t>& f) {
    constexpr std::size_t link=19,width=26,slots=pair_pool_slots;
    if(f.size()!=86) throw assets::BankError("invalid probe hit case");
    auto w=[&](std::size_t i){if(f[i]>65535)throw assets::BankError("probe hit word outside range");return static_cast<std::uint16_t>(f[i]);};
    auto b=[&](std::size_t i){if(f[i]>255)throw assets::BankError("probe hit byte outside range");return static_cast<std::uint8_t>(f[i]);};
    const std::size_t s=f[14],l1=f[15],l2=f[16],top=f[81],below=f[82];
    if(s>=slots || l1>=slots || l2>=slots || s==l1 || s==l2 || l1==l2 || f[17]>1 || f[18]>1) throw assets::BankError("probe hit slots invalid");
    if(top>=slots || below>=slots || top==below || top==s || top==l1 || top==l2 || below==s || below==l1 || below==l2) throw assets::BankError("probe hit free slots invalid");
    if(f[77]>1 || f[80]>64 || !f[83] || f[83]>64 || f[84]>64 || f[85]>64) throw assets::BankError("probe hit context invalid");
    std::vector<sim::PoolObject> objects(slots,sim::ExternalReservation{});std::vector<std::size_t> free;
    for(std::size_t i=0;i<slots && free.size()+2<f[80];++i) if(i!=s && i!=l1 && i!=l2 && i!=top && i!=below) free.push_back(i);
    if(f[80]>=2) free.push_back(below);
    if(f[80]>=1) free.push_back(top);
    for(auto i:free) objects[i]=std::monostate{};
    objects[s]=sim::CollisionProbe{{w(0),w(1)},w(2),{b(3),{w(4),w(5),w(6)},b(7),b(8)},w(9),w(10),{f[11]},w(12),w(13)};
    const std::array<std::size_t,2> links{l1,l2};
    for(std::size_t k=0;k<2;++k) objects[links[k]]=authored_link(f,link+width*k,f[17+k]);
    sim::MixedPool pool(std::move(objects),free);
    auto id=[&](std::size_t slot){return sim::EffectId{slot,pool.slots()[slot].generation};};
    sim::PickupWorld world;world.controls={sim::ActorId{0xffff0690U},sim::ActorId{0xffff0838U}};world.links={id(l1),id(l2)};
    const auto rise=static_cast<std::uint32_t>(w(71))<<16U | w(72);
    sim::CollisionInputs inputs{{w(73),w(74)},{w(75),w(76),{}}};
    if(f[77]) inputs.config.secondary=sim::Position{w(78),w(79)};
    else if(f[78] || f[79]) throw assets::BankError("unconsumed secondary coordinates");
    std::vector<sim::EffectId> created;
    try {
        for(unsigned n=0;n<f[83];++n) {
            if(f[84] && n==f[84]) inputs.primary.y=static_cast<std::uint16_t>(inputs.primary.y+0x4000U);
            if(f[85] && n==f[85] && inputs.config.secondary) inputs.config.secondary->y=static_cast<std::uint16_t>(inputs.config.secondary->y+0x4000U);
            if(const auto ids=pool.walk_probe(id(s),inputs,rise,world)) {created.push_back(ids->sparkle);created.push_back(ids->copy);}
        }
    } catch(const assets::BankError& e) {
        const std::string_view reason=e.what();
        if(reason=="delivery allocation exhausted") {std::cout<<"0 1";return;}
        if(reason=="unsupported collision probe callback") {std::cout<<"0 3";return;}
        throw;
    }
    const auto& p=std::get<sim::CollisionProbe>(pool.slots()[s].object);
    std::cout<<'1';print_hit_fields(p,p.countdown);std::cout<<' '<<p.control.value<<' '<<p.x_extent<<' '<<p.y_extent;
    for(auto l:links) print_link(pool.slots()[l].object);
    std::cout<<' '<<created.size();
    for(const auto& c:created) {
        const auto& o=pool.at(c).object;
        if(const auto* t=std::get_if<sim::TrailParticle>(&o)) {
            const auto& q=t->presentation;std::cout<<" 0 "<<c.slot;
            for(auto v:std::array<unsigned,10>{t->position.x,t->position.y,t->flags,q.mode,q.words[0],q.words[1],q.words[2],q.counter,q.reload,t->target})std::cout<<' '<<v;
            continue;
        }
        const auto& d=std::get<sim::DeliveredPickup>(o);
        std::cout<<" 1 "<<c.slot;print_hit_fields(d,d.carried.count);
        std::cout<<' '<<d.control.value<<' '<<d.frames[0]<<' '<<d.frames[1]<<' '<<d.carried.x_extent<<' '<<d.carried.y_extent<<' '<<d.carried.record;
    }
    std::cout<<' '<<world.sounds.size();
    for(const auto& q:world.sounds)std::cout<<' '<<q.id<<' '<<q.priority<<' '<<q.parameter<<' '<<q.selector;
    std::cout<<' '<<pool.available();
}
// Authored later walks of one 7910 object (21 fields): kind (0 the 59AE
// sparkle, 1 the copy), x y flags mode w06 w08 w0a c0c r0d target count,
// control, frames (+22/+26), extents, record (all of count..record zero for a
// sparkle), slot, free depth (ascending slots), walks. Success prints "1
// released", the fields in the same order (a sparkle stops at target) and the
// free depth; the copy's 79B6 callback prints "0 2".
inline void authored_delivered(const std::vector<std::uint32_t>& f) {
    constexpr std::size_t slots=pair_pool_slots;
    if(f.size()!=21) throw assets::BankError("invalid delivered case");
    auto w=[&](std::size_t i){if(f[i]>65535)throw assets::BankError("delivered word outside range");return static_cast<std::uint16_t>(f[i]);};
    auto b=[&](std::size_t i){if(f[i]>255)throw assets::BankError("delivered byte outside range");return static_cast<std::uint8_t>(f[i]);};
    const std::size_t s=f[18];
    if(f[0]>1 || s>=slots || f[17]>15 || f[19]>64 || !f[20] || f[20]>64) throw assets::BankError("delivered context invalid");
    if(!f[0] && std::any_of(f.begin()+11,f.begin()+18,[](auto v){return v!=0;})) throw assets::BankError("sparkle residue must be zero");
    std::vector<sim::PoolObject> objects(slots,sim::ExternalReservation{});std::vector<std::size_t> free;
    for(std::size_t i=0;i<slots && free.size()<f[19];++i) if(i!=s) {objects[i]=std::monostate{};free.push_back(i);}
    const sim::Position at{w(1),w(2)};const sim::MotionPresentation presentation{b(4),{w(5),w(6),w(7)},b(8),b(9)};
    if(f[0]) objects[s]=sim::DeliveredPickup{at,w(3),presentation,w(10),{f[12]},{w(13),w(14)},{w(11),f[17],w(15),w(16)}};
    else objects[s]=sim::TrailParticle{at,w(3),presentation,w(10)};
    sim::MixedPool pool(std::move(objects),free);
    sim::TrailRandom random;bool released=false;
    try {
        for(unsigned n=0;n<f[20];++n)
            for(const auto& e:pool.step({},{},random,slots)) released|=e.kind==sim::PoolEventKind::release;
    } catch(const assets::BankError& e) {
        if(std::string_view(e.what())=="unsupported delivered pickup callback 79B6") {std::cout<<"0 2";return;}
        throw;
    }
    const auto& o=pool.slots()[s].object;
    std::cout<<"1 "<<released;
    if(const auto* d=std::get_if<sim::DeliveredPickup>(&o)) {
        print_hit_fields(*d,d->carried.count);
        std::cout<<' '<<d->control.value<<' '<<d->frames[0]<<' '<<d->frames[1]<<' '<<d->carried.x_extent<<' '<<d->carried.y_extent<<' '<<d->carried.record;
    } else {
        print_hit_fields(std::get<sim::TrailParticle>(o),0);
        for(int i=0;i<6;++i)std::cout<<" 0";
    }
    std::cout<<' '<<pool.available();
}
} // namespace wiz::transport
namespace wiz::transport {
// Authored copy walks through callback79B6's first-ingredient path (31
// fields): x y flags mode w06 w08 w0a c0c r0d target count, control (FF0690 or
// FF0838), frames (+22/+26), extents, record; the copy's slot, the FF31B4
// object's slot (dormant) and the record's holder slot; the record's entry;
// FF31AC set (0/1); the control's +46 code (0 none, 1 MIX THOSE FRUIT, 2 FRUIT
// RETURNED, 3 FIRST, 4 SECOND INGREDIENT), +53 and +56; FF0D60 as two words;
// FF31BC; FF31BE; free depth; walks. Success prints "1 called released", then
// without a callback the copy as --delivered does, and after it the released
// copy and the FF31B4 object as table objects (eleven fields, control, cursor,
// +32, +36), FF31AC's slot, the record's holder and entry, the +46 code, +53,
// +56, the row clears, FF31BC and FF31BE; last the free depth. The
// second-ingredient path (see --second-ingredient) prints "0 3".
inline void authored_ingredient(const std::vector<std::uint32_t>& f) {
    constexpr std::size_t slots=pair_pool_slots;
    if(f.size()!=31) throw assets::BankError("invalid ingredient case");
    auto w=[&](std::size_t i){if(f[i]>65535)throw assets::BankError("ingredient word outside range");return static_cast<std::uint16_t>(f[i]);};
    auto b=[&](std::size_t i){if(f[i]>255)throw assets::BankError("ingredient byte outside range");return static_cast<std::uint8_t>(f[i]);};
    const std::size_t s=f[17],t=f[18],h=f[19];
    if(s>=slots || t>=slots || h>=slots || s==t || s==h || t==h || f[16]>15 || f[20]>15 || f[21]>1 || f[22]>4 || f[29]>64 || !f[30] || f[30]>64
       || (f[11]!=0xffff0690U && f[11]!=0xffff0838U)) throw assets::BankError("ingredient context invalid");
    std::vector<sim::PoolObject> objects(slots,sim::ExternalReservation{});std::vector<std::size_t> free;
    for(std::size_t i=0;i<slots && free.size()<f[29];++i) if(i!=s && i!=t && i!=h) {objects[i]=std::monostate{};free.push_back(i);}
    objects[s]=sim::DeliveredPickup{{w(0),w(1)},w(2),{b(3),{w(4),w(5),w(6)},b(7),b(8)},w(9),{f[11]},{w(12),w(13)},{w(10),f[16],w(14),w(15)}};
    objects[t]=sim::ReturnOnlyObject{};
    sim::MixedPool pool(std::move(objects),free);
    auto id=[&](std::size_t slot){return sim::EffectId{slot,pool.slots()[slot].generation};};
    sim::PickupWorld world;world.controls={sim::ActorId{0xffff0690U},sim::ActorId{0xffff0838U}};
    world.records[f[16]]=sim::PickupRecord{id(h),f[20]};world.dormant[0]=id(t);
    if(f[21]) world.activation=id(h);
    const auto k=f[11]==0xffff0838U ? 1U : 0U;
    world.messages[k]=sim::ControlMessage{f[22] ? std::optional{static_cast<sim::SetupMessage>(f[22]-1)} : std::nullopt,b(23),w(24)};
    world.message_tilemap=static_cast<std::uint32_t>(w(25))<<16U | w(26);world.ingredient_timer=w(28);
    sim::PrivateGlobals globals;globals.table_loop_count=w(27);
    bool released=false;
    try {
        for(unsigned n=0;n<f[30] && !released;++n) released=pool.walk_delivered(id(s),globals,world);
    } catch(const assets::BankError& e) {
        // With FF31AC set this corpus names no table object, so the callback stops
        // where the original harness stops for the first-ingredient corpus (7A00).
        if(std::string_view(e.what())=="79B6 FF31AC object is not a table object") {std::cout<<"0 3";return;}
        throw;
    }
    const bool called=released; // The first-ingredient path always releases the copy.
    std::cout<<"1 "<<called<<' '<<released;
    if(!called) {
        const auto& d=std::get<sim::DeliveredPickup>(pool.slots()[s].object);
        print_hit_fields(d,d.carried.count);
        std::cout<<' '<<d.control.value<<' '<<d.frames[0]<<' '<<d.frames[1]<<' '<<d.carried.x_extent<<' '<<d.carried.y_extent<<' '<<d.carried.record;
    } else {
        for(auto slot:{s,t}) {
            const auto& m=std::get<sim::TableMotion>(pool.slots()[slot].object);
            print_hit_fields(m,m.countdown);std::cout<<' '<<m.control.value<<' '<<m.cursor<<' '<<m.delta_x<<' '<<m.toggle;
        }
        const auto& r=*world.records[f[16]];const auto& m=*world.messages[k];
        std::cout<<' '<<world.activation->slot<<' '<<r.object.slot<<' '<<r.entry<<' '<<(m.message ? static_cast<unsigned>(*m.message)+1 : 0U)<<' '<<static_cast<unsigned>(m.priority)<<' '<<m.row;
        std::cout<<' '<<world.clears.size();for(const auto& c:world.clears)std::cout<<' '<<c.vram;
        std::cout<<' '<<*globals.table_loop_count<<' '<<world.ingredient_timer;
    }
    std::cout<<' '<<pool.available();
}
} // namespace wiz::transport
