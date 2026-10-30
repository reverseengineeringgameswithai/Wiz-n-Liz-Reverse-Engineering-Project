#include "sim/session.hpp"
#include <iostream>
#include <limits>
#include <tuple>

namespace {
using namespace wiz;
void check(bool ok) { if (!ok) throw std::runtime_error("session check failed"); }
template<class F> void rejects(F f) { try {f();} catch(const assets::BankError&) {return;} throw std::runtime_error("session accepted unsupported work"); }
auto fields(const sim::P1SessionState& s) {
    const auto& a=s.actor;const auto& m=a.motion;const auto& p=m.presentation;
    return std::tuple{m.position.x,m.position.y,m.horizontal_speed,m.vertical_motion,m.airborne_delay,m.flags,m.update,
        p.mode,p.words,p.counter,p.reload,a.presentation_target,a.presentation_cycles,a.callback,a.service,
        s.tracking.selector,s.tracking.position.x,s.tracking.position.y,s.scratch.x,s.scratch.y,s.control,s.invocations};
}
}
int main() {
    try {
        // Authored producer examples, including opposed axes and all buttons.
        check(sim::produce_pad_control({})==sim::PadControl{});
        auto c=sim::produce_pad_control({false,false,false,false,true});
        check(c.raw==0xbf && c.any_action==255 && c.jump==0 && c.drop==255 && c.a==255);
        c=sim::produce_pad_control({false,false,false,true,false,true});
        check(c.raw==0xe7 && c.right==255 && c.jump==255 && c.drop==0 && c.b==255);
        c=sim::produce_pad_control({true,true,true,true,true,true,true,true});
        check(c.raw==0 && c.up==0 && c.down==0 && c.left==0 && c.right==0 && c.start==255 && c.jump==255 && c.drop==255);
        c=sim::produce_pad_control({true,false,true,false,false,false,true});
        const auto input=sim::actor_input(c,0x8000);
        check(c.raw==0xda && input.up==255 && input.left==255 && input.jump==255 && input.acceleration_gate==0x8000);
        assets::PatternBank bank;bank.logical_id="base";bank.patterns.resize(1);bank.patterns[0].opaque_record.fill(5);
        assets::SceneResource scene;scene.base_bank_id="base";scene.columns=128;scene.rows=32;scene.cells.resize(4096);
        sim::P1SessionConfig config;
        for (unsigned i=0;i<4;++i) {
            sim::TerrainScratch scratch{0xbeef,0x1234};
            constexpr std::array<std::uint16_t,4> finals{7,15,31,55}, offsets{56,52,54,58};
            const auto difficulty=static_cast<sim::Difficulty>(i);
            auto banner=sim::request_level_banner({difficulty,finals[i],6},scratch);
            check(scratch.x==0xbeef && scratch.y==6 && banner.label==2*i+1 && banner.destination==0xe300 && !banner.number);
            banner=sim::request_level_banner({difficulty,65535,256},scratch);
            check(banner.label==2*i && banner.destination==0x6000 && banner.number==sim::BannerNumberRequest{0,static_cast<std::uint16_t>(0x6000+offsets[i])});
            banner=sim::request_level_banner({difficulty,0,65535},scratch);
            check(banner.destination==0xdf80 && scratch.y==65535 && banner.number->value==1);
        }
        sim::TerrainScratch untouched{10,20};
        rejects([&]{sim::request_level_banner({static_cast<sim::Difficulty>(4),0,6},untouched);});
        check(untouched.x==10 && untouched.y==20);
        for (bool right:{false,true}) {
            sim::P1SessionState s;auto& a=s.actor;auto& m=a.motion;
            m.position={200,109};m.update=right ? sim::MotionUpdate::idle_right : sim::MotionUpdate::idle_left;
            m.flags=right ? 0x800 : 0;m.presentation.mode=128;a.service=sim::ActorService::return_only;s.scratch={9,10};
            sim::ThreeButtonPad pad;pad.right=right;pad.left=!right;
            sim::step_p1_session(scene,bank,s,config,pad);
            check(s.invocations==1 && m.position.x==200 && m.horizontal_speed==0);
            check(m.update==(right ? sim::MotionUpdate::ground_right : sim::MotionUpdate::ground_left));
            sim::step_p1_session(scene,bank,s,config,pad);
            check(m.position.x==(right ? 201 : 199) && m.horizontal_speed==(right ? 8 : 65528));
            pad.b=true;auto r=sim::step_p1_session(scene,bank,s,config,pad);
            check(r.actor.handler_entries==2 && r.actor.sound_requests.size()==2 && m.position.y==105 && m.vertical_motion==29 && m.airborne_delay==9);
            sim::step_p1_session(scene,bank,s,config,pad);check(m.vertical_motion==30 && m.airborne_delay==8);
            pad.b=false;sim::step_p1_session(scene,bank,s,config,pad);check(m.vertical_motion==26 && m.airborne_delay==7);
            pad.left=right;pad.right=!right;sim::step_p1_session(scene,bank,s,config,pad);check(bool(m.flags&0x800)!=right);
            // Seed an authored landing boundary, then check its immediate idle.
            m.position={200,109};m.horizontal_speed=0;m.vertical_motion=0;m.update=sim::MotionUpdate::airborne_fall;
            r=sim::step_p1_session(scene,bank,s,config,{});
            check(r.actor.handler_entries==2 && r.actor.landings==1 && r.actor.settle_calls==2 && s.invocations==7);
            check(m.update==(right ? sim::MotionUpdate::idle_left : sim::MotionUpdate::idle_right));
            check(s.tracking.position.x==204 && s.tracking.position.y==115);
            // Late service failure must roll back control and ordinal too.
            a.service=sim::ActorService::unsupported;const auto before=fields(s);
            rejects([&]{sim::step_p1_session(scene,bank,s,config,{});});check(fields(s)==before);
            a.service=sim::ActorService::return_only;
            for (auto unsupported:{sim::ThreeButtonPad{true},sim::ThreeButtonPad{false,true},sim::ThreeButtonPad{false,false,false,false,false,false,false,true}}) {
                const auto previous=fields(s);rejects([&]{sim::step_p1_session(scene,bank,s,config,unsupported);});check(fields(s)==previous);
            }
            // Reversal allocation and failed terrain work stay explicit.
            m.update=sim::MotionUpdate::fast_right;m.horizontal_speed=160;pad={};pad.left=true;
            auto previous=fields(s);rejects([&]{sim::step_p1_session(scene,bank,s,config,pad);});check(fields(s)==previous);
            m.update=sim::MotionUpdate::ground_right;pad={};pad.b=true;config.actor_budget.horizontal=0;
            previous=fields(s);rejects([&]{sim::step_p1_session(scene,bank,s,config,pad);});check(fields(s)==previous);config.actor_budget={};
        }
        // Presentation can choose the handler that executes in this invocation.
        sim::P1SessionState s;s.actor.motion.position={200,109};s.actor.motion.presentation={0x87,{542,542,551},1,3};
        s.actor.motion.update=sim::MotionUpdate::return_only;s.actor.presentation_target=542;
        s.actor.callback=sim::PresentationCallback::enter_airborne;s.actor.service=sim::ActorService::return_only;
        auto r=sim::step_p1_session(scene,bank,s,config,{});
        check(r.actor.handler_entries==2 && r.actor.landings==1 && s.actor.motion.update==sim::MotionUpdate::idle_left);
        // Inactive tracking wraps; invocation limits include inactive calls.
        s.actor.motion.presentation.mode=0;s.actor.motion.position={65534,65532};
        sim::step_p1_session(scene,bank,s,config,{});check(s.tracking.position.x==2 && s.tracking.position.y==2);
        s.tracking.selector=65535;sim::step_p1_session(scene,bank,s,config,{});check(s.tracking.position.x==0xff80);
        config.max_invocations=s.invocations;auto before=fields(s);
        rejects([&]{sim::step_p1_session(scene,bank,s,config,{});});check(fields(s)==before);
        // Banner precedes terrain above the map, where queries retain scratch;
        // a failed service after that phase must still roll everything back.
        s={};config={};config.banner=sim::LevelBannerConfig{sim::Difficulty::wizard,2,6};
        s.actor.motion.presentation.mode=0;s.actor.motion.position={200,100};s.scratch={77,99};
        r=sim::step_p1_session(scene,bank,s,config,{});
        check(r.banner && r.banner->label==2 && r.banner->number->value==3 && s.scratch.x==77 && s.scratch.y==6);
        s.actor.motion.presentation.mode=128;s.actor.motion.update=sim::MotionUpdate::idle_right;
        s.actor.service=sim::ActorService::unsupported;s.scratch.y=123;before=fields(s);
        rejects([&]{sim::step_p1_session(scene,bank,s,config,{});});check(fields(s)==before);
        s.actor.service=sim::ActorService::return_only;
        r=sim::step_p1_session(scene,bank,s,config,{});
        check(s.scratch.x==77 && s.scratch.y==6 && r.banner->destination==0xe300);
        s.invocations=std::numeric_limits<std::uint64_t>::max();config.max_invocations=s.invocations;before=fields(s);
        rejects([&]{sim::step_p1_session(scene,bank,s,config,{});});check(fields(s)==before);
        // A carried 1345A timer runs once per call and rolls back with a failed call.
        s={};config={};s.actor.motion.presentation.mode=0;s.transition=sim::TransitionState{0xffff,1,1,12};
        sim::step_p1_session(scene,bank,s,config,{});check(s.transition->countdown==0 && s.transition->level==12 && !s.transition->dirty);
        sim::step_p1_session(scene,bank,s,config,{});check(s.transition->level==14 && s.transition->countdown==1 && s.transition->dirty==0xffff);
        s.actor.motion.presentation.mode=128;s.actor.motion.update=sim::MotionUpdate::idle_right;s.actor.service=sim::ActorService::unsupported;
        rejects([&]{sim::step_p1_session(scene,bank,s,config,{});});check(s.transition->countdown==1 && s.transition->direction==0xffff);
        for (bool right:{false,true}) {
            s={};config={};config.banner=sim::LevelBannerConfig{sim::Difficulty::apprentice,0,6};
            s.actor.motion.position={200,109};s.actor.motion.presentation.mode=128;
            s.actor.motion.update=right ? sim::MotionUpdate::fast_right : sim::MotionUpdate::fast_left;
            s.actor.motion.horizontal_speed=right ? 160 : 65376;s.actor.service=sim::ActorService::return_only;
            s.effects.emplace(1);s.scratch={10,20};sim::ThreeButtonPad reverse;reverse.left=right;reverse.right=!right;
            config.effect_budget=0;before=fields(s);
            rejects([&]{sim::step_p1_session(scene,bank,s,config,reverse);});
            check(fields(s)==before && s.effects->available()==1);
            config.effect_budget=1;r=sim::step_p1_session(scene,bank,s,config,reverse);
            check(r.actor.spawned_effects.size()==1 && r.effects.size()==1 && s.effects->available()==0);
            const auto id=r.actor.spawned_effects[0];check(id.generation==1 && r.effects[0].id==id);
            check(r.effects[0].state.position.x==std::uint16_t(s.actor.motion.position.x+(right ? 22 : -6)));
            check(r.effects[0].state.position.y==(right ? 124 : 125) && r.effects[0].state.presentation.counter==1);
            // Empty input keeps native actor and effect alive without external state feeds.
            for (unsigned i=1;i<12;++i) {
                r=sim::step_p1_session(scene,bank,s,config,{});
                check(r.effects.size()==1 && r.effects[0].released==(i==11));
                check(r.effects[0].state.position.y==(right ? 124 : 125));
            }
            check(s.effects->available()==1 && s.effects->at(id).presentation.mode==0);
            r=sim::step_p1_session(scene,bank,s,config,{});check(r.effects.empty());
            // Effect-owner rejection occurs after the actor has run, yet rolls it back.
            auto bad=s.effects->spawn({2},{20,30},sim::ReversalSide::from_right);before=fields(s);
            rejects([&]{sim::step_p1_session(scene,bank,s,config,{});});
            check(fields(s)==before && s.effects->at(bad).presentation.counter==2 && s.effects->available()==0);
        }
        std::cout<<"physical input, retained sessions, reversal phase/lifetime and transactional failures passed\n";
    } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
