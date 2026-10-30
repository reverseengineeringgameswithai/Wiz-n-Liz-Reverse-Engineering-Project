#include "sim/movement.hpp"

#include <iostream>

namespace {
using namespace wiz;
void check(bool v) {if (!v) throw std::runtime_error("movement check failed");}
template<typename F> void rejects(F f) {try {f();} catch (const assets::BankError&) {return;} throw std::runtime_error("invalid movement accepted");}
}
int main() {
    try {
        assets::PatternBank bank;bank.logical_id="base";bank.patterns.resize(1);bank.patterns[0].opaque_record.fill(5);
        assets::SceneResource scene;scene.base_bank_id="base";scene.columns=128;scene.rows=32;scene.cells.resize(4096);
        sim::MotionParameters parameters;sim::TerrainScratch scratch{9,10};
        sim::MotionState state{{200,109},32,0x1357,0x2468,{0xa5,{1,2,3},4,5}};
        const auto result=sim::step_horizontal(scene,bank,state,parameters,scratch);
        check(state.position.x==202 && state.position.y==109 && result.horizontal_steps==2 && !result.airborne_transitions);
        check(state.vertical_motion==0x1357 && state.presentation.mode==0xa5 && scratch.x==86 && scratch.y==4);
        for (auto y:{108,110}) {
            state.position={200,static_cast<std::uint16_t>(y)};
            check(sim::step_right(scene,bank,state,parameters,scratch).airborne_transitions==0 && state.position.y==109);
        }
        state.position={200,105};state.horizontal_speed=32;parameters.positive_limit=1;
        const auto loss=sim::step_horizontal(scene,bank,state,parameters,scratch);
        check(loss.horizontal_steps==2 && loss.airborne_transitions==2 && state.position.x==202 && state.position.y==107);
        check(state.horizontal_speed==1 && state.vertical_motion==0 && state.airborne_delay==65535);
        check(state.update==sim::MotionUpdate::airborne && state.presentation.words==std::array<std::uint16_t,3>{0x3a,0x3c,0x3d});
        check(state.presentation.mode==0x81 && state.presentation.counter==6 && state.presentation.reload==6);
        check(sim::horizontal_step_count(0)==0 && sim::horizontal_step_count(1)==1 && sim::horizontal_step_count(31)==1);
        check(sim::horizontal_step_count(32)==2 && sim::horizontal_step_count(0xffff)==1);
        check(sim::horizontal_step_count(0x8000)==64513 && sim::horizontal_step_count(0x8001)==1024);
        state.position={200,109};state.horizontal_speed=0x8000;scratch={9,10};
        rejects([&]{sim::step_horizontal(scene,bank,state,parameters,scratch);});
        check(state.position.x==200 && state.horizontal_speed==0x8000 && scratch.x==9 && scratch.y==10);
        const auto large=sim::step_horizontal(scene,bank,state,parameters,scratch,65536);
        check(large.horizontal_steps==64513 && state.position.x==1223 && state.position.y==109);
        // Failure after an earlier successful pixel must roll back the whole call.
        state.position={200,359};state.horizontal_speed=32;scratch={9,10};
        // Empty record permits a step to y360, then the next step crosses the map.
        bank.patterns[0].opaque_record.fill(0);
        rejects([&]{sim::step_horizontal(scene,bank,state,parameters,scratch);});
        check(state.position.x==200 && state.position.y==359 && state.horizontal_speed==32 && scratch.x==9 && scratch.y==10);
        state.horizontal_speed=0x8000;parameters.damping_count_minus_one=0;
        sim::damp_horizontal(state,parameters);check(state.horizontal_speed==0x8001);
        parameters.damping_count_minus_one=65535;sim::damp_horizontal(state,parameters);check(state.horizontal_speed==0);
        state.horizontal_speed=0xffff;sim::damp_once(state);check(state.horizontal_speed==0);
        parameters={};state.horizontal_speed=32767;sim::clamp_positive(state,parameters);check(state.horizontal_speed==192);
        state.horizontal_speed=0x8000;sim::clamp_negative(state,parameters);check(state.horizontal_speed==0xff40);
        std::cout<<"movement contact, loop counts, signed limits, state transition, damping and rollback passed\n";return 0;
    } catch (const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
