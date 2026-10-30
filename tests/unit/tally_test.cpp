#include "sim/presentation.hpp"
#include <iostream>
#include <tuple>

namespace {
using namespace wiz;
void check(bool ok) { if (!ok) throw std::runtime_error("tally check failed"); }
template<class F> void rejects(F f) { try { f(); } catch (const assets::BankError&) { return; } throw std::runtime_error("tally failed to reject"); }
auto fields(const sim::TallyState& t) { return std::tuple{t.palette_gate,t.remaining,t.skip,t.countdown,t.credit,t.special_gate}; }
}
int main() {
    try {
        assets::PatternBank bank;bank.logical_id="base";bank.patterns.resize(1);bank.patterns[0].opaque_record.fill(5);
        assets::SceneResource scene;scene.base_bank_id="base";scene.columns=128;scene.rows=32;scene.cells.resize(4096);
        sim::ActorState a;a.motion.position={200,109};a.motion.update=sim::MotionUpdate::tally;a.motion.presentation.mode=128;a.service=sim::ActorService::return_only;
        sim::ActorTracking tracking{0,{1,2}};sim::TerrainScratch scratch{9,10};sim::ActorInput input;sim::ActionGlobals globals{19,77,88};
        sim::TallyState totals{0,1,0,0,65534,0};
        auto step=[&]{return sim::step_actor_dispatch(scene,bank,a,tracking,{},input,scratch,{}, {},&globals,nullptr,&totals);};
        auto r=step();check(totals.countdown==65535 && totals.remaining==1 && r.sound_requests.empty());
        r=step();check(totals.remaining==0 && totals.credit==1 && totals.countdown==3 && r.sound_requests.size()==1 && globals.mode==19);
        r=step();check(r.sound_requests.empty() && globals.mode==19 && totals.countdown==3);
        input.start=255;r=step();check(globals.mode==3 && a.motion.update==sim::MotionUpdate::tally);
        totals={0,2,0,120,179,0};globals.mode=19;r=step();check(totals.skip==65535 && totals.remaining==1 && totals.credit==180 && totals.countdown==3);
        r=step();check(totals.remaining==1 && totals.countdown==2 && r.sound_requests.empty());
        // Late service failure undoes actor movement, consumed units, sound and shared state.
        totals={0,1,0,65535,0,0};input.start=0;a.motion.horizontal_speed=1;a.service=sim::ActorService::unsupported;
        auto before=fields(totals);const auto position=a.motion.position;tracking.position={1,2};scratch={9,10};
        rejects(step);check(fields(totals)==before && a.motion.position.x==position.x && a.motion.horizontal_speed==1 && scratch.x==9 && scratch.y==10 && tracking.position.x==1 && globals.mode==19);
        a.service=sim::ActorService::return_only;
        // Both unsupported paths must reject transactionally, including after coasting.
        totals.palette_gate=1;before=fields(totals);rejects(step);check(fields(totals)==before && a.motion.horizontal_speed==1);
        totals={0,0,0,120,0,0};input.start=255;input.raw_buttons=0x10;before=fields(totals);
        rejects(step);check(fields(totals)==before && a.motion.position.x==position.x && scratch.x==9 && tracking.position.x==1 && globals.mode==19);
        // Missing context and exhausted budgets cannot expose partial changes.
        rejects([&]{sim::step_actor_dispatch(scene,bank,a,tracking,{},input,scratch);});
        totals.remaining=1;input.start=0;
        rejects([&]{sim::step_actor_dispatch(scene,bank,a,tracking,{},input,scratch,{1,0,0},{},&globals,nullptr,&totals);});
        check(totals.remaining==1 && a.motion.horizontal_speed==1 && scratch.x==9);
        // The direct common entry ignores the palette gate. Inactive wrappers invoke neither path.
        a.motion.horizontal_speed=0;a.motion.update=sim::MotionUpdate::tally_wait;totals.palette_gate=65535;r=step();check(totals.countdown==119);
        a.motion.presentation.mode=0;a.motion.update=sim::MotionUpdate::tally;before=fields(totals);r=step();check(fields(totals)==before && r.handler_entries==0);
        std::cout<<"tally ordering, deferred completion, wrapping credit, shared skip, rollback and unsupported paths passed\n";
    } catch (const std::exception& e) { std::cerr<<e.what()<<'\n';return 1; }
}
