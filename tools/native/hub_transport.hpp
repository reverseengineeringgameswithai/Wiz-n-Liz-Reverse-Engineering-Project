#pragma once
#include "completion_transport.hpp"

namespace wiz::transport {
// A seeded curve long: a known resource maps to its code; anything else is retained.
inline sim::TransitionCurve seeded_curve(std::uint32_t value) {
    return value==0x1356aU ? sim::TransitionCurve::exit_red_green : value==0x135aaU ? sim::TransitionCurve::exit_blue
        : value==0x135eaU ? sim::TransitionCurve::tally : sim::TransitionCurve::retained;
}
// FF3398 as 623C stores it: FF330C plus the word-sign-extended low word of
// MULU.W #0E (LEA (A0,D0.W)).
inline std::uint32_t hub_record_address(std::uint16_t number) {
    const auto offset=static_cast<std::int16_t>(static_cast<std::uint16_t>(number*14U));
    return static_cast<std::uint32_t>(0xffff330cU+static_cast<std::uint32_t>(static_cast<std::int32_t>(offset)));
}
// FF330C records from nine groups of seven words starting at `at`.
inline sim::HubDoorTable hub_table(const std::vector<std::uint32_t>& f, std::size_t at) {
    sim::HubDoorTable table{};
    for(std::size_t r=0;r<table.size();++r) {
        std::array<std::uint16_t,7> v{};
        for(std::size_t k=0;k<7;++k){if(f[at+7*r+k]>65535)throw assets::BankError("hub door record word outside range");v[k]=static_cast<std::uint16_t>(f[at+7*r+k]);}
        table[r]={{v[0],v[1]},v[2],v[3],v[4],v[5],v[6]};
    }
    return table;
}
// --hub-doors prints each popped object: slot kind mode x y w06 flags +14,
// doors (kind 0 closed, 1 waiting) adding number and both number slots, waiting
// doors w08 w0a c0c r0d +10; kind 2 is a return-only object.
inline void print_hub_object(const sim::MixedPool& pool, sim::EffectId id) {
    const auto& object=pool.at(id).object;
    if(const auto* d=std::get_if<sim::HubDoor>(&object)) {
        const bool waiting=d->phase==sim::HubDoorPhase::waiting;
        if(!waiting && d->phase!=sim::HubDoorPhase::closed) throw assets::BankError("hub setup door phase differs");
        const auto& p=d->presentation;
        std::cout<<' '<<id.slot<<' '<<(waiting ? 1 : 0)<<' '<<unsigned(p.mode)<<' '<<d->position.x<<' '<<d->position.y<<' '<<p.words[0]<<' '<<d->flags<<" 0 "
                 <<d->number<<' '<<d->numbers[0].slot<<' '<<d->numbers[1].slot;
        if(waiting) std::cout<<' '<<p.words[1]<<' '<<p.words[2]<<' '<<unsigned(p.counter)<<' '<<unsigned(p.reload)<<' '<<d->countdown;
    } else if(const auto* r=std::get_if<sim::ReturnOnlyObject>(&object)) {
        std::cout<<' '<<id.slot<<" 2 "<<unsigned(r->presentation.mode)<<' '<<r->position.x<<' '<<r->position.y<<' '<<r->presentation.words[0]<<' '<<r->flags<<" 0";
    } else throw assets::BankError("hub setup object kind differs");
}
// The setup's [5E86,5E8E): FF33E2, FF33C4, FF33DE's seed, nine records, the
// free depth and 68 slots bottom first (the others stay reserved).
inline void authored_hub_doors(const std::vector<std::uint32_t>& f) {
    constexpr std::size_t slots=pair_pool_slots;
    if(f.size()!=3+9*7+1+slots || f[0]>65535 || f[1]>65535 || f[2]>255 || f[66]>slots) throw assets::BankError("invalid hub doors case");
    std::vector<bool> used(slots);
    for(std::size_t i=0;i<slots;++i){if(f[67+i]>=slots || used[f[67+i]])throw assets::BankError("hub doors slot order is not a permutation");used[f[67+i]]=true;}
    std::vector<sim::PoolObject> objects(slots,sim::ExternalReservation{});std::vector<std::size_t> free;
    for(std::size_t i=0;i<f[66];++i){objects[f[67+i]]=std::monostate{};free.push_back(f[67+i]);}
    sim::MixedPool pool(std::move(objects),free);
    auto table=hub_table(f,3);const bool two_player=f[0]!=0;
    const bool rewrote=sim::update_hub_door_states(table,static_cast<std::uint16_t>(f[1]),two_player);
    std::vector<sim::EffectId> ids;
    try { ids=pool.initialize_hub_doors(table,two_player); }
    catch(const assets::BankError& e) {
        const std::string_view what=e.what();
        const unsigned code=what=="hub door allocation exhausted" ? 0xfa1eU : what=="hub door number allocation exhausted" ? 0xf9d0U : 0U;
        if(!code) throw;
        std::cout<<"1 "<<code;return;
    }
    std::cout<<"0 "<<(rewrote ? 0U : f[2])<<' '<<ids.size();
    for(const auto id:ids) print_hub_object(pool,id);
    for(const auto& r:table) std::cout<<' '<<r.state;
}
// Walks of one hub door (59 fields, see the reference's hub_door_cases) until
// 623C runs; both controls' 630A is applied here as the session applies P1's.
inline void authored_hub_door(const std::vector<std::uint32_t>& f) {
    constexpr std::size_t slots=pair_pool_slots;
    if(f.size()!=59 || f[14]>4 || !f[26] || f[26]>96 || f[27]>64) throw assets::BankError("invalid hub door case");
    const std::array<std::size_t,3> at{f[19],f[15],f[16]};
    for(std::size_t i=0;i<3;++i){if(at[i]>=slots)throw assets::BankError("hub door slot outside pool");for(std::size_t j=0;j<i;++j)if(at[i]==at[j])throw assets::BankError("hub door slots repeat");}
    auto w=[&](std::size_t i){if(f[i]>65535)throw assets::BankError("hub door word outside range");return static_cast<std::uint16_t>(f[i]);};
    auto b=[&](std::size_t i){if(f[i]>255)throw assets::BankError("hub door byte outside range");return static_cast<std::uint8_t>(f[i]);};
    std::vector<sim::PoolObject> objects(slots,sim::ExternalReservation{});std::vector<std::size_t> free;
    for(std::size_t i=0;i<slots && free.size()<f[27];++i) if(i!=at[0] && i!=at[1] && i!=at[2]) {objects[i]=std::monostate{};free.push_back(i);}
    for(std::size_t k=0;k<2;++k){sim::ReturnOnlyObject number;number.presentation.mode=b(17+k);objects[at[1+k]]=number;}
    objects[at[0]]=sim::HubDoor{{w(0),w(1)},w(2),{b(3),{w(4),w(5),w(6)},b(7),b(8)},w(9),w(10),w(11),w(12),w(13),
        {sim::EffectId{at[1],1},sim::EffectId{at[2],1}},static_cast<sim::HubDoorPhase>(f[14])}; // Seeded objects start at generation 1.
    sim::MixedPool pool(std::move(objects),free);
    sim::HubWorld hub;hub.two_player=w(25)!=0;
    sim::CollisionInputs collision{{w(20),w(21)},{w(24),w(25),sim::Position{w(22),w(23)}}};
    sim::TransitionState timer{w(33),w(34),w(35),w(36)};
    for(std::size_t i=0;i<3;++i) timer.curves[i]=seeded_curve(f[37+i]);
    timer.palette_scope=w(40);timer.requested_position={w(30),w(31)};
    std::array<sim::ActorState,2> actors{};std::array<sim::ActorTracking,2> tracking{};
    for(std::size_t k=0;k<2;++k){actors[k].motion.presentation.mode=b(41+2*k);actors[k].motion.presentation.words[0]=w(42+2*k);tracking[k].selector=w(28+k);}
    for(std::size_t k=0;k<2;++k){(void)b(47+7*k);(void)b(48+7*k);(void)w(49+7*k);(void)w(50+7*k);(void)w(51+7*k);}
    sim::TrailRandom random;
    try {
        for(unsigned n=0;n<f[26] && !hub.entry;++n) pool.step(sim::ActorId{},{},random,slots,nullptr,&collision,nullptr,&timer,&hub);
    } catch(const assets::BankError& e) {
        const std::string_view what=e.what();
        const unsigned code=what=="unsupported hub door callback" ? 0xcaf0U : what=="unsupported hub door revival after release" ? 0xfac4U : 0U;
        if(!code) throw;
        std::cout<<"1 "<<code;return;
    }
    const auto& d=std::get<sim::HubDoor>(pool.slots()[at[0]].object);const auto& p=d.presentation;
    std::cout<<"0 "<<static_cast<unsigned>(d.phase);
    for(auto v:std::array<unsigned,14>{d.position.x,d.position.y,d.flags,p.mode,p.words[0],p.words[1],p.words[2],p.counter,p.reload,d.target,d.countdown,d.x_extent,d.y_extent,d.number})
        std::cout<<' '<<v;
    for(std::size_t k=0;k<2;++k) std::cout<<' '<<unsigned(std::get<sim::ReturnOnlyObject>(pool.slots()[at[1+k]].object).presentation.mode);
    const bool entered=hub.entry.has_value();
    std::cout<<' '<<pool.available()<<' '<<entered;
    if(!entered) return;
    // 62EE/62F8: 630A on both controls.
    for(std::size_t k=0;k<2;++k) sim::begin_coasting(actors[k],tracking[k]);
    const auto& t=timer;
    std::cout<<' '<<hub.entry->control<<' '<<t.requested_position.x<<' '<<t.requested_position.y<<' '<<(hub.selected ? hub_record_address(*hub.selected) : f[32]);
    std::cout<<' '<<t.direction<<' '<<t.countdown<<' '<<t.reload<<' '<<t.level;
    for(std::size_t i=0;i<3;++i){const auto a=curve_address(t.curves[i]);std::cout<<' '<<(a ? a : f[37+i]);}
    std::cout<<' '<<t.palette_scope;
    for(std::size_t k=0;k<2;++k) {
        const auto& m=actors[k].motion;
        std::cout<<' '<<tracking[k].selector<<' '<<unsigned(m.presentation.mode)<<' '<<m.presentation.words[0]<<' '<<(m.update==sim::MotionUpdate::coast ? 0x632aU : 0xa1beU);
        // 17298 on the touching control: +46/+4E FFFFFFFF, +52..+58 cleared.
        if(hub.entry->control==k) std::cout<<' '<<0xffffffffU<<' '<<0xffffffffU<<" 0 0 0 0 0";
        else for(std::size_t i=0;i<7;++i) std::cout<<' '<<f[45+7*k+i];
    }
}
// The hub session's pool image after a loop: the free stack (depth, then
// slots bottom first), then every other slot: slot mode x y w06 w08 w0a c0c
// r0d target countdown flags handler service callback x_extent y_extent
// number +26 +2A, with the original handler/service/callback addresses each
// phase implies and unwritten fields as zero (the 1535..1536 reset left them
// zero). Other object kinds reject.
inline void print_hub_pool(const sim::MixedPool& pool) {
    std::cout<<' '<<pool.free_stack().size();
    for(const auto i:pool.free_stack()) std::cout<<' '<<i;
    std::vector<bool> free(pool.slots().size());
    for(const auto i:pool.free_stack()) free[i]=true;
    auto address=[](sim::EffectId id){return 0xffff1b50U+78U*static_cast<unsigned>(id.slot);};
    for(std::size_t i=0;i<pool.slots().size();++i) {
        if(free[i]) continue;
        const auto& object=pool.slots()[i].object;
        if(const auto* d=std::get_if<sim::HubDoor>(&object)) {
            static constexpr std::array<std::array<unsigned,3>,5> handlers{{{0x12646,0x12646,0},{0x61f6,0x12646,0},{0x6218,0x621a,0},{0xfac4,0x6218,0xfaa4},{0xfae2,0x6218,0xfaa4}}};
            const auto& h=handlers[static_cast<std::size_t>(d->phase)];const auto& p=d->presentation;
            std::cout<<' '<<i;
            for(auto v:std::array<unsigned,19>{p.mode,d->position.x,d->position.y,p.words[0],p.words[1],p.words[2],p.counter,p.reload,d->target,d->countdown,d->flags,
                    h[0],h[1],h[2],d->x_extent,d->y_extent,d->number,address(d->numbers[0]),address(d->numbers[1])}) std::cout<<' '<<v;
        } else if(const auto* r=std::get_if<sim::ReturnOnlyObject>(&object)) {
            if(r->control.value) throw assets::BankError("hub return-only object names a control");
            const auto& p=r->presentation;
            std::cout<<' '<<i;
            for(auto v:std::array<unsigned,19>{p.mode,r->position.x,r->position.y,p.words[0],p.words[1],p.words[2],p.counter,p.reload,r->target,r->countdown,r->flags,
                    0x12646,0x12646,0,0,0,0,0,0}) std::cout<<' '<<v;
        } else throw assets::BankError("unsupported hub pool object");
    }
}
// --scene-change: "FF4446 FF4448 FF0838+A2 FF0838+A4 FF0690+30 FF0838+30 FF33E2
// FF13E0 seed" (only the first six are read natively). Per control: its
// actor's mode x y w06 w08 w0a target cycles flags +22 +26 +2A counter reload
// handler callback service +4A, the control's actor pointer, +1A6 and 9952's
// nine native parameters; then the timer after 131C2/001E/000A and the reset
// pool (slots reset, free depth, bottom-first order).
inline void authored_scene_change(const std::vector<std::uint32_t>& f) {
    if(f.size()!=9 || std::any_of(f.begin(),f.end(),[](auto v){return v>65535;})) throw assets::BankError("invalid scene change case");
    auto w=[&](std::size_t i){return static_cast<std::uint16_t>(f[i]);};
    const std::array<sim::Position,2> anchors{{{w(0),w(1)},{w(2),w(3)}}};
    for(std::size_t k=0;k<2;++k) {
        const auto a=sim::make_hub_actor(anchors[k]);const auto& m=a.motion;const auto& q=m.presentation;
        if(m.update!=sim::MotionUpdate::return_only || a.callback!=sim::PresentationCallback::enter_airborne || a.service!=sim::ActorService::return_only)
            throw assets::BankError("hub actor selectors differ");
        const auto p=sim::hub_actor_parameters(f[4+k]!=0);
        if(k) std::cout<<' ';
        for(auto v:std::array<unsigned,18>{q.mode,m.position.x,m.position.y,q.words[0],q.words[1],q.words[2],a.presentation_target,a.presentation_cycles,m.flags,
                m.horizontal_speed,m.vertical_motion,m.airborne_delay,q.counter,q.reload,0x12646,0xaa50,0x12646,k ? 0xffff0838U : 0xffff0690U}) std::cout<<v<<' ';
        std::cout<<(k ? 0xffff1b02U : 0xffff1ab4U)<<" 0";
        for(auto v:std::array<unsigned,9>{p.airborne.motion.positive_limit,p.airborne.motion.negative_limit,p.ground_acceleration,p.airborne.acceleration,p.jump_impulse,
                p.jump_delay,p.airborne.motion.damping_count_minus_one,p.airborne.contact_damping_count_minus_one,p.airborne.gravity}) std::cout<<' '<<v;
    }
    sim::TransitionState t;sim::start_fade_in(t);t.countdown=0x1e;t.countdown=0x0a;
    std::cout<<' '<<t.direction<<' '<<t.countdown<<' '<<t.reload<<' '<<t.level;
    for(auto c:t.curves) std::cout<<' '<<curve_address(c);
    // 16FB4 clears FF0F16 (enter_hub_scene's acceleration_gate).
    std::cout<<' '<<t.palette_scope<<" 0";
    const auto pool=sim::reset_object_pool();
    const auto reset=static_cast<unsigned>(std::count_if(pool.slots().begin(),pool.slots().end(),[](const auto& s){return std::holds_alternative<std::monostate>(s.object);}));
    bool ascending=true;for(std::size_t i=0;i<pool.free_stack().size();++i) ascending=ascending && pool.free_stack()[i]==i;
    std::cout<<' '<<reset<<' '<<pool.free_stack().size()<<' '<<ascending;
}
// The second level's entry as reference mode 14 runs it: per actor its fields,
// FF0690/FF0838's actor pointer, +1A6 and the nine parameters (P1 by 9880 at a
// zero anchor and 118C's 9952 again, P2 by 9880 at its anchor); the timer after
// 16EA4's 131C2/001E, FF0EDE, FF0F16; the reset pool; FF33D8, FF33E0 and E918's
// state and mirror.
inline void authored_second_level(const std::vector<std::uint32_t>& f) {
    if(f.size()!=12 || std::any_of(f.begin(),f.end(),[](auto v){return v>65535;})) throw assets::BankError("invalid second level case");
    auto w=[&](std::size_t i){return static_cast<std::uint16_t>(f[i]);};
    std::array<sim::ActorState,2> actors{sim::make_hub_actor({}),sim::make_hub_actor({w(0),w(1)})};
    sim::reset_actor_appearance(actors[0]);
    sim::TrailRandom random{(f[7]<<16U)|f[8],(f[9]<<16U)|f[10]};
    const auto cooldown=sim::choose_action_cooldown(w(6),random);
    for(std::size_t k=0;k<2;++k) {
        const auto& a=actors[k];const auto& m=a.motion;const auto& q=m.presentation;
        if(m.update!=sim::MotionUpdate::return_only || a.callback!=sim::PresentationCallback::enter_airborne || a.service!=sim::ActorService::return_only)
            throw assets::BankError("second level actor selectors differ");
        const auto p=sim::hub_actor_parameters(f[2+k]!=0);
        if(k) std::cout<<' ';
        for(auto v:std::array<unsigned,18>{q.mode,m.position.x,m.position.y,q.words[0],q.words[1],q.words[2],a.presentation_target,a.presentation_cycles,m.flags,
                m.horizontal_speed,m.vertical_motion,m.airborne_delay,q.counter,q.reload,0x12646,0xaa50,0x12646,k ? 0xffff0838U : 0xffff0690U}) std::cout<<v<<' ';
        std::cout<<(k ? 0xffff1b02U : 0xffff1ab4U)<<" 0";
        for(auto v:std::array<unsigned,9>{p.airborne.motion.positive_limit,p.airborne.motion.negative_limit,p.ground_acceleration,p.airborne.acceleration,p.jump_impulse,
                p.jump_delay,p.airborne.motion.damping_count_minus_one,p.airborne.contact_damping_count_minus_one,p.airborne.gravity}) std::cout<<' '<<v;
    }
    sim::TransitionState t;sim::start_fade_in(t);t.countdown=0x1e;
    std::cout<<' '<<t.direction<<' '<<t.countdown<<' '<<t.reload<<' '<<t.level;
    for(auto c:t.curves) std::cout<<' '<<curve_address(c);
    std::cout<<' '<<t.palette_scope<<" 0";
    const auto pool=sim::reset_object_pool();
    const auto reset=static_cast<unsigned>(std::count_if(pool.slots().begin(),pool.slots().end(),[](const auto& s){return std::holds_alternative<std::monostate>(s.object);}));
    bool ascending=true;for(std::size_t i=0;i<pool.free_stack().size();++i) ascending=ascending && pool.free_stack()[i]==i;
    std::cout<<' '<<reset<<' '<<pool.free_stack().size()<<' '<<ascending<<' '<<cooldown<<' '<<0x13<<' '<<random.state<<' '<<random.mirror;
}
// The hint screen's loop test as reference mode 15 runs it (14E3C unless
// FF0F0E is set, then the test): whether it returned, the timer and curves,
// FF0EDE, FF0F0E, FF0F10 and +16 (0 once ending: 14E3C does not run).
inline void authored_hint_screen(const std::vector<std::uint32_t>& f) {
    if(f.size()!=12 || std::any_of(f.begin(),f.end(),[](auto v){return v>65535;}) || std::any_of(f.begin()+7,f.begin()+11,[](auto v){return v>255;}))
        throw assets::BankError("invalid hint screen case");
    auto w=[&](std::size_t i){return static_cast<std::uint16_t>(f[i]);};
    sim::TransitionState t{w(0),w(1),w(2),w(3)};t.curves={sim::TransitionCurve::tally,sim::TransitionCurve::tally,sim::TransitionCurve::tally};t.palette_scope=w(4);
    sim::HintScreen hint{w(5),f[6]!=0};
    sim::PadControl control;control.raw=static_cast<std::uint8_t>(f[7]);
    control.a=static_cast<std::uint8_t>(f[8]);control.b=static_cast<std::uint8_t>(f[9]);control.c=static_cast<std::uint8_t>(f[10]);
    if(!hint.ending) sim::merge_action_buttons(control);
    const bool returned=sim::continue_hint_screen(hint,t,!(control.raw & 0x80U));
    std::cout<<returned<<' '<<t.direction<<' '<<t.countdown<<' '<<t.reload<<' '<<t.level;
    for(auto c:t.curves) std::cout<<' '<<curve_address(c);
    std::cout<<' '<<t.palette_scope<<' '<<(f[6] ? f[6] : hint.ending ? 0xffffU : 0U)<<' '<<hint.countdown<<' '<<(f[6] ? 0U : unsigned(control.jump));
}
// 6024's test: 1 when the loop returns (the scene ends).
inline void authored_hub_exit(const std::vector<std::uint32_t>& f) {
    if(f.size()!=2 || f[0]>65535 || f[1]>65535) throw assets::BankError("invalid hub exit case");
    sim::TransitionState timer;timer.direction=static_cast<std::uint16_t>(f[1]);
    std::cout<<sim::hub_loop_ends(static_cast<std::uint16_t>(f[0]),timer);
}
} // namespace wiz::transport
