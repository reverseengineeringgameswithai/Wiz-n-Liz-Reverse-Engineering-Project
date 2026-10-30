#include "sim/actor.hpp"
#include <iostream>
#include <tuple>

namespace {
using namespace wiz;
void check(bool b) { if (!b) throw std::runtime_error("actor check failed"); }
auto fields(const sim::ActorState& a) {
    const auto& s=a.motion;
    return std::tuple{s.position.x,s.position.y,s.horizontal_speed,s.vertical_motion,s.airborne_delay,
        s.flags,s.update,s.presentation.mode,s.presentation.words,s.presentation.counter,s.presentation.reload,
        a.presentation_target,a.presentation_cycles,a.callback};
}
template<class F> void rejects(F f) {try {f();} catch(const assets::BankError&) {return;} throw std::runtime_error("actor accepted invalid path");}
}
int main() {
    try {
        assets::PatternBank bank;bank.logical_id="base";bank.patterns.resize(1);bank.patterns[0].opaque_record.fill(5);
        assets::SceneResource scene;scene.base_bank_id="base";scene.columns=128;scene.rows=32;scene.cells.resize(4096);
        sim::ActorParameters p;sim::TerrainScratch scratch{9,10};
        sim::ActorState state;auto& s=state.motion;s.position={200,109};s.update=sim::MotionUpdate::idle_right;s.flags=0x800;
        sim::ActorInput input;input.right=255;
        auto result=sim::step_actor(scene,bank,state,p,input,scratch);
        check(s.update==sim::MotionUpdate::ground_right && s.position.x==200 && s.horizontal_speed==0);
        result=sim::step_actor(scene,bank,state,p,input,scratch);check(s.position.x==201 && s.horizontal_speed==8);
        input.jump=255;result=sim::step_actor(scene,bank,state,p,input,scratch);
        check(s.update==sim::MotionUpdate::airborne && s.vertical_motion==29 && s.airborne_delay==9 && s.position.y==105);
        check(result.sound_requests.size()==2 && result.handler_entries==2);
        result=sim::step_actor(scene,bank,state,p,input,scratch);check(s.vertical_motion==30 && s.airborne_delay==8 && result.sound_requests.empty());
        input.jump=0;result=sim::step_actor(scene,bank,state,p,input,scratch);check(s.vertical_motion==26 && s.airborne_delay==7);
        input={};input.left=1;result=sim::step_actor(scene,bank,state,p,input,scratch);check(!(s.flags&0x800));
        s.position={200,109};s.horizontal_speed=0;s.vertical_motion=0;s.update=sim::MotionUpdate::airborne_fall;
        result=sim::step_actor(scene,bank,state,p,{},scratch);
        check(s.update==sim::MotionUpdate::idle_left && result.handler_entries==2 && result.settle_calls==2);
        // Failure after landing and idle effects must roll back the entire call.
        s.update=sim::MotionUpdate::airborne_fall;s.vertical_motion=0;scratch={9,10};auto before=fields(state);
        input={};input.up=1;
        rejects([&]{sim::step_actor(scene,bank,state,p,input,scratch);});check(fields(state)==before && scratch.x==9 && scratch.y==10);
        rejects([&]{sim::step_actor(scene,bank,state,p,{},scratch,{1,1024,4096});});check(fields(state)==before && scratch.x==9);
        // A query with bit 15 set cancels dropping, but still updates scratch.
        s.update=sim::MotionUpdate::idle_right;for(auto& cell:scene.cells) cell.source_word=0x8000;
        input={};input.drop=1;result=sim::step_actor(scene,bank,state,p,input,scratch);check(s.update==sim::MotionUpdate::idle_right && s.position.y==109);
        // Fast reversal's allocation is rejected after the drop query too.
        s.update=sim::MotionUpdate::fast_right;input.left=1;before=fields(state);scratch={9,10};
        rejects([&]{sim::step_actor(scene,bank,state,p,input,scratch);});check(fields(state)==before && scratch.x==9 && scratch.y==10);
        // No sound effects publish and no state commits if jump exceeds motion budget.
        s.update=sim::MotionUpdate::ground_right;s.horizontal_speed=64;input={};input.jump=1;before=fields(state);
        rejects([&]{sim::step_actor(scene,bank,state,p,input,scratch,{32,0,4096});});check(fields(state)==before && scratch.x==9);
        // Deliberate landing/jump cycle has a bounded failure, not an endless call.
        s.update=sim::MotionUpdate::idle_right;s.horizontal_speed=0;p.jump_impulse=0xffff;p.airborne.gravity=0;p.jump_delay=0;
        before=fields(state);rejects([&]{sim::step_actor(scene,bank,state,p,input,scratch,{4,1024,4096});});check(fields(state)==before);
        std::cout<<"actor sequences, priorities, same-call landing, effects, budgets and rollback passed\n";
    } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
