#pragma once
#include "spell_transport.hpp"

namespace wiz::transport {
// Curve resources as the original's FF0B98..FF0BA3 pointers (zero: none started).
inline unsigned curve_address(sim::TransitionCurve c) {
    switch(c) {
    case sim::TransitionCurve::exit_red_green: return 0x1356a;
    case sim::TransitionCurve::exit_blue: return 0x135aa;
    case sim::TransitionCurve::tally: return 0x135ea;
    default: return 0;
    }
}
// FF0B90..FF0B97, the three curves and FF0EDE.
inline void print_transition(const sim::TransitionState& t) {
    std::cout<<' '<<t.direction<<' '<<t.countdown<<' '<<t.reload<<' '<<t.level;
    for(auto c:t.curves)std::cout<<' '<<curve_address(c);
    std::cout<<' '<<t.palette_scope;
}
inline sim::TransitionState seeded_transition(const std::vector<std::uint32_t>& f, std::size_t j) {
    for(std::size_t i=j;i<j+5;++i) if(f[i]>65535) throw assets::BankError("transition word outside range");
    sim::TransitionState t{static_cast<std::uint16_t>(f[j]),static_cast<std::uint16_t>(f[j+1]),static_cast<std::uint16_t>(f[j+2]),static_cast<std::uint16_t>(f[j+3])};
    t.palette_scope=static_cast<std::uint16_t>(f[j+4]);return t;
}
// Authored walks of the FF31C0 anchor (20 fields): x y flags mode w06 w08 w0a
// c0c r0d target countdown, control, slot, walks, phase (0 7B42, 1 7B58, 2
// 7B8A), FF0B90 FF0B92 FF0B94 FF0B96, FF0EDE. Prints the phase (3 once 7B8A
// installed 12646, 4 when 7B58 reaches its completion), the eleven fields,
// control and the transition block.
inline void authored_anchor(const std::vector<std::uint32_t>& f) {
    if(f.size()!=20 || f[12]>=pair_pool_slots || !f[13] || f[13]>512 || f[14]>2) throw assets::BankError("invalid anchor case");
    auto w=[&](std::size_t i){if(f[i]>65535)throw assets::BankError("anchor word outside range");return static_cast<std::uint16_t>(f[i]);};
    auto b=[&](std::size_t i){if(f[i]>255)throw assets::BankError("anchor byte outside range");return static_cast<std::uint8_t>(f[i]);};
    sim::SpellCountdown anchor{{w(0),w(1)},w(2),{b(3),{w(4),w(5),w(6)},b(7),b(8)},w(9),w(10),{f[11]},static_cast<sim::SpellPhase>(f[14])};
    auto t=seeded_transition(f,15);
    std::optional<sim::ReturnOnlyObject> done;bool complete=false;
    for(unsigned n=0;n<f[13] && !complete;++n) {
        if(done) {sim::step_return_only_object(*done);continue;}
        const auto step=sim::step_spell_countdown(anchor,&t);
        complete=step==sim::SpellStep::complete;
        if(step==sim::SpellStep::revealed) done=sim::ReturnOnlyObject{anchor.position,anchor.flags,anchor.presentation,anchor.target,anchor.countdown,anchor.control};
    }
    std::cout<<(done ? 3U : complete ? 4U : static_cast<unsigned>(anchor.phase));
    if(done) {print_hit_fields(*done,done->countdown);std::cout<<' '<<done->control.value;}
    else {print_hit_fields(anchor,anchor.countdown);std::cout<<' '<<anchor.control.value;}
    print_transition(t);
}
inline sim::TableMotion authored_table(const std::vector<std::uint32_t>& f, std::size_t j) {
    // x y w06 w08 w0a c0c r0d +10 +36 +32 cursor-index mode flags target control.
    auto w=[&](std::size_t i){if(f[i]>65535)throw assets::BankError("table word outside range");return static_cast<std::uint16_t>(f[i]);};
    auto b=[&](std::size_t i){if(f[i]>255)throw assets::BankError("table byte outside range");return static_cast<std::uint8_t>(f[i]);};
    if(f[j+10]>=24) throw assets::BankError("table cursor outside table");
    return sim::TableMotion{{w(j),w(j+1)},w(j+12),{b(j+11),{w(j+2),w(j+3),w(j+4)},b(j+5),b(j+6)},w(j+13),w(j+7),{f[j+14]},f[j+10],w(j+9),w(j+8)};
}
inline void print_table(const sim::TableMotion& m) {
    print_hit_fields(m,m.countdown);std::cout<<' '<<m.control.value<<' '<<m.cursor<<' '<<m.delta_x<<' '<<m.toggle;
}
// Authored 7B58 walks with the completion (67 fields): the anchor's eleven
// fields and control; the anchor, FF31AC and FF31B0 slots; both table objects;
// their records and entries; FF31A8, FF316C, FF33E2, FF31A6, FF31A4; FF0690
// +3C/+3E; the control's +46 code, +53, +56; FF0D60 as two words; free depth;
// FF0B90 FF0B92 FF0B94 FF0B96, FF0EDE. Prints "2 pc" for a path outside the
// native recipe; else 0 (waiting) or 1, the anchor and control and, once
// completed, both table objects, the two FF312C entries, FF31C4/FF31C6, the
// +46 code, +53, +56, the row clear, the sound requests, the sparkle (slot x y
// flags mode frame +10 extents), the sign (slot x y flags mode frame), the door
// (slot x y flags mode frame +10 control), FF316C and the transition block; last
// the free depth.
inline void authored_completion(const std::vector<std::uint32_t>& f) {
    constexpr std::size_t slots=pair_pool_slots;
    if(f.size()!=67) throw assets::BankError("invalid completion case");
    auto w=[&](std::size_t i){if(f[i]>65535)throw assets::BankError("completion word outside range");return static_cast<std::uint16_t>(f[i]);};
    auto b=[&](std::size_t i){if(f[i]>255)throw assets::BankError("completion byte outside range");return static_cast<std::uint8_t>(f[i]);};
    const std::size_t s=f[12],sa=f[13],sb=f[14];
    if(s>=slots || sa>=slots || sb>=slots || s==sa || s==sb || sa==sb || (f[11]!=0xffff0690U && f[11]!=0xffff0838U)
       || f[45]>15 || f[46]>15 || f[47]>15 || f[48]>15 || f[45]==f[47] || f[56]>4 || f[61]>65) throw assets::BankError("completion context invalid");
    std::vector<sim::PoolObject> objects(slots,sim::ExternalReservation{});std::vector<std::size_t> free;
    for(std::size_t i=0;i<slots && free.size()<f[61];++i) if(i!=s && i!=sa && i!=sb) {objects[i]=std::monostate{};free.push_back(i);}
    objects[s]=sim::SpellCountdown{{w(0),w(1)},w(2),{b(3),{w(4),w(5),w(6)},b(7),b(8)},w(9),w(10),{f[11]},sim::SpellPhase::completion};
    objects[sa]=authored_table(f,15);objects[sb]=authored_table(f,30);
    sim::MixedPool pool(std::move(objects),free);
    auto id=[&](std::size_t slot){return sim::EffectId{slot,pool.slots()[slot].generation};};
    sim::PickupWorld world;world.controls={sim::ActorId{0xffff0690U},sim::ActorId{0xffff0838U}};
    world.records[f[45]]=sim::PickupRecord{id(sa),f[46]};world.records[f[47]]=sim::PickupRecord{id(sb),f[48]};
    for(std::size_t k=0;k<world.kinds.size();++k) world.kinds[k]=static_cast<std::uint16_t>(0x100U+k);
    world.activation=id(sa);world.spell=id(sb);world.anchor=id(s);
    const auto k=f[11]==0xffff0838U ? 1U : 0U;
    world.messages={world_message(0,0,0),world_message(0,0,0)};world.messages[k]=world_message(f[56],b(57),w(58));
    world.message_tilemap=static_cast<std::uint32_t>(w(59))<<16U | w(60);
    world.spell_flags=w(49);world.pair_request=w(50);world.two_player=w(51)!=0;world.control_origin={w(54),w(55)};
    sim::PrivateGlobals globals;globals.rise_gate=1;globals.flags_gate=w(52);globals.hide_gate=w(53);
    auto timer=seeded_transition(f,62);
    std::vector<sim::PoolEvent> events;
    try { events=pool.walk_anchor(id(s),world,globals,timer); }
    catch(const assets::BankError& e) {
        const std::string_view what=e.what();
        auto fruit=[&](std::size_t j){return sim::ingredient_fruit(w(j+3));};
        const unsigned code=what=="unsupported 7ED6 FF31A8 path" ? 0x7ef4U : what=="unsupported 9288 recipe" ? 0x9288U
            : what=="unsupported recipe effect" ? static_cast<unsigned>(*sim::recipe_effect(fruit(15),fruit(30))) : what=="unsupported 9182 recipe path" ? 0x9182U
            : what=="unsupported two-player 6F44 door position" ? 0x6f44U : what=="unsupported 95EE 9682 path" ? 0x9682U : what=="unsupported 95EE 9614 path" ? 0x9614U
            : what=="mixed pool allocation exhausted" ? 0xfa1eU : what=="unsupported spell countdown callback" ? 0xcaf0U : 0U;
        if(!code) throw;
        std::cout<<"2 "<<code;return;
    }
    const auto& anchor=std::get<sim::SpellCountdown>(pool.slots()[s].object);const bool completed=anchor.phase==sim::SpellPhase::reveal;
    std::cout<<completed;print_hit_fields(anchor,anchor.countdown);std::cout<<' '<<anchor.control.value;
    if(completed) {
        for(auto slot:{sa,sb}) print_table(std::get<sim::TableMotion>(pool.slots()[slot].object));
        const auto& m=*world.messages[k];
        std::cout<<' '<<world.kinds[f[46]]<<' '<<world.kinds[f[48]]<<' '<<(*world.recipe)[0]<<' '<<(*world.recipe)[1]
                 <<' '<<message_code(world.messages[k])<<' '<<unsigned(m.priority)<<' '<<m.row<<' '<<world.clears.size();
        for(const auto& clear:world.clears) std::cout<<' '<<clear.vram;
        std::cout<<' '<<world.sounds.size();
        for(const auto& q:world.sounds) std::cout<<' '<<q.id<<' '<<q.priority<<' '<<q.parameter<<' '<<q.selector;
        const auto& sparkle_id=events.at(0).id;const auto& sparkle=std::get<sim::SpellSparkle>(pool.slots()[sparkle_id.slot].object);
        std::cout<<' '<<sparkle_id.slot<<' '<<sparkle.position.x<<' '<<sparkle.position.y<<' '<<sparkle.flags<<' '<<unsigned(sparkle.presentation.mode)
                 <<' '<<sparkle.presentation.words[0]<<' '<<sparkle.countdown<<' '<<sparkle.x_extent<<' '<<sparkle.y_extent;
        const auto& door=std::get<sim::ExitDoor>(pool.slots()[world.door->slot].object);const auto& sign=std::get<sim::DoorSign>(pool.slots()[door.sign.slot].object);
        std::cout<<' '<<door.sign.slot<<' '<<sign.position.x<<' '<<sign.position.y<<' '<<sign.flags<<' '<<unsigned(sign.presentation.mode)<<' '<<sign.presentation.words[0];
        std::cout<<' '<<world.door->slot<<' '<<door.position.x<<' '<<door.position.y<<' '<<door.flags<<' '<<unsigned(door.presentation.mode)<<' '<<door.presentation.words[0]
                 <<' '<<door.countdown<<' '<<door.control.value;
        std::cout<<' '<<world.pair_request;print_transition(timer);
    }
    std::cout<<' '<<pool.available();
}
// Authored walks of 7F08's sparkle (13 fields): x y flags mode frame +10
// extents, E918 state (FF0BAC, FF0BAE), slot, free depth, walks. Prints "1 n"
// when walk n exhausts the stack; else 0, the sparkle's eight fields, the E918
// state and mirror, the particles (slot and ten fields each) and the free depth.
inline void authored_sparkle(const std::vector<std::uint32_t>& f) {
    constexpr std::size_t slots=pair_pool_slots;
    if(f.size()!=13 || f[10]>=slots || f[11]>67 || !f[12] || f[12]>96) throw assets::BankError("invalid sparkle case");
    auto w=[&](std::size_t i){if(f[i]>65535)throw assets::BankError("sparkle word outside range");return static_cast<std::uint16_t>(f[i]);};
    if(f[3]>255) throw assets::BankError("sparkle byte outside range");
    std::vector<sim::PoolObject> objects(slots,sim::ExternalReservation{});std::vector<std::size_t> free;
    for(std::size_t i=0;i<slots && free.size()<f[11];++i) if(i!=f[10]) {objects[i]=std::monostate{};free.push_back(i);}
    objects[f[10]]=sim::SpellSparkle{{w(0),w(1)},w(2),{static_cast<std::uint8_t>(f[3]),{w(4),0,0},0,0},0,w(5),w(6),w(7)};
    sim::MixedPool pool(std::move(objects),free);
    const sim::EffectId id{f[10],pool.slots()[f[10]].generation};
    sim::TrailRandom random{static_cast<std::uint32_t>(w(8))<<16U | w(9),0xa5a5a5a5U};
    std::vector<std::pair<std::size_t,sim::TrailParticle>> particles;
    for(unsigned n=0;n<f[12];++n) {
        try {
            for(const auto& e:pool.walk_sparkle(id,random))
                if(e.kind==sim::PoolEventKind::spawn) particles.emplace_back(e.id.slot,std::get<sim::TrailParticle>(e.object));
        } catch(const assets::BankError& e) {
            const std::string_view what=e.what();
            if(what!="trail allocation exhausted" && what!="mixed pool allocation exhausted") throw;
            std::cout<<"1 "<<n+1;return;
        }
    }
    const auto& s=std::get<sim::SpellSparkle>(pool.slots()[f[10]].object);
    std::cout<<"0 "<<s.position.x<<' '<<s.position.y<<' '<<s.flags<<' '<<unsigned(s.presentation.mode)<<' '<<s.presentation.words[0]<<' '<<s.countdown<<' '<<s.x_extent<<' '<<s.y_extent;
    std::cout<<' '<<random.state<<' '<<random.mirror<<' '<<particles.size();
    for(const auto& [slot,q]:particles) {
        const auto& p=q.presentation;
        std::cout<<' '<<slot;
        for(auto v:std::array<unsigned,10>{q.position.x,q.position.y,q.flags,p.mode,p.words[0],p.words[1],p.words[2],p.counter,p.reload,q.target})std::cout<<' '<<v;
    }
    std::cout<<' '<<pool.available();
}
// Authored walks of 6F02's door and sign (39 fields): door x y flags mode w06
// w08 w0a c0c r0d target +10 extents, phase (0 6FB6, 1 appearing, 2 705C); sign
// x y flags mode frame cursor, bobbing; the door and sign slots; FF0690
// +42/+44; FF13AE; FF33E2; FF0690 +3A (4C08's frame, replaced at 7052); walks;
// the +1A2 link's slot and mode; the FF31C0 anchor's slot (inactive return-only);
// FF0836; FF444A/FF444C; FF0F00; P1's actor mode and frame; free depth. Walks
// stop once the door is entered. Prints "1 pc" at a stop (7072 two players,
// 70FE an active link, CAF0 a callback); else 0, the door's phase (3 entered)
// with its eleven fields and extents (entered: its ten vanish fields), the sign
// (raised x y flags mode frame cursor), the sound requests, once entered FF0F00,
// FF444A, FF444C, P1's actor mode, frame, handler and +4A, FF0836 and the
// anchor's handler; last the free depth.
inline void authored_door(const std::vector<std::uint32_t>& f) {
    constexpr std::size_t slots=pair_pool_slots;
    if(f.size()!=39 || f[13]>2 || f[20]>1 || f[19]>13 || !f[28] || f[28]>96 || f[38]>64) throw assets::BankError("invalid door case");
    const std::array<std::size_t,4> at{f[21],f[22],f[29],f[31]};
    for(std::size_t i=0;i<4;++i){if(at[i]>=slots)throw assets::BankError("door slot outside pool");for(std::size_t j=0;j<i;++j)if(at[i]==at[j])throw assets::BankError("door slots repeat");}
    auto w=[&](std::size_t i){if(f[i]>65535)throw assets::BankError("door word outside range");return static_cast<std::uint16_t>(f[i]);};
    auto b=[&](std::size_t i){if(f[i]>255)throw assets::BankError("door byte outside range");return static_cast<std::uint8_t>(f[i]);};
    std::vector<sim::PoolObject> objects(slots,sim::ExternalReservation{});std::vector<std::size_t> free;
    for(std::size_t i=0;i<slots && free.size()<f[38];++i) if(i!=at[0] && i!=at[1] && i!=at[2] && i!=at[3]) {objects[i]=std::monostate{};free.push_back(i);}
    const sim::EffectId sign{f[22],1}; // Seeded objects start at generation 1.
    objects[f[22]]=sim::DoorSign{{w(14),w(15)},w(16),{b(17),{w(18),0,0},0,0},0,f[19],f[20]!=0};
    objects[f[21]]=sim::ExitDoor{{w(0),w(1)},w(2),{b(3),{w(4),w(5),w(6)},b(7),b(8)},w(9),w(10),w(11),w(12),{0xffff0690U},sign,static_cast<sim::DoorPhase>(f[13])};
    sim::ReturnOnlyObject link;link.presentation.mode=b(30);objects[f[29]]=link; // Counter 0: never steps here.
    objects[f[31]]=sim::ReturnOnlyObject{};
    sim::MixedPool pool(std::move(objects),free);
    sim::PickupWorld world;world.two_player=w(26)!=0;(void)w(27);world.controls={sim::ActorId{0xffff0690U},sim::ActorId{0xffff0838U}};
    world.links[0]=sim::EffectId{f[29],1};world.anchor=sim::EffectId{f[31],1};
    const sim::CollisionInputs collision{{w(23),w(24)},{w(25),0,{}}};
    sim::ActorState actor;actor.motion.presentation.mode=b(36);actor.motion.presentation.words[0]=w(37);
    sim::ActorTracking tracking{w(32),{}};
    sim::TrailRandom random;
    try {
        for(unsigned n=0;n<f[28] && !world.door_entered;++n) pool.step(sim::ActorId{},{},random,slots,nullptr,&collision,&world);
    } catch(const assets::BankError& e) {
        const std::string_view what=e.what();
        const unsigned code=what=="unsupported two-player door service" ? 0x7072U : what=="unsupported 70FE active link at door entry" ? 0x70feU
            : what=="unsupported exit door callback" || what=="unsupported door sign callback" ? 0xcaf0U : 0U;
        if(!code) throw;
        std::cout<<"1 "<<code;return;
    }
    // As step_world_phase applies 7082's tail to the session's P1.
    const bool entered=world.door_entered;if(entered) sim::begin_exit_transition(actor,tracking);
    const auto& g=std::get<sim::DoorSign>(pool.slots()[f[22]].object);
    if(entered) {
        const auto& v=std::get<sim::TrailParticle>(pool.slots()[f[21]].object);const auto& q=v.presentation;
        std::cout<<"0 3";
        for(auto x:std::array<unsigned,10>{v.position.x,v.position.y,v.flags,q.mode,q.words[0],q.words[1],q.words[2],q.counter,q.reload,v.target})std::cout<<' '<<x;
    } else {
        const auto& d=std::get<sim::ExitDoor>(pool.slots()[f[21]].object);
        std::cout<<"0 "<<static_cast<unsigned>(d.phase);print_hit_fields(d,d.countdown);std::cout<<' '<<d.x_extent<<' '<<d.y_extent;
    }
    std::cout<<' '<<g.bobbing<<' '<<g.position.x<<' '<<g.position.y<<' '<<g.flags<<' '<<unsigned(g.presentation.mode)<<' '<<g.presentation.words[0]<<' '<<g.cursor;
    std::cout<<' '<<world.sounds.size();
    for(const auto& q:world.sounds) std::cout<<' '<<q.id<<' '<<q.priority<<' '<<q.parameter<<' '<<q.selector;
    if(entered) {
        const auto camera=world.exit_camera.value_or(sim::Position{w(33),w(34)});
        std::cout<<' '<<(world.exit_control ? world.exit_control->value : f[35])<<' '<<camera.x<<' '<<camera.y<<' '<<unsigned(actor.motion.presentation.mode)<<' '<<actor.motion.presentation.words[0]
                 <<' '<<(actor.motion.update==sim::MotionUpdate::transition_start ? 0x710eU : 0xa1beU)<<' '<<0xffff0690U<<' '<<tracking.selector
                 <<' '<<(std::holds_alternative<sim::ReturnOnlyObject>(pool.slots()[f[31]].object) ? 0x12646U : 0U);
    }
    std::cout<<' '<<pool.available();
}
} // namespace wiz::transport
