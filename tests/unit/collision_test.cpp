#include "sim/mixed_pool.hpp"
#include <algorithm>
#include <iostream>
#include <source_location>
#include <string>
#include <tuple>
namespace {
using namespace wiz;
void check(bool ok,std::source_location at=std::source_location::current()){if(!ok)throw std::runtime_error("collision check failed at line "+std::to_string(at.line()));}
template<class F>void rejects(F f,const char* text){try{f();}catch(const assets::BankError& e){check(std::string(e.what()).find(text)!=std::string::npos);return;}throw std::runtime_error("collision accepted unsupported work");}
auto fields(const sim::CollisionProbe& o){return std::tuple{o.position.x,o.position.y,o.flags,o.presentation.mode,o.presentation.words,o.presentation.counter,o.presentation.reload,o.target,o.countdown,o.control.value,o.x_extent,o.y_extent};}
sim::CollisionProbe seed(){return {{150,262},0xbeef,{0x81,{7,3,11},2,2},100,14,{123},56,8};}
}
int main(){try{
    using sim::overlaps_control;
    check(overlaps_control({100,100},{56,8},{84,88},1023)); // Inclusive X=72, Y=20.
    check(!overlaps_control({100,100},{56,8},{83,88},1023));
    check(!overlaps_control({100,100},{56,8},{84,87},1023));
    check(overlaps_control({65535,65535},{0,0},{65520,65524},65535));
    check(overlaps_control({65535,0},{0,0},{0,0},0));
    check(!overlaps_control({65535,0},{0,0},{0,0},0x5555));
    check(overlaps_control({16,12},{65520,65524},{0,0},65535)); // Both thresholds wrap to zero.
    check(!overlaps_control({17,12},{65520,65524},{0,0},65535));
    check(!overlaps_control({16,13},{65520,65524},{0,0},65535));
    check(overlaps_control({0,0},{65519,65523},{30000,40000},65535)); // Both thresholds FFFF.
    auto p=seed();const sim::CollisionInputs miss{{0,0},{1023,0,{}}};
    sim::step_collision_probe(p,miss,true);check(p.presentation.counter==1 && p.position.x==150 && p.control.value==123);
    auto before=p;auto input=miss;input.primary=p.position;
    rejects([&]{sim::step_collision_probe(p,input,true);},"collision-hit7910 (primary)");check(fields(p)==fields(before));
    input.config.secondary_gate=0x8000; // Full-word gate; primary hit precedes missing P2.
    rejects([&]{sim::step_collision_probe(p,input);},"collision-hit7910 (primary)");
    input.primary={0,0};rejects([&]{sim::step_collision_probe(p,input);},"secondary collision input unavailable");
    input.config.secondary=p.position;rejects([&]{sim::step_collision_probe(p,input);},"collision-hit7910 (secondary)");
    input.config.secondary=sim::Position{30000,30000};sim::step_collision_probe(p,input);check(fields(p)==fields(before));
    input.config.secondary_gate=0;input.config.secondary=p.position;sim::step_collision_probe(p,input);check(fields(p)==fields(before));
    p.presentation={0x85,{7,3,11},1,2};p.target=7;before=p;
    rejects([&]{sim::step_collision_probe(p,miss,true);},"callback");check(fields(p)==fields(before));
    p.presentation.mode=5;before=p;input.primary=p.position;sim::step_collision_probe(p,input,true);check(fields(p)==fields(before));
    // A late hit rolls back releases, table state, and RNG in the shared phase.
    auto dying=sim::make_trail_particle({},true);dying.presentation.counter=1;dying.presentation.words[0]=dying.target;
    sim::TableMotion table{{99,0},0,{0x80,{7,3,11},2,2},100,14,{1},0,65535,0};
    sim::TrailEmitter emitter{{100,200},0,{{{10,20},{30,40},{50,60},{70,80},{90,100}}},{0x81,{638,638,643},5,5},0,0x800,{1}};
    sim::MixedPool pool({dying,table,emitter,seed()},{});sim::TrailRandom rng{123,456};sim::PrivateGlobals globals{0,0,0,0};
    input.primary=seed().position;
    rejects([&]{pool.step({1},{},rng,4,&globals,&input);},"collision-hit7910");
    check(pool.available()==0 && rng.state==123 && rng.mirror==456 && std::get<sim::TableMotion>(pool.slots()[1].object).cursor==0);
    check(pool.slots()[0].generation==1 && std::get<sim::TrailParticle>(pool.slots()[0].object).presentation.counter==1);
    check(std::get<sim::TrailEmitter>(pool.slots()[2].object).countdown==0);
    rejects([&]{pool.step({1},{},rng,4,&globals);},"collision inputs unavailable");check(pool.available()==0);
    // The session consumes the tracking coordinates produced by the P1 wrapper.
    // Raw actor X=100 misses this narrow object; tracked X=104 hits it.
    assets::PatternBank bank;bank.logical_id="base";bank.patterns.resize(1);bank.patterns[0].opaque_record.fill(5);
    assets::SceneResource scene;scene.base_bank_id="base";scene.columns=128;scene.rows=32;scene.cells.resize(4096);
    sim::P1SessionState p1;p1.actor.motion.position={100,100};p1.actor.service=sim::ActorService::return_only;
    p1.tracking.position={30000,30000};p1.scratch={7,9};
    auto narrow=seed();narrow.position={117,106};narrow.x_extent=0;narrow.y_extent=0;
    sim::MixedSessionState world{p1,sim::MixedPool({narrow},{}),{123,456},{},sim::CollisionConfig{65535,0,{}}};
    sim::P1SessionConfig config;config.banner=sim::LevelBannerConfig{sim::Difficulty::apprentice,0,6};
    rejects([&]{sim::step_mixed_session(scene,bank,world,config,{});},"collision-hit7910");
    check(world.p1.invocations==0 && world.p1.tracking.position.x==30000 && world.p1.scratch.x==7 && world.p1.scratch.y==9);
    world.p1.tracking.selector=0xffff;sim::step_mixed_session(scene,bank,world,config,{});
    check(world.p1.invocations==1 && world.p1.tracking.position.x==0xff80 && world.p1.tracking.position.y==0xff80);
    // Also roll back active P1 movement, banner scratch and a reversal allocation.
    p1.actor.motion.position={200,109};p1.actor.motion.presentation.mode=128;
    p1.actor.motion.update=sim::MotionUpdate::fast_right;p1.actor.motion.horizontal_speed=160;
    auto hit=seed();hit.position={0,0};hit.x_extent=65519;hit.y_extent=65523; // Always overlaps.
    world={p1,sim::MixedPool({hit,std::monostate{}},{1}),{123,456},{},sim::CollisionConfig{65535,0,{}}};
    sim::ThreeButtonPad held;held.left=true;rejects([&]{sim::step_mixed_session(scene,bank,world,config,held);},"collision-hit7910");
    check(world.p1.invocations==0 && world.p1.actor.motion.position.x==200 && world.p1.actor.motion.horizontal_speed==160);
    check(world.p1.actor.motion.update==sim::MotionUpdate::fast_right && world.p1.scratch.x==7 && world.p1.scratch.y==9);
    check(world.p1.control==p1.control && world.pool.free_stack()==std::vector<std::size_t>{1} && world.pool.slots()[1].generation==0);
    // 783A: four LIFO pops; probe first, then return-only members from its
    // position. Every member keeps +08..+0D, target and countdown; only the
    // probe stores the caller control.
    using Inherited=std::optional<sim::InheritedObjectFields>;
    auto inherit=[](std::uint16_t n){return sim::InheritedObjectFields{static_cast<std::uint16_t>(900+n),static_cast<std::uint16_t>(n),{n},
        sim::InheritedPresentation{{static_cast<std::uint16_t>(10+n),static_cast<std::uint16_t>(20+n)},static_cast<std::uint8_t>(30+n),static_cast<std::uint8_t>(40+n)}};};
    auto quad_pool=[&](std::vector<std::size_t> free,std::vector<Inherited> inherited) {
        std::vector<sim::PoolObject> objects(6,sim::ExternalReservation{});for(auto i:free)objects[i]=std::monostate{};
        return sim::MixedPool(objects,free,inherited);
    };
    auto known=std::vector<Inherited>{Inherited{},inherit(1),inherit(2),inherit(3),inherit(4),Inherited{}};
    auto quad=quad_pool({0,4,3,2,1},known);const auto ids=quad.initialize_collision_quad({1});
    check(ids.members==std::array<sim::EffectId,4>{sim::EffectId{1,1},sim::EffectId{2,1},sim::EffectId{3,1},sim::EffectId{4,1}} && quad.free_stack()==std::vector<std::size_t>{0});
    check(fields(std::get<sim::CollisionProbe>(quad.at(ids.members[0]).object))==fields(sim::CollisionProbe{{150,262},0,{0x80,{912,11,21},31,41},901,1,{1},0x38,8}));
    auto ro=[](const sim::ReturnOnlyObject& o){return std::tuple{o.position.x,o.position.y,o.flags,o.presentation.mode,o.presentation.words,o.presentation.counter,o.presentation.reload,o.target,o.countdown,o.control.value};};
    const std::array<std::tuple<std::uint16_t,std::uint16_t,std::uint16_t>,3> placed{{{182,262,913},{150,294,914},{182,294,915}}};
    for(std::uint16_t m=1;m<4;++m) {
        const auto [x,y,frame]=placed[m-1];
        check(ro(std::get<sim::ReturnOnlyObject>(quad.at(ids.members[m]).object))==ro(sim::ReturnOnlyObject{{x,y},0,{0x80,{frame,static_cast<std::uint16_t>(10+m+1),static_cast<std::uint16_t>(20+m+1)},static_cast<std::uint8_t>(30+m+1),static_cast<std::uint8_t>(40+m+1)},static_cast<std::uint16_t>(901+m),static_cast<std::uint16_t>(m+1),{static_cast<std::uint64_t>(m+1)}}));
        check(!quad.slots()[m+1].inherited);
    }
    const auto wrapped=sim::make_quad_return_only(sim::QuadMember::diagonal,inherit(0),{65520,65530});check(wrapped.position.x==16 && wrapped.position.y==26);
    rejects([&]{sim::make_quad_return_only(sim::QuadMember::probe,inherit(0),{});},"probe");
    rejects([&]{sim::make_quad_probe({},{1});},"unknown presentation");
    // Mode 80 never advances its frame; misses leave all four unchanged, and
    // the probe still requires explicit collision inputs.
    auto walked=quad;sim::TrailRandom unused{};const sim::CollisionInputs far{{0,0},{1023,0,{}}};
    for(unsigned n=0;n<64;++n){const auto ev=walked.step({},{},unused,6,nullptr,&far);check(ev.size()==4);}
    check(fields(std::get<sim::CollisionProbe>(walked.slots()[1].object))==fields(std::get<sim::CollisionProbe>(quad.slots()[1].object)));
    for(std::size_t i=2;i<5;++i)check(ro(std::get<sim::ReturnOnlyObject>(walked.slots()[i].object))==ro(std::get<sim::ReturnOnlyObject>(quad.slots()[i].object)));
    rejects([&]{walked.step({},{},unused,6);},"collision inputs unavailable");
    // Exhaustion at each pop, missing inheritance or presentation at each member:
    // no allocation, generation, inheritance or free-order change.
    for(std::size_t depth=0;depth<4;++depth) {
        std::vector<std::size_t> free{4,3,2,1};free.resize(depth);std::reverse(free.begin(),free.end());
        std::vector<Inherited> inherited(6);for(auto i:free)inherited[i]=known[i];
        auto bad=quad_pool(free,inherited);const auto before=bad.slots();
        rejects([&]{bad.initialize_collision_quad({1});},"allocation exhausted");
        check(bad.free_stack()==free);
        for(std::size_t i=0;i<before.size();++i)check(bad.slots()[i].generation==before[i].generation && bool(bad.slots()[i].inherited)==bool(before[i].inherited));
    }
    for(std::size_t m=0;m<4;++m) for(bool partial:{false,true}) {
        auto inherited=known;
        if(partial)inherited[4-m]->presentation.reset();else inherited[4-m].reset();
        auto bad=quad_pool({0,1,2,3,4},inherited);const auto before=bad.slots();
        rejects([&]{bad.initialize_collision_quad({1});},"unknown slot state");
        check(bad.free_stack()==std::vector<std::size_t>{0,1,2,3,4});
        for(std::size_t i=0;i<before.size();++i)check(bad.slots()[i].generation==before[i].generation && bool(bad.slots()[i].inherited)==bool(before[i].inherited));
    }
    // Pairs overwrite +08..+0D, so they do not need inherited presentation.
    auto pairs=quad_pool({0,2,1},{Inherited{},sim::InheritedObjectFields{},sim::InheritedObjectFields{},Inherited{},Inherited{},Inherited{}});
    pairs.initialize_return_only_pair();check(pairs.free_stack()==std::vector<std::size_t>{0});
    // 6AF0/6B44/6BB2: frames by kind (signed < 14 via word MULU/ADDI), the three
    // fixed families otherwise, cadence 1/1 only for count 2, Y + 16 wrapped.
    auto pk=[&](std::uint16_t kind,std::uint16_t count,sim::Position at){return sim::make_pickup(inherit(3),{1},at,kind,count,7);};
    auto frames=[](const sim::Pickup& p){return std::tuple{p.presentation.words,p.presentation.counter,p.presentation.reload};};
    check(frames(pk(5,9,{0,0}))==std::tuple{std::array<std::uint16_t,3>{0x27e,0x27e,0x283},std::uint8_t{5},std::uint8_t{5}});
    check(frames(pk(0,2,{0,0}))==std::tuple{std::array<std::uint16_t,3>{0x260,0x260,0x265},std::uint8_t{1},std::uint8_t{1}});
    check(pk(0x8000,0,{0,0}).presentation.words[0]==0x260 && pk(0xfffe,0,{0,0}).presentation.words[0]==static_cast<std::uint16_t>(0xfffe*6U+0x260U));
    check(pk(0xd3ff,0,{0,0}).presentation.words[2]==static_cast<std::uint16_t>(0xd3ff*6U+0x265U));
    check(pk(0x20d,0,{0,0}).presentation.words==std::array<std::uint16_t,3>{0x20d,0x20d,0x214} && pk(0x205,0,{0,0}).presentation.words==std::array<std::uint16_t,3>{0x205,0x205,0x20c});
    check(pk(14,0,{0,0}).presentation.words==std::array<std::uint16_t,3>{0x1fd,0x1fd,0x204} && pk(0x7fff,0,{0,0}).presentation.words[0]==0x1fd);
    const auto made=pk(6,3,{0x370,0xfff8});
    check(made.position.x==0x370 && made.position.y==8 && made.countdown==3 && made.target==903 && made.control.value==1 && made.x_extent==16 && made.y_extent==16 && made.record==7 && made.presentation.mode==0x81 && made.flags==0);
    // 6BD6's miss path matches 78EE's; a hit is the unsupported 6C00 target.
    auto pickup=made;pickup.position={100,100};
    sim::step_pickup(pickup,far,true);check(pickup.presentation.counter==4);
    rejects([&]{auto q=pickup;sim::step_pickup(q,{{100,116},{1023,0,{}}},true);},"pickup-hit 6C00 (primary)");
    rejects([&]{auto q=pickup;sim::step_pickup(q,{{0,0},{1023,1,sim::Position{100,116}}},true);},"pickup-hit 6C00 (secondary)");
    rejects([&]{auto q=pickup;sim::step_pickup(q,{{0,0},{1023,1,{}}},true);},"secondary collision input unavailable");
    const auto unchanged=pickup;try{sim::step_pickup(pickup,{{100,116},{1023,0,{}}},true);}catch(const assets::BankError&){}
    check(pickup.presentation.counter==unchanged.presentation.counter);
    // 6C00 within a pool: pickup in slot 2, P1/P2 links in slots 1/0, slot 3
    // free. Records 0 and 1 name the pickup (entry 6) and slot 4 (entry 9).
    const sim::ReturnOnlyObject dormant{{0x1234,0x567},0,{0,{0x21d,9,11},13,15},900,3,{0xffff0690}};
    auto ground=made;ground.record=0;ground.position={100,100};
    auto hit_pool=[&](sim::PoolObject p1_link,sim::PoolObject p2_link,sim::Pickup pickup){
        return sim::MixedPool({p2_link,p1_link,pickup,std::monostate{},sim::ExternalReservation{}},{3});
    };
    auto hit_world=[]{
        sim::PickupWorld w;w.controls={sim::ActorId{1},sim::ActorId{2}};w.links={sim::EffectId{1,1},sim::EffectId{0,1}};
        w.records[0]=sim::PickupRecord{{2,1},6};w.records[1]=sim::PickupRecord{{4,1},9};w.kinds[6]=6;w.kinds[9]=0x20d;return w;
    };
    auto pickup_at=[](const sim::MixedPool& pool){return std::get<sim::Pickup>(pool.slots()[2].object);};
    const sim::CollisionInputs touch{{100,100},{1023,0,{}}},away{{100,0x4064},{1023,0,{}}};const sim::EffectId at{2,1};
    sim::TrailEmitter carrier;
    {   // Dormant P1 link: FB06 copy into the link as a carrying emitter, the
        // record names it, the pickup moves X - 8 and vanishes, then releases.
        auto pool=hit_pool(dormant,dormant,ground);auto world=hit_world();
        check(!pool.walk_pickup(at,touch,world));
        carrier=std::get<sim::TrailEmitter>(pool.slots()[1].object);const auto q=pickup_at(pool);
        check(carrier.position.x==100 && carrier.owner.value==1 && carrier.countdown==0 && carrier.history[4].x==0xff80 && carrier.carried==sim::CarriedPickup{3,0,16,16});
        check(carrier.presentation.words==made.presentation.words && carrier.presentation.counter==4 && carrier.target==903);
        check(q.position.x==92 && q.phase==sim::PickupPhase::vanishing && q.presentation.mode==0x85 && q.target==0x227 && q.presentation.words==std::array<std::uint16_t,3>{0x21e,0x21e,0x227});
        check(world.records[0]->object==sim::EffectId{1,1} && world.sounds.size()==1 && world.sounds[0].id==0x89 && world.sounds[0].selector==1);
        bool released=false;std::size_t walks=1;
        while(!released && walks<64){released=pool.walk_pickup(at,touch,world);++walks;}
        check(released && walks==31 && pool.free_stack()==std::vector<std::size_t>{3,2} && !pickup_at(pool).presentation.mode);
        check(!pool.walk_pickup(at,touch,world) && pool.available()==2 && world.sounds.size()==1); // Inactive afterwards.
    }
    {   // That carrier meets a second pickup (record 1, count 2): frames, reload,
        // count and record swap; the pickup vanishes, returns through 5964 and is
        // re-dressed from record 0's kind and, P1 gone, stays collectable.
        auto second=ground;second.record=1;second.countdown=2;
        auto pool=hit_pool(carrier,dormant,second);auto w=hit_world();w.records[1]=sim::PickupRecord{at,9};w.records[0]=sim::PickupRecord{{1,1},6};
        check(!pool.walk_pickup(at,touch,w));
        const auto& e=std::get<sim::TrailEmitter>(pool.slots()[1].object);const auto q=pickup_at(pool);
        check(e.carried->record==1 && e.carried->count==2 && q.record==0 && q.countdown==3 && q.phase==sim::PickupPhase::swapped_out);
        check(w.records[1]->object==sim::EffectId{1,1} && w.records[0]->object==at && e.presentation.reload==made.presentation.reload);
        std::size_t walks=1;while(pickup_at(pool).phase!=sim::PickupPhase::collectable && walks<64){pool.walk_pickup(at,away,w);++walks;}
        const auto back=pickup_at(pool);
        check(walks==51 && back.position.x==100 && back.presentation.mode==0x81 && back.presentation.words==std::array<std::uint16_t,3>{0x284,0x284,0x289} && back.presentation.counter==5 && back.target==0x21e);
        // The kind is read through the record: without it the re-dress rejects.
        auto returning=second;returning.phase=sim::PickupPhase::swapped_in;returning.presentation={0x87,{0x21e,0x21e,0x227},1,2};returning.target=0x21e;
        auto lost=hit_pool(carrier,dormant,returning);auto lw=hit_world();lw.records[1].reset();
        rejects([&]{lost.walk_pickup(at,away,lw);},"pickup kind unavailable");
    }
    {   // Family frames on +08, an active non-emitter link, an emitter without
        // carried bytes, a missing record and no link all reject with no change.
        auto special=ground;special.presentation.words={0x20d,0x20d,0x214};
        auto family=hit_pool(dormant,dormant,special);auto w=hit_world();
        rejects([&]{family.walk_pickup(at,touch,w);},"6C00 family");check(w.sounds.empty() && std::holds_alternative<sim::ReturnOnlyObject>(family.slots()[1].object));
        auto awake=dormant;awake.presentation.mode=0x80;
        auto active=hit_pool(awake,dormant,ground);w=hit_world();rejects([&]{active.walk_pickup(at,touch,w);},"link state");
        sim::TrailEmitter bare;bare.presentation.mode=0x81;bare.owner={1};
        auto unknown=hit_pool(bare,dormant,ground);w=hit_world();rejects([&]{unknown.walk_pickup(at,touch,w);},"carried pickup unknown");
        auto norecord=hit_pool(dormant,dormant,ground);w=hit_world();w.records[0].reset();
        rejects([&]{norecord.walk_pickup(at,touch,w);},"record unavailable");check(w.sounds.empty());
        auto nolink=hit_pool(dormant,dormant,ground);w=hit_world();w.links[0].reset();rejects([&]{nolink.walk_pickup(at,touch,w);},"link unavailable");
        // P2 behind the gate uses its own link and identity.
        auto p2=hit_pool(dormant,dormant,ground);w=hit_world();
        p2.walk_pickup(at,{{0,0},{1023,1,sim::Position{100,100}}},w);check(std::get<sim::TrailEmitter>(p2.slots()[0].object).owner.value==2 && w.records[0]->object==sim::EffectId{0,1});
        // The pool phase without a world keeps the earlier rejection.
        auto plain=hit_pool(dormant,dormant,ground);sim::TrailRandom unused{};
        rejects([&]{plain.step({},{},unused,8,nullptr,&touch);},"pickup-hit 6C00 (primary)");
        auto worlded=hit_pool(dormant,dormant,ground);w=hit_world();worlded.step({},{},unused,8,nullptr,&touch,&w);
        check(std::holds_alternative<sim::TrailEmitter>(worlded.slots()[1].object) && w.sounds.size()==1);
    }
    {   // 7910 with a carrying P1 link: sound 008C, the 59AE sparkle (the top
        // free slot, 4) at the emitter's position - (8,8), the F994 copy (slot 3)
        // and the link left dormant; touched again, the dormant link returns.
        auto probe=seed();probe.presentation={0x80,{912,0,0},0,0};probe.target=0;
        auto probe_pool=[&](sim::PoolObject p1_link,std::vector<std::size_t> free){
            return sim::MixedPool({dormant,p1_link,probe,std::monostate{},std::monostate{},sim::ExternalReservation{}},free);
        };
        const sim::CollisionInputs on{{150,262},{1023,0,{}}},off{{150,0x4106},{1023,0,{}}};const sim::EffectId pid{2,1};
        auto w=hit_world();auto pool=probe_pool(carrier,{3,4});
        const auto ids=pool.walk_probe(pid,on,0,w);
        check(ids && ids->sparkle==sim::EffectId{4,1} && ids->copy==sim::EffectId{3,1} && pool.available()==0);
        const auto sparkle=std::get<sim::TrailParticle>(pool.slots()[4].object);
        check(sparkle.position.x==92 && sparkle.position.y==static_cast<std::uint16_t>(carrier.position.y-8U) && sparkle.flags==0 && sparkle.target==0x227);
        check(sparkle.presentation.mode==0x85 && sparkle.presentation.words==std::array<std::uint16_t,3>{0x21e,0x21e,0x227} && sparkle.presentation.counter==3);
        const auto copy=std::get<sim::DeliveredPickup>(pool.slots()[3].object);
        check(copy.position.x==0xa4 && copy.position.y==0xf6 && copy.presentation.mode==0x87 && copy.presentation.words==std::array<std::uint16_t,3>{0x227,0x21e,0x227});
        check(copy.presentation.counter==3 && copy.presentation.reload==3 && copy.target==0x21e && copy.control.value==1 && copy.carried==*carrier.carried);
        check(copy.frames==std::array<std::uint16_t,2>{carrier.presentation.words[1],carrier.presentation.words[2]} && copy.flags==(carrier.flags&0x9fffU));
        const auto link=std::get<sim::ReturnOnlyObject>(pool.slots()[1].object);
        check(!link.presentation.mode && link.position.x==0xa4 && link.position.y==0xf6 && link.countdown==3 && link.control.value==1 && link.target==0x21e);
        check(w.sounds.size()==1 && w.sounds[0].id==0x8c && w.sounds[0].priority==6 && w.sounds[0].parameter==0xc0 && w.sounds[0].selector==1 && w.records==hit_world().records);
        check(!pool.walk_probe(pid,on,0,w) && w.sounds.size()==1 && pool.available()==0);
        // The copy reaches 79B6 on its 30th walk, which rejects with no change;
        // the sparkle releases on its 30th.
        auto c=copy;for(int n=0;n<29;++n)sim::step_delivered_pickup(c);
        const auto last=c;rejects([&]{sim::step_delivered_pickup(c);},"79B6");check(c.presentation.words==last.presentation.words && c.presentation.counter==last.presentation.counter);
        auto s=sparkle;int walks=1;while(!sim::step_trail_particle(s) && walks<64)++walks;check(walks==30 && !s.presentation.mode);
        // FF31B0 is a long: either word closes the gate before any work.
        for(std::uint32_t rise:{1U,0x10000U}){auto g=hit_world();auto closed=probe_pool(carrier,{3,4});check(!closed.walk_probe(pid,on,rise,g) && g.sounds.empty() && std::holds_alternative<sim::TrailEmitter>(closed.slots()[1].object));}
        // Exhaustion (zero or one entry), other link states and a missing link reject with no change.
        for(auto free:{std::vector<std::size_t>{},std::vector<std::size_t>{4}}) {
            std::vector<sim::PoolObject> objects{dormant,carrier,probe,sim::ExternalReservation{},sim::ExternalReservation{},sim::ExternalReservation{}};
            for(auto i:free)objects[i]=std::monostate{};
            auto g=hit_world();auto bad=sim::MixedPool(objects,free);
            rejects([&]{bad.walk_probe(pid,on,0,g);},"delivery allocation exhausted");check(g.sounds.empty() && bad.free_stack()==free && std::holds_alternative<sim::TrailEmitter>(bad.slots()[1].object));
        }
        auto awake=dormant;awake.presentation.mode=0x80;sim::TrailEmitter bare;bare.presentation.mode=0x81;bare.owner={1};
        auto g=hit_world();auto active=probe_pool(awake,{3,4});rejects([&]{active.walk_probe(pid,on,0,g);},"7910 link state");
        auto unknown=probe_pool(bare,{3,4});rejects([&]{unknown.walk_probe(pid,on,0,g);},"carried pickup unknown");check(g.sounds.empty());
        auto nolink=probe_pool(carrier,{3,4});g.links[0].reset();rejects([&]{nolink.walk_probe(pid,on,0,g);},"probe control link unavailable");
        rejects([&]{nolink.walk_probe(sim::EffectId{1,1},on,0,g);},"not a collision probe");
        // P2 behind the gate delivers its own link with its identity.
        auto p2=sim::MixedPool({carrier,dormant,probe,std::monostate{},std::monostate{},sim::ExternalReservation{}},{3,4});g=hit_world();
        check(p2.walk_probe(pid,{{0,0},{1023,1,sim::Position{150,262}}},0,g) && std::get<sim::DeliveredPickup>(p2.slots()[3].object).control.value==2 && std::holds_alternative<sim::ReturnOnlyObject>(p2.slots()[0].object));
        // In the pool phase both births follow the probe's slot, so they are
        // walked in the same phase; without FF31B0 or a world a contact rejects.
        sim::TrailRandom rng{};sim::PrivateGlobals globals{};g=hit_world();auto phase=probe_pool(carrier,{3,4});
        const auto ev=phase.step({1},{0,0},rng,8,&globals,&on,&g);
        std::vector<std::pair<sim::PoolEventKind,std::size_t>> seen;for(const auto& e:ev)seen.emplace_back(e.kind,e.id.slot);
        check(seen==std::vector<std::pair<sim::PoolEventKind,std::size_t>>{{sim::PoolEventKind::inactive,0},{sim::PoolEventKind::update,1},{sim::PoolEventKind::spawn,4},
            {sim::PoolEventKind::spawn,3},{sim::PoolEventKind::update,2},{sim::PoolEventKind::update,3},{sim::PoolEventKind::update,4}});
        check(std::get<sim::DeliveredPickup>(phase.slots()[3].object).presentation.counter==2 && std::get<sim::TrailParticle>(phase.slots()[4].object).presentation.counter==2);
        auto nogate=probe_pool(carrier,{3,4});g=hit_world();rejects([&]{nogate.step({1},{0,0},rng,8,nullptr,&on,&g);},"rise gate unavailable");
        auto noworld=probe_pool(carrier,{3,4});rejects([&]{noworld.step({1},{0,0},rng,8,&globals,&on);},"collision-hit7910 (primary)");
        auto missed=probe_pool(carrier,{3,4});missed.step({1},{0,0},rng,8,&globals,&off,&g);check(missed.available()==2);
    }
    {   // callback79B6's first-ingredient path on the copy's 30th walk: the copy
        // becomes the 7A88 object, D20E is posted, 7AD6 copies it into the
        // dormant FF31B4 object (slot 4), names it in FF31AC and the record,
        // and releases the copy, which then runs 7A88 once with FF31BC = 0.
        const sim::DeliveredPickup last{{0xa4,0xf6},0,{0x87,{0x21e,0x21e,0x227},1,3},0x21e,{1},{0x284,0x289},{0,1,16,16}};
        auto ingredient_pool=[&]{return sim::MixedPool({sim::ExternalReservation{},last,std::monostate{},sim::ExternalReservation{},sim::ReturnOnlyObject{}},{2});};
        auto ingredient_world=[]{
            sim::PickupWorld w;w.controls={sim::ActorId{1},sim::ActorId{2}};w.records[1]=sim::PickupRecord{{0,1},6};w.dormant[0]=sim::EffectId{4,1};
            w.messages[0]=sim::ControlMessage{sim::SetupMessage::mix_those_fruit,0,3};w.message_tilemap=0xe000;w.ingredient_timer=7;return w;
        };
        auto pool=ingredient_pool();auto w=ingredient_world();sim::PrivateGlobals g;g.table_loop_count=5;
        check(pool.walk_delivered({1,1},g,w) && pool.free_stack()==std::vector<std::size_t>{2,1});
        const auto table=std::get<sim::TableMotion>(pool.slots()[4].object);
        check(table.position.x==0xac && table.position.y==0xfa && table.presentation.mode==0x81 && table.presentation.words==std::array<std::uint16_t,3>{0x284,0x284,0x289});
        check(table.presentation.counter==5 && table.target==0x21e && table.countdown==0x0e && table.control.value==1 && table.cursor==0 && table.delta_x==0xffff && table.toggle==0);
        const auto residue=std::get<sim::TableMotion>(pool.slots()[1].object);
        check(!residue.presentation.mode && residue.position.x==0xab && residue.position.y==0xfb && residue.countdown==0x0d && residue.cursor==1 && residue.toggle==1);
        check(w.activation==sim::EffectId{4,1} && w.records[1]->object==sim::EffectId{4,1} && w.records[1]->entry==6 && g.table_loop_count==0 && w.ingredient_timer==0x50);
        check(w.messages[0]==sim::ControlMessage{sim::SetupMessage::first_ingredient,1,3} && w.clears==std::vector<sim::MessageRowClear>{{static_cast<std::uint16_t>(0xe000+14+(3<<7))}});
        // A higher held priority refuses D20E (+46 = FFFFFFFF, no row clear).
        auto held=ingredient_pool();w=ingredient_world();w.messages[0]->priority=0x64;g.table_loop_count=5;
        check(held.walk_delivered({1,1},g,w) && !w.messages[0]->message && w.messages[0]->priority==0x64 && w.clears.empty());
        // FF31AC naming no table object, a missing or awake FF31B4 object, a
        // missing record or message and missing globals reject with no change.
        auto reject=[&](auto change,const char* text){
            auto p=ingredient_pool();auto x=ingredient_world();sim::PrivateGlobals y;y.table_loop_count=5;change(p,x);
            const auto free=p.free_stack();const auto activation=x.activation;rejects([&]{p.walk_delivered({1,1},y,x);},text);
            check(p.free_stack()==free && std::holds_alternative<sim::DeliveredPickup>(p.slots()[1].object) && x.activation==activation && *y.table_loop_count==5 && x.clears.empty());
        };
        reject([](auto&,auto& x){x.activation=sim::EffectId{0,1};},"FF31AC object is not a table object");
        reject([](auto&,auto& x){x.dormant[0].reset();},"FF31B4 object unavailable");
        reject([](auto&,auto& x){x.dormant[0]=sim::EffectId{3,1};},"not dormant");
        reject([](auto&,auto& x){x.records[1].reset();},"record unavailable");
        reject([](auto&,auto& x){x.messages[0].reset();},"control message unavailable");
        // Earlier walks only animate; the pool phase walks the new table object
        // (a later slot) with the stored FF31BC; without a world 79B6 rejects.
        auto early=ingredient_pool();w=ingredient_world();auto first=last;first.presentation.counter=2;
        early=sim::MixedPool({sim::ExternalReservation{},first,std::monostate{},sim::ExternalReservation{},sim::ReturnOnlyObject{}},{2});
        check(!early.walk_delivered({1,1},g,w) && std::get<sim::DeliveredPickup>(early.slots()[1].object).presentation.counter==1 && !w.activation);
        auto phase=ingredient_pool();w=ingredient_world();g.table_loop_count=5;sim::TrailRandom rng{};
        const auto ev=phase.step({},{},rng,8,&g,nullptr,&w);
        check(ev.size()==2 && ev[0].kind==sim::PoolEventKind::release && ev[0].id.slot==1 && ev[1].kind==sim::PoolEventKind::update && ev[1].id.slot==4);
        const auto walked=std::get<sim::TableMotion>(phase.slots()[4].object).position;
        check(walked.x==0xab && walked.y==0xfb && g.table_loop_count==0 && w.ingredient_timer==0x50);
        auto bare=ingredient_pool();rejects([&]{bare.step({},{},rng,8,&g);},"79B6");
    }
    {   // The second ingredient: with FF31AC naming the first table object (slot
        // 0, +32 FFFF), D22F is posted, the copy becomes a table object drifting
        // the other way in the dormant FF31B8 object (slot 3), FF31B0 names it,
        // the FF31C0 anchor (slot 4) becomes a 300-walk spell countdown and the
        // copy is released; FF31BE/FF31BC are untouched.
        const sim::DeliveredPickup last{{0xa4,0xf6},0,{0x87,{0x21e,0x21e,0x227},1,3},0x21e,{1},{0x27e,0x283},{0,1,16,16}};
        const sim::TableMotion first{{0x60,0x80},0,{0x81,{0x284,0x284,0x289},5,5},0x21e,0x0e,{1},3,0xffff,1};
        const sim::ReturnOnlyObject anchor{{164,270},0x800,{0x81,{919,916,921},5,5},0,0,{0}};
        auto pool2=[&]{return sim::MixedPool({first,last,std::monostate{},sim::ReturnOnlyObject{},anchor},{2});};
        auto world2=[]{
            sim::PickupWorld w;w.controls={sim::ActorId{1},sim::ActorId{2}};w.records[1]=sim::PickupRecord{{0,1},6};w.activation=sim::EffectId{0,1};
            w.dormant={sim::EffectId{0,1},sim::EffectId{3,1}};w.anchor=sim::EffectId{4,1};w.messages[0]=sim::ControlMessage{std::nullopt,0,12};
            w.message_tilemap=0xe000;w.ingredient_timer=0x50;return w;
        };
        auto pool=pool2();auto w=world2();sim::PrivateGlobals g;g.table_loop_count=0;
        check(pool.walk_delivered({1,1},g,w) && pool.free_stack()==std::vector<std::size_t>{2,1});
        const auto copy=std::get<sim::TableMotion>(pool.slots()[3].object);
        check(copy.position.x==0xac && copy.position.y==0xfa && copy.presentation.words==std::array<std::uint16_t,3>{0x27e,0x27e,0x283} && copy.delta_x==1 && copy.countdown==0x0e);
        const auto spell=std::get<sim::SpellCountdown>(pool.slots()[4].object);
        check(spell.countdown==0x12c && spell.control.value==1 && spell.position.x==164 && spell.presentation.words[0]==919 && spell.flags==0x800);
        check(w.spell==sim::EffectId{3,1} && g.rise_gate && w.records[1]->object==sim::EffectId{3,1} && w.activation==sim::EffectId{0,1});
        check(w.messages[0]==sim::ControlMessage{sim::SetupMessage::second_ingredient,1,12} && w.clears.size()==1 && w.ingredient_timer==0x50 && *g.table_loop_count==0);
        check(std::holds_alternative<sim::TableMotion>(pool.slots()[1].object) && !std::get<sim::TableMotion>(pool.slots()[1].object).presentation.mode);
        auto reject=[&](auto change,const char* text){
            auto p=pool2();auto x=world2();sim::PrivateGlobals y;y.table_loop_count=0;change(p,x,y);
            const auto free=p.free_stack();rejects([&]{p.walk_delivered({1,1},y,x);},text);
            check(p.free_stack()==free && std::holds_alternative<sim::DeliveredPickup>(p.slots()[1].object) && !x.spell && !y.rise_gate && x.clears.empty());
        };
        reject([](auto&,auto& x,auto&){x.anchor.reset();},"FF31C0 anchor unavailable");
        reject([](auto&,auto& x,auto&){x.anchor=sim::EffectId{0,1};},"anchor is not return-only");
        reject([](auto&,auto& x,auto&){x.dormant[1].reset();},"FF31B8 object unavailable");
        reject([](auto&,auto& x,auto&){x.dormant[1]=sim::EffectId{4,1};},"not dormant");
        reject([](auto&,auto&,auto& y){y.table_loop_count.reset();},"table motion input unavailable");
        // The countdown walks 300 more times; the 301st runs 13294 (the fade-out
        // keeps the level) and selects 7B58, which waits for FF0B90 to clear;
        // without a timer it rejects. 7B8A then reports the reveal.
        auto countdown=spell;countdown.countdown=1;check(sim::step_spell_countdown(countdown,nullptr)==sim::SpellStep::none && countdown.countdown==0);
        const auto before=countdown;rejects([&]{sim::step_spell_countdown(countdown,nullptr);},"timer unavailable");
        check(countdown.countdown==before.countdown && countdown.presentation.counter==before.presentation.counter);
        sim::TransitionState fade;fade.level=14;
        check(sim::step_spell_countdown(countdown,&fade)==sim::SpellStep::none && countdown.phase==sim::SpellPhase::completion && countdown.countdown==0xffff);
        check(fade.direction==1 && fade.countdown==6 && fade.reload==0 && fade.level==14 && fade.curves[0]==sim::TransitionCurve::tally);
        check(sim::step_spell_countdown(countdown,&fade)==sim::SpellStep::none);
        fade.direction=0;check(sim::step_spell_countdown(countdown,&fade)==sim::SpellStep::complete && countdown.phase==sim::SpellPhase::completion);
        countdown.phase=sim::SpellPhase::reveal;fade.direction=0xffff;check(sim::step_spell_countdown(countdown,&fade)==sim::SpellStep::none);
        fade.direction=0;check(sim::step_spell_countdown(countdown,&fade)==sim::SpellStep::revealed);
        // 7CC8: FF31BE counts down and reloads 0028 as FF31BC increments; the
        // FF31AC object (+32 negative) and a higher FF31B0 object exchange state.
        auto mixed=pool;w.ingredient_timer=0;g.table_loop_count=6;const auto a=std::get<sim::TableMotion>(mixed.slots()[0].object);
        mixed.mix_spell(w,&g);check(w.ingredient_timer==0x28 && *g.table_loop_count==7);
        const auto b0=std::get<sim::TableMotion>(mixed.slots()[0].object),b3=std::get<sim::TableMotion>(mixed.slots()[3].object);
        check(b0.delta_x==copy.delta_x && b3.delta_x==a.delta_x && b0.position.x==copy.position.x && b3.cursor==a.cursor && b0.control.value==1 && b0.presentation.mode==0x81);
        mixed.mix_spell(w,&g);check(w.ingredient_timer==0x27 && std::get<sim::TableMotion>(mixed.slots()[0].object).delta_x==1); // +32 now positive, FF31B0 higher: kept.
        auto quiet=pool;auto q=w;q.spell.reset();const auto t=q.ingredient_timer;quiet.mix_spell(q,nullptr);check(q.ingredient_timer==t);
        rejects([&]{auto p=pool;auto x=w;p.mix_spell(x,nullptr);},"FF31BC unavailable");
        rejects([&]{auto p=pool;auto x=w;x.spell=sim::EffectId{4,1};auto y=g;p.mix_spell(x,&y);},"not table objects");
    }
    {
        // 705C's contact (7082): the open door at (352,240) with its sign above;
        // P1 at the door. The sign is released (its slot pushed), the door
        // vanishes at (344,248), FF0F00 and the camera words (0048,0018) are set
        // and the session hands P1 to 710E with selector FFFF. A miss changes
        // nothing; an active +1A2 link rejects with no change.
        std::vector<sim::PoolObject> objects(6,sim::ExternalReservation{});
        sim::DoorSign sign=sim::make_door_sign();sim::raise_door_sign(sign,{352,240});objects[1]=sign;
        sim::ExitDoor door=sim::make_exit_door({360,216},sim::ActorId{1},{1,1});
        door.presentation={0x81,{0xb0,0xa8,0xb7},3,3};door.x_extent=16;door.y_extent=32;door.phase=sim::DoorPhase::open;objects[2]=door;
        objects[3]=sim::ReturnOnlyObject{};objects[4]=sim::ReturnOnlyObject{};objects[5]=std::monostate{};
        sim::MixedSessionState base{{},sim::MixedPool(objects,{5}),{}};
        base.world=sim::PickupWorld{};base.world->controls={sim::ActorId{1},sim::ActorId{2}};
        base.world->links[0]=sim::EffectId{3,1};base.world->anchor=sim::EffectId{4,1};base.world->door=sim::EffectId{2,1};
        base.p1.actor.motion.presentation.mode=0x81;base.p1.actor.motion.update=sim::MotionUpdate::idle_right;
        const sim::CollisionInputs at_door{{352,240},{1023,0,{}}},away{{900,900},{1023,0,{}}};
        auto missed=base;sim::step_world_phase(missed,sim::ActorId{1},{},&away,64,{});
        check(std::holds_alternative<sim::ExitDoor>(missed.pool.slots()[2].object) && !missed.world->exit_control && missed.p1.actor.motion.update==sim::MotionUpdate::idle_right);
        auto entered=base;const auto out=sim::step_world_phase(entered,sim::ActorId{1},{},&at_door,64,{});
        const auto& vanished=std::get<sim::TrailParticle>(entered.pool.slots()[2].object);
        check(vanished.position.x==344 && vanished.position.y==248 && vanished.presentation.mode==0x85 && vanished.target==0x227 && vanished.presentation.words[2]==0x227);
        // The sign's own walk, then its release inside the door's walk before the door's update.
        std::vector<std::pair<sim::PoolEventKind,std::size_t>> order;for(const auto& e:out.events) order.emplace_back(e.kind,e.id.slot);
        check(std::get<sim::DoorSign>(entered.pool.slots()[1].object).presentation.mode==0 && entered.pool.free_stack().back()==1);
        check(order.size()==5 && order[0]==std::pair{sim::PoolEventKind::update,std::size_t{1}} && order[1]==std::pair{sim::PoolEventKind::release,std::size_t{1}}
              && order[2]==std::pair{sim::PoolEventKind::update,std::size_t{2}});
        const auto& w=*entered.world;
        check(w.exit_control==sim::ActorId{1} && w.exit_camera && w.exit_camera->x==0x48 && w.exit_camera->y==0x18 && !w.door_entered);
        const auto& a=entered.p1.actor;
        check(a.motion.update==sim::MotionUpdate::transition_start && a.motion.presentation.mode==0x80 && a.motion.presentation.words[0]==0x21d && entered.p1.tracking.selector==0xffff);
        auto linked=base;
        std::vector<sim::PoolObject> with_link=objects;sim::ReturnOnlyObject live;live.presentation.mode=0x81;with_link[3]=live;
        linked.pool=sim::MixedPool(with_link,{5});const auto kept=linked.pool.free_stack();
        rejects([&]{sim::step_world_phase(linked,sim::ActorId{1},{},&at_door,64,{});},"70FE active link");
        check(linked.pool.free_stack()==kept && std::holds_alternative<sim::ExitDoor>(linked.pool.slots()[2].object) && !linked.world->exit_control);
    }
    {
        // The scene between levels: 6090's records over an empty pool (0..67,
        // pops from 67), then door 0's 61 walks, P1's contact and the puff.
        sim::HubDoorTable table{};
        const std::array<std::array<std::uint16_t,4>,9> rows{{{0x1b0,0xa4,0,0},{0x1e0,0x114,1,0},{0x2b0,0x84,2,0},{0x320,0xa8,3,0},{0x2c0,0x10c,4,0},
            {0x88,0x54,5,0},{0x458,0xa8,6,0},{0x400,0x64,7,0},{0x128,0x7c,8,0xffff}}};
        for(std::size_t r=0;r<9;++r) table[r]={{rows[r][0],rows[r][1]},rows[r][2],0,rows[r][3],0xffff,0xffff};
        std::vector<std::size_t> all(68);for(std::size_t i=0;i<68;++i) all[i]=i;
        sim::MixedSessionState base{{},sim::MixedPool(std::vector<sim::PoolObject>(68),all),{}};
        base.hub=sim::HubWorld{table,false,{},{}};
        base.p1.transition=sim::TransitionState{};base.p1.actions=sim::ActionGlobals{7,0,0};
        const auto ids=sim::initialize_hub(base,0);
        check(ids.size()==24 && ids[0].slot==67 && ids[1].slot==66 && ids[2].slot==65 && ids[23].slot==44 && base.pool.available()==44);
        const auto& d0=std::get<sim::HubDoor>(base.pool.slots()[67].object);
        check(d0.phase==sim::HubDoorPhase::waiting && d0.countdown==0x3c && d0.presentation.mode==0x81 && d0.numbers[0].slot==66 && d0.numbers[1].slot==65);
        const auto& left=std::get<sim::ReturnOnlyObject>(base.pool.slots()[45].object);
        check(left.position.x==0x3f0 && left.position.y==0x5a && left.presentation.words[0]==0xc8); // Door 7: 00B8 + 10.
        const sim::CollisionInputs away{{0xff80,0xff80},{1023,0,{}}},at_door{{0x1a1,0xbc},{1023,0,{}}};
        auto walked=base;
        for(int n=0;n<61;++n) sim::step_world_phase(walked,sim::ActorId{1},{},&away,64,{});
        check(std::get<sim::HubDoor>(walked.pool.slots()[67].object).phase==sim::HubDoorPhase::open);
        auto entered=walked;const auto out=sim::step_world_phase(entered,sim::ActorId{1},{},&at_door,64,{});
        check(out.hub_entry && out.hub_entry->control==0 && out.hub_entry->number==0 && entered.hub->selected==0 && !entered.hub->entry);
        const auto& v=std::get<sim::HubDoor>(entered.pool.slots()[67].object);
        check(v.phase==sim::HubDoorPhase::vanishing && v.position.x==0x1ac && v.position.y==0xac && v.presentation.mode==0x85 && v.target==0x227 && v.countdown==0);
        check(entered.pool.free_stack().size()==46 && entered.pool.free_stack()[44]==66 && entered.pool.free_stack()[45]==65);
        const auto& t=*entered.p1.transition;
        check(t.requested_position.x==0x98 && t.requested_position.y==0x08 && t.direction==1 && t.level==14);
        check(entered.p1.actor.motion.update==sim::MotionUpdate::coast && entered.p1.tracking.selector==0xffff);
        check(sim::hub_loop_ends(0xffff,sim::TransitionState{}) && !sim::hub_loop_ends(0xffff,t) && !sim::hub_loop_ends(0xfffe,sim::TransitionState{}));
        // FAC4 on the next walk (X - 4, frame back to 021E), then FAA4 at 0227.
        auto puff=entered;sim::step_world_phase(puff,sim::ActorId{1},{},&away,64,{});
        check(std::get<sim::HubDoor>(puff.pool.slots()[67].object).phase==sim::HubDoorPhase::puffing && std::get<sim::HubDoor>(puff.pool.slots()[67].object).position.x==0x1a8);
        for(int n=0;n<40 && puff.pool.free_stack().size()==46;++n) sim::step_world_phase(puff,sim::ActorId{1},{},&away,64,{});
        check(puff.pool.free_stack().size()==47 && puff.pool.free_stack().back()==67);
        // Unsupported: an empty stack, a number outside 639A, a hub beside a level world.
        auto empty=base;empty.pool=sim::MixedPool(std::vector<sim::PoolObject>(68,sim::ExternalReservation{}),{});
        rejects([&]{sim::initialize_hub(empty,0);},"hub door allocation exhausted");
        auto wide=base;wide.pool=sim::MixedPool(std::vector<sim::PoolObject>(68),all);wide.hub->table[3].number=10;
        rejects([&]{sim::initialize_hub(wide,0);},"639A table");check(wide.pool.available()==68);
        auto both=walked;both.world=sim::PickupWorld{};
        rejects([&]{sim::step_world_phase(both,sim::ActorId{1},{},&at_door,64,{});},"beside a level world");
    }
    {
        // The scene change: P1 rebuilt at FF4446/48 + (0114, 00B0), the timer's
        // fade-in (001E, then 000A), the reset pool with 60E6's doors, the
        // banner's scratch row and FF33E0 = 7; the level's world is dropped.
        // A level pool with eight occupied slots, which the reset frees.
        std::vector<sim::PoolObject> occupied(68);std::vector<std::size_t> spare(60);
        for(std::size_t i=0;i<60;++i) spare[i]=i;
        for(std::size_t i=60;i<68;++i) occupied[i]=sim::ExternalReservation{};
        sim::MixedSessionState level{{},sim::MixedPool(occupied,spare),{}};
        level.p1.transition=sim::TransitionState{};level.p1.transition->requested_position={0,0x30};level.p1.actions=sim::ActionGlobals{0x0e,5,6};
        level.p1.actor.motion.update=sim::MotionUpdate::coast;level.p1.tracking={0xffff,{0xff80,0xff80}};level.p1.scratch={0x1234,6};level.world=sim::PickupWorld{};
        sim::HubDoorTable table{};for(std::size_t r=0;r<9;++r) table[r]={{static_cast<std::uint16_t>(0x100+r*0x40),0x80},static_cast<std::uint16_t>(r),0,static_cast<std::uint16_t>(r==8 ? 0xffff : 0),0xffff,0xffff};
        auto hub=level;const auto entry=sim::enter_hub_scene(hub,{table,false,false,0,{sim::Difficulty::apprentice,0,0x0d}});
        const auto& a=hub.p1.actor;
        check(a.motion.position.x==0x114 && a.motion.position.y==0xe0 && a.motion.presentation.mode==0x87 && a.motion.presentation.counter==0x19 && a.presentation_target==0x21e);
        check(a.motion.update==sim::MotionUpdate::return_only && a.callback==sim::PresentationCallback::enter_airborne && a.motion.flags==0x0800);
        check(hub.p1.tracking.selector==0 && hub.p1.tracking.position.x==0xff80 && hub.p1.scratch.x==0x1234 && hub.p1.scratch.y==0x0d);
        const auto& t=*hub.p1.transition;
        check(t.direction==0xffff && t.countdown==0x0a && t.reload==1 && t.level==0 && t.curves[2]==sim::TransitionCurve::exit_blue && hub.p1.actions->mode==7);
        check(!hub.world && hub.hub && entry.doors.size()==24 && entry.doors[0].slot==67 && hub.pool.available()==44 && entry.acceleration_gate==0 && entry.banner);
        check(entry.parameters.airborne.motion.positive_limit==0xc0 && sim::hub_actor_parameters(true).airborne.motion.negative_limit==0xffa0);
        check(sim::reset_object_pool().free_stack().size()==68 && sim::reset_object_pool().free_stack().back()==67);
        auto two=level;rejects([&]{sim::enter_hub_scene(two,{table,true,false,0,{}});},"two-player scene change");check(two.world && !two.hub);
        auto bare=level;bare.p1.transition.reset();rejects([&]{sim::enter_hub_scene(bare,{table,false,false,0,{}});},"timer or action globals");
        // After the hub: the hint screen (16EA4, FF0F10 = 00F0) and its loops: 44
        // fade-in loops, 241 decrements to FFFF, 16 fade-out loops (the movie's 301).
        auto after=hub;after.p1.tracking.selector=0xffff;after.p1.transition->direction=0;after.random={0xf00eed1f,0xf00eed1f};
        auto screen=sim::enter_hint_screen(after);
        check(!after.hub && !after.world && screen.countdown==0xf0 && !screen.ending && after.p1.transition->countdown==0x1e && after.p1.transition->direction==0xffff);
        check(after.p1.actor.motion.presentation.mode==0 && after.p1.actor.motion.update==sim::MotionUpdate::return_only && after.p1.tracking.selector==0xffff);
        check(after.pool.available()==68 && after.p1.scratch.x==0x1234);
        sim::PadControl control;std::size_t loops=0;bool done=false;
        while(!done && loops<1000){done=sim::step_hint_screen(screen,*after.p1.transition,control,{});++loops;}
        check(done && loops==301 && screen.ending && screen.countdown==0xffff && !after.p1.transition->direction && control.raw==0xff);
        // Start skips the countdown once the fade-in is over; 14E3C makes +16 A|B|C.
        auto skipped=sim::enter_hint_screen(after);auto timer=*after.p1.transition;timer.direction=0;sim::PadControl pad;
        check(!sim::step_hint_screen(skipped,timer,pad,{false,false,false,false,true,false,false,true}) && skipped.ending && skipped.countdown==0xf0 && timer.direction==1);
        check(pad.jump==0xff && pad.start==0xff && !(pad.raw & 0x80));
        sim::PadControl merged;merged.a=0x0f;merged.c=0x30;sim::merge_action_buttons(merged);check(merged.jump==0x3f);
        check(!sim::continue_hint_screen(skipped,timer,false) && timer.direction==1);
        // The second level's entry: 9880 at a zero anchor, 9952 again, FF33D8, FF33E0.
        auto second=after;const auto entered=sim::enter_second_level(second,{false,false,0x3c,1,12});
        const auto& b=second.p1.actor;
        check(b.motion.position.x==0x114 && b.motion.position.y==0xb0 && b.motion.presentation.mode==0x87 && b.motion.presentation.counter==3 && b.motion.flags==0);
        check(b.callback==sim::PresentationCallback::enter_airborne && b.service==sim::ActorService::return_only && b.presentation_target==0x21e);
        check(second.p1.tracking.selector==0 && second.p1.actions->cooldown==0xffff && second.p1.actions->mode==0x13 && second.p1.transition->countdown==0x1e);
        check(!second.p1.transition->saved_position.x && !second.p1.transition->saved_position.y && second.p1.transition->requested_position.y==hub.p1.transition->requested_position.y);
        check(second.random.state==0x92970f3d && second.random.mirror==0x92970f3d && entered.acceleration_gate==0 && entered.parameters.airborne.motion.positive_limit==0xc0);
        sim::TrailRandom draws{0xf00eed1f,0};
        check(sim::choose_action_cooldown(0,draws)==0 && sim::choose_action_cooldown(0x0b,draws)==0xffff && sim::choose_action_cooldown(0x8000,draws)<0x8002 && draws.state!=0xf00eed1f);
        auto pair=after;rejects([&]{sim::enter_second_level(pair,{true,false,0x3c,1,0});},"two-player second level");check(pair.p1.actions->mode==7);
        auto none=after;rejects([&]{sim::enter_second_level(none,{false,false,0x3c,0,0});},"54BA draws E918");
    }
    std::cout<<"overlap boundaries, wrap, masks, primary/secondary misses, unsupported hits, tracked inputs, rollback, 783A quad initialization, pickups, 6C00 and 7910 hits, both ingredient callbacks, the spell countdown, 7CC8, the door entry, the hub's doors, the scene change, the hint screen and the second level's entry passed\n";
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
