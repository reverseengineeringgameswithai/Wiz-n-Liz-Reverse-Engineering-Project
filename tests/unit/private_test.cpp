#include "sim/mixed_pool.hpp"
#include <iostream>
#include <optional>
#include <source_location>
#include <string>
#include <tuple>
namespace {
using namespace wiz;
void check(bool ok,std::source_location at=std::source_location::current()){if(!ok)throw std::runtime_error("private check failed at line "+std::to_string(at.line()));}
template<class F>void rejects(F f){try{f();}catch(const assets::BankError&){return;}throw std::runtime_error("private unsupported path accepted");}
auto fields(const sim::PrivateObject& o){return std::tuple{o.update,o.position.x,o.position.y,o.flags,o.presentation.mode,o.presentation.words,o.presentation.counter,o.presentation.reload,o.target,o.countdown,o.control.value};}
sim::PrivateObject seed(){return {sim::PrivateUpdate::rising,{99,262},0xbeef,{0x81,{7,3,11},2,2},100,8,{123}};}
}
int main(){try{
    sim::PrivateGlobals rising{0x10000,0,0};auto p=seed();
    for(unsigned n=0;n<144;++n)sim::step_private_object(p,rising,true);
    check(p.position.x==99 && p.position.y==246 && p.countdown==8 && p.control.value==123 && p.flags==0xbeef);
    auto frozen=p;for(unsigned n=0;n<256;++n)sim::step_private_object(p,rising);
    check(fields(p)==fields(frozen));sim::step_private_object(p,{});check(p.position.y==262 && p.countdown==8);
    for(auto [timer,y,after]:{std::tuple{0,65535,8},std::tuple{1,0,0},std::tuple{32768,0,32767},std::tuple{32769,65535,8}}){
        p=seed();p.position.y=0;p.countdown=static_cast<std::uint16_t>(timer);sim::step_private_object(p,rising);
        check(p.position.y==y && p.countdown==after);
    }
    p=seed();p.update=sim::PrivateUpdate::gated_visibility;sim::step_private_object(p,{0,0x8000,0});
    check(p.flags==0x2000 && p.position.x==99 && p.position.y==262 && p.countdown==8);
    sim::step_private_object(p,{0,0,0x100});check(p.position.x==0xff80 && p.position.y==0xff80);
    frozen=p;sim::step_private_object(p,{});check(fields(p)==fields(frozen));
    // Inactive skips all work; callback failure rolls back preceding animation.
    p=seed();p.presentation.mode=0x05;p.presentation.counter=1;p.target=7;frozen=p;
    sim::step_private_object(p,{},true);check(fields(p)==fields(frozen));
    p.presentation.mode=0x85;frozen=p;rejects([&]{sim::step_private_object(p,{},true);});check(fields(p)==fields(frozen));
    p=seed();p.update=static_cast<sim::PrivateUpdate>(99);frozen=p;
    rejects([&]{sim::step_private_object(p,{},true);});check(fields(p)==fields(frozen));
    // A private object succeeds before a later callback/budget failure: both
    // private mutations and earlier free-stack releases roll back together.
    auto dying=sim::make_trail_particle({},true);dying.presentation.counter=1;dying.presentation.words[0]=dying.target;
    p=seed();p.presentation.mode=0x85;p.presentation.counter=1;p.target=7;
    sim::MixedPool pool({dying,seed(),p},{});sim::TrailRandom rng{123,456};
    rejects([&]{pool.step({1},{},rng,3,&rising);});
    check(pool.available()==0 && rng.state==123 && rng.mirror==456 && fields(std::get<sim::PrivateObject>(pool.slots()[1].object))==fields(seed()));
    rejects([&]{pool.step({1},{},rng,3);});check(pool.available()==0);
    rejects([&]{pool.step({1},{},rng,2,&rising);});check(pool.available()==0);
    sim::MixedPool good({seed()},{});auto ev=good.step({},{},rng,1,&rising);
    check(ev.size()==1 && ev[0].kind==sim::PoolEventKind::update && ev[0].id==sim::EffectId{0,1});
    check(std::get<sim::PrivateObject>(ev[0].object).countdown==7 && good.available()==0);
    // 7C26: two LIFO pops typed over verified inheritance; no anchor or flags.
    using Inherited=std::optional<sim::InheritedObjectFields>;
    const sim::InheritedObjectFields known{901,5,{2}};
    sim::MixedPool pair({sim::ExternalReservation{},std::monostate{},std::monostate{}},{2,1},{Inherited{},known,Inherited{sim::InheritedObjectFields{}}});
    const auto ids=pair.initialize_visibility_pair();check(ids.first==sim::EffectId{1,1} && ids.second==sim::EffectId{2,1} && pair.available()==0);
    const auto& first=std::get<sim::PrivateObject>(pair.at(ids.first).object);const auto& second=std::get<sim::PrivateObject>(pair.at(ids.second).object);
    check(fields(first)==fields(sim::PrivateObject{sim::PrivateUpdate::gated_visibility,{287,152},0,{0x81,{892,892,901},5,5},901,5,{2}}));
    check(fields(second)==fields(sim::PrivateObject{sim::PrivateUpdate::gated_visibility,{287,184},0,{0x81,{902,902,911},5,5},0,0,{0}}));
    // Mode 81 never tests the inherited 901 target; zero gates leave state alone.
    sim::PrivateGlobals closed{};auto copy=pair;for(unsigned n=0;n<120;++n)copy.step({},{},rng,3,&closed);
    check(std::get<sim::PrivateObject>(copy.slots()[1].object).target==901 && std::get<sim::PrivateObject>(copy.slots()[1].object).flags==0);
    rejects([&]{copy.step({},{},rng,3);});
    for(auto [free,inherited]:{std::pair{std::vector<std::size_t>{1},std::vector<Inherited>{Inherited{},known,Inherited{}}},
            std::pair{std::vector<std::size_t>{2,1},std::vector<Inherited>{Inherited{},Inherited{},known}},
            std::pair{std::vector<std::size_t>{2,1},std::vector<Inherited>{Inherited{},known,Inherited{}}}}) {
        std::vector<sim::PoolObject> objects{sim::ExternalReservation{},sim::ExternalReservation{},sim::ExternalReservation{}};
        for(auto i:free)objects[i]=std::monostate{};
        sim::MixedPool bad(objects,free,inherited);const auto before=bad.slots();rejects([&]{bad.initialize_visibility_pair();});
        check(bad.free_stack()==free);
        for(std::size_t i=0;i<before.size();++i)check(bad.slots()[i].generation==before[i].generation && bad.slots()[i].object.index()==before[i].object.index());
    }
    // 7772: caller control stored in both, countdown cleared, second at first X+32.
    sim::MixedPool risers({sim::ExternalReservation{},std::monostate{},std::monostate{}},{1,2},{Inherited{},Inherited{sim::InheritedObjectFields{3,77,{9}}},known});
    const auto rid=risers.initialize_rising_pair({1});check(rid.first==sim::EffectId{2,1} && rid.second==sim::EffectId{1,1});
    check(fields(std::get<sim::PrivateObject>(risers.at(rid.first).object))==fields(sim::PrivateObject{sim::PrivateUpdate::rising,{158,262},0,{0x81,{922,922,927},5,5},901,0,{1}}));
    check(fields(std::get<sim::PrivateObject>(risers.at(rid.second).object))==fields(sim::PrivateObject{sim::PrivateUpdate::rising,{190,262},0,{0x81,{928,928,933},5,5},3,0,{1}}));
    const auto wrapped=sim::make_rising_pair_member(sim::PairMember::second,{},{1},{65530,9});check(wrapped.position.x==26 && wrapped.position.y==9);
    // A closed rise gate pins Y=0106 and reloads countdown 8 on the next update.
    auto stepped=risers;sim::PrivateGlobals none{};stepped.step({},{},rng,3,&none);
    check(std::get<sim::PrivateObject>(stepped.at(rid.first).object).countdown==8 && std::get<sim::PrivateObject>(stepped.at(rid.second).object).position.y==262);
    for(auto free:{std::vector<std::size_t>{2},std::vector<std::size_t>{}}) {
        std::vector<sim::PoolObject> objects{sim::ExternalReservation{},sim::ExternalReservation{},sim::ExternalReservation{}};
        for(auto i:free)objects[i]=std::monostate{};
        std::vector<Inherited> inherited(3);for(auto i:free)inherited[i]=known;
        sim::MixedPool bad(objects,free,inherited);const auto before=bad.slots();rejects([&]{bad.initialize_rising_pair({1});});
        check(bad.free_stack()==free && bad.slots()[2].generation==before[2].generation);
    }
    std::cout<<"private gates, wrap, freeze, retained sequence, presentation, visibility/rising pairs and shared pool rollback passed\n";
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
