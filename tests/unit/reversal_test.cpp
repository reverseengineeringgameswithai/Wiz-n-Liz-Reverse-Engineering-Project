#include "sim/presentation.hpp"
#include <iostream>
#include <tuple>

namespace {
using namespace wiz;
void check(bool ok) { if (!ok) throw std::runtime_error("reversal check failed"); }
template<class F> void rejects(F f) { try { f(); } catch (const assets::BankError&) { return; } throw std::runtime_error("unexpected success"); }
auto fields(const sim::ActorState& a) {
    const auto& m=a.motion;const auto& p=m.presentation;
    return std::tuple{m.position.x,m.position.y,m.horizontal_speed,m.vertical_motion,m.airborne_delay,
        m.flags,m.update,p.mode,p.words,p.counter,p.reload,a.callback,a.presentation_target,a.presentation_cycles};
}
}
int main() {
    using namespace wiz;
    try {
        sim::ReversalEffects effects(2);sim::ActorId owner{41};
        auto first=effects.spawn(owner,{65530,65530},sim::ReversalSide::from_right);
        auto second=effects.spawn(owner,{2,65530},sim::ReversalSide::from_left);
        check(effects.at(first).position.x==16 && effects.at(first).position.y==9);
        check(effects.at(second).position.x==65532 && effects.at(second).position.y==10);
        rejects([&]{effects.spawn(owner,{},sim::ReversalSide::from_left);});
        rejects([&]{effects.step(first,{42},{123,456});});
        check(effects.at(first).presentation.counter==2 && effects.available()==0);
        for (unsigned i=0;i<11;++i) check(!effects.step(first,owner,{static_cast<std::uint16_t>(i),100}));
        check(effects.at(first).presentation.words[0]==220 && effects.at(first).presentation.counter==1);
        check(effects.step(first,owner,{20,999}));
        check(effects.at(first).position.x==42 && effects.at(first).position.y==9);
        check(effects.at(first).presentation.mode==0 && effects.available()==1);
        check(!effects.step(first,{},{}));check(effects.available()==1); // No double release.
        auto reused=effects.spawn(owner,{100,200},sim::ReversalSide::from_left);
        check(reused.slot==first.slot && reused.generation!=first.generation);
        rejects([&]{effects.at(first);});
        sim::ReversalEffects empty(0);
        rejects([&]{empty.spawn(owner,{},sim::ReversalSide::from_right);});
        rejects([&]{sim::ReversalEffects too_large(4097);});
        rejects([&]{sim::make_reversal_effect({}, {},sim::ReversalSide::from_right);});
        rejects([&]{sim::make_reversal_effect(owner,{},static_cast<sim::ReversalSide>(9));});
        // A phase walks slot order, even when allocation order is reversed.
        sim::ReversalEffects phase(2);
        auto high=phase.spawn(owner,{100,100},sim::ReversalSide::from_left);
        auto low=phase.spawn(owner,{200,200},sim::ReversalSide::from_right);
        rejects([&]{phase.step_active(owner,{300,400},1);});
        check(phase.at(low).presentation.counter==2 && phase.at(high).position.x==94 && phase.available()==0);
        for (unsigned i=0;i<12;++i) {
            auto updates=phase.step_active(owner,{static_cast<std::uint16_t>(300+i),400},2);
            check(updates.size()==2 && updates[0].id==low && updates[1].id==high);
            check(updates[0].released==(i==11) && updates[1].released==(i==11));
        }
        check(phase.available()==2 && phase.step_active({}, {},0).empty());
        auto reuse=phase.spawn(owner,{},sim::ReversalSide::from_right);
        check(reuse.slot==high.slot && reuse.generation==2);
        // A late ownership failure must undo the earlier slot's successful work.
        sim::ReversalEffects mixed(2);
        high=mixed.spawn({99},{100,100},sim::ReversalSide::from_left);
        low=mixed.spawn(owner,{200,200},sim::ReversalSide::from_right);
        rejects([&]{mixed.step_active(owner,{300,400},2);});
        check(mixed.at(low).presentation.counter==2 && mixed.at(low).position.x==222 && mixed.available()==0);

        assets::PatternBank bank;bank.logical_id="base";bank.patterns.resize(1);bank.patterns[0].opaque_record.fill(5);
        assets::SceneResource scene;scene.base_bank_id="base";scene.columns=128;scene.rows=32;scene.cells.resize(4096);
        for (bool right : {false,true}) {
            sim::ActorState a;auto& m=a.motion;
            m.position={200,109};m.presentation.mode=0x80;m.horizontal_speed=right ? 160 : 65376;
            m.update=right ? sim::MotionUpdate::fast_right : sim::MotionUpdate::fast_left;
            a.presentation_cycles=123;
            sim::ActorInput input;input.left=right;input.right=!right;
            sim::TerrainScratch scratch{9,10};sim::ReversalEffects pool(1);
            auto before=fields(a);
            rejects([&]{sim::step_scheduled_actor(scene,bank,a,{},input,scratch,{}, {&empty,owner});});
            check(fields(a)==before && scratch.x==9 && scratch.y==10);
            // Allocation has succeeded internally before horizontal budget failure.
            rejects([&]{sim::step_scheduled_actor(scene,bank,a,{},input,scratch,{32,0,4096},{&pool,owner});});
            check(fields(a)==before && scratch.x==9 && pool.available()==1);
            auto r=sim::step_scheduled_actor(scene,bank,a,{},input,scratch,{}, {&pool,owner});
            check(r.spawned_effects.size()==1 && pool.available()==0 && r.handler_entries==2);
            check(m.position.x==(right ? 205 : 195) && m.horizontal_speed==(right ? 148 : 65388));
            check(m.update==(right ? sim::MotionUpdate::fast_reverse_left : sim::MotionUpdate::fast_reverse_right));
            check(a.presentation_cycles==123 && pool.at(r.spawned_effects[0]).position.x==(right ? 222 : 194));
            // A press during reversal ignores the acceleration gate, enters
            // the fast jump immediately, and does not allocate another object.
            input.jump=1;input.acceleration_gate=1;
            r=sim::step_scheduled_actor(scene,bank,a,{},input,scratch,{}, {&pool,owner});
            check(m.update==sim::MotionUpdate::airborne && r.sound_requests.size()==2 && r.spawned_effects.empty());
            check(a.callback==(right ? sim::PresentationCallback::fast_jump_right : sim::PresentationCallback::fast_jump_left));
            // Completion callback selects the opposite ground handler within
            // this invocation, retaining unrelated flag bits and cycle count.
            m.position={200,109};m.horizontal_speed=0;m.presentation={0x85,{57,52,57},1,3};
            a.presentation_target=57;a.callback=right ? sim::PresentationCallback::fast_reverse_left : sim::PresentationCallback::fast_reverse_right;
            input.jump=0;input.acceleration_gate=0;
            sim::step_scheduled_actor(scene,bank,a,{},input,scratch);
            check(m.update==(right ? sim::MotionUpdate::ground_left : sim::MotionUpdate::ground_right));
            check(m.horizontal_speed==(right ? 65528 : 8));
        }
        std::cout<<"fast reversal, owned effects, lifetime, reuse and atomic failure checks passed\n";
    } catch(const std::exception& e) { std::cerr<<e.what()<<'\n';return 1; }
}
