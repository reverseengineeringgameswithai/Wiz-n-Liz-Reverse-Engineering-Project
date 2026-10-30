#include "sim/trail.hpp"
#include <iostream>
#include <tuple>
namespace {
using namespace wiz;
void check(bool ok){if(!ok)throw std::runtime_error("trail check failed");}
template<class F>void rejects(F f){try{f();}catch(const assets::BankError&){return;}throw std::runtime_error("trail accepted unsupported path");}
auto fields(const sim::TrailEmitter& e,const sim::TrailRandom& r) {
    std::array<std::uint16_t,10> h{};for(std::size_t i=0;i<5;++i){h[2*i]=e.history[i].x;h[2*i+1]=e.history[i].y;}
    const auto& p=e.presentation;
    return std::tuple{e.position.x,e.position.y,e.countdown,h,p.mode,p.words,p.counter,p.reload,e.target,e.flags,e.owner.value,r.state,r.mirror};
}
sim::TrailEmitter emitter() {
    return {{100,200},0,{{{10,20},{30,40},{50,60},{70,80},{90,100}}},{0x81,{638,638,643},5,5},0,0x800,{1}};
}
}
int main(){
    try {
        sim::TrailRandom rng{1,0xdeadbeef};check(sim::next_trail_random(rng)==32768 && rng.state==65536 && rng.mirror==65536);
        check(sim::next_trail_random(rng)==129 && rng.state==258 && rng.mirror==258);
        rng={0,0xffffffff};check(sim::next_trail_random(rng)==0 && rng.state==0 && rng.mirror==0);
        auto e=emitter();rng={1,0xdeadbeef};auto p=sim::step_trail_emitter(e,rng,{1},{65534,7},true);
        check(p && p->position.x==96 && p->position.y==197 && p->presentation.counter==2 && p->presentation.reload==2);
        check(e.position.x==90 && e.position.y==100 && e.countdown==3 && e.history[0].x==2 && e.history[0].y==7);
        check(e.history[1].x==10 && e.history[4].x==70 && rng.state==258 && e.presentation.counter==5);
        for(unsigned i=0;i<3;++i)check(!sim::step_trail_emitter(e,rng,{1},{65534,7},false));
        // Both coordinates participate in the equality test; delay resets even
        // when the two positions agree and no allocation/RNG call is made.
        e=emitter();e.history[1]=e.history[0];rng={1,99};p=sim::step_trail_emitter(e,rng,{1},{0,0},false);
        check(!p && e.countdown==3 && rng.state==1 && rng.mirror==99);
        e=emitter();e.history[1].x=e.history[0].x;rng={0,1};check(sim::step_trail_emitter(e,rng,{1},{0,0},true).has_value());
        for(auto count:{0U,0x8001U,0xffffU}){e=emitter();e.countdown=static_cast<std::uint16_t>(count);rng={0,0};check(sim::step_trail_emitter(e,rng,{1},{0,0},true).has_value() && e.countdown==3);}
        e=emitter();e.countdown=0x8000;check(!sim::step_trail_emitter(e,rng,{1},{0,0},false) && e.countdown==0x7fff);
        e=emitter();e.position={0,65535};rng={0,7};p=sim::step_trail_emitter(e,rng,{1},{0,0},true);
        check(p->position.x==65532 && p->position.y==65531);
        for(bool scheduled:{false,true}) {
            e=emitter();rng={1,99};auto before=fields(e,rng);
            rejects([&]{sim::step_trail_emitter(e,rng,{1},{0,0},false,scheduled);});check(fields(e,rng)==before);
            rejects([&]{sim::step_trail_emitter(e,rng,{2},{0,0},true,scheduled);});check(fields(e,rng)==before);
        }
        e=emitter();e.presentation={0x85,{7,0,10},1,2};e.target=7;auto before=fields(e,rng);
        rejects([&]{sim::step_trail_emitter(e,rng,{1},{0,0},true,true);});check(fields(e,rng)==before);
        e.presentation.mode=0;before=fields(e,rng);check(!sim::step_trail_emitter(e,rng,{}, {},false,true) && fields(e,rng)==before);
        e=emitter();e.countdown=2;sim::step_trail_emitter(e,rng,{1},{0,0},true,true);check(e.presentation.counter==4 && e.countdown==1);
        auto particle=sim::make_trail_particle({0,65535},true);check(particle.presentation.counter==3 && particle.flags==0);
        rejects([&]{sim::make_trail_particle({},false);});
        for(unsigned i=1;i<=24;++i)check(sim::step_trail_particle(particle)==(i==24));
        check(particle.presentation.mode==0 && particle.presentation.words[0]==227 && particle.position.y==65535);
        check(!sim::step_trail_particle(particle));
        particle=*p;for(unsigned i=1;i<=16;++i)check(sim::step_trail_particle(particle)==(i==16));
        check(particle.position.x==65532 && particle.presentation.mode==0);
        std::cout<<"trail delay/history, random consumption, wrap, lifetime and transactional failures passed\n";
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
