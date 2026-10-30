#include "sim/presentation.hpp"
#include <iostream>
namespace {
using namespace wiz;
void check(bool ok) { if (!ok) throw std::runtime_error("exit tally check failed"); }
template<class F> void rejects(F f) { try { f(); } catch (const assets::BankError&) { return; } throw std::runtime_error("exit tally failed to reject"); }
}
int main() {
 try {
    assets::PatternBank bank;bank.logical_id="base";bank.patterns.resize(1);bank.patterns[0].opaque_record.fill(5);
    assets::SceneResource scene;scene.base_bank_id="base";scene.columns=128;scene.rows=32;scene.cells.resize(4096);
    sim::ActorState a;a.motion.position={200,109};a.motion.presentation.mode=128;a.motion.update=sim::MotionUpdate::exit_tally;a.service=sim::ActorService::return_only;
    sim::ActorTracking tracking{0,{1,2}};sim::TerrainScratch scratch{9,10};sim::ActionGlobals globals{19,77,88};
    sim::TransitionState transition;transition.requested_position={65535,32768};transition.saved_position={8,9};
    sim::TallyState tally{0,1,0,120,65534,0};tally.exit_state=sim::ExitTallyState{0,0,65535,2,2};
    sim::ActorInput input;input.start=255;
    auto step=[&]{return sim::step_actor_dispatch(scene,bank,a,tracking,{},input,scratch,{}, {},&globals,&transition,&tally);};
    auto r=step();check(tally.remaining==0 && tally.countdown==60 && tally.credit==1 && tally.skip==65535 && r.sound_requests.size()==1 && a.motion.update==sim::MotionUpdate::exit_tally && transition.direction==0 && globals.mode==19);
    r=step();check(a.motion.update==sim::MotionUpdate::exit_tally_wait && transition.direction==1 && transition.level==14 && r.sound_requests.empty() && globals.mode==19);
    step();check(globals.mode==19 && tally.exit_state->marker==65535); // No implicit timer step.
    for (unsigned i=0;i<16;++i) sim::step_transition_timer(transition);
    check(transition.direction==0);step();check(globals.mode==1 && tally.exit_state->marker==0 && transition.saved_position.x==65535 && transition.saved_position.y==32768);
    tally.exit_state->marker=32768;tally.exit_state->selection=3;step();check(tally.exit_state->marker==32768);
    // Completion writes position/marker/mode before the service; all roll back.
    a.service=sim::ActorService::unsupported;transition.saved_position={8,9};tally.exit_state->selection=2;globals.mode=19;a.motion.horizontal_speed=1;
    rejects(step);check(a.motion.position.x==200 && a.motion.horizontal_speed==1 && transition.saved_position.x==8 && tally.exit_state->marker==32768 && globals.mode==19 && scratch.x==9);
    a.service=sim::ActorService::return_only;a.motion.update=sim::MotionUpdate::exit_tally;tally.exit_state->secondary_gate=1;tally.exit_state->secondary_remaining=1;
    rejects(step);check(a.motion.position.x==200 && tally.skip==65535 && tally.exit_state->marker==32768);
    tally.remaining=1;tally.countdown=0;input.start=0;step();check(tally.countdown==65535 && tally.remaining==1); // Secondary branch not reached.
    tally.exit_state.reset();step();check(tally.remaining==0 && tally.countdown==60);rejects(step);
    a.motion.update=sim::MotionUpdate::exit_tally_wait;transition.direction=1;step(); // Busy wait needs no exit fields.
    transition.direction=0;rejects(step);
    std::cout<<"exit tally last-unit/deferred transition, timer separation, equality, context and rollback passed\n";
 } catch (const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
