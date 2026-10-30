#include "sim/presentation.hpp"
#include <iostream>
#include <tuple>

namespace {
using namespace wiz;
void check(bool ok) { if (!ok) throw std::runtime_error("transition check failed"); }
template<class F> void rejects(F f) { try { f(); } catch (const assets::BankError&) { return; } throw std::runtime_error("transition failed to reject"); }
auto fields(const sim::TransitionState& s) {
    return std::tuple{s.direction,s.countdown,s.reload,s.level,s.curves,s.dirty,s.palette_scope,
        s.requested_position.x,s.requested_position.y,s.saved_position.x,s.saved_position.y};
}
}
int main() {
    try {
        assets::PatternBank bank;bank.logical_id="base";bank.patterns.resize(1);bank.patterns[0].opaque_record.fill(5);
        assets::SceneResource scene;scene.base_bank_id="base";scene.columns=128;scene.rows=32;scene.cells.resize(4096);
        sim::MotionState m;m.position={200,109};sim::TerrainScratch scratch{9,10};
        check(sim::step_transition_coast(scene,bank,m,scratch,0)==0 && m.position.y==109 && scratch.x==9);
        m.horizontal_speed=1;
        check(sim::step_transition_coast(scene,bank,m,scratch)==1 && m.position.x==201 && m.position.y==108 && m.horizontal_speed==0);
        m.position={200,109};m.horizontal_speed=65535;
        check(sim::step_transition_coast(scene,bank,m,scratch)==1 && m.position.x==199 && m.position.y==108 && m.horizontal_speed==0);
        // Count comes from the original speed; the second pixel still executes.
        m.position={200,109};m.horizontal_speed=32;
        check(sim::step_transition_coast(scene,bank,m,scratch)==2 && m.position.x==202 && m.horizontal_speed==28);
        m.horizontal_speed=32768;scratch={9,10};const auto x=m.position.x;
        rejects([&]{sim::step_transition_coast(scene,bank,m,scratch);});check(m.position.x==x && m.horizontal_speed==32768 && scratch.x==9);
        // First pixel succeeds, next crosses into an unsupported pattern: no partial commit.
        m.position={122,109};m.horizontal_speed=32;scene.cells[1].source_word=1;
        rejects([&]{sim::step_transition_coast(scene,bank,m,scratch);});
        check(m.position.x==122 && m.position.y==109 && m.horizontal_speed==32 && scratch.x==9 && scratch.y==10);
        scene.cells[1].source_word=0;
        sim::TransitionState fade;fade.dirty=123;fade.palette_scope=456;fade.saved_position={8,9};fade.requested_position={10,11};
        sim::start_transition(fade);check(fade.direction==1 && fade.level==14 && fade.dirty==123 && fade.palette_scope==0);
        for (int i=0;i<15;++i) sim::step_transition_timer(fade);
        check(fade.direction==1 && fade.level==0 && fade.countdown==0);
        sim::step_transition_timer(fade);check(fade.direction==0 && fade.dirty==65535);
        fade.direction=65535;fade.level=65535;fade.reload=3;sim::step_transition_timer(fade);
        check(fade.level==1 && fade.countdown==3 && fade.direction==65535);
        fade.countdown=32768;sim::step_transition_timer(fade);check(fade.countdown==32767);
        fade.direction=0;auto frozen=fields(fade);sim::step_transition_timer(fade);check(fields(fade)==frozen);
        sim::ActorState a;a.motion.update=sim::MotionUpdate::transition_start;a.motion.presentation.mode=128;
        a.motion.position={200,109};a.motion.horizontal_speed=1;a.service=sim::ActorService::unsupported;
        sim::ActorTracking tracking{0,{1,2}};sim::ActionGlobals globals{19,65535,12};
        // Late service failure must undo coasting and transition initialization.
        rejects([&]{sim::step_actor_dispatch(scene,bank,a,tracking,{}, {},scratch,{}, {},&globals,&fade);});
        check(fields(fade)==frozen && a.motion.update==sim::MotionUpdate::transition_start && a.motion.position.x==200 && scratch.x==9);
        check(tracking.position.x==1 && globals.mode==19);
        a.service=sim::ActorService::return_only;
        rejects([&]{sim::step_actor_dispatch(scene,bank,a,tracking,{}, {},scratch);});
        auto result=sim::step_actor_dispatch(scene,bank,a,tracking,{}, {},scratch,{}, {},&globals,&fade);
        check(result.handler_entries==1 && result.horizontal_steps==1 && a.motion.update==sim::MotionUpdate::transition_wait);
        check(fade.direction==1 && globals.mode==19 && fade.saved_position.x==8);
        fade.direction=0;frozen=fields(fade);a.service=sim::ActorService::unsupported;
        rejects([&]{sim::step_actor_dispatch(scene,bank,a,tracking,{}, {},scratch,{}, {},&globals,&fade);});
        check(fields(fade)==frozen && globals.mode==19);
        a.service=sim::ActorService::return_only;
        rejects([&]{sim::step_actor_dispatch(scene,bank,a,tracking,{}, {},scratch,{}, {},nullptr,&fade);});
        check(fields(fade)==frozen);
        result=sim::step_actor_dispatch(scene,bank,a,tracking,{}, {},scratch,{}, {},&globals,&fade);
        check(result.handler_entries==1 && result.horizontal_steps==0 && globals.mode==7 && globals.cooldown==65535);
        check(fade.saved_position.x==10 && fade.saved_position.y==11 && a.motion.update==sim::MotionUpdate::transition_wait);
        std::cout<<"transition ordering, fixed coasting budget, terrain failure, timer wrap and late rollback passed\n";
    } catch (const std::exception& e) { std::cerr<<e.what()<<'\n';return 1; }
}
