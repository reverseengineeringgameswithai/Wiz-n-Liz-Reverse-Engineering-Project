#include "sim/presentation.hpp"
#include <iostream>

namespace {
using namespace wiz;
void check(bool ok) { if (!ok) throw std::runtime_error("bonus check failed"); }
template<class F> void rejects(F f) { try { f(); } catch (const assets::BankError&) { return; } throw std::runtime_error("bonus failed to reject"); }
sim::BonusSlots slots() { return {{0,0,0,0,0,65535},{11,12,13,14,15,0},6,1}; }
}
int main() {
    try {
        auto s=slots();auto r=sim::allocate_bonus(s);check(s.assigned==std::vector<std::uint16_t>({11,12,13,14,15,65535}) && s.cursor==6 && r.probes==10);
        check(r.assignments==std::vector<sim::BonusAssignment>({{4,15},{3,14},{2,13},{1,12},{0,11}}));
        r=sim::allocate_bonus(s);check(r.assignments.empty() && r.probes==6);
        s=slots();s.assigned={11,12,13,0,0,65535};r=sim::allocate_bonus(s);check(r.assignments.size()==2 && s.cursor==3 && r.probes==16);
        s={{0,65535},{0,0},1,0};r=sim::allocate_bonus(s);check(r.assignments.size()==5 && s.assigned[0]==0 && r.probes==14);
        s={{0,65535},{65535,0},1,65535};r=sim::allocate_bonus(s);check(r.assignments.size()==1 && s.cursor==0 && r.probes==3);
        // A sentinel may end before any count/choice access. Scan past extent rejects.
        s={{65535},{},0,12};r=sim::allocate_bonus(s,1);check(r.assignments.empty() && s.cursor==12);
        s={{1,2},{},0,0};rejects([&]{sim::allocate_bonus(s);});check(s.assigned[0]==1);
        s=slots();s.count=0;rejects([&]{sim::allocate_bonus(s);});check(s.cursor==1 && s.assigned[4]==0);
        s.count=7;rejects([&]{sim::allocate_bonus(s);});
        // Availability sees an empty entry outside selection count: original search cycles.
        s={{1,0,65535},{10,11,0},1,0};rejects([&]{sim::allocate_bonus(s,12);});check(s.cursor==0);
        // Budget expires after four internal successes; no assignments become visible.
        s=slots();rejects([&]{sim::allocate_bonus(s,9);});check(s.assigned==slots().assigned && s.cursor==1);
        // Native logical tables can exceed the original adapter's eleven-word region.
        s.assigned.assign(100,0);s.assigned.back()=65535;s.choices.assign(100,123);s.count=100;
        r=sim::allocate_bonus(s);check(r.assignments.size()==5);
        assets::PatternBank bank;bank.logical_id="base";bank.patterns.resize(1);bank.patterns[0].opaque_record.fill(5);
        assets::SceneResource scene;scene.base_bank_id="base";scene.columns=128;scene.rows=32;scene.cells.resize(4096);
        sim::ActorState a;a.motion.position={200,109};a.motion.update=sim::MotionUpdate::tally;a.motion.presentation.mode=128;a.motion.horizontal_speed=1;a.service=sim::ActorService::unsupported;
        sim::ActorTracking tracking{0,{1,2}};sim::TerrainScratch scratch{9,10};sim::ActionGlobals globals{19,77,88};
        sim::TallyState totals{0,0,0,120,179,0,slots()};sim::ActorInput input;input.start=255;input.raw_buttons=0x10;
        auto step=[&]{return sim::step_actor_dispatch(scene,bank,a,tracking,{},input,scratch,{}, {},&globals,nullptr,&totals);};
        rejects(step);check(totals.special_gate==0 && totals.bonus->assigned==slots().assigned && totals.bonus->cursor==1 && a.motion.position.x==200 && a.motion.horizontal_speed==1 && scratch.x==9 && tracking.position.x==1 && globals.mode==19);
        a.service=sim::ActorService::return_only;
        rejects([&]{sim::step_actor_dispatch(scene,bank,a,tracking,{},input,scratch,{32,1024,4096,9}, {},&globals,nullptr,&totals);});
        check(totals.special_gate==0 && a.motion.position.x==200);
        auto result=step();check(result.bonus_assignments.size()==5 && result.sample_requests.size()==1 && totals.special_gate==65535 && globals.mode==3 && a.motion.position.x==201);
        result=step();check(result.bonus_assignments.empty() && result.sample_requests.empty()); // Gate suppresses held input.
        totals.special_gate=0;totals.bonus.reset();rejects(step);check(totals.special_gate==0);
        std::cout<<"bonus order, partial/full exhaustion, word cursor, invalid data, budgets and wrapper rollback passed\n";
    } catch (const std::exception& e) { std::cerr<<e.what()<<'\n';return 1; }
}
