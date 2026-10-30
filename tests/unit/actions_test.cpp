#include "sim/presentation.hpp"
#include <iostream>
#include <tuple>

namespace {
using namespace wiz;
void check(bool ok) { if (!ok) throw std::runtime_error("action check failed"); }
template<class F> void rejects(F f) {try {f();} catch(const assets::BankError&) {return;} throw std::runtime_error("action failed to reject");}
auto fields(const sim::ActorState& a) {
    const auto& m=a.motion;const auto& p=m.presentation;
    return std::tuple{m.position.x,m.position.y,m.horizontal_speed,m.vertical_motion,m.airborne_delay,m.flags,m.update,
        p.mode,p.words,p.counter,p.reload,a.callback,a.presentation_target,a.presentation_cycles};
}
sim::ActorState release(bool right) {
    sim::ActorState a;a.motion.position={200,109};a.motion.flags=right ? 0x800 : 0;
    a.motion.presentation={0x87,{31,30,35},1,2};a.motion.update=sim::MotionUpdate::up_release;
    a.presentation_target=31;a.presentation_cycles=0xabcd;a.callback=sim::PresentationCallback::action_idle;
    return a;
}
}
int main() {
    try {
        assets::PatternBank bank;bank.logical_id="base";bank.patterns.resize(1);bank.patterns[0].opaque_record.fill(5);
        assets::SceneResource scene;scene.base_bank_id="base";scene.columns=128;scene.rows=32;scene.cells.resize(4096);
        sim::ActorParameters p;sim::ActionGlobals globals{19,65535,12};sim::TerrainScratch scratch{9,10};
        for (bool right:{false,true}) {
            auto a=release(right);auto result=sim::step_scheduled_actor(scene,bank,a,p,{},scratch,{}, {},&globals);
            check(a.motion.update==(right ? sim::MotionUpdate::idle_right : sim::MotionUpdate::idle_left));
            check(result.handler_entries==2 && result.settle_calls==2 && a.presentation_cycles==0xabcd);
            a=release(right);sim::ActorInput input;input.jump=1;
            result=sim::step_scheduled_actor(scene,bank,a,p,input,scratch,{}, {},&globals);
            check(result.sound_requests.size()==2 && result.settle_calls==2 && a.motion.position.y==102);
            check(a.motion.airborne_delay==8 && a.motion.vertical_motion==30 && a.motion.flags==(right ? 0x800 : 0));
            // Context-free presentation cannot silently discard idle's effects.
            a=release(right);const auto before=fields(a);rejects([&]{sim::step_presentation(a);});check(fields(a)==before);
        }
        // Hold -> final held frame -> release -> immediate idle callback.
        sim::ActorState a;a.motion.position={200,109};a.motion.update=sim::MotionUpdate::idle_left;a.motion.presentation.mode=0x80;
        sim::ActorInput input;input.down=1;
        auto result=sim::step_scheduled_actor(scene,bank,a,p,input,scratch);
        check(a.motion.update==sim::MotionUpdate::down_hold && result.settle_calls==0);
        for (int i=0;i<15;++i) sim::step_scheduled_actor(scene,bank,a,p,input,scratch);
        check(a.motion.presentation.mode==0x80 && a.motion.presentation.words[0]==41);
        input={};sim::step_scheduled_actor(scene,bank,a,p,input,scratch);
        check(a.motion.update==sim::MotionUpdate::down_release && a.presentation_target==37);
        for (int i=0;i<10;++i) result=sim::step_scheduled_actor(scene,bank,a,p,input,scratch);
        check(a.motion.update==sim::MotionUpdate::idle_left && result.settle_calls==2);
        // Hold jump defers exactly one invocation, preserving the animation.
        a.motion.update=sim::MotionUpdate::up_hold;input.jump=1;const auto presentation=a.motion.presentation;
        result=sim::step_actor(scene,bank,a,p,input,scratch); // Jump precedes shared-global reads.
        check(a.motion.update==sim::MotionUpdate::jump_entry && result.sound_requests.empty() && result.settle_calls==0);
        check(a.motion.presentation.words==presentation.words);
        result=sim::step_actor(scene,bank,a,p,input,scratch);
        check(result.sound_requests.size()==2 && a.motion.airborne_delay==9);
        // Callback can publish a request before the wrapper's next call fails.
        // The outer transaction must roll back every owner and shared state.
        a=release(true);input={};input.up=1;input.raw_buttons=0xbf;scratch={9,10};globals={19,65535,12};
        sim::ReversalEffects effects(2);const auto before=fields(a);
        rejects([&]{sim::step_scheduled_actor(scene,bank,a,p,input,scratch,{2,1024,4096},{&effects,{1}},&globals);});
        check(fields(a)==before && globals.cooldown==65535 && globals.interval==12 && scratch.x==9 && scratch.y==10);
        check(effects.available()==2);
        result=sim::step_scheduled_actor(scene,bank,a,p,input,scratch,{}, {&effects,{1}},&globals);
        check(result.sample_requests.size()==1 && globals.cooldown==2 && globals.interval==15 && a.motion.update==sim::MotionUpdate::up_hold);
        // A stale global timer is never advanced by the actor, and held action
        // keeps position/speed untouched even with directions/drop asserted.
        a.motion.horizontal_speed=0x8000;input.down=input.left=input.drop=255;
        const auto x=a.motion.position.x,y=a.motion.position.y;
        result=sim::step_actor(scene,bank,a,p,input,scratch,{}, {},&globals);
        check(result.sample_requests.empty() && a.motion.horizontal_speed==0x8000 && a.motion.position.x==x && a.motion.position.y==y);
        globals={19,65535,9};input.up=0;
        result=sim::step_actor(scene,bank,a,p,input,scratch,{}, {},&globals);
        check(result.sample_requests.size()==1 && globals.cooldown==0 && globals.interval==12 && a.motion.update==sim::MotionUpdate::up_release);
        std::cout<<"up/down lifetimes, deferred jumps, callback double execution and shared rollback passed\n";
    } catch (const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
