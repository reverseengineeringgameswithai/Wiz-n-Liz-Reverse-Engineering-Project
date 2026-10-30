#include "sim/airborne.hpp"

#include <iostream>
#include <tuple>

namespace {
using namespace wiz;
void check(bool value) {if (!value) throw std::runtime_error("airborne check failed");}
template<typename F> void rejects(F f) {try {f();} catch (const assets::BankError&) {return;} throw std::runtime_error("invalid airborne update accepted");}
auto fields(const sim::MotionState& s) {
    return std::tuple{s.position.x,s.position.y,s.horizontal_speed,s.vertical_motion,s.airborne_delay,
        s.presentation.mode,s.presentation.words,s.presentation.counter,s.presentation.reload,s.update,s.flags};
}
}
int main() {
    try {
        assets::PatternBank bank;bank.logical_id="base";bank.patterns.resize(1);bank.patterns[0].opaque_record.fill(5);
        assets::SceneResource scene;scene.base_bank_id="base";scene.columns=128;scene.rows=32;scene.cells.resize(4096);
        sim::AirborneParameters parameters;sim::TerrainScratch scratch{9,10};
        sim::MotionState state{{200,109},0,0,65535,{0xa5,{1,2,3},4,5},sim::MotionUpdate::airborne,0};
        auto result=sim::step_airborne(scene,bank,state,parameters,{},scratch);
        check(state.position.y==109 && state.vertical_motion==65532 && state.airborne_delay==65534);
        check(state.update==sim::MotionUpdate::idle_left && result.landings==1 && result.immediate_continuation && result.settle_calls==1);
        check(state.presentation.mode==128 && state.presentation.words==std::array<std::uint16_t,3>{2,0,5});
        check(state.presentation.counter==4 && state.presentation.reload==4);
        const auto idle=fields(state);
        rejects([&]{sim::step_airborne(scene,bank,state,parameters,{},scratch);});check(fields(state)==idle);
        state.update=sim::MotionUpdate::airborne;state.airborne_delay=32768;state.vertical_motion=0;
        result=sim::step_airborne(scene,bank,state,parameters,{255,0,0,0},scratch);
        check(state.airborne_delay==32767 && state.vertical_motion==1 && state.position.y==108 && state.update==sim::MotionUpdate::airborne);
        // Whole-call rollback after damping, delay, flags, and scratch can change.
        state={{200,107},0,0,65535,{0xa5,{1,2,3},4,5},sim::MotionUpdate::airborne,0xa5a5};scratch={9,10};
        auto before=fields(state);
        rejects([&]{sim::step_airborne(scene,bank,state,parameters,{},scratch,{1024,0});});
        check(fields(state)==before && scratch.x==9 && scratch.y==10);
        // Acceleration wraps to 8000 after damping; reject the large loop atomically.
        state.horizontal_speed=0x7ffc;parameters.acceleration=8;before=fields(state);
        rejects([&]{sim::step_airborne(scene,bank,state,parameters,{0,0,1,0},scratch);});
        check(fields(state)==before && scratch.x==9 && scratch.y==10);
        parameters={};state.position={200,361};state.horizontal_speed=0;before=fields(state);
        rejects([&]{sim::step_airborne(scene,bank,state,parameters,{},scratch);});check(fields(state)==before);
        state.position={200,109};state.horizontal_speed=32768;before=fields(state);
        rejects([&]{sim::step_airborne_horizontal(scene,bank,state,parameters,scratch);});check(fields(state)==before);
        result=sim::step_airborne_horizontal(scene,bank,state,parameters,scratch,65536);
        check(state.position.x==1223 && result.horizontal_steps==64513 && !result.horizontal_contact);
        state.position={200,110};state.horizontal_speed=32;
        result=sim::step_airborne_horizontal(scene,bank,state,parameters,scratch);
        check(state.position.x==202 && state.position.y==109 && state.horizontal_speed==20 && result.horizontal_steps==2);
        check(!result.horizontal_contact && scratch.x==86 && scratch.y==3);
        state.position={200,109};state.horizontal_speed=0;state.vertical_motion=0;state.update=sim::MotionUpdate::airborne_fall;state.flags=0xffff;
        result=sim::step_airborne(scene,bank,state,parameters,{0,1,1,0},scratch);
        check(state.horizontal_speed==0xfff4 && state.position.x==199 && state.flags==0xf7ff && state.update==sim::MotionUpdate::ground_left);
        check(result.landings==1 && !result.immediate_continuation);
        for (const auto pair : {std::pair{std::uint16_t(0),std::size_t(0)}, {1,0},{32767,0},{32768,4096},{65527,2},{65528,1},{65535,1}})
            check(sim::airborne_downward_count(pair.first)==pair.second);
        std::cout<<"airborne ordering, signed edges, landing continuations, budgets and rollback passed\n";return 0;
    } catch (const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
