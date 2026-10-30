#include "sim/mixed_pool.hpp"
#include <iostream>
#include <sstream>
#include <tuple>

namespace {
using namespace wiz;
void check(bool ok) { if(!ok)throw std::runtime_error("mixed pool check failed"); }
template<class F>void rejects(F f) {try{f();}catch(const assets::BankError&){return;}throw std::runtime_error("mixed pool accepted unsupported state");}
sim::TrailEmitter emitter(sim::ActorId owner={1}) {
    return {{100,200},0,{{{10,20},{30,40},{50,60},{70,80},{90,100}}},{0x81,{638,638,643},5,5},0,0x800,owner};
}
std::string signature(const sim::MixedPool& pool,sim::TrailRandom rng) {
    std::ostringstream out;out<<rng.state<<','<<rng.mirror<<';';
    for(auto i:pool.free_stack())out<<i<<',';
    out<<';';
    for(const auto& s:pool.slots()) {
        out<<s.generation<<','<<s.object.index()<<':';
        std::visit([&](const auto& e) {
            using T=std::decay_t<decltype(e)>;
            if constexpr (!std::is_same_v<T,std::monostate> && !std::is_same_v<T,sim::ExternalReservation>) {
                out<<e.position.x<<','<<e.position.y<<','<<e.flags<<','<<e.target<<','<<unsigned(e.presentation.mode)<<',';
                for(auto w:e.presentation.words)out<<w<<',';
                out<<unsigned(e.presentation.counter)<<','<<unsigned(e.presentation.reload)<<',';
                if constexpr(std::is_same_v<T,sim::ReversalEffect>)out<<e.owner.value<<','<<unsigned(e.side);
                if constexpr(std::is_same_v<T,sim::TrailEmitter>) {out<<e.owner.value<<','<<e.countdown<<',';for(auto p:e.history)out<<p.x<<','<<p.y<<',';}
            }
        },s.object);out<<';';
    }return out.str();
}
auto fields(const sim::P1SessionState& s) {
    const auto& a=s.actor;const auto& m=a.motion;const auto& p=m.presentation;
    return std::tuple{m.position.x,m.position.y,m.horizontal_speed,m.vertical_motion,m.airborne_delay,m.flags,m.update,p.mode,p.words,p.counter,p.reload,
        a.presentation_target,a.presentation_cycles,a.callback,a.service,s.tracking.selector,s.tracking.position.x,s.tracking.position.y,s.scratch.x,s.scratch.y,s.control,s.invocations};
}
}
int main(){try {
    // Nontrivial imported free order, explicit reservations, and exact host bounds.
    rejects([]{sim::MixedPool({std::monostate{}},{});});
    rejects([]{sim::MixedPool({std::monostate{}},{0,0});});
    rejects([]{sim::MixedPool({std::monostate{}},{1});});
    rejects([]{sim::MixedPool({sim::ExternalReservation{}},{0});});
    rejects([]{sim::MixedPool({sim::TrailParticle{}},{});});
    rejects([]{sim::MixedPool(std::vector<sim::PoolObject>(4097),{});});
    sim::MixedPool empty({},{});sim::TrailRandom rng{1,99};check(empty.step({},{},rng,0).empty());
    rejects([&]{empty.spawn(sim::make_trail_particle({},true));});
    for(bool later:{false,true}) {
        std::vector<sim::PoolObject> objects(3,sim::ExternalReservation{});objects[1]=emitter();objects[later ? 2U : 0U]=std::monostate{};
        sim::MixedPool pool(objects,{later ? 2U : 0U});rng={1,99};auto updates=pool.step({1},{65534,7},rng,2);
        check(updates.size()==(later ? 3U : 2U) && updates[0].kind==sim::PoolEventKind::spawn && updates[1].id.slot==1);
        const auto id=updates[0].id;check(id.generation==1 && id.slot==(later ? 2U : 0U));
        const auto& p=std::get<sim::TrailParticle>(pool.at(id).object);
        check(p.position.x==96 && p.position.y==197 && p.presentation.counter==(later ? 1 : 2) && rng.state==258);
        pool.step({1},{0,0},rng,2);check(std::get<sim::TrailParticle>(pool.at(id).object).presentation.words[0]==(later ? 228 : 227));
        rejects([&]{pool.at({id.slot,0});});rejects([&]{pool.at({99,1});});
    }
    // An earlier live particle releases, then the emitter reuses that same slot.
    auto dying=sim::make_trail_particle({0,65535},true);dying.presentation.words[0]=dying.target;dying.presentation.counter=1;
    sim::MixedPool reuse({dying,emitter(),std::monostate{}},{2});rng={0,7};auto r=reuse.step({1},{0,0},rng,2);
    check(r.size()==3 && r[0].kind==sim::PoolEventKind::release && r[0].id==sim::EffectId{0,1});
    check(r[1].kind==sim::PoolEventKind::spawn && r[1].id==sim::EffectId{0,2} && reuse.free_stack()==std::vector<std::size_t>{2});
    check(std::get<sim::TrailParticle>(reuse.at({0,2}).object).presentation.counter==2);
    rejects([&]{reuse.at({0,1});});
    // A later release becomes the top free slot; no same-pass rewind occurs.
    sim::MixedPool later_release({emitter(),dying,std::monostate{}},{2});rng={0,0};r=later_release.step({1},{0,0},rng,3);
    check(r.size()==4 && r[0].id.slot==2 && r[2].kind==sim::PoolEventKind::release && r[3].id.slot==2);
    check(later_release.free_stack()==std::vector<std::size_t>{1});
    auto spawned=later_release.spawn(sim::make_reversal_effect({1},{1,2},sim::ReversalSide::from_left));check(spawned==sim::EffectId{1,2});
    for(bool right:{false,true}) {
        auto effect=sim::make_reversal_effect({1},{0,65535},right ? sim::ReversalSide::from_right : sim::ReversalSide::from_left);
        sim::MixedPool pool({effect},{});rng={1,2};
        for(unsigned n=1;n<=12;++n) {
            r=pool.step({1},{65535,7},rng,1);check(r.size()==1 && (r[0].kind==sim::PoolEventKind::release)==(n==12));
            const auto& e=std::get<sim::ReversalEffect>(r[0].object);
            check(e.position.x==std::uint16_t(65535+(right ? 22U : 65530U)) && e.position.y==(right ? 14 : 15));
        }
        check(pool.available()==1 && pool.step({1},{},rng,0).empty());
    }
    // Failure after a release, an allocation and RNG consumption rolls back all.
    for(unsigned failure=0;failure<3;++failure) {
        auto bad=emitter(failure==0 ? sim::ActorId{2} : sim::ActorId{1});
        if(failure==1)bad.presentation={0x85,{7,0,10},1,2},bad.target=7;
        std::vector<sim::PoolObject> objects{dying,emitter(),bad};std::vector<std::size_t> free;
        if(failure!=2){objects.emplace_back(std::monostate{});free.push_back(3);}
        sim::MixedPool pool(objects,free);rng={1,99};const auto old=signature(pool,rng);
        rejects([&]{pool.step({1},{0,0},rng,10);});check(signature(pool,rng)==old);
    }
    sim::MixedPool budget({dying,emitter()},{});rng={1,99};auto old=signature(budget,rng);
    rejects([&]{budget.step({1},{0,0},rng,1);});check(signature(budget,rng)==old);
    // P1's staged reversal and later trail allocations compete for one stack.
    assets::PatternBank bank;bank.logical_id="base";bank.patterns.resize(1);bank.patterns[0].opaque_record.fill(5);
    assets::SceneResource scene;scene.base_bank_id="base";scene.columns=128;scene.rows=32;scene.cells.resize(4096);
    for(bool right:{false,true}) {
        sim::P1SessionState p1;p1.actor.motion.position={200,109};p1.actor.motion.presentation.mode=128;
        p1.actor.motion.update=right ? sim::MotionUpdate::fast_right : sim::MotionUpdate::fast_left;
        p1.actor.motion.horizontal_speed=right ? 160 : 65376;p1.actor.service=sim::ActorService::return_only;p1.scratch={7,9};
        sim::P1SessionConfig config;config.banner=sim::LevelBannerConfig{sim::Difficulty::apprentice,0,6};
        sim::MixedSessionState world{p1,sim::MixedPool({std::monostate{},emitter(),std::monostate{}},{0,2}),{1,99}};
        sim::ThreeButtonPad held;held.left=right;held.right=!right;
        const auto result=sim::step_mixed_session(scene,bank,world,config,held);
        check(result.p1.actor.spawned_effects==std::vector<sim::EffectId>{{2,1}} && world.pool.available()==0 && world.p1.invocations==1);
        check(result.events.size()==4 && result.events[0].id.slot==2 && result.events[1].id.slot==0);
        check(std::get<sim::TrailEmitter>(world.pool.slots()[1].object).history[0].x==std::uint16_t(world.p1.actor.motion.position.x+4));
        check(std::get<sim::TrailParticle>(world.pool.slots()[0].object).presentation.counter==2);
        sim::MixedSessionState fail{p1,sim::MixedPool({emitter(),std::monostate{}},{1}),{1,99}};
        auto pbefore=fields(fail.p1);old=signature(fail.pool,fail.random);
        rejects([&]{sim::step_mixed_session(scene,bank,fail,config,held);});check(fields(fail.p1)==pbefore && signature(fail.pool,fail.random)==old);
        config.effect_budget=0;fail.pool=sim::MixedPool({std::monostate{},emitter(),std::monostate{}},{0,2});old=signature(fail.pool,fail.random);
        rejects([&]{sim::step_mixed_session(scene,bank,fail,config,held);});check(fields(fail.p1)==pbefore && signature(fail.pool,fail.random)==old);
        config.effect_budget=64;config.max_invocations=0;
        rejects([&]{sim::step_mixed_session(scene,bank,fail,config,held);});check(fields(fail.p1)==pbefore);
        config.max_invocations=600;fail.p1.effects.emplace(1);
        rejects([&]{sim::step_mixed_session(scene,bank,fail,config,held);});
    }
    // The setup's identities move into one carried world; its loops take
    // external E918 counts and message updates, roll back as a whole and hand
    // the world's requests to the caller.
    {
        const sim::Pickup fruit{{100,116},0,{0x81,{0x27e,0x27e,0x283},5,5},0,0,{1},16,16,0};
        const sim::ReturnOnlyObject link{{0,0},0,{0,{0x21d,0,0},0,0},0,0,{1}};
        sim::MixedSessionState s{{},sim::MixedPool({link,fruit,std::monostate{}},{2}),{1,99}};
        s.private_globals=sim::PrivateGlobals{};s.control_links={sim::EffectId{0,1},std::nullopt};s.pickup_records[0]=sim::PickupRecord{{1,1},0};
        s.p1_message=sim::ControlMessage{std::nullopt,0,3};s.setup_gates=sim::SetupGates{0,0,0,0xe000};
        sim::PickupTables tables;tables.kinds.fill(0xffff);tables.kinds[0]=5;
        auto missing=s;missing.p1_message.reset();rejects([&]{sim::establish_world(missing,tables,{sim::ActorId{1},sim::ActorId{2}},{},0);});check(!missing.world);
        rejects([&]{sim::step_world_phase(missing,{},{},nullptr,8,{0,{sim::ControlMessage{},std::nullopt}});});check(missing.random.state==1);
        sim::establish_world(s,tables,{sim::ActorId{1},sim::ActorId{2}},{},0x50);
        check(s.world && s.world->links[0]==sim::EffectId{0,1} && s.world->records[0]->object==sim::EffectId{1,1} && s.world->messages[0]->row==3 && s.world->kinds[0]==5);
        check(!s.control_links[0] && !s.pickup_records[0] && !s.p1_message && s.world->ingredient_timer==0x50 && s.world->message_tilemap==0xe000);
        rejects([&]{sim::establish_world(s,tables,{sim::ActorId{1},sim::ActorId{2}},{},0);});
        // The link sits below the pickup, as link 53 below pickups 54/55.
        // No collision inputs: the pickup's walk rejects after the updates, and nothing commits.
        auto old=signature(s.pool,s.random);
        rejects([&]{sim::step_world_phase(s,{},{},nullptr,8,{3,{sim::ControlMessage{std::nullopt,0x64,12},std::nullopt}});});
        check(signature(s.pool,s.random)==old && s.world->messages[0]->row==3);
        const sim::CollisionInputs away{{0,0},{1023,0,{}}},touch{{100,116},{1023,0,{}}};
        auto phase=sim::step_world_phase(s,{},{},&away,8,{1,{sim::ControlMessage{std::nullopt,0x64,12},std::nullopt}});
        check(s.random.state==65536 && s.random.mirror==65536 && s.world->messages[0]->priority==0x64 && phase.sounds.empty() && phase.events.size()==2);
        phase=sim::step_world_phase(s,{},{},&touch,8);
        check(phase.sounds.size()==1 && phase.sounds[0].id==0x89 && s.world->sounds.empty() && s.world->records[0]->object==sim::EffectId{0,1});
        check(std::holds_alternative<sim::TrailEmitter>(s.pool.slots()[0].object) && std::get<sim::Pickup>(s.pool.slots()[1].object).phase==sim::PickupPhase::vanishing);
    }
    std::cout<<"mixed free order, initial lifetimes, iterator births, generations, owner/RNG, full-session rollback and the carried world passed\n";
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
