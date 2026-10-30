#pragma once
#include "mixed_transport.hpp"
#include <algorithm>
#include <string_view>

namespace wiz::transport {
constexpr std::size_t pair_pool_slots=68;
template<class T> void print_pair_member(const T& o) {
    const auto& p=o.presentation;
    for(auto v:std::array<unsigned,11>{o.position.x,o.position.y,o.flags,p.mode,p.words[0],p.words[1],p.words[2],p.counter,p.reload,o.target,o.countdown})std::cout<<' '<<v;
    std::cout<<' '<<o.control.value;
    if constexpr (std::is_same_v<T,sim::CollisionProbe>) std::cout<<' '<<o.x_extent<<' '<<o.y_extent;
    if constexpr (std::is_same_v<T,sim::Pickup>) std::cout<<' '<<o.x_extent<<' '<<o.y_extent<<' '<<o.record;
    if constexpr (std::is_same_v<T,sim::GatedLead>) std::cout<<' '<<static_cast<unsigned>(o.pair)<<' '<<o.partner.slot;
}
inline std::vector<sim::EffectId> group_ids(const sim::ObjectPair& p) { return {p.first,p.second}; }
inline std::vector<sim::EffectId> group_ids(const sim::ObjectQuad& q) { return {q.members.begin(),q.members.end()}; }
inline std::vector<sim::EffectId> group_ids(sim::EffectId id) { return {id}; }
inline std::vector<sim::EffectId> group_ids(const sim::LevelSetupPairs& p) {
    std::vector<sim::EffectId> ids;
    for(const auto& pair:p.pairs) if(pair) { ids.push_back(pair->partner);ids.push_back(pair->lead); }
    return ids;
}
inline std::vector<sim::EffectId> group_ids(const sim::LevelSetupPrefix& p) {
    std::vector<sim::EffectId> ids{p.dormant[0],p.dormant[1],p.rising.first,p.rising.second};
    ids.insert(ids.end(),p.quad.members.begin(),p.quad.members.end());
    for(auto id:{p.return_only.first,p.return_only.second,p.visibility.first,p.visibility.second}) ids.push_back(id);
    return ids;
}
// Prints a retained member with the shared field order of print_pair_member.
inline void print_group_member(const sim::PoolObject& object) {
    std::visit([](const auto& o) {
        using T=std::decay_t<decltype(o)>;
        if constexpr (std::is_same_v<T,sim::ReturnOnlyObject> || std::is_same_v<T,sim::PrivateObject> || std::is_same_v<T,sim::CollisionProbe> || std::is_same_v<T,sim::Pickup>
                      || std::is_same_v<T,sim::GatedLead>) print_pair_member(o);
        else throw assets::BankError("unexpected group member type");
    },object);
}
// Authored component case shared with the restricted original:
// count top second reg fill, then b01 target countdown link callback private
// for the top and the entry below it. Other free entries are ascending slots.
// `reg` is the caller register the routine consumes: A6 for 7B9C/7C26 (then
// replaced), A5 for 7772 (stored as the control link).
// Inheritance is representable only when +01, +1A and +1E..+45 are zero.
// Success prints "1 first second [anchor] available" and both members;
// exhaustion prints "0 1" and unknown inheritance "0 2".
template<class T,class Init> void authored_pair(const std::vector<std::uint32_t>& f,Init init,std::string_view exhausted,std::string_view unknown,bool anchored) {
    if(f.size()!=17 || f[0]>pair_pool_slots || f[1]>=pair_pool_slots || f[2]>=pair_pool_slots || f[1]==f[2] || f[4]>255)
        throw assets::BankError("invalid pair case");
    for(std::size_t j:{5u,11u}) if(f[j]>255 || f[j+1]>65535 || f[j+2]>65535 || f[j+5]>255) throw assets::BankError("pair residue outside range");
    std::vector<std::size_t> stack;
    for(std::size_t i=0;i<pair_pool_slots && stack.size()+2<f[0];++i) if(i!=f[1] && i!=f[2]) stack.push_back(i);
    if(f[0]>=2) stack.push_back(f[2]);
    if(f[0]>=1) stack.push_back(f[1]);
    std::vector<sim::PoolObject> objects(pair_pool_slots,sim::ExternalReservation{});
    std::vector<std::optional<sim::InheritedObjectFields>> inherited(pair_pool_slots);
    for(auto i:stack) objects[i]=std::monostate{};
    for(std::size_t j:{5u,11u}) {
        const auto slot=f[j==5 ? 1 : 2];
        if(std::holds_alternative<std::monostate>(objects[slot]) && !f[j] && !f[j+4] && !f[j+5])
            inherited[slot]=sim::InheritedObjectFields{static_cast<std::uint16_t>(f[j+1]),static_cast<std::uint16_t>(f[j+2]),{f[j+3]}};
    }
    sim::MixedPool pool(std::move(objects),stack,std::move(inherited));const auto before=pool.free_stack();
    try {
        const auto pair=init(pool);
        std::cout<<"1 "<<pair.first.slot<<' '<<pair.second.slot;
        if(anchored) std::cout<<' '<<pair.second.slot;
        std::cout<<' '<<pool.available();
        print_pair_member(std::get<T>(pool.at(pair.first).object));
        print_pair_member(std::get<T>(pool.at(pair.second).object));
    } catch(const assets::BankError& e) {
        const std::string_view reason=e.what();
        if(pool.free_stack()!=before) throw assets::BankError("pair rejection changed the pool");
        if(reason==exhausted) std::cout<<"0 1";
        else if(reason==unknown) std::cout<<"0 2";
        else throw;
    }
}
// Authored 783A case: count s0 s1 s2 s3 a5 fill, then per popped member
// b01 target countdown link callback private w08 w0a c0c r0d. s0 is the top
// entry; other free entries are ascending slots below s3. Inheritance is
// representable only when +01, +1A and +1E..+45 are zero. Success prints
// "1 s0 s1 s2 s3 available", the probe (with extents) and three return-only
// members; exhaustion prints "0 1" and unknown inheritance "0 2".
inline void authored_quad(const std::vector<std::uint32_t>& f) {
    constexpr std::size_t members=4,head=7,width=10;
    if(f.size()!=head+members*width || f[0]>pair_pool_slots || f[6]>255) throw assets::BankError("invalid collision quad case");
    for(std::size_t m=0;m<members;++m) {
        if(f[1+m]>=pair_pool_slots) throw assets::BankError("collision quad slot outside pool");
        for(std::size_t k=0;k<m;++k) if(f[1+m]==f[1+k]) throw assets::BankError("collision quad slots repeat");
        const auto j=head+m*width;
        if(f[j]>255 || f[j+1]>65535 || f[j+2]>65535 || f[j+5]>255 || f[j+6]>65535 || f[j+7]>65535 || f[j+8]>255 || f[j+9]>255)
            throw assets::BankError("collision quad residue outside range");
    }
    std::vector<std::size_t> stack;
    auto member_slot=[&](std::size_t i){return std::find(f.begin()+1,f.begin()+1+members,i)!=f.begin()+1+members;};
    for(std::size_t i=0;i<pair_pool_slots && stack.size()+members<f[0];++i) if(!member_slot(i)) stack.push_back(i);
    for(std::size_t m=members;m-->0;) if(f[0]>=m+1) stack.push_back(f[1+m]);
    std::vector<sim::PoolObject> objects(pair_pool_slots,sim::ExternalReservation{});
    std::vector<std::optional<sim::InheritedObjectFields>> inherited(pair_pool_slots);
    for(auto i:stack) objects[i]=std::monostate{};
    for(std::size_t m=0;m<members;++m) {
        const auto j=head+m*width;const auto slot=f[1+m];
        if(std::holds_alternative<std::monostate>(objects[slot]) && !f[j] && !f[j+4] && !f[j+5])
            inherited[slot]=sim::InheritedObjectFields{static_cast<std::uint16_t>(f[j+1]),static_cast<std::uint16_t>(f[j+2]),{f[j+3]},
                sim::InheritedPresentation{{static_cast<std::uint16_t>(f[j+6]),static_cast<std::uint16_t>(f[j+7])},static_cast<std::uint8_t>(f[j+8]),static_cast<std::uint8_t>(f[j+9])}};
    }
    sim::MixedPool pool(std::move(objects),stack,std::move(inherited));const auto before=pool.free_stack();
    try {
        const auto quad=pool.initialize_collision_quad({f[5]});
        std::cout<<'1';for(const auto& id:quad.members)std::cout<<' '<<id.slot;
        std::cout<<' '<<pool.available();
        print_pair_member(std::get<sim::CollisionProbe>(pool.at(quad.members[0]).object));
        for(std::size_t m=1;m<members;++m)print_pair_member(std::get<sim::ReturnOnlyObject>(pool.at(quad.members[m]).object));
    } catch(const assets::BankError& e) {
        const std::string_view reason=e.what();
        if(pool.free_stack()!=before) throw assets::BankError("collision quad rejection changed the pool");
        if(reason=="collision quad allocation exhausted") std::cout<<"0 1";
        else if(reason=="collision quad inherits unknown slot state") std::cout<<"0 2";
        else throw;
    }
}
// Authored [6886,68A4) case: count fill s0..s11, then per popped member b01
// target countdown link callback private w08 w0a c0c r0d x y. s0 is the top
// entry; other free entries are ascending slots below s11. The prefix sets A5
// to FF0690 itself, so its raw value is the control. Success prints "1", the
// twelve slots, the FF31B4/FF31B8/FF31C0 slots, availability and all twelve
// members (the 783A probe with extents); exhaustion prints "0 1" and unknown
// inheritance "0 2".
inline void authored_prefix(const std::vector<std::uint32_t>& f) {
    constexpr std::size_t members=12,head=14,width=12;
    if(f.size()!=head+members*width || f[0]>pair_pool_slots || f[1]>255) throw assets::BankError("invalid setup prefix case");
    for(std::size_t m=0;m<members;++m) {
        if(f[2+m]>=pair_pool_slots) throw assets::BankError("setup prefix slot outside pool");
        for(std::size_t k=0;k<m;++k) if(f[2+m]==f[2+k]) throw assets::BankError("setup prefix slots repeat");
        const auto j=head+m*width;
        if(f[j]>255 || f[j+1]>65535 || f[j+2]>65535 || f[j+5]>255 || f[j+6]>65535 || f[j+7]>65535 || f[j+8]>255 || f[j+9]>255 || f[j+10]>65535 || f[j+11]>65535)
            throw assets::BankError("setup prefix residue outside range");
    }
    std::vector<std::size_t> stack;
    auto member_slot=[&](std::size_t i){return std::find(f.begin()+2,f.begin()+2+members,i)!=f.begin()+2+members;};
    for(std::size_t i=0;i<pair_pool_slots && stack.size()+members<f[0];++i) if(!member_slot(i)) stack.push_back(i);
    for(std::size_t m=members;m-->0;) if(f[0]>=m+1) stack.push_back(f[2+m]);
    std::vector<sim::PoolObject> objects(pair_pool_slots,sim::ExternalReservation{});
    std::vector<std::optional<sim::InheritedObjectFields>> inherited(pair_pool_slots);
    for(auto i:stack) objects[i]=std::monostate{};
    auto w=[&](std::size_t i){return static_cast<std::uint16_t>(f[i]);};
    for(std::size_t m=0;m<members;++m) {
        const auto j=head+m*width;const auto slot=f[2+m];
        if(std::holds_alternative<std::monostate>(objects[slot]) && !f[j] && !f[j+4] && !f[j+5])
            inherited[slot]=sim::InheritedObjectFields{w(j+1),w(j+2),{f[j+3]},
                sim::InheritedPresentation{{w(j+6),w(j+7)},static_cast<std::uint8_t>(f[j+8]),static_cast<std::uint8_t>(f[j+9])},sim::Position{w(j+10),w(j+11)}};
    }
    sim::MixedSessionState world{{},sim::MixedPool(std::move(objects),stack,std::move(inherited)),{}};
    const auto before=world.pool.free_stack();
    try {
        const auto ids=group_ids(sim::initialize_level_setup_prefix(world,{0xffff0690U}));
        std::cout<<'1';for(const auto& id:ids)std::cout<<' '<<id.slot;
        for(const auto& anchor:{world.dormant_anchors[0],world.dormant_anchors[1],world.return_only_anchor})std::cout<<' '<<anchor->slot;
        std::cout<<' '<<world.pool.available();
        for(const auto& id:ids)print_group_member(world.pool.at(id).object);
    } catch(const assets::BankError& e) {
        const std::string_view reason=e.what();
        if(world.pool.free_stack()!=before || world.dormant_anchors[0] || world.return_only_anchor) throw assets::BankError("setup prefix rejection changed the world");
        if(reason.ends_with("allocation exhausted")) std::cout<<"0 1";
        else if(reason.ends_with("inherits unknown slot state")) std::cout<<"0 2";
        else throw;
    }
}
// FF312C kinds, FF314C counts, then FF4C80 x/y pairs: 64 words.
inline sim::PickupTables pickup_tables(const std::vector<std::uint32_t>& f, std::size_t at) {
    if(f.size()<at+64) throw assets::BankError("pickup tables incomplete");
    sim::PickupTables t;
    for(std::size_t i=0;i<64;++i) if(f[at+i]>65535) throw assets::BankError("pickup table word outside range");
    for(std::size_t k=0;k<16;++k) {
        t.kinds[k]=static_cast<std::uint16_t>(f[at+k]);t.counts[k]=static_cast<std::uint16_t>(f[at+16+k]);
        t.positions[k]={static_cast<std::uint16_t>(f[at+32+2*k]),static_cast<std::uint16_t>(f[at+33+2*k])};
    }
    return t;
}
inline void print_records(const sim::MixedSessionState& w) {
    for(const auto& r:w.pickup_records) std::cout<<' '<<(r ? r->object.slot+1 : 0)<<' '<<(r ? r->entry : 0);
}
// Authored [68A4,68BC) case: count fill s0..s17, the 64 table words, then per
// member b01 target countdown link callback private w08 w0a c0c r0d x y for all
// eighteen slots. Members are one pickup per non-FFFF kind, then the P1 and P2
// links; s0 is the top entry and other free entries are ascending slots below.
// A5 is FF0690 from the prefix, so its raw value is the control. Success prints
// "1 n", the member slots, both link slots, sixteen (slot+1, entry) records, the
// rise gate, FF31AC presence and availability, then every member; exhaustion
// prints "0 1" and unknown inheritance "0 2".
inline void authored_tail(const std::vector<std::uint32_t>& f) {
    constexpr std::size_t slots=18,tables=20,head=84,width=12;
    if(f.size()!=head+slots*width || f[0]>pair_pool_slots || f[1]>255) throw assets::BankError("invalid setup tail case");
    const auto t=pickup_tables(f,tables);
    std::size_t members=2;for(auto k:t.kinds) members+=k!=0xffff;
    for(std::size_t m=0;m<slots;++m) {
        if(f[2+m]>=pair_pool_slots) throw assets::BankError("setup tail slot outside pool");
        for(std::size_t k=0;k<m;++k) if(f[2+m]==f[2+k]) throw assets::BankError("setup tail slots repeat");
        const auto j=head+m*width;
        if(f[j]>255 || f[j+1]>65535 || f[j+2]>65535 || f[j+5]>255 || f[j+6]>65535 || f[j+7]>65535 || f[j+8]>255 || f[j+9]>255 || f[j+10]>65535 || f[j+11]>65535)
            throw assets::BankError("setup tail residue outside range");
    }
    std::vector<std::size_t> stack;
    const auto last=f.begin()+2+static_cast<std::ptrdiff_t>(members);
    auto member_slot=[&](std::size_t i){return std::find(f.begin()+2,last,i)!=last;};
    for(std::size_t i=0;i<pair_pool_slots && stack.size()+members<f[0];++i) if(!member_slot(i)) stack.push_back(i);
    for(std::size_t m=members;m-->0;) if(f[0]>=m+1) stack.push_back(f[2+m]);
    std::vector<sim::PoolObject> objects(pair_pool_slots,sim::ExternalReservation{});
    std::vector<std::optional<sim::InheritedObjectFields>> inherited(pair_pool_slots);
    for(auto i:stack) objects[i]=std::monostate{};
    auto w=[&](std::size_t i){return static_cast<std::uint16_t>(f[i]);};
    for(std::size_t m=0;m<members;++m) {
        const auto j=head+m*width;const auto slot=f[2+m];
        if(std::holds_alternative<std::monostate>(objects[slot]) && !f[j] && !f[j+4] && !f[j+5])
            inherited[slot]=sim::InheritedObjectFields{w(j+1),w(j+2),{f[j+3]},
                sim::InheritedPresentation{{w(j+6),w(j+7)},static_cast<std::uint8_t>(f[j+8]),static_cast<std::uint8_t>(f[j+9])},sim::Position{w(j+10),w(j+11)}};
    }
    sim::MixedSessionState world{{},sim::MixedPool(std::move(objects),stack,std::move(inherited)),{}};
    // Stale state the tail must clear: a nonzero rise gate, FF31AC and records.
    world.private_globals=sim::PrivateGlobals{0x13579bdf,0,0};world.activation_target=sim::EffectId{9999,1};
    world.pickup_records.fill(sim::PickupRecord{{9999,1},15});
    const auto before=world.pool.free_stack();
    try {
        const auto out=sim::initialize_level_setup_tail(world,t,{0xffff0690U});
        std::cout<<"1 "<<out.pickups.size();for(const auto& id:out.pickups)std::cout<<' '<<id.slot;
        for(const auto& id:out.control_links)std::cout<<' '<<id.slot;
        print_records(world);
        std::cout<<' '<<world.private_globals->rise_gate<<' '<<bool(world.activation_target)<<' '<<world.pool.available();
        for(const auto& id:out.pickups)print_group_member(world.pool.at(id).object);
        for(const auto& id:out.control_links)print_group_member(world.pool.at(id).object);
    } catch(const assets::BankError& e) {
        const std::string_view reason=e.what();
        if(world.pool.free_stack()!=before || world.control_links[0] || !world.activation_target) throw assets::BankError("setup tail rejection changed the world");
        if(reason.ends_with("allocation exhausted")) std::cout<<"0 1";
        else if(reason.ends_with("inherits unknown slot state")) std::cout<<"0 2";
        else throw;
    }
}
// Seeded [68A4,68BC): header slots free phases p1-control, free row, slot rows,
// one 64-word table row, then one collision row per phase (pickups consume them;
// the dormant links do not). Prints identities (pickups then links), both link
// identities, sixteen records (present slot generation entry), availability,
// the free stack and every member, then each phase's events.
inline void tail_pool(std::istream& input) {
    const auto h=pool_row(input);
    if(h.size()!=4 || h[0]>4096 || h[1]>h[0] || h[2]>4096) throw assets::BankError("invalid setup tail pool header");
    auto pool=pool_seed(input,h[0],h[1]);
    const auto t=pickup_tables(pool_row(input),0);
    std::vector<sim::CollisionInputs> collisions;
    for(unsigned n=0;n<h[2];++n) {
        const auto g=pool_row(input);
        if(g.size()!=7 || g[4]>1) throw assets::BankError("invalid setup tail phase");
        for(auto v:g) if(v>65535) throw assets::BankError("setup tail phase word outside range");
        sim::CollisionInputs c{{static_cast<std::uint16_t>(g[0]),static_cast<std::uint16_t>(g[1])},{static_cast<std::uint16_t>(g[2]),static_cast<std::uint16_t>(g[3]),{}}};
        if(g[4]) c.config.secondary=sim::Position{static_cast<std::uint16_t>(g[5]),static_cast<std::uint16_t>(g[6])};
        else if(g[5] || g[6]) throw assets::BankError("unconsumed secondary coordinates in phase");
        collisions.push_back(c);
    }
    if(input.peek()!=std::char_traits<char>::eof()) throw assets::BankError("unconsumed setup tail input");
    sim::MixedSessionState world{{},std::move(pool),{}};
    const auto out=sim::initialize_level_setup_tail(world,t,{h[3]});
    std::vector<sim::EffectId> ids=out.pickups;ids.insert(ids.end(),out.control_links.begin(),out.control_links.end());
    for(std::size_t i=0;i<ids.size();++i) std::cout<<(i ? " " : "")<<ids[i].slot<<' '<<ids[i].generation;
    print_anchor(world.control_links[0]);print_anchor(world.control_links[1]);
    for(const auto& r:world.pickup_records) std::cout<<' '<<bool(r)<<' '<<(r ? r->object.slot : 0)<<' '<<(r ? r->object.generation : 0)<<' '<<(r ? r->entry : 0);
    std::cout<<' '<<world.pool.available();for(auto i:world.pool.free_stack())std::cout<<' '<<i;
    for(const auto& id:ids) print_object(world.pool.at(id).object);
    std::cout<<'\n';
    sim::TrailRandom unused{};
    for(unsigned n=0;n<h[2];++n) {
        const auto events=world.pool.step({},{},unused,world.pool.slots().size(),nullptr,&collisions[n]);
        std::cout<<events.size();
        for(const auto& e:events){std::cout<<' '<<static_cast<unsigned>(e.kind)<<' '<<e.id.slot<<' '<<e.id.generation;print_object(e.object);}
        std::cout<<'\n';
    }
}
// Authored [68BC,68C4) case: two_player fruit_returned pair_request tilemap
// priority row, then sixteen FF312C kinds. Prints "1 selected message priority
// fruit_returned cleared vram" with selected/message 0 none, 1 MIX THOSE FRUIT,
// 2 FRUIT RETURNED and message 3 when +46 is untouched; the open 6EF0 path
// prints "0 3".
inline void authored_message(const std::vector<std::uint32_t>& f) {
    if(f.size()!=22 || f[0]>65535 || f[1]>65535 || f[2]>65535 || f[4]>255 || f[5]>65535) throw assets::BankError("invalid setup message case");
    sim::PickupTables t;for(std::size_t k=0;k<16;++k){if(f[6+k]>65535)throw assets::BankError("setup message kind outside range");t.kinds[k]=static_cast<std::uint16_t>(f[6+k]);}
    sim::MixedSessionState world{{},sim::MixedPool({},{}),{}};
    world.setup_gates=sim::SetupGates{static_cast<std::uint16_t>(f[0]),static_cast<std::uint16_t>(f[1]),static_cast<std::uint16_t>(f[2]),f[3]};
    world.p1_message=sim::ControlMessage{std::nullopt,static_cast<std::uint8_t>(f[4]),static_cast<std::uint16_t>(f[5])};
    const auto before=*world.setup_gates;
    try {
        const auto r=sim::continue_level_setup(world,t);
        auto code=[](const std::optional<sim::SetupMessage>& m){return m ? static_cast<unsigned>(*m)+1 : 0U;};
        std::cout<<"1 "<<code(r.selected)<<' '<<(r.selected ? code(world.p1_message->message) : 3U)<<' '<<unsigned(world.p1_message->priority)
                 <<' '<<world.setup_gates->fruit_returned<<' '<<bool(r.clear)<<' '<<(r.clear ? r.clear->vram : 0);
    } catch(const assets::BankError& e) {
        if(std::string_view(e.what())!="unsupported 6EF0 pair allocation" || world.setup_gates->fruit_returned!=before.fruit_returned) throw;
        std::cout<<"0 3";
    }
}
// Authored [68C4,68D4) case: count fill a5 g3172 g3174 g3176 g3178 p2x p2y
// s0..s7, then per member b01 target countdown link callback private w08 w0a
// c0c r0d. Members are two pops per open gate in gate order; s0 is the top
// entry and other free entries are ascending slots below. A5 is the caller's
// control (7FBE); the others store FF0690. Success prints "1 mask", each open
// pair's partner and lead slots, availability, then each pair's partner and
// lead (with its pair code and partner slot); exhaustion prints "0 1" and
// unknown inheritance "0 2".
inline void authored_pairs(const std::vector<std::uint32_t>& f) {
    constexpr std::size_t slots=8,head=17,width=10;
    if(f.size()!=head+slots*width || f[0]>pair_pool_slots || f[1]>255) throw assets::BankError("invalid setup pairs case");
    for(std::size_t i=3;i<9;++i) if(f[i]>65535) throw assets::BankError("setup pairs word outside range");
    sim::GatedPairInputs inputs{{},sim::Position{static_cast<std::uint16_t>(f[7]),static_cast<std::uint16_t>(f[8])},{f[2]},{0xffff0690U}};
    std::size_t members=0;
    for(std::size_t i=0;i<4;++i){inputs.gates[i]=static_cast<std::uint16_t>(f[3+i]);members+=inputs.gates[i] ? 2U : 0U;}
    for(std::size_t m=0;m<slots;++m) {
        if(f[9+m]>=pair_pool_slots) throw assets::BankError("setup pairs slot outside pool");
        for(std::size_t k=0;k<m;++k) if(f[9+m]==f[9+k]) throw assets::BankError("setup pairs slots repeat");
        const auto j=head+m*width;
        if(f[j]>255 || f[j+1]>65535 || f[j+2]>65535 || f[j+5]>255 || f[j+6]>65535 || f[j+7]>65535 || f[j+8]>255 || f[j+9]>255)
            throw assets::BankError("setup pairs residue outside range");
    }
    std::vector<std::size_t> stack;
    const auto last=f.begin()+9+static_cast<std::ptrdiff_t>(members);
    auto member_slot=[&](std::size_t i){return std::find(f.begin()+9,last,i)!=last;};
    for(std::size_t i=0;i<pair_pool_slots && stack.size()+members<f[0];++i) if(!member_slot(i)) stack.push_back(i);
    for(std::size_t m=members;m-->0;) if(f[0]>=m+1) stack.push_back(f[9+m]);
    std::vector<sim::PoolObject> objects(pair_pool_slots,sim::ExternalReservation{});
    std::vector<std::optional<sim::InheritedObjectFields>> inherited(pair_pool_slots);
    for(auto i:stack) objects[i]=std::monostate{};
    auto w=[&](std::size_t i){return static_cast<std::uint16_t>(f[i]);};
    for(std::size_t m=0;m<members;++m) {
        const auto j=head+m*width;const auto slot=f[9+m];
        if(std::holds_alternative<std::monostate>(objects[slot]) && !f[j] && !f[j+4] && !f[j+5])
            inherited[slot]=sim::InheritedObjectFields{w(j+1),w(j+2),{f[j+3]},
                sim::InheritedPresentation{{w(j+6),w(j+7)},static_cast<std::uint8_t>(f[j+8]),static_cast<std::uint8_t>(f[j+9])}};
    }
    sim::MixedSessionState world{{},sim::MixedPool(std::move(objects),stack,std::move(inherited)),{}};
    const auto before=world.pool.free_stack();
    try {
        const auto out=sim::initialize_gated_pairs(world,inputs);
        unsigned mask=0;for(std::size_t i=0;i<4;++i) mask|=out.pairs[i] ? 1U<<i : 0U;
        std::cout<<"1 "<<mask;
        for(const auto& p:out.pairs) if(p) std::cout<<' '<<p->partner.slot<<' '<<p->lead.slot;
        std::cout<<' '<<world.pool.available();
        for(const auto& id:group_ids(out)) print_group_member(world.pool.at(id).object);
    } catch(const assets::BankError& e) {
        const std::string_view reason=e.what();
        if(world.pool.free_stack()!=before) throw assets::BankError("setup pairs rejection changed the pool");
        if(reason.ends_with("allocation exhausted")) std::cout<<"0 1";
        else if(reason.ends_with("inherits unknown slot state")) std::cout<<"0 2";
        else throw;
    }
}
// Per-phase explicit inputs: none, private gates ("rise flags hide") or 78EE
// collision inputs ("p1x p1y mask gate present p2x p2y"; P2 only when gated).
enum class PhaseInputs { none, gates, collision };
// Seeded pool (header: slots free phases [extra...]; free row; slot rows), then
// one input row per phase. One group initialization, then that many ordered
// pool phases with no other inputs. `init` receives the header so an
// initializer can take explicit caller inputs from `extra` fields.
// Retained identities printed after the members' ids: none, FF31C0, or
// FF31B4/FF31B8/FF31C0 (each as present slot generation).
enum class Anchors { none, return_only, all };
template<class Init> void pair_pool(std::istream& input,Init init,Anchors anchored,PhaseInputs kind,std::size_t extra=0) {
    const auto h=pool_row(input);
    if(h.size()!=3+extra || h[0]>4096 || h[1]>h[0] || h[2]>4096) throw assets::BankError("invalid pair pool header");
    auto pool=pool_seed(input,h[0],h[1]);
    std::vector<sim::PrivateGlobals> gates;std::vector<sim::CollisionInputs> collisions;
    for(unsigned n=0;kind!=PhaseInputs::none && n<h[2];++n) {
        const auto g=pool_row(input);
        if(kind==PhaseInputs::gates) {
            if(g.size()!=3 || g[1]>65535 || g[2]>65535) throw assets::BankError("invalid pair phase gates");
            gates.push_back({g[0],static_cast<std::uint16_t>(g[1]),static_cast<std::uint16_t>(g[2])});
            continue;
        }
        if(g.size()!=7 || g[4]>1) throw assets::BankError("invalid pair phase collision inputs");
        for(auto v:g) if(v>65535) throw assets::BankError("pair phase collision word outside range");
        auto w=[&](std::size_t i){return static_cast<std::uint16_t>(g[i]);};
        sim::CollisionInputs c{{w(0),w(1)},{w(2),w(3),{}}};
        if(g[4]) c.config.secondary=sim::Position{w(5),w(6)};
        else if(g[5] || g[6]) throw assets::BankError("unconsumed secondary coordinates in phase");
        collisions.push_back(c);
    }
    if(input.peek()!=std::char_traits<char>::eof()) throw assets::BankError("unconsumed pair pool input");
    sim::MixedSessionState world{{},std::move(pool),{}};
    const auto ids=group_ids(init(world,h));
    for(std::size_t i=0;i<ids.size();++i) std::cout<<(i ? " " : "")<<ids[i].slot<<' '<<ids[i].generation;
    if(anchored==Anchors::all) { print_anchor(world.dormant_anchors[0]);print_anchor(world.dormant_anchors[1]); }
    if(anchored!=Anchors::none) print_anchor(world.return_only_anchor);
    std::cout<<' '<<world.pool.available();for(auto i:world.pool.free_stack())std::cout<<' '<<i;
    for(const auto& id:ids) print_object(world.pool.at(id).object);
    std::cout<<'\n';
    sim::TrailRandom unused{};
    for(unsigned n=0;n<h[2];++n) {
        const auto events=world.pool.step({},{},unused,world.pool.slots().size(),kind==PhaseInputs::gates ? &gates[n] : nullptr,
            kind==PhaseInputs::collision ? &collisions[n] : nullptr);
        std::cout<<events.size();
        for(const auto& e:events){std::cout<<' '<<static_cast<unsigned>(e.kind)<<' '<<e.id.slot<<' '<<e.id.generation;print_object(e.object);}
        std::cout<<'\n';
    }
}
} // namespace wiz::transport
