#pragma once
#include "world_transport.hpp"

namespace wiz::transport {
// Authored copy walks through callback79B6's second-ingredient path (45
// fields): copy x y flags mode w06 w08 w0a c0c r0d target count, control
// (FF0690 or FF0838), frames (+22/+26), extents, record; the copy, FF31AC,
// FF31B8, FF31C0-anchor and record-holder slots; the record's entry; the FF31AC
// object's +32; the anchor's eleven fields and control; the control's +46 code,
// +53 and +56; FF0D60 as two words; FF31BC; FF31BE; free depth; walks. Prints
// "1 called released", then without a callback the copy as --delivered does,
// and after it the released copy and the FF31B8 object as table objects, the
// anchor's eleven fields (+10 its countdown) and control, the FF31AC slot, the
// FF31B0 slot, the record's holder and entry, the +46 code, +53, +56, the row
// clear, FF31BC and FF31BE; last the free depth.
inline void authored_second_ingredient(const std::vector<std::uint32_t>& f) {
    constexpr std::size_t slots=pair_pool_slots;
    if(f.size()!=45) throw assets::BankError("invalid second ingredient case");
    auto w=[&](std::size_t i){if(f[i]>65535)throw assets::BankError("second ingredient word outside range");return static_cast<std::uint16_t>(f[i]);};
    auto b=[&](std::size_t i){if(f[i]>255)throw assets::BankError("second ingredient byte outside range");return static_cast<std::uint8_t>(f[i]);};
    const std::array<std::size_t,5> at{f[17],f[18],f[19],f[20],f[21]};
    for(std::size_t i=0;i<5;++i){if(at[i]>=slots)throw assets::BankError("second ingredient slot outside pool");for(std::size_t j=0;j<i;++j)if(at[i]==at[j])throw assets::BankError("second ingredient slots repeat");}
    const auto [s,a,t,c,h]=at;
    if(f[16]>15 || f[22]>15 || f[36]>4 || f[43]>64 || !f[44] || f[44]>64 || (f[11]!=0xffff0690U && f[11]!=0xffff0838U)) throw assets::BankError("second ingredient context invalid");
    std::vector<sim::PoolObject> objects(slots,sim::ExternalReservation{});std::vector<std::size_t> free;
    for(std::size_t i=0;i<slots && free.size()<f[43];++i) if(i!=s && i!=a && i!=t && i!=c && i!=h) {objects[i]=std::monostate{};free.push_back(i);}
    objects[s]=sim::DeliveredPickup{{w(0),w(1)},w(2),{b(3),{w(4),w(5),w(6)},b(7),b(8)},w(9),{f[11]},{w(12),w(13)},{w(10),f[16],w(14),w(15)}};
    sim::TableMotion first;first.presentation.mode=0x81;first.delta_x=w(23); // Only +32 is read.
    objects[a]=first;objects[t]=sim::ReturnOnlyObject{};
    objects[c]=sim::ReturnOnlyObject{{w(24),w(25)},w(26),{b(27),{w(28),w(29),w(30)},b(31),b(32)},w(33),w(34),{f[35]}};
    sim::MixedPool pool(std::move(objects),free);
    auto id=[&](std::size_t slot){return sim::EffectId{slot,pool.slots()[slot].generation};};
    sim::PickupWorld world;world.controls={sim::ActorId{0xffff0690U},sim::ActorId{0xffff0838U}};
    world.records[f[16]]=sim::PickupRecord{id(h),f[22]};world.activation=id(a);world.dormant={id(a),id(t)};world.anchor=id(c);
    const auto k=f[11]==0xffff0838U ? 1U : 0U;
    world.messages[k]=world_message(f[36],f[37],f[38]);
    world.message_tilemap=static_cast<std::uint32_t>(w(39))<<16U | w(40);world.ingredient_timer=w(42);
    sim::PrivateGlobals globals;globals.table_loop_count=w(41);
    bool released=false;
    for(unsigned n=0;n<f[44] && !released;++n) released=pool.walk_delivered(id(s),globals,world);
    std::cout<<"1 "<<released<<' '<<released;
    if(!released) {
        const auto& d=std::get<sim::DeliveredPickup>(pool.slots()[s].object);
        print_hit_fields(d,d.carried.count);
        std::cout<<' '<<d.control.value<<' '<<d.frames[0]<<' '<<d.frames[1]<<' '<<d.carried.x_extent<<' '<<d.carried.y_extent<<' '<<d.carried.record;
    } else {
        for(auto slot:{s,t}) {
            const auto& m=std::get<sim::TableMotion>(pool.slots()[slot].object);
            print_hit_fields(m,m.countdown);std::cout<<' '<<m.control.value<<' '<<m.cursor<<' '<<m.delta_x<<' '<<m.toggle;
        }
        const auto& anchor=std::get<sim::SpellCountdown>(pool.slots()[c].object);
        print_hit_fields(anchor,anchor.countdown);std::cout<<' '<<anchor.control.value;
        const auto& r=*world.records[f[16]];const auto& m=*world.messages[k];
        std::cout<<' '<<world.activation->slot<<' '<<world.spell->slot<<' '<<r.object.slot<<' '<<r.entry<<' '<<message_code(world.messages[k])<<' '<<unsigned(m.priority)<<' '<<m.row;
        std::cout<<' '<<world.clears.size();for(const auto& clear:world.clears)std::cout<<' '<<clear.vram;
        std::cout<<' '<<*globals.table_loop_count<<' '<<world.ingredient_timer;
    }
    std::cout<<' '<<pool.available();
}
// Authored 7CC8 calls (36 fields): FF31B0 present, FF31AC present, FF31BE,
// FF31BC, the FF31AC and FF31B0 objects' slots, then per table object x y w06
// w08 w0a c0c r0d +10 +36 +32 cursor-index mode flags target control. Prints
// FF31BE, FF31BC and both objects in the same order.
inline void authored_spell_mix(const std::vector<std::uint32_t>& f) {
    constexpr std::size_t width=15;
    if(f.size()!=6+2*width || f[0]>1 || f[1]>1 || f[4]>=pair_pool_slots || f[5]>=pair_pool_slots || f[4]==f[5]) throw assets::BankError("invalid spell mix case");
    auto w=[&](std::size_t i){if(f[i]>65535)throw assets::BankError("spell mix word outside range");return static_cast<std::uint16_t>(f[i]);};
    auto b=[&](std::size_t i){if(f[i]>255)throw assets::BankError("spell mix byte outside range");return static_cast<std::uint8_t>(f[i]);};
    std::vector<sim::PoolObject> objects(pair_pool_slots,sim::ExternalReservation{});
    for(std::size_t k=0;k<2;++k) {
        const auto j=6+width*k;
        if(f[j+10]>=24) throw assets::BankError("spell mix cursor outside table");
        objects[f[4+k]]=sim::TableMotion{{w(j),w(j+1)},w(j+12),{b(j+11),{w(j+2),w(j+3),w(j+4)},b(j+5),b(j+6)},w(j+13),w(j+7),{f[j+14]},f[j+10],w(j+9),w(j+8)};
    }
    sim::MixedPool pool(std::move(objects),{});
    auto id=[&](std::size_t slot){return sim::EffectId{slot,pool.slots()[slot].generation};};
    sim::PickupWorld world;world.ingredient_timer=w(2);
    if(f[1]) world.activation=id(f[4]);
    if(f[0]) world.spell=id(f[5]);
    sim::PrivateGlobals globals;globals.table_loop_count=w(3);
    pool.mix_spell(world,&globals);
    std::cout<<world.ingredient_timer<<' '<<*globals.table_loop_count;
    for(std::size_t k=0;k<2;++k) {
        const auto& m=std::get<sim::TableMotion>(pool.slots()[f[4+k]].object);const auto& p=m.presentation;
        for(auto v:std::array<std::uint64_t,15>{m.position.x,m.position.y,p.words[0],p.words[1],p.words[2],p.counter,p.reload,m.countdown,m.toggle,m.delta_x,m.cursor,p.mode,m.flags,m.target,m.control.value})
            std::cout<<' '<<v;
    }
}
} // namespace wiz::transport
