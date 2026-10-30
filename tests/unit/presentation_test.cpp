#include "sim/presentation.hpp"
#include <iostream>
#include <tuple>

namespace {
using namespace wiz;
void check(bool ok) { if (!ok) throw std::runtime_error("presentation check failed"); }
auto fields(const sim::ActorState& a) {
    const auto& s=a.motion;
    return std::tuple{s.position.x,s.position.y,s.horizontal_speed,s.vertical_motion,s.airborne_delay,
        s.flags,s.update,s.presentation.mode,s.presentation.words,s.presentation.counter,s.presentation.reload,
        a.presentation_target,a.presentation_cycles,a.callback};
}
template<class F> void rejects(F f) { try {f();} catch(const assets::BankError&) {return;} throw std::runtime_error("unexpected success"); }
}
int main() {
    using namespace wiz;
    try {
        assets::PatternBank bank;bank.logical_id="base";bank.patterns.resize(1);bank.patterns[0].opaque_record.fill(5);
        assets::SceneResource scene;scene.base_bank_id="base";scene.columns=128;scene.rows=32;scene.cells.resize(4096);
        sim::ActorState a;auto& m=a.motion;
        m.position={200,109};m.flags=0x800;m.update=sim::MotionUpdate::idle_right;m.presentation.mode=0x80;
        sim::TerrainScratch scratch{9,10};sim::ActorParameters p;sim::ActorInput input;input.left=1;
        sim::step_scheduled_actor(scene,bank,a,p,input,scratch);
        check(m.update==sim::MotionUpdate::turn_left && m.presentation.words[0]==47);
        // Six countdown expiries: 47->46->45->44->43->42->callback.
        // Target arrival alone does not fire; the eighteenth following call does.
        for (unsigned i=0;i<17;++i) {
            sim::step_scheduled_actor(scene,bank,a,p,{},scratch);
            check(m.update==sim::MotionUpdate::turn_left);
        }
        check(m.presentation.words[0]==42 && m.presentation.counter==1);
        sim::step_scheduled_actor(scene,bank,a,p,input,scratch);
        check(m.update==sim::MotionUpdate::ground_left && m.horizontal_speed==65528 && m.position.x==199);
        check(m.presentation.words[0]==2 && m.presentation.counter==4);
        // Right-facing completion selects ground RIGHT before jump priority,
        // and the jump executes immediately in that same scheduled invocation.
        m.presentation={0x87,{42,42,47},1,3};a.presentation_target=42;
        a.callback=sim::PresentationCallback::turn_right;m.update=sim::MotionUpdate::turn_right;
        input={};input.jump=1;
        auto result=sim::step_scheduled_actor(scene,bank,a,p,input,scratch);
        check(m.update==sim::MotionUpdate::airborne && m.airborne_delay==9 && result.sound_requests.size()==2);
        // A failure after presentation completed must roll back callback writes,
        // the countdown and terrain scratch along with the handler's changes.
        m.presentation={0x87,{42,42,47},1,3};m.horizontal_speed=0;a.presentation_target=42;
        auto before=fields(a);scratch={9,10};
        rejects([&]{sim::step_scheduled_actor(scene,bank,a,p,input,scratch,{0,1024,4096});});
        check(fields(a)==before && scratch.x==9 && scratch.y==10);
        a.callback=sim::PresentationCallback::retained;before=fields(a);
        rejects([&]{sim::step_presentation(a);});check(fields(a)==before);
        a.callback=static_cast<sim::PresentationCallback>(99);before=fields(a);
        rejects([&]{sim::step_presentation(a);});check(fields(a)==before);
        // Inactive wrapper suppresses both phases, including an otherwise
        // unsupported callback. Calling the presentation component directly
        // still observes bit 0 only, as does F76C for non-player objects.
        m.presentation.mode=7;before=fields(a);
        result=sim::step_scheduled_actor(scene,bank,a,p,input,scratch,{0,0,0});
        check(fields(a)==before && result.handler_entries==0 && scratch.x==9);
        rejects([&]{sim::step_presentation(a);});check(fields(a)==before);
        // Reload zero is a full 256-tick wrapped countdown, not every tick.
        m.presentation={0x81,{2,0,5},1,0};sim::step_presentation(a);
        check(m.presentation.words[0]==3 && m.presentation.counter==0);
        for (unsigned i=0;i<255;++i) sim::step_presentation(a);
        check(m.presentation.words[0]==3 && m.presentation.counter==1);
        sim::step_presentation(a);check(m.presentation.words[0]==4 && m.presentation.counter==0);
        std::cout<<"presentation timing, callback-before-handler sequences, inactivity and atomic failures passed\n";
    } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
