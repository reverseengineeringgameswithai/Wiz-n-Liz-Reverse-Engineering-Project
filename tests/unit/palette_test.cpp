#include "sim/presentation.hpp"
#include <iostream>
#include <tuple>

namespace {
using namespace wiz;
void check(bool ok) { if (!ok) throw std::runtime_error("palette check failed"); }
template<class F> void rejects(F f) { try { f(); } catch (const assets::BankError&) { return; } throw std::runtime_error("palette failed to reject"); }
auto fade_fields(const sim::TransitionState& f) { return std::tuple{f.direction,f.countdown,f.reload,f.level,f.curves,f.dirty,f.palette_scope,f.requested_position.x,f.requested_position.y,f.saved_position.x,f.saved_position.y}; }
}
int main() {
    try {
        assets::PatternBank bank;bank.logical_id="base";bank.patterns.resize(1);bank.patterns[0].opaque_record.fill(5);
        assets::SceneResource scene;scene.base_bank_id="base";scene.columns=128;scene.rows=32;scene.cells.resize(4096);
        sim::ActorState a;a.motion.position={200,109};a.motion.update=sim::MotionUpdate::tally;a.motion.presentation.mode=128;a.service=sim::ActorService::return_only;
        sim::ActorTracking tracking{0,{1,2}};sim::TerrainScratch scratch{9,10};sim::ActionGlobals globals{19,77,88};
        sim::TallyState totals{1,1,0,120,179,0};sim::TransitionState fade;fade.dirty=123;fade.palette_scope=456;fade.saved_position={8,9};
        sim::PalettePreparation palette;palette.colors.fill(0x0246);palette.components.fill({255,254,253});
        auto step=[&]{return sim::step_actor_dispatch(scene,bank,a,tracking,{}, {},scratch,{}, {},&globals,&fade,&totals,&palette);};
        // Late service failure must roll back palette preparation, transition and motion together.
        const auto before=fade_fields(fade);const auto colors=palette.colors;const auto components=palette.components;
        a.service=sim::ActorService::unsupported;a.motion.horizontal_speed=1;
        rejects(step);check(palette.colors==colors && palette.components==components && fade_fields(fade)==before && a.motion.position.x==200 && a.motion.horizontal_speed==1 && tracking.position.x==1 && scratch.x==9 && totals.countdown==120);
        a.service=sim::ActorService::return_only;
        // Preparation is required only when the initial wait has ended. Coasting failure is also atomic.
        rejects([&]{sim::step_actor_dispatch(scene,bank,a,tracking,{}, {},scratch,{}, {},&globals,&fade,&totals);});
        rejects([&]{sim::step_actor_dispatch(scene,bank,a,tracking,{}, {},scratch,{1,0,0}, {},&globals,&fade,&totals,&palette);});
        check(fade_fields(fade)==before && a.motion.position.x==200 && palette.components==components);
        fade.direction=1;
        auto r=sim::step_actor_dispatch(scene,bank,a,tracking,{}, {},scratch,{}, {},&globals,&fade,&totals);
        check(a.motion.position.x==201 && a.motion.horizontal_speed==0 && a.motion.update==sim::MotionUpdate::tally && r.handler_entries==1 && fade.direction==1);
        fade.direction=0;r=step();check(a.motion.update==sim::MotionUpdate::tally_palette_wait && r.handler_entries==1 && totals.countdown==120);
        check(palette.colors==colors && palette.components[0]==std::array<std::uint8_t,3>{8,16,24} && palette.components[15]==palette.components[0]);
        check(fade.direction==65535 && fade.countdown==6 && fade.reload==0 && fade.level==0 && fade.dirty==123 && fade.palette_scope==0 && fade.saved_position.x==8);
        for (int i=0;i<13;++i) { sim::step_transition_timer(fade);r=step();check(a.motion.update==sim::MotionUpdate::tally_palette_wait && totals.countdown==120); }
        sim::step_transition_timer(fade);check(fade.direction==0 && fade.level==14);
        // 5204 needs neither tally nor palette state. It selects 5222 and returns.
        r=sim::step_actor_dispatch(scene,bank,a,tracking,{}, {},scratch,{}, {},&globals,&fade);
        check(a.motion.update==sim::MotionUpdate::tally_wait && r.handler_entries==1 && totals.countdown==120);
        r=step();check(totals.countdown==119 && palette.colors==colors && palette.components[0][0]==8);
        a.motion.update=sim::MotionUpdate::tally_palette_wait;
        rejects([&]{sim::step_actor_dispatch(scene,bank,a,tracking,{}, {},scratch);});
        a.motion.presentation.mode=0;r=sim::step_actor_dispatch(scene,bank,a,tracking,{}, {},scratch);check(r.handler_entries==0);
        std::cout<<"palette triplet order, deferred waits, external timer sequence, missing contexts, budgets and full rollback passed\n";
    } catch (const std::exception& e) { std::cerr<<e.what()<<'\n';return 1; }
}
