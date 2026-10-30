#include "sim/mixed_pool.hpp"
#include <iostream>
#include <tuple>
namespace {
using namespace wiz;
void check(bool ok){if(!ok)throw std::runtime_error("table motion check failed");}
template<class F>void rejects(F f){try{f();}catch(const assets::BankError&){return;}throw std::runtime_error("table motion accepted unsupported work");}
auto fields(const sim::TableMotion& o){return std::tuple{o.position.x,o.position.y,o.flags,o.presentation.mode,o.presentation.words,o.presentation.counter,o.presentation.reload,o.target,o.countdown,o.control.value,o.cursor,o.delta_x,o.toggle};}
sim::TableMotion seed(){return {{99,0},0xbeef,{0x81,{7,3,11},2,2},100,14,{123},0,65535,0};}
}
int main(){try{
    auto p=seed();sim::step_table_motion(p,0);
    check(p.position.x==98 && p.position.y==1 && p.countdown==13 && p.cursor==1 && p.toggle==1);
    auto before=p;sim::step_table_motion(p,0);before.toggle=0;check(fields(p)==fields(before));
    // Full cycle restores Y; 24 moving iterations, with alternating idle work.
    p=seed();p.delta_x=1;sim::step_table_motion(p,47);
    check(p.cursor==0 && p.position.y==0 && p.position.x==105 && p.countdown==19 && p.delta_x==65535 && p.toggle==0);
    p=seed();p.cursor=23;p.countdown=0;p.position={0,65535};sim::step_table_motion(p,0);
    check(p.cursor==0 && p.position.y==65535 && p.position.x==65535 && p.countdown==28 && p.delta_x==1);
    sim::step_table_motion(p,1);check(p.position.y==0 && p.position.x==0 && p.cursor==1 && p.countdown==27);
    // The toggle is a full word. Values 2 and 3 both take the motion path.
    p=seed();p.toggle=2;sim::step_table_motion(p,1);
    check(p.position.x==97 && p.position.y==1 && p.cursor==2 && p.countdown==12 && p.toggle==2);
    for(auto [timer,after,delta]:{std::tuple{0,28,1},std::tuple{1,0,65535},std::tuple{32768,32767,65535},std::tuple{32769,28,1}}){
        p=seed();p.countdown=static_cast<std::uint16_t>(timer);sim::step_table_motion(p,0);
        check(p.countdown==after && p.delta_x==delta);
    }
    p=seed();p.delta_x=32768;p.countdown=0;sim::step_table_motion(p,0);check(p.delta_x==32768 && p.position.x==32867);
    p=seed();p.toggle=2;sim::step_table_motion(p,65535,false,65536);check(p.cursor==16 && p.toggle==2); // 65,536, not zero.
    p=seed();before=p;rejects([&]{sim::step_table_motion(p,4096);});check(fields(p)==fields(before));
    rejects([&]{sim::step_table_motion(p,65535,false,65535);});check(fields(p)==fields(before));
    p.cursor=24;before=p;rejects([&]{sim::step_table_motion(p,0);});check(fields(p)==fields(before));
    p=seed();p.presentation.mode=0x85;p.presentation.counter=1;p.target=7;before=p;
    rejects([&]{sim::step_table_motion(p,0,true);});check(fields(p)==fields(before));
    p.presentation.mode=5;p.cursor=999;before=p;sim::step_table_motion(p,65535,true,0);check(fields(p)==fields(before));
    // Retained count changes, followed by a missing-input failure after release.
    sim::PrivateGlobals globals{0,0,0,0};sim::TrailRandom rng{123,456};
    sim::MixedPool good({seed()},{});good.step({},{},rng,1,&globals);globals.table_loop_count=2;
    good.step({},{},rng,1,&globals);const auto& retained=std::get<sim::TableMotion>(good.slots()[0].object);
    check(retained.position.x==97 && retained.cursor==2 && retained.toggle==0);
    auto dying=sim::make_trail_particle({},true);dying.presentation.counter=1;dying.presentation.words[0]=dying.target;
    auto bad=seed();bad.presentation={0x85,{7,3,11},1,2};bad.target=7;
    sim::MixedPool pool({dying,seed(),bad},{});globals.table_loop_count=0;
    rejects([&]{pool.step({},{},rng,3,&globals);});check(pool.available()==0 && rng.state==123 && rng.mirror==456);
    check(fields(std::get<sim::TableMotion>(pool.slots()[1].object))==fields(seed()));
    globals.table_loop_count.reset();rejects([&]{pool.step({},{},rng,3,&globals);});check(pool.available()==0);
    globals.table_loop_count=4096;rejects([&]{pool.step({},{},rng,3,&globals);});check(pool.available()==0);
    globals.table_loop_count=0;rejects([&]{pool.step({},{},rng,1,&globals);});check(pool.available()==0);
    // A late table failure also rolls back P1, banner scratch and a newborn
    // reversal allocation in the containing session transaction.
    assets::PatternBank bank;bank.logical_id="base";bank.patterns.resize(1);bank.patterns[0].opaque_record.fill(5);
    assets::SceneResource scene;scene.base_bank_id="base";scene.columns=128;scene.rows=32;scene.cells.resize(4096);
    sim::P1SessionState p1;p1.actor.motion.position={200,109};p1.actor.motion.presentation.mode=128;
    p1.actor.motion.update=sim::MotionUpdate::fast_right;p1.actor.motion.horizontal_speed=160;
    p1.actor.service=sim::ActorService::return_only;p1.scratch={7,9};
    sim::P1SessionConfig config;config.banner=sim::LevelBannerConfig{sim::Difficulty::apprentice,0,6};
    sim::MixedSessionState world{p1,sim::MixedPool({bad,std::monostate{}},{1}),{123,456},globals};
    sim::ThreeButtonPad held;held.left=true;
    rejects([&]{sim::step_mixed_session(scene,bank,world,config,held);});
    check(world.p1.invocations==0 && world.p1.actor.motion.position.x==200 && world.p1.actor.motion.horizontal_speed==160);
    check(world.p1.actor.motion.update==sim::MotionUpdate::fast_right && world.p1.scratch.x==7 && world.p1.scratch.y==9);
    check(world.p1.control==p1.control && world.pool.free_stack()==std::vector<std::size_t>{1} && world.pool.slots()[1].generation==0);
    check(fields(std::get<sim::TableMotion>(world.pool.slots()[0].object))==fields(bad) && world.random.state==123 && world.random.mirror==456);
    std::cout<<"table cycle, signed wrap, full-word toggle, DBRA, presentation, retained input and pool rollback passed\n";
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
