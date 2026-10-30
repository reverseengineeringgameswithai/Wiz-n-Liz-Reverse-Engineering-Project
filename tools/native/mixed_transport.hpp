#pragma once
#include "sim/mixed_pool.hpp"
#include <iostream>
#include <sstream>

namespace wiz::transport {
inline std::vector<std::uint32_t> pool_row(std::istream& input) {
    std::string line;if (!std::getline(input,line) || line.size()>32768) throw assets::BankError("invalid mixed seed row");
    std::istringstream row(line);std::uint64_t v;std::vector<std::uint32_t> f;
    while (row>>v) {if(v>0xffffffffU) throw assets::BankError("mixed seed field outside range");f.push_back(static_cast<std::uint32_t>(v));}
    if (!row.eof()) throw assets::BankError("invalid mixed seed field");
    return f;
}
// One seeded slot row. Tag 9 is a free slot with verified inherited fields
// (target, countdown, control), optionally followed by verified +08/+0A words
// and +0C/+0D counter/reload, then optionally the +02/+04 position; tag 0 is a
// free slot whose residue is unknown.
struct SeedSlot { sim::PoolObject object; std::optional<sim::InheritedObjectFields> inherited; };
inline SeedSlot pool_object(const std::vector<std::uint32_t>& f) {
    if(f.empty() || f[0]>9)throw assets::BankError("unknown mixed seed object");
    const auto type=f[0];const std::size_t expected=type<2 ? 1 : type==2 ? 13 : type==3 ? 11 : type==4 ? 23 : type==5 ? 14 : type==6 ? 16 : type==7 ? 15 : type==8 ? 13 : f.size()==10 ? 10 : f.size()==8 ? 8 : 4;
    if(f.size()!=expected)throw assets::BankError("mixed seed object extent differs");
    auto w=[&](std::size_t j){if(f[j]>65535)throw assets::BankError("mixed word outside range");return static_cast<std::uint16_t>(f[j]);};
    auto b=[&](std::size_t j){if(f[j]>255)throw assets::BankError("mixed byte outside range");return static_cast<std::uint8_t>(f[j]);};
    if(type==0)return {std::monostate{},{}};
    if(type==9) {
        sim::InheritedObjectFields inherited{w(1),w(2),{f[3]}};
        if(f.size()>=8)inherited.presentation=sim::InheritedPresentation{{w(4),w(5)},b(6),b(7)};
        if(f.size()==10)inherited.position=sim::Position{w(8),w(9)};
        return {std::monostate{},inherited};
    }
    if(type==1)return {sim::ExternalReservation{},{}};
    if(type==2) {
        if(!f[1] || f[2]>1)throw assets::BankError("invalid mixed reversal identity");
        return {sim::ReversalEffect{{f[1]},{w(3),w(4)},{b(6),{w(7),w(8),w(9)},b(10),b(11)},w(12),w(5),static_cast<sim::ReversalSide>(f[2])},{}};
    }
    if(type==3)return {sim::TrailParticle{{w(1),w(2)},w(3),{b(4),{w(5),w(6),w(7)},b(8),b(9)},w(10)},{}};
    if(type==4) {
        sim::TrailEmitter e;e.position={w(1),w(2)};e.countdown=w(3);
        for(std::size_t j=0;j<5;++j)e.history[j]={w(4+2*j),w(5+2*j)};
        e.presentation={b(14),{w(15),w(16),w(17)},b(18),b(19)};e.target=w(20);e.flags=w(21);e.owner={f[22]};return {e,{}};
    }
    if(type==5) {
        if(f[1]>1)throw assets::BankError("unknown private object handler");
        return {sim::PrivateObject{static_cast<sim::PrivateUpdate>(f[1]),{w(2),w(3)},w(4),{b(5),{w(6),w(7),w(8)},b(9),b(10)},w(11),w(12),{f[13]}},{}};
    }
    if(type==6)return {sim::TableMotion{{w(1),w(2)},w(3),{b(4),{w(5),w(6),w(7)},b(8),b(9)},w(10),w(11),{f[12]},f[13],w(14),w(15)},{}};
    if(type==7)return {sim::CollisionProbe{{w(1),w(2)},w(3),{b(4),{w(5),w(6),w(7)},b(8),b(9)},w(10),w(11),{f[12]},w(13),w(14)},{}};
    return {sim::ReturnOnlyObject{{w(1),w(2)},w(3),{b(4),{w(5),w(6),w(7)},b(8),b(9)},w(10),w(11),{f[12]}},{}};
}
inline sim::MixedPool pool_seed(std::istream& input,std::uint32_t slots,std::uint32_t free_count) {
    const auto free=pool_row(input);if(free.size()!=free_count)throw assets::BankError("invalid mixed free extent");
    std::vector<sim::PoolObject> objects;std::vector<std::optional<sim::InheritedObjectFields>> inherited;
    objects.reserve(slots);inherited.reserve(slots);
    for(unsigned i=0;i<slots;++i){auto s=pool_object(pool_row(input));objects.push_back(std::move(s.object));inherited.push_back(s.inherited);}
    return sim::MixedPool(std::move(objects),{free.begin(),free.end()},std::move(inherited));
}
// Header sizes 4/7/8/13 retain their earlier meanings; size 14 adds the
// FF31C0 anchor as slot+1 (0 = none), whose generation is the seeded one.
inline sim::MixedSessionState mixed_seed(std::istream& input,sim::P1SessionState p1,bool* anchored=nullptr) {
    const auto header=pool_row(input);
    if((header.size()!=4 && header.size()!=7 && header.size()!=8 && header.size()!=13 && header.size()!=14) || header[0]>4096 || header[1]>header[0]) throw assets::BankError("invalid mixed seed header");
    auto pool=pool_seed(input,header[0],header[1]);
    std::optional<sim::PrivateGlobals> globals;
    if(header.size()>=7) {
        if(header[5]>65535 || header[6]>65535)throw assets::BankError("private gate word outside range");
        globals=sim::PrivateGlobals{header[4],static_cast<std::uint16_t>(header[5]),static_cast<std::uint16_t>(header[6])};
    }
    if(header.size()>=8) {
        if(header[7]>65535)throw assets::BankError("table loop count outside range");
        globals->table_loop_count=static_cast<std::uint16_t>(header[7]);
    }
    std::optional<sim::CollisionConfig> collision;
    if(header.size()>=13) {
        if(header[8]>65535 || header[9]>65535 || header[10]>1 || header[11]>65535 || header[12]>65535)
            throw assets::BankError("invalid collision seed context");
        collision=sim::CollisionConfig{static_cast<std::uint16_t>(header[8]),static_cast<std::uint16_t>(header[9]),{}};
        if(header[10]) collision->secondary=sim::Position{static_cast<std::uint16_t>(header[11]),static_cast<std::uint16_t>(header[12])};
        else if(header[11] || header[12]) throw assets::BankError("unconsumed secondary coordinates in seed");
    }
    std::optional<sim::EffectId> anchor;
    if(header.size()==14 && header[13]) {
        if(header[13]>header[0])throw assets::BankError("return-only anchor outside pool");
        const auto& slot=pool.slots()[header[13]-1];
        if(!std::holds_alternative<sim::ReturnOnlyObject>(slot.object))throw assets::BankError("return-only anchor names another object");
        anchor=sim::EffectId{header[13]-1,slot.generation};
    }
    if(anchored)*anchored=header.size()==14;
    return {std::move(p1),std::move(pool),{header[2],header[3]},globals,collision,anchor};
}
inline void print_object(const sim::PoolObject& object) {
    std::cout<<' '<<object.index();
    std::visit([](const auto& e) {
        using T=std::decay_t<decltype(e)>;
        if constexpr (std::is_same_v<T,sim::ReversalEffect>) {
            std::cout<<' '<<e.owner.value<<' '<<static_cast<unsigned>(e.side);
            for(auto v:std::array<unsigned,3>{e.position.x,e.position.y,e.flags})std::cout<<' '<<v;
        } else if constexpr (std::is_same_v<T,sim::PrivateObject>) {
            std::cout<<' '<<static_cast<unsigned>(e.update)<<' '<<e.position.x<<' '<<e.position.y<<' '<<e.flags;
        } else if constexpr (std::is_same_v<T,sim::TrailParticle> || std::is_same_v<T,sim::TableMotion> || std::is_same_v<T,sim::CollisionProbe> || std::is_same_v<T,sim::ReturnOnlyObject> || std::is_same_v<T,sim::Pickup> || std::is_same_v<T,sim::GatedLead> || std::is_same_v<T,sim::DeliveredPickup>) {
            for(auto v:std::array<unsigned,3>{e.position.x,e.position.y,e.flags})std::cout<<' '<<v;
        } else if constexpr (std::is_same_v<T,sim::TrailEmitter>) {
            std::cout<<' '<<e.position.x<<' '<<e.position.y<<' '<<e.countdown;
            for(auto h:e.history)std::cout<<' '<<h.x<<' '<<h.y;
        }
        if constexpr (!std::is_same_v<T,std::monostate> && !std::is_same_v<T,sim::ExternalReservation>) {
            const auto& p=e.presentation;
            for(auto v:std::array<unsigned,7>{p.mode,p.words[0],p.words[1],p.words[2],p.counter,p.reload,e.target})std::cout<<' '<<v;
            if constexpr (std::is_same_v<T,sim::CollisionProbe>)std::cout<<' '<<e.countdown<<' '<<e.control.value<<' '<<e.x_extent<<' '<<e.y_extent;
            if constexpr (std::is_same_v<T,sim::Pickup>)std::cout<<' '<<e.countdown<<' '<<e.control.value<<' '<<e.x_extent<<' '<<e.y_extent<<' '<<e.record;
            if constexpr (std::is_same_v<T,sim::ReturnOnlyObject>)std::cout<<' '<<e.countdown<<' '<<e.control.value;
            if constexpr (std::is_same_v<T,sim::GatedLead>)std::cout<<' '<<e.countdown<<' '<<e.control.value<<' '<<static_cast<unsigned>(e.pair)<<' '<<e.partner.slot<<' '<<e.partner.generation;
            if constexpr (std::is_same_v<T,sim::TableMotion>)std::cout<<' '<<e.countdown<<' '<<e.control.value<<' '<<e.cursor<<' '<<e.delta_x<<' '<<e.toggle;
            if constexpr (std::is_same_v<T,sim::PrivateObject>)std::cout<<' '<<e.countdown<<' '<<e.control.value;
            if constexpr (std::is_same_v<T,sim::TrailEmitter>)std::cout<<' '<<e.flags<<' '<<e.owner.value;
            if constexpr (std::is_same_v<T,sim::DeliveredPickup>)
                for(auto v:std::array<std::uint64_t,7>{e.control.value,e.frames[0],e.frames[1],e.carried.count,e.carried.record,e.carried.x_extent,e.carried.y_extent})std::cout<<' '<<v;
        }
    },object);
}
inline void print_anchor(const std::optional<sim::EffectId>& anchor) {
    std::cout<<' '<<bool(anchor)<<' '<<(anchor ? anchor->slot : 0)<<' '<<(anchor ? anchor->generation : 0);
}
inline void print_mixed(const sim::MixedSessionState& state,const std::vector<sim::PoolEvent>& events,bool anchored=false) {
    std::cout<<' '<<state.pool.available();for(auto i:state.pool.free_stack())std::cout<<' '<<i;
    std::cout<<' '<<state.random.state<<' '<<state.random.mirror;
    if(anchored)print_anchor(state.return_only_anchor);
    std::cout<<' '<<events.size();
    for(const auto& e:events){std::cout<<' '<<static_cast<unsigned>(e.kind)<<' '<<e.id.slot<<' '<<e.id.generation;print_object(e.object);}
}
} // namespace wiz::transport
