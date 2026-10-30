#include "sim/presentation.hpp"
#include <iostream>
#include <tuple>

namespace {
using namespace wiz;
void check(bool ok) { if (!ok) throw std::runtime_error("dispatch check failed"); }
template<class F> void rejects(F f) { try { f(); } catch (const assets::BankError&) { return; } throw std::runtime_error("dispatch failed to reject"); }
auto fields(const sim::ActorState& a) {
    const auto& m=a.motion; const auto& p=m.presentation;
    return std::tuple{m.position.x,m.position.y,m.horizontal_speed,m.vertical_motion,m.airborne_delay,m.flags,m.update,
        p.mode,p.words,p.counter,p.reload,a.callback,a.presentation_target,a.presentation_cycles,a.service};
}
sim::ActorState waiting() {
    sim::ActorState a;a.motion.position={200,109};a.motion.update=sim::MotionUpdate::return_only;
    a.motion.presentation={0x87,{542,542,551},2,3};a.callback=sim::PresentationCallback::enter_airborne;
    a.presentation_target=542;a.service=sim::ActorService::return_only;return a;
}
}
int main() {
    try {
        assets::PatternBank bank;bank.logical_id="base";bank.patterns.resize(1);bank.patterns[0].opaque_record.fill(5);
        assets::SceneResource scene;scene.base_bank_id="base";scene.columns=128;scene.rows=32;scene.cells.resize(4096);
        sim::ActorParameters p;sim::TerrainScratch scratch{9,10};sim::ActorTracking tracking{0,{1,2}};
        auto a=waiting();sim::ActorInput input;input.left=input.right=input.jump=input.drop=input.up=input.down=1;
        auto result=sim::step_actor_dispatch(scene,bank,a,tracking,p,input,scratch);
        check(result.handler_entries==1 && result.settle_calls==0 && a.motion.presentation.counter==1);
        check(a.motion.update==sim::MotionUpdate::return_only && tracking.position.x==204 && tracking.position.y==115);
        // The callback itself performs no motion or terrain work.
        auto initialized=a;check(sim::step_presentation(initialized));
        check(initialized.motion.update==sim::MotionUpdate::airborne && initialized.motion.position.y==109);
        check(initialized.motion.vertical_motion==0 && initialized.motion.airborne_delay==65535);
        result=sim::step_actor_dispatch(scene,bank,a,tracking,p,{},scratch);
        check(result.handler_entries==2 && result.settle_calls==2 && result.landings==1 && a.motion.position.y==109 && tracking.position.y==115);
        check(a.motion.update==sim::MotionUpdate::idle_left && a.callback==sim::PresentationCallback::enter_airborne);
        // Inactive bypasses unknown selectors and zero work budgets, but not the tail.
        a=waiting();a.motion.presentation.mode=5;a.motion.update=sim::MotionUpdate::retained;
        a.callback=sim::PresentationCallback::retained;a.service=sim::ActorService::unsupported;
        a.motion.position={65534,65532};const auto inactive=fields(a);
        result=sim::step_actor_dispatch(scene,bank,a,tracking,p,input,scratch,{0,0,0});
        check(fields(a)==inactive && result.handler_entries==0 && tracking.position.x==2 && tracking.position.y==2);
        tracking.selector=65535;sim::step_actor_dispatch(scene,bank,a,tracking,p,input,scratch);
        check(tracking.position.x==0xff80 && tracking.position.y==0xff80);
        // Service failure occurs after action effects; the outer transaction restores all owners.
        a=waiting();a.motion.presentation.mode=128;a.motion.update=sim::MotionUpdate::up_hold;a.service=sim::ActorService::unsupported;
        sim::ActionGlobals globals{19,65535,12};input={};input.up=1;input.raw_buttons=0xbf;
        scratch={9,10};tracking={0,{1,2}};auto before=fields(a);
        rejects([&]{sim::step_actor_dispatch(scene,bank,a,tracking,p,input,scratch,{}, {},&globals);});
        check(fields(a)==before && globals.cooldown==65535 && globals.interval==12 && tracking.position.x==1 && tracking.position.y==2);
        check(scratch.x==9 && scratch.y==10);
        // Allocation performed by a fast reversal is also rolled back at a late service failure.
        a.motion.update=sim::MotionUpdate::fast_right;a.motion.horizontal_speed=160;input={};input.left=1;
        before=fields(a);sim::ReversalEffects effects(1);
        rejects([&]{sim::step_actor_dispatch(scene,bank,a,tracking,p,input,scratch,{}, {&effects,{1}},&globals);});
        check(fields(a)==before && effects.available()==1 && scratch.x==9 && scratch.y==10 && tracking.position.x==1);
        a.service=sim::ActorService::return_only;
        result=sim::step_actor_dispatch(scene,bank,a,tracking,p,input,scratch,{}, {&effects,{1}},&globals);
        check(result.spawned_effects.size()==1 && effects.available()==0 && tracking.position.x==a.motion.position.x+4U);
        a=waiting();before=fields(a);rejects([&]{sim::step_actor_dispatch(scene,bank,a,tracking,p,{},scratch,{0,0,0});});check(fields(a)==before);
        a.motion.update=sim::MotionUpdate::retained;rejects([&]{sim::step_actor_dispatch(scene,bank,a,tracking,p,{},scratch);});
        std::cout<<"complete actor wrapper, callback ordering, inactive tracking, wrap and late rollback passed\n";
    } catch (const std::exception& e) { std::cerr<<e.what()<<'\n';return 1; }
}
