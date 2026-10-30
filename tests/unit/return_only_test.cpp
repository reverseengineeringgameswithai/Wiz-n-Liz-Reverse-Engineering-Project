#include "sim/mixed_pool.hpp"
#include <algorithm>
#include <iostream>
#include <optional>
#include <set>
#include <source_location>
#include <string>
#include <tuple>
namespace {
using namespace wiz;
void check(bool ok,std::source_location at=std::source_location::current()){if(!ok)throw std::runtime_error("return-only check failed at line "+std::to_string(at.line()));}
template<class F>void rejects(F f){try{f();}catch(const assets::BankError&){return;}throw std::runtime_error("return-only accepted unsupported work");}
auto fields(const sim::ReturnOnlyObject& o){return std::tuple{o.position.x,o.position.y,o.flags,o.presentation.mode,o.presentation.words,o.presentation.counter,o.presentation.reload,o.target,o.countdown,o.control.value};}
sim::ReturnOnlyObject seed(){return {{164,270},0x800,{0x81,{921,916,921},3,5},0,17,{123}};}
sim::TrailEmitter emitter(){return {{100,200},0,{{{10,20},{30,40},{50,60},{70,80},{90,100}}},{0x81,{638,638,643},5,5},0,0x800,{1}};}
}
int main(){try{
    auto p=seed();sim::step_return_only_object(p);check(p.presentation.counter==2);
    sim::step_return_only_object(p);sim::step_return_only_object(p);
    check(p.presentation.counter==5 && p.presentation.words[0]==916 && p.position.x==164 && p.countdown==17 && p.control.value==123);
    p=seed();p.presentation.mode=0x8b;p.presentation.words[0]=916;p.presentation.counter=1;
    sim::step_return_only_object(p);check(p.presentation.mode==0x89 && p.presentation.words[0]==916);
    p=seed();p.presentation.words={65535,0,65534};p.presentation.counter=1;
    sim::step_return_only_object(p);check(p.presentation.words[0]==0);
    p=seed();p.presentation.mode=0x85;p.presentation.counter=1;p.target=921;auto before=p;
    rejects([&]{sim::step_return_only_object(p);});check(fields(p)==fields(before));
    p.presentation.mode=5;before=p;for(unsigned i=0;i<256;++i)sim::step_return_only_object(p);check(fields(p)==fields(before));
    // Activity can only come from a separately verified producer. Supplying an
    // active component input must enforce callback rejection, not reuse a skip.
    p.presentation.mode|=128;before=p;rejects([&]{sim::step_return_only_object(p);});check(fields(p)==fields(before));
    auto dormant=seed();dormant.presentation.mode=0;auto dying=sim::make_trail_particle({},true);
    dying.presentation.words[0]=dying.target;dying.presentation.counter=1;
    rejects([&]{sim::MixedPool({dormant},{0});});
    sim::MixedPool occupied({dormant},{});sim::TrailRandom rng{1,99};
    rejects([&]{occupied.spawn(sim::make_trail_particle({},true));});
    auto events=occupied.step({},{},rng,0);check(events.size()==1 && events[0].kind==sim::PoolEventKind::inactive && events[0].id==sim::EffectId{0,1});
    check(occupied.available()==0 && fields(std::get<sim::ReturnOnlyObject>(occupied.slots()[0].object))==fields(dormant));
    // Inactive occupied slots are skipped by allocation even after a release.
    sim::MixedPool reuse({dormant,dying,emitter(),std::monostate{}},{3});rng={1,99};
    events=reuse.step({1},{0,0},rng,2);
    check(events.size()==4 && events[0].kind==sim::PoolEventKind::inactive && events[1].kind==sim::PoolEventKind::release);
    check(events[2].kind==sim::PoolEventKind::spawn && events[2].id==sim::EffectId{1,2});
    check(reuse.free_stack()==std::vector<std::size_t>{3} && reuse.slots()[0].generation==1);
    // Late callback failure discards earlier presentation, release, allocation,
    // inactive observations and RNG consumption in the same phase.
    sim::MixedPool fail({dormant,dying,emitter(),seed(),p},{});rng={1,99};
    rejects([&]{fail.step({1},{0,0},rng,4);});
    check(fail.available()==0 && fail.slots()[1].generation==1 && rng.state==1 && rng.mirror==99);
    check(fields(std::get<sim::ReturnOnlyObject>(fail.slots()[3].object))==fields(seed()));
    // Same failure after active P1/banner and a staged reversal allocation.
    assets::PatternBank bank;bank.logical_id="base";bank.patterns.resize(1);bank.patterns[0].opaque_record.fill(5);
    assets::SceneResource scene;scene.base_bank_id="base";scene.columns=128;scene.rows=32;scene.cells.resize(4096);
    sim::P1SessionState p1;p1.actor.motion.position={200,109};p1.actor.motion.presentation.mode=128;
    p1.actor.motion.update=sim::MotionUpdate::fast_right;p1.actor.motion.horizontal_speed=160;p1.actor.service=sim::ActorService::return_only;p1.scratch={7,9};
    sim::MixedSessionState world{p1,sim::MixedPool({dormant,p,std::monostate{}},{2}),{1,99}};
    sim::P1SessionConfig config;config.banner=sim::LevelBannerConfig{sim::Difficulty::apprentice,0,6};
    sim::ThreeButtonPad held;held.left=true;rejects([&]{sim::step_mixed_session(scene,bank,world,config,held);});
    check(world.p1.invocations==0 && world.p1.actor.motion.position.x==200 && world.p1.actor.motion.horizontal_speed==160 && world.p1.scratch.x==7 && world.p1.scratch.y==9);
    check(world.p1.control==p1.control && world.pool.free_stack()==std::vector<std::size_t>{2} && world.pool.slots()[2].generation==0);
    // 7B9C pair: LIFO order over verified inherited fields, then FF31C0 identity.
    using Inherited=std::optional<sim::InheritedObjectFields>;
    auto pair_pool=[&](std::vector<std::size_t> free,std::vector<Inherited> inherited) {
        std::vector<sim::PoolObject> objects(5,sim::ExternalReservation{});objects[4]=dormant;
        for(auto i:free)objects[i]=std::monostate{};
        return sim::MixedPool(objects,free,inherited);
    };
    const sim::InheritedObjectFields top{921,300,{7}},below{0,0,{0}};
    auto pool=pair_pool({0,2,1},{Inherited{},top,below,Inherited{},Inherited{}});
    const auto pair=pool.initialize_return_only_pair();
    check(pair.first==sim::EffectId{1,1} && pair.second==sim::EffectId{2,1} && pool.free_stack()==std::vector<std::size_t>{0});
    const auto& a=std::get<sim::ReturnOnlyObject>(pool.at(pair.first).object);const auto& b=std::get<sim::ReturnOnlyObject>(pool.at(pair.second).object);
    check(fields(a)==std::tuple{std::uint16_t(161),std::uint16_t(270),std::uint16_t(0),std::uint8_t(0x81),std::array<std::uint16_t,3>{916,916,921},std::uint8_t(4),std::uint8_t(4),std::uint16_t(921),std::uint16_t(300),std::uint64_t(7)});
    check(fields(b)==std::tuple{std::uint16_t(164),std::uint16_t(270),std::uint16_t(0x800),std::uint8_t(0x81),std::array<std::uint16_t,3>{919,916,921},std::uint8_t(5),std::uint8_t(5),std::uint16_t(0),std::uint16_t(0),std::uint64_t(0)});
    check(!pool.slots()[1].inherited && !pool.slots()[2].inherited && !pool.slots()[0].inherited);
    // Mode 81 never tests target, so an inherited 921 is retained without firing
    // through repeated 916..921 loops; only mode bit 2 could reach a callback.
    rng={1,99};auto copy=pool;std::set<std::uint16_t> frames;
    for(unsigned i=0;i<64;++i){copy.step({},{},rng,8);frames.insert(std::get<sim::ReturnOnlyObject>(copy.slots()[1].object).presentation.words[0]);}
    check(frames==std::set<std::uint16_t>{916,917,918,919,920,921} && std::get<sim::ReturnOnlyObject>(copy.slots()[1].object).target==921);
    // Exhaustion at either call and unknown inheritance at either member reject
    // with no allocation, generation, inheritance or free-order change.
    for(auto [free,inherited]:{std::pair{std::vector<std::size_t>{},std::vector<Inherited>{}},
            std::pair{std::vector<std::size_t>{2},std::vector<Inherited>{Inherited{},Inherited{},top,Inherited{},Inherited{}}},
            std::pair{std::vector<std::size_t>{0,2},std::vector<Inherited>{below,Inherited{},Inherited{},Inherited{},Inherited{}}},
            std::pair{std::vector<std::size_t>{0,2},std::vector<Inherited>{Inherited{},Inherited{},top,Inherited{},Inherited{}}}}) {
        auto bad=pair_pool(free,inherited);const auto before=bad.slots();
        rejects([&]{bad.initialize_return_only_pair();});
        check(bad.free_stack()==free);
        for(std::size_t i=0;i<before.size();++i)check(bad.slots()[i].generation==before[i].generation && bad.slots()[i].object.index()==before[i].object.index() && bool(bad.slots()[i].inherited)==bool(before[i].inherited));
    }
    rejects([&]{pair_pool({0},{below});});
    rejects([&]{pair_pool({0},{Inherited{},below,Inherited{},Inherited{},Inherited{}});});
    // A released slot's residue is not known natively, so 7B9C cannot reuse it.
    sim::MixedPool released({dying,std::monostate{}},{1},{Inherited{},top});rng={1,99};released.step({},{},rng,1);
    check(released.free_stack()==std::vector<std::size_t>{1,0} && !released.slots()[0].inherited);
    rejects([&]{released.initialize_return_only_pair();});
    // Session API commits pair and FF31C0 anchor together; the anchor persists
    // through later sessions and a mismatched identity rolls the step back.
    sim::MixedSessionState retained{p1,pair_pool({0,2,1},{Inherited{},top,below,Inherited{},Inherited{}}),{1,99}};
    const auto anchored=sim::initialize_return_only_pair(retained);check(retained.return_only_anchor==anchored.second);
    sim::MixedSessionState none{p1,pair_pool({},{}),{1,99}};const auto empty_before=none.pool.slots().size();
    rejects([&]{sim::initialize_return_only_pair(none);});check(!none.return_only_anchor && none.pool.slots().size()==empty_before);
    sim::P1SessionConfig quiet;quiet.banner=sim::LevelBannerConfig{sim::Difficulty::apprentice,0,6};
    auto stepped=sim::step_mixed_session(scene,bank,retained,quiet,{});
    check(retained.return_only_anchor==anchored.second && retained.p1.invocations==1 && std::get<sim::ReturnOnlyObject>(retained.pool.at(anchored.second).object).presentation.counter==4);
    check(stepped.events.size()==3 && stepped.events[0].kind==sim::PoolEventKind::update && stepped.events[2].kind==sim::PoolEventKind::inactive);
    auto wrong=retained;wrong.return_only_anchor=sim::EffectId{3,1};
    rejects([&]{sim::step_mixed_session(scene,bank,wrong,quiet,{});});check(wrong.p1.invocations==1);
    wrong.return_only_anchor=sim::EffectId{1,2};rejects([&]{sim::step_mixed_session(scene,bank,wrong,quiet,{});});
    // 6EC8/6EDC: one pop left dormant (mode 0, frame 021D) keeping position,
    // +08..+0D, target, countdown and link; both position and presentation
    // must be verified. The identity commits with the allocation.
    auto full=[](std::uint16_t n){return sim::InheritedObjectFields{static_cast<std::uint16_t>(900+n),n,{n},
        sim::InheritedPresentation{{static_cast<std::uint16_t>(10+n),static_cast<std::uint16_t>(20+n)},static_cast<std::uint8_t>(30+n),static_cast<std::uint8_t>(40+n)},
        sim::Position{static_cast<std::uint16_t>(100+n),static_cast<std::uint16_t>(200+n)}};};
    check(fields(sim::make_dormant(full(1)))==fields(sim::ReturnOnlyObject{{101,201},0,{0,{0x21d,11,21},31,41},901,1,{1}}));
    for(auto drop:{0,1}) {auto f=full(1);if(drop)f.position.reset();else f.presentation.reset();rejects([&]{sim::make_dormant(f);});}
    sim::MixedSessionState sleeping{p1,pair_pool({0,2,1},{Inherited{},full(1),full(2),Inherited{},Inherited{}}),{1,99}};
    const auto d1=sim::initialize_dormant(sleeping,sim::DormantAnchor::first);const auto d2=sim::initialize_dormant(sleeping,sim::DormantAnchor::second);
    check(d1==sim::EffectId{1,1} && d2==sim::EffectId{2,1} && sleeping.dormant_anchors[0]==d1 && sleeping.dormant_anchors[1]==d2 && sleeping.pool.free_stack()==std::vector<std::size_t>{0});
    // Dormant objects emit inactive observations and never change.
    const auto walked=sim::step_mixed_session(scene,bank,sleeping,quiet,{});
    // Slot 4 of this helper pool already holds a dormant object.
    check(walked.events.size()==3 && std::ranges::all_of(walked.events,[](const auto& e){return e.kind==sim::PoolEventKind::inactive;}));
    check(fields(std::get<sim::ReturnOnlyObject>(sleeping.pool.at(d2).object))==fields(sim::make_dormant(full(2))));
    auto stale=sleeping;stale.dormant_anchors[0]=sim::EffectId{1,7};rejects([&]{sim::step_mixed_session(scene,bank,stale,quiet,{});});check(stale.p1.invocations==sleeping.p1.invocations);
    for(auto parts:{0,1,2}) {
        auto f=full(1);if(parts==0)f.position.reset();else if(parts==1)f.presentation.reset();
        sim::MixedSessionState bad{p1,pair_pool({0,1},{Inherited{},parts==2 ? Inherited{} : Inherited{f},Inherited{},Inherited{},Inherited{}}),{1,99}};
        rejects([&]{sim::initialize_dormant(bad,sim::DormantAnchor::first);});
        check(!bad.dormant_anchors[0] && bad.pool.free_stack()==std::vector<std::size_t>{0,1} && bad.pool.slots()[1].generation==0);
    }
    // [6886,68A4): twelve pops in order, every identity committed together.
    auto prefix_pool=[&](std::size_t depth,std::size_t unknown) {
        std::vector<sim::PoolObject> objects(14,sim::ExternalReservation{});std::vector<std::size_t> free;std::vector<Inherited> inherited(14);
        for(std::size_t k=0;k<depth;++k){const auto slot=13-k;objects[slot]=std::monostate{};free.insert(free.begin(),slot);if(k!=unknown)inherited[slot]=full(static_cast<std::uint16_t>(k));}
        return sim::MixedSessionState{p1,sim::MixedPool(objects,free,inherited),{1,99}};
    };
    auto setup=prefix_pool(13,99);const auto ids=sim::initialize_level_setup_prefix(setup,{1});
    check(ids.dormant[0]==sim::EffectId{13,1} && ids.dormant[1]==sim::EffectId{12,1} && ids.rising.first==sim::EffectId{11,1} && ids.rising.second==sim::EffectId{10,1});
    check(ids.quad.members[0]==sim::EffectId{9,1} && ids.quad.members[3]==sim::EffectId{6,1} && ids.return_only.second==sim::EffectId{4,1} && ids.visibility.second==sim::EffectId{2,1});
    check(setup.dormant_anchors[0]==ids.dormant[0] && setup.dormant_anchors[1]==ids.dormant[1] && setup.return_only_anchor==ids.return_only.second && setup.pool.available()==1);
    check(std::get<sim::PrivateObject>(setup.pool.at(ids.rising.first).object).control.value==1 && std::get<sim::CollisionProbe>(setup.pool.at(ids.quad.members[0]).object).control.value==1);
    // Exhaustion at any of the twelve pops, or unknown inheritance at any member,
    // leaves pool and all three identities untouched.
    for(std::size_t depth=0;depth<12;++depth) for(std::size_t unknown:{std::size_t{99},depth ? depth-1 : 99}) {
        auto bad=prefix_pool(depth,unknown);const auto before=bad.pool.free_stack();
        rejects([&]{sim::initialize_level_setup_prefix(bad,{1});});
        check(bad.pool.free_stack()==before && !bad.dormant_anchors[0] && !bad.dormant_anchors[1] && !bad.return_only_anchor);
    }
    for(std::size_t unknown=0;unknown<12;++unknown) {
        auto bad=prefix_pool(12,unknown);rejects([&]{sim::initialize_level_setup_prefix(bad,{1});});
        check(bad.pool.available()==12 && !bad.dormant_anchors[0] && !bad.return_only_anchor);
    }
    // [68A4,68BC): 6A94 clears records, FF31AC and the rise gate, then one pickup
    // per non-FFFF kind with densely consumed positions; 6EB6 links P1 then P2.
    sim::PickupTables tables;tables.kinds.fill(0xffff);
    tables.kinds[3]=5;tables.counts[3]=9;tables.kinds[9]=6;tables.counts[9]=2;tables.counts[0]=77;
    tables.positions[0]={0x2d0,0xa0};tables.positions[1]={0x370,0xa0};tables.positions[3]={1,2};
    auto tail=prefix_pool(6,99);tail.private_globals=sim::PrivateGlobals{0x1234,5,6};tail.activation_target=sim::EffectId{0,0};
    tail.pickup_records[15]=sim::PickupRecord{sim::EffectId{0,0},4};
    const auto t=sim::initialize_level_setup_tail(tail,tables,{1});
    check(t.pickups==std::vector<sim::EffectId>{{13,1},{12,1}} && t.control_links==std::array<sim::EffectId,2>{sim::EffectId{11,1},sim::EffectId{10,1}});
    check(tail.control_links[0]==t.control_links[0] && tail.control_links[1]==t.control_links[1] && !tail.activation_target && tail.private_globals->rise_gate==0 && tail.private_globals->flags_gate==5);
    check(tail.pickup_records[0]==sim::PickupRecord{{13,1},3} && tail.pickup_records[1]==sim::PickupRecord{{12,1},9} && !tail.pickup_records[2] && !tail.pickup_records[15]);
    const auto& first=std::get<sim::Pickup>(tail.pool.at(t.pickups[0]).object);const auto& second=std::get<sim::Pickup>(tail.pool.at(t.pickups[1]).object);
    check(first.position.x==0x2d0 && first.position.y==0xb0 && first.presentation.words[0]==0x27e && first.countdown==9 && first.record==0 && first.target==900);
    check(second.position.x==0x370 && second.presentation.words[0]==0x284 && second.presentation.counter==1 && second.record==1);
    check(std::holds_alternative<sim::ReturnOnlyObject>(tail.pool.at(t.control_links[0]).object) && !(std::get<sim::ReturnOnlyObject>(tail.pool.at(t.control_links[1]).object).presentation.mode&0x80U));
    // Exhaustion or unknown inheritance at any of the four pops leaves every
    // record, link, clear and the pool untouched.
    for(std::size_t depth=0;depth<4;++depth) {
        auto bad=prefix_pool(depth,99);bad.private_globals=sim::PrivateGlobals{0x1234,5,6};bad.activation_target=sim::EffectId{0,0};
        const auto before=bad.pool.free_stack();rejects([&]{sim::initialize_level_setup_tail(bad,tables,{1});});
        check(bad.pool.free_stack()==before && bad.private_globals->rise_gate==0x1234 && bad.activation_target && !bad.control_links[0] && !bad.pickup_records[0]);
    }
    for(std::size_t unknown=0;unknown<4;++unknown) {
        auto bad=prefix_pool(4,unknown);rejects([&]{sim::initialize_level_setup_tail(bad,tables,{1});});check(bad.pool.available()==4 && !bad.control_links[1]);
    }
    // No pickups at all still clears, then links both players.
    sim::PickupTables blank;blank.kinds.fill(0xffff);auto empty=prefix_pool(2,99);
    const auto e=sim::initialize_level_setup_tail(empty,blank,{1});check(e.pickups.empty() && empty.pool.available()==0);
    rejects([&]{sim::initialize_control_link(empty,2);});
    // [68BC,68C4): 7DB8 message selection through CB72's signed priority gate,
    // then 6EF0's gate. Two pickup kinds select MIX THOSE FRUIT.
    auto message_world=[&](std::uint16_t two_player,std::uint16_t returned,std::uint16_t pair,std::uint8_t priority) {
        auto w=prefix_pool(0,99);w.setup_gates=sim::SetupGates{two_player,returned,pair,0xffffe000};
        w.p1_message=sim::ControlMessage{std::nullopt,priority,3};return w;
    };
    using MessageState=std::tuple<std::optional<sim::SetupMessage>,std::uint8_t,std::uint16_t>;
    auto msg=[](const sim::MixedSessionState& w){return MessageState{w.p1_message->message,w.p1_message->priority,w.setup_gates->fruit_returned};};
    for(auto [priority,accepted]:{std::pair{std::uint8_t{0x10},true},std::pair{std::uint8_t{0x64},true},std::pair{std::uint8_t{0x80},true},std::pair{std::uint8_t{0x65},false},std::pair{std::uint8_t{0x7f},false}}) {
        auto w=message_world(0,0,0,priority);const auto r=sim::continue_level_setup(w,tables);
        check(r.selected==sim::SetupMessage::mix_those_fruit && bool(r.clear)==accepted);
        if(accepted)check(msg(w)==MessageState{sim::SetupMessage::mix_those_fruit,0x64,0} && r.clear->vram==static_cast<std::uint16_t>(0xe000+14+(3<<7)));
        else check(msg(w)==MessageState{std::nullopt,priority,0});
    }
    auto back=message_world(0,7,0,0);const auto rb=sim::continue_level_setup(back,blank);
    check(rb.selected==sim::SetupMessage::fruit_returned && msg(back)==MessageState{sim::SetupMessage::fruit_returned,0x64,0});
    // Fewer than two kinds and no returned fruit: no message, so no fields needed.
    auto quiet_world=message_world(0,0,0,0);quiet_world.p1_message.reset();
    check(!sim::continue_level_setup(quiet_world,blank).selected && !quiet_world.p1_message);
    auto wrap=message_world(0,0,0,0);wrap.p1_message->row=0x1ff;wrap.setup_gates->message_tilemap=0x1234fff0;
    check(sim::continue_level_setup(wrap,tables).clear->vram==static_cast<std::uint16_t>(0xfff0+14+(0x1ff<<7)));
    // Two players skip 7DB8 but open 6EF0, whose allocating path rejects with no change.
    for(auto [two,pair]:{std::pair{std::uint16_t{1},std::uint16_t{0}},std::pair{std::uint16_t{0},std::uint16_t{9}}}) {
        auto w=message_world(two,5,pair,0);rejects([&]{sim::continue_level_setup(w,tables);});check(msg(w)==MessageState{std::nullopt,0,5});
    }
    auto none_gates=message_world(0,0,0,0);none_gates.setup_gates.reset();rejects([&]{sim::continue_level_setup(none_gates,tables);});
    auto missing=message_world(0,0,0,0);missing.p1_message.reset();rejects([&]{sim::continue_level_setup(missing,tables);});
    // [68C4,68D4): two pops per open gate, ordered by address. prefix_pool pops
    // 13 then 12, so each pair exchanges: the lower slot is the partner.
    const sim::GatedPairInputs open{{1,0x8000,2,0xffff},sim::Position{7,0xffe7},{5},{6}};
    auto gated=prefix_pool(9,99);const auto g=sim::initialize_gated_pairs(gated,open);
    for(std::size_t i=0;i<4;++i) {
        const auto lower=static_cast<std::size_t>(12-2*i);
        check(g.pairs[i] && g.pairs[i]->partner==sim::EffectId{lower,1} && g.pairs[i]->lead==sim::EffectId{lower+1,1});
        const auto k=static_cast<std::uint16_t>(13-lower);
        check(fields(std::get<sim::ReturnOnlyObject>(gated.pool.at(g.pairs[i]->partner).object))==fields(sim::ReturnOnlyObject{
            {static_cast<std::uint16_t>(i ? 0 : 0xff80),static_cast<std::uint16_t>(i ? 0 : 0xff80)},0,{0x80,{0x21d,static_cast<std::uint16_t>(10+k),static_cast<std::uint16_t>(20+k)},
            static_cast<std::uint8_t>(30+k),static_cast<std::uint8_t>(40+k)},static_cast<std::uint16_t>(900+k),k,{k}}));
        const auto& lead=std::get<sim::GatedLead>(gated.pool.at(g.pairs[i]->lead).object);
        const auto j=static_cast<std::uint16_t>(k-1);
        check(lead.pair==static_cast<sim::GatedPair>(i) && lead.partner==g.pairs[i]->partner && lead.presentation.mode==0x80 && lead.presentation.words[0]==0x21d);
        check(lead.presentation.words[1]==10+j && lead.presentation.counter==30+j && lead.target==900+j && lead.flags==0);
        check(lead.countdown==(i ? 30 : 60) && lead.control.value==(i ? 6U : 5U));
    }
    // 7FBE: (+3C - 8, +3E + 18) wraps; the others are fixed.
    const auto lead_at=[&](std::size_t i){return std::get<sim::GatedLead>(gated.pool.at(g.pairs[i]->lead).object).position;};
    check(lead_at(0).x==0xffff && lead_at(0).y==0xffff && lead_at(1).x==0x310 && lead_at(1).y==0xb0 && lead_at(2).x==0x39c && lead_at(2).y==0x66 && lead_at(3).x==0x234 && lead_at(3).y==0x78);
    check(gated.pool.available()==1);
    // An active lead's handler is not native: the whole phase rolls back.
    {auto copy=gated;sim::TrailRandom unused{};rejects([&]{copy.pool.step({},{},unused,64);});check(copy.pool.slots()[13].generation==1 && copy.pool.available()==1);}
    // Popped lower first: no exchange, same roles, each from its own residue.
    {
        std::vector<sim::PoolObject> objects(14,sim::ExternalReservation{});objects[12]=objects[13]=std::monostate{};
        std::vector<Inherited> inherited(14);inherited[12]=full(1);inherited[13]=full(2);
        sim::MixedSessionState w{p1,sim::MixedPool(objects,{13,12},inherited),{1,99}};
        const auto r=sim::initialize_gated_pairs(w,{{0,1,0,0},std::nullopt,{5},{6}});
        check(r.pairs[1] && r.pairs[1]->partner==sim::EffectId{12,1} && r.pairs[1]->lead==sim::EffectId{13,1} && !r.pairs[0] && !r.pairs[2]);
        check(std::get<sim::ReturnOnlyObject>(w.pool.at(r.pairs[1]->partner).object).target==901 && std::get<sim::GatedLead>(w.pool.at(r.pairs[1]->lead).object).target==902);
    }
    // Closed gates allocate nothing, even from an empty pool.
    auto closed=prefix_pool(0,99);check(std::ranges::none_of(sim::initialize_gated_pairs(closed,{{},std::nullopt,{5},{6}}).pairs,[](const auto& p){return bool(p);}));
    // 7FBE needs the P2 control's +3C/+3E only when its gate is open.
    {auto w=prefix_pool(9,99);rejects([&]{sim::initialize_gated_pairs(w,{{1,0,0,0},std::nullopt,{5},{6}});});check(w.pool.available()==9);}
    // Exhaustion at any pop, unknown inheritance or absent presentation at any
    // member leaves the pool untouched.
    for(std::size_t depth=0;depth<8;++depth) {auto w=prefix_pool(depth,99);rejects([&]{sim::initialize_gated_pairs(w,open);});check(w.pool.available()==depth);}
    for(std::size_t unknown=0;unknown<8;++unknown) {auto w=prefix_pool(8,unknown);rejects([&]{sim::initialize_gated_pairs(w,open);});check(w.pool.available()==8);}
    for(auto drop:{0,1}) {auto f=full(1);f.presentation.reset();rejects([&]{drop ? (void)sim::make_gated_lead(sim::GatedPair::first_fixed,f,{6},{}) : (void)sim::make_gated_partner(sim::GatedPair::first_fixed,f);});}
    std::cout<<"return-only presentation, inactive occupancy, callback rejection, allocation order, pair initialization/exhaustion/inheritance, anchor, dormant initializers, setup prefix/tail/messages/gated pairs and complete rollback passed\n";
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
