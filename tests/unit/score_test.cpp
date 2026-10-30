#include "sim/presentation.hpp"
#include <iostream>
namespace {
using namespace wiz;
void check(bool b) { if (!b) throw std::runtime_error("score check failed"); }
template<class F> void rejects(F f) { try { f(); } catch(const assets::BankError&) { return; } throw std::runtime_error("score failed to reject"); }
std::uint32_t packed(unsigned n) { std::uint32_t v=0;for(unsigned s=0;s<32;s+=4) {v|=(n%10)<<s;n/=10;}return v; }
}
int main() {
 try {
    for(unsigned a=0;a<10000;++a) for(unsigned b: {0U,1U,9U,99U,999U,9999U})
        check(sim::add_packed_score(packed(a),packed(b))==packed(a+b));
    check(sim::add_packed_score(0x99999999,1)==0);
    for(unsigned digit=10;digit<16;++digit) for(unsigned shift=0;shift<32;shift+=4)
        rejects([&]{sim::add_packed_score(digit<<shift,0);});
    sim::ScoreState q{0x80000,0x10000,0x20000,0xdeadbeef,8};
    auto result=sim::add_score(q,0x10000);check(result.reward && result.threshold_advances==4 && q.value==0x90000 && q.threshold==0x90000 && q.rewards==9 && q.scratch==0x20000);
    const auto before=q;q.increment=0;auto stuck=q;rejects([&]{sim::add_score(q,0x10000,3);});check(q==stuck);
    q=before;q.value=0x90000;q.threshold=0x99999999;q.increment=0xffffffff;check(!sim::add_score(q,1,0).reward); // Unconsumed increment is opaque.
    assets::PatternBank bank;bank.logical_id="base";bank.patterns.resize(1);bank.patterns[0].opaque_record.fill(5);
    assets::SceneResource scene;scene.base_bank_id="base";scene.columns=128;scene.rows=32;scene.cells.resize(4096);
    sim::ActorState a;a.motion.position={200,109};a.motion.presentation.mode=128;a.motion.update=sim::MotionUpdate::exit_tally;a.service=sim::ActorService::return_only;
    sim::ActorTracking tracking{0,{1,2}};sim::TerrainScratch scratch{9,10};sim::ActionGlobals globals{19,77,88};sim::TransitionState fade;
    sim::TallyState t;t.countdown=65535;t.exit_state=sim::ExitTallyState{1,1,7,2,3};t.score=sim::ScoreState{0x10000,0x10000,0x10000,5,65535};
    sim::ActorBudget budget;auto step=[&]{return sim::step_actor_dispatch(scene,bank,a,tracking,{}, {},scratch,budget,{},&globals,&fade,&t);};
    budget.score_advances=0;const auto score_before=*t.score;rejects(step);check(*t.score==score_before && t.countdown==65535 && t.exit_state->secondary_remaining==1);
    budget.score_advances=1;a.service=sim::ActorService::unsupported;a.motion.horizontal_speed=1;rejects(step);check(*t.score==score_before && t.exit_state->secondary_remaining==1 && scratch.x==9 && a.motion.position.x==200);
    a.service=sim::ActorService::return_only;auto r=step();check(r.sample_requests.size()==1 && r.sample_requests[0].sample==sim::ActionSample::score_reward && r.sound_requests.size()==1 && t.score->rewards==0 && t.exit_state->secondary_remaining==0 && t.countdown==3 && a.motion.update==sim::MotionUpdate::exit_tally);
    t.skip=1;step();check(a.motion.update==sim::MotionUpdate::exit_tally_wait && fade.direction==1);
    std::cout<<"packed decimal arithmetic, threshold/reward ordering, budget and late-service rollback passed\n";
 } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
