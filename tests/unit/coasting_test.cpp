#include "sim/presentation.hpp"
#include <iostream>
#include <tuple>

namespace {
using namespace wiz;
void check(bool ok) { if (!ok) throw std::runtime_error("coasting check failed"); }
template<class F> void rejects(F f) { try { f(); } catch (const assets::BankError&) { return; } throw std::runtime_error("coasting failed to reject"); }
auto fields(const sim::ActorState& a) {
    const auto& m=a.motion;const auto& p=m.presentation;
    return std::tuple{m.position.x,m.position.y,m.horizontal_speed,m.vertical_motion,m.airborne_delay,m.flags,m.update,
        p.mode,p.words,p.counter,p.reload,a.presentation_target,a.presentation_cycles,a.callback,a.service};
}
}
int main() {
    try {
        assets::PatternBank bank;bank.logical_id="base";bank.patterns.resize(1);bank.patterns[0].opaque_record.fill(5);
        assets::SceneResource scene;scene.base_bank_id="base";scene.columns=128;scene.rows=32;scene.cells.resize(4096);
        sim::ActorState a;a.motion={{200,109},32,32768,65535,{255,{542,123,456},1,3},sim::MotionUpdate::ground_left,65535};
        a.presentation_target=542;a.presentation_cycles=9;a.callback=sim::PresentationCallback::enter_airborne;a.service=sim::ActorService::return_only;
        sim::ActorTracking tracking{0,{1,2}};auto expected=a;
        expected.motion.presentation.mode=128;expected.motion.presentation.words[0]=541;expected.motion.update=sim::MotionUpdate::coast;
        sim::begin_coasting(a,tracking);check(fields(a)==fields(expected) && tracking.selector==65535 && tracking.position.x==1 && tracking.position.y==2);
        sim::TerrainScratch scratch{9,10};sim::ActorInput input;input.jump=input.drop=input.up=input.down=input.left=input.right=255;input.raw_buttons=0;
        // No action/transition globals required; held inputs and facing do not redirect this handler.
        auto result=sim::step_actor_dispatch(scene,bank,a,tracking,{},input,scratch);
        check(result.handler_entries==1 && result.horizontal_steps==2 && result.settle_calls==0 && result.sound_requests.empty() && result.sample_requests.empty());
        check(a.motion.update==sim::MotionUpdate::coast && a.motion.position.x==202 && a.motion.position.y==108 && a.motion.horizontal_speed==28);
        check(a.motion.vertical_motion==32768 && a.motion.airborne_delay==65535 && a.callback==sim::PresentationCallback::enter_airborne);
        check(tracking.position.x==0xff80 && tracking.position.y==0xff80);
        // A late service failure must undo coasting, scratch and tracking.
        a.service=sim::ActorService::unsupported;scratch={9,10};tracking.position={1,2};auto before=fields(a);
        rejects([&]{sim::step_actor_dispatch(scene,bank,a,tracking,{},input,scratch);});
        check(fields(a)==before && scratch.x==9 && scratch.y==10 && tracking.position.x==1 && tracking.position.y==2);
        a.service=sim::ActorService::return_only;before=fields(a);
        rejects([&]{sim::step_actor_dispatch(scene,bank,a,tracking,{},input,scratch,{32,0,4096});});check(fields(a)==before && scratch.x==9);
        // Initializer accepts retained selectors because it never executes them.
        a.motion.update=sim::MotionUpdate::retained;sim::begin_coasting(a,tracking);check(a.motion.update==sim::MotionUpdate::coast);
        a.motion.horizontal_speed=0;a.motion.position={65535,65535};scratch={9,10};
        result=sim::step_actor_dispatch(scene,bank,a,tracking,{},input,scratch,{1,0,0});
        check(result.horizontal_steps==0 && a.motion.position.y==65535 && scratch.x==9 && scratch.y==10);
        std::cout<<"coasting entry retention, deferred motion, context independence, budgets and late rollback passed\n";
    } catch (const std::exception& e) { std::cerr<<e.what()<<'\n';return 1; }
}
